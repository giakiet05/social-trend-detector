"""
Batch Consumer - Process Kafka data in batch mode (not streaming).

This consumer runs once, processes all new messages from Kafka since last checkpoint,
then exits. Designed to be scheduled externally (e.g., by APScheduler).
"""

import logging
import json
from pathlib import Path
from typing import List, Dict
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json

from consumer.config.settings import settings
from consumer.models.spark_schemas import TIKTOK_VIDEO_SCHEMA, NEWS_ARTICLE_SCHEMA, YOUTUBE_VIDEO_SCHEMA
from consumer.enrichment.llm_factory import create_embedding_client, create_llm_client
from consumer.processing.clusterer import TrendClusterer
from consumer.processing.pipeline import TrendDetectionPipeline
from consumer.storage.mongo_client import MongoDBClient
from common.models import KafkaMessage, TikTokVideo, NewsArticle, YouTubeVideo

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manage Kafka offsets for batch processing."""

    def __init__(self, checkpoint_dir: str = "consumer/checkpoints"):
        import os

        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "batch_offsets.json"

        # Reset checkpoints if env var is set (for testing)
        if os.getenv("RESET_CHECKPOINTS", "false").lower() == "true":
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                logger.info("Checkpoint reset: starting from earliest")

    def get_starting_offsets(self, topic: str) -> str:
        """
        Get starting offset for a topic.

        Returns:
            Offset string in format: {"topic":{"0":123}}
            If no checkpoint exists, returns "earliest"
        """
        if not self.checkpoint_file.exists():
            logger.info(f"No checkpoint found, starting from 'earliest'")
            return "earliest"

        try:
            with open(self.checkpoint_file, "r") as f:
                offsets = json.load(f)

            if topic in offsets:
                logger.info(f"Resuming from checkpoint: {offsets[topic]}")
                return json.dumps({topic: offsets[topic]})
            else:
                logger.info(f"No checkpoint for topic '{topic}', starting from 'earliest'")
                return "earliest"

        except Exception as e:
            logger.error(f"Failed to read checkpoint: {e}")
            return "earliest"

    def save_ending_offsets(self, topic: str, offsets: Dict[str, int]):
        """
        Save ending offsets for a topic.

        Args:
            topic: Kafka topic name
            offsets: Dict mapping partition -> offset (e.g., {"0": 123, "1": 456})
        """
        try:
            # Load existing checkpoints
            all_offsets = {}
            if self.checkpoint_file.exists():
                with open(self.checkpoint_file, "r") as f:
                    all_offsets = json.load(f)

            # Update this topic's offsets
            all_offsets[topic] = offsets

            # Save
            with open(self.checkpoint_file, "w") as f:
                json.dump(all_offsets, f, indent=2)

            logger.info(f"Checkpoint saved: {topic} -> {offsets}")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")


class BatchConsumer:
    """
    Batch Consumer for trend detection.

    Reads all new messages from Kafka since last checkpoint,
    processes them through the pipeline, then exits.
    """

    def __init__(self):
        """Initialize Spark session and clients."""
        self.spark = self._create_spark_session()
        self.checkpoint_manager = CheckpointManager()

        # Initialize clients (separate embedding & LLM providers)
        self.embedding_client = create_embedding_client()
        self.llm_client = create_llm_client()
        self.clusterer = TrendClusterer()
        self.mongo_client = MongoDBClient()

        # Initialize pipeline
        self.pipeline = TrendDetectionPipeline(
            embedding_client=self.embedding_client,
            llm_client=self.llm_client,
            mongo_client=self.mongo_client,
            clusterer=self.clusterer
        )

        logger.info("BatchConsumer initialized")

    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with Kafka support."""
        import os

        # Use pre-downloaded JARs if available (Docker), otherwise download
        jars_dir = "/opt/spark/jars"
        if os.path.exists(jars_dir):
            jar_files = ",".join([
                f"{jars_dir}/spark-sql-kafka-0-10_2.12-3.5.0.jar",
                f"{jars_dir}/spark-token-provider-kafka-0-10_2.12-3.5.0.jar",
                f"{jars_dir}/kafka-clients-3.4.1.jar",
                f"{jars_dir}/commons-pool2-2.11.1.jar"
            ])
            spark = SparkSession.builder \
                .appName("SocialTrendBatchConsumer") \
                .master(settings.spark.MASTER) \
                .config("spark.jars", jar_files) \
                .getOrCreate()
        else:
            # Fallback to downloading (local development)
            spark = SparkSession.builder \
                .appName("SocialTrendBatchConsumer") \
                .master(settings.spark.MASTER) \
                .config("spark.jars.packages", settings.kafka.SPARK_KAFKA_PACKAGE) \
                .getOrCreate()

        spark.sparkContext.setLogLevel(settings.spark.LOG_LEVEL)
        logger.info(f"Spark session created")
        return spark

    def _read_kafka_batch(self, topic: str, schema) -> tuple[List[Dict], Dict[int, int]]:
        """
        Read batch of messages from Kafka topic.

        Args:
            topic: Kafka topic name
            schema: Spark schema for parsing JSON

        Returns:
            Tuple of (items, partition_offsets)
            - items: List of message dictionaries
            - partition_offsets: Dict mapping partition -> next offset to read
        """
        # Get starting offset from checkpoint
        starting_offsets = self.checkpoint_manager.get_starting_offsets(topic)

        # Read batch from Kafka
        logger.info(f"Reading from Kafka topic: {topic}")
        kafka_df = self.spark.read \
            .format("kafka") \
            .option("kafka.bootstrap.servers", settings.kafka.BOOTSTRAP_SERVERS) \
            .option("subscribe", topic) \
            .option("startingOffsets", starting_offsets) \
            .option("endingOffsets", "latest") \
            .load()

        count = kafka_df.count()
        logger.info(f"Found {count} messages in topic '{topic}'")

        if count == 0:
            return [], {}

        # Parse JSON with provided schema
        parsed_df = kafka_df.select(
            col("partition"),
            col("offset"),
            from_json(col("value").cast("string"), schema).alias("data")
        )

        # Collect to Python
        rows = parsed_df.collect()

        # Extract data and track offsets
        items = []
        partition_offsets = {}

        for row in rows:
            partition = int(row["partition"])  # Ensure int type
            offset = int(row["offset"])  # Ensure int type

            # Parse Spark Row to dict
            kafka_msg_dict = row["data"].asDict(recursive=True) if row["data"] else None

            if kafka_msg_dict:
                # Deserialize to KafkaMessage object (typed)
                kafka_msg = KafkaMessage.from_dict(kafka_msg_dict)

                # Extract nested data (source-specific dict)
                # Keep as dict for NormalizationStage to handle
                if kafka_msg.data:
                    items.append(kafka_msg.data)

            # Track max offset per partition
            if partition not in partition_offsets or offset > partition_offsets[partition]:
                partition_offsets[partition] = offset + 1  # Next offset to read

        return items, partition_offsets

    def _read_all_topics(self) -> tuple[List[Dict], Dict[str, Dict[int, int]]]:
        """
        Read from all 3 Kafka topics (multi-source).

        Returns:
            Tuple of (all_items, all_offsets)
            - all_items: List of mixed items (TikTok + News + YouTube)
            - all_offsets: Dict mapping topic -> partition_offsets
        """
        logger.info("Reading from all Kafka topics...")

        all_items = []
        all_offsets = {}

        # Read TikTok (skip if topic doesn't exist)
        try:
            tiktok_items, tiktok_offsets = self._read_kafka_batch(settings.kafka.TIKTOK_TOPIC, TIKTOK_VIDEO_SCHEMA)
            logger.info(f"   TikTok: {len(tiktok_items)} items")
            all_items.extend(tiktok_items)
            if tiktok_offsets:
                all_offsets[settings.kafka.TIKTOK_TOPIC] = tiktok_offsets
        except Exception as e:
            if "UnknownTopicOrPartitionException" in str(e):
                logger.warning(f"   TikTok: topic not found, skipping")
            else:
                raise

        # Read News (skip if topic doesn't exist)
        try:
            news_items, news_offsets = self._read_kafka_batch(settings.kafka.NEWS_TOPIC, NEWS_ARTICLE_SCHEMA)
            logger.info(f"   News: {len(news_items)} items")
            all_items.extend(news_items)
            if news_offsets:
                all_offsets[settings.kafka.NEWS_TOPIC] = news_offsets
        except Exception as e:
            if "UnknownTopicOrPartitionException" in str(e):
                logger.warning(f"   News: topic not found, skipping")
            else:
                raise

        # Read YouTube (skip if topic doesn't exist)
        try:
            youtube_items, youtube_offsets = self._read_kafka_batch(settings.kafka.YOUTUBE_TOPIC, YOUTUBE_VIDEO_SCHEMA)
            logger.info(f"   YouTube: {len(youtube_items)} items")
            all_items.extend(youtube_items)
            if youtube_offsets:
                all_offsets[settings.kafka.YOUTUBE_TOPIC] = youtube_offsets
        except Exception as e:
            if "UnknownTopicOrPartitionException" in str(e):
                logger.warning(f"   YouTube: topic not found, skipping")
            else:
                raise

        logger.info(f"Total items from all sources: {len(all_items)}")
        return all_items, all_offsets

    def run_once(self):
        """
        Run batch processing once, then exit.

        Steps:
        1. Read all new messages from Kafka (since last checkpoint)
        2. Check if batch size meets minimum threshold
        3. Process through pipeline
        4. Save checkpoint ONLY if processing succeeded
        5. Exit
        """
        logger.info("\n" + "=" * 70)
        logger.info("BATCH CONSUMER - STARTING")
        logger.info("=" * 70)

        try:
            # Step 1: Read from all Kafka topics (multi-source)
            items, all_offsets = self._read_all_topics()

            if not items:
                logger.warning("No new messages in Kafka, nothing to process")
                return

            logger.info(f"Retrieved {len(items)} items from Kafka")

            # Step 2: Check minimum batch size
            min_batch_size = settings.processing.MIN_BATCH_SIZE
            if len(items) < min_batch_size:
                logger.warning(
                    f"Batch size ({len(items)}) < minimum ({min_batch_size}), skipping processing"
                )
                logger.warning(f"Items will be included in next batch (checkpoint NOT saved)")
                return  # Exit without saving checkpoint

            # Step 3: Process through pipeline
            logger.info(f"Processing {len(items)} items through pipeline...")
            self.pipeline.process(items)

            # Step 4: Save checkpoint ONLY after successful processing
            for topic, offsets in all_offsets.items():
                self.checkpoint_manager.save_ending_offsets(topic, offsets)

            logger.info("Checkpoint saved for all topics")

            logger.info("=" * 70)
            logger.info("BATCH CONSUMER - COMPLETED")
            logger.info(f"   Processed: {len(items)} items")
            logger.info("=" * 70 + "\n")

        except Exception as e:
            logger.error(f"Batch processing failed: {e}", exc_info=True)
            logger.error("Checkpoint NOT saved due to failure")
            raise

        finally:
            # Always cleanup
            self.spark.stop()
            self.mongo_client.close()
            logger.info("Batch consumer stopped")


if __name__ == "__main__":
    consumer = BatchConsumer()
    consumer.run_once()
