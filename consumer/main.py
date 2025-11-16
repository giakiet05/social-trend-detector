"""
TikTok Trend Consumer - Spark Streaming Application
"""

import logging
import json
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StructType, StructField, StringType, LongType, ArrayType, FloatType
import numpy as np

from config.settings import settings
from enrichment.openai_client import OpenAIClient
from processing.clusterer import TrendClusterer
from storage.mongo_client import MongoDBClient
from models import Trend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TikTokConsumer:
    """Spark Streaming Consumer for TikTok trend detection."""

    def __init__(self):
        """Initialize Spark session and clients."""
        self.spark = self._create_spark_session()
        self.openai_client = OpenAIClient()
        self.clusterer = TrendClusterer()
        self.mongo_client = MongoDBClient()

        logger.info("✅ TikTokConsumer initialized")

    def _create_spark_session(self) -> SparkSession:
        """Create Spark session with Kafka support."""
        spark = SparkSession.builder \
            .appName(settings.spark.APP_NAME) \
            .master(settings.spark.MASTER) \
            .config("spark.jars.packages", settings.kafka.SPARK_KAFKA_PACKAGE) \
            .config("spark.sql.streaming.checkpointLocation", settings.spark.CHECKPOINT_DIR) \
            .getOrCreate()

        spark.sparkContext.setLogLevel(settings.spark.LOG_LEVEL)
        logger.info(f"✅ Spark session created: {settings.spark.APP_NAME}")
        return spark

    def _get_kafka_stream(self):
        """Read streaming data from Kafka."""
        # Define schema for TikTok video JSON
        schema = StructType([
            StructField("video_id", StringType(), True),
            StructField("text", StringType(), True),
            StructField("hashtags", ArrayType(StringType()), True),
            StructField("likes", LongType(), True),
            StructField("comments", LongType(), True),
            StructField("shares", LongType(), True),
            StructField("views", LongType(), True),
            StructField("author", StringType(), True),
            StructField("timestamp", StringType(), True),
        ])

        # Read from Kafka
        kafka_df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", settings.kafka.BOOTSTRAP_SERVERS) \
            .option("subscribe", settings.kafka.TOPIC) \
            .option("startingOffsets", settings.kafka.STARTING_OFFSETS) \
            .load()

        # Parse JSON from Kafka value
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")

        logger.info(f"✅ Kafka stream configured: topic={settings.kafka.TOPIC}")
        return parsed_df

    def _process_batch(self, batch_df, batch_id):
        """
        Process each micro-batch from Kafka.

        Pipeline:
        1. Clean & validate
        2. Embed text → vectors
        3. Cluster with DBSCAN
        4. LLM analyze each cluster
        5. Save trends to MongoDB
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 Processing batch {batch_id}")
        logger.info(f"{'='*60}")

        # Check if batch is empty
        count = batch_df.count()
        if count == 0:
            logger.warning("⚠️  Empty batch, skipping")
            return

        logger.info(f"📊 Batch size: {count} videos")

        try:
            # Step 1: Clean & validate (filter out null text)
            clean_df = batch_df.filter(col("text").isNotNull())
            clean_count = clean_df.count()
            logger.info(f"✅ Step 1: Cleaned {clean_count}/{count} videos")

            if clean_count == 0:
                logger.warning("⚠️  No valid videos after cleaning")
                return

            # Step 2: Collect to Python (small batch, OK to collect)
            videos = [row.asDict() for row in clean_df.collect()]
            logger.info(f"✅ Step 2: Collected {len(videos)} videos to Python")

            # Step 3: Embed text using OpenAI
            texts = [v.get('text', '') for v in videos]
            embeddings = self.openai_client.embed_texts(texts)
            embeddings_array = np.array(embeddings)
            logger.info(f"✅ Step 3: Embedded {len(embeddings)} texts → vectors shape {embeddings_array.shape}")

            # Step 4: Cluster with DBSCAN
            labels = self.clusterer.cluster(embeddings_array)
            clusters = self.clusterer.group_by_cluster(videos, labels)
            logger.info(f"✅ Step 4: Found {len(clusters)} clusters")

            if len(clusters) == 0:
                logger.warning("⚠️  No clusters found (all noise)")
                return

            # Step 5: Analyze each cluster with LLM
            trends = []
            for cluster_id, cluster_videos in clusters.items():
                logger.info(f"   Analyzing cluster {cluster_id}: {len(cluster_videos)} videos")

                # LLM analysis
                analysis = self.openai_client.analyze_cluster(cluster_videos)

                # Calculate stats (handle None values)
                total_views = sum(v.get('views') or 0 for v in cluster_videos)
                total_likes = sum(v.get('likes') or 0 for v in cluster_videos)

                # Sample videos (top 5 by views, handle None)
                sorted_videos = sorted(cluster_videos, key=lambda v: v.get('views') or 0, reverse=True)
                sample_videos = sorted_videos[:settings.processing.SAMPLE_VIDEOS_COUNT]

                # Create Trend object
                trend = Trend(
                    timestamp=datetime.utcnow(),
                    topic=analysis['topic'],
                    summary=analysis['summary'],
                    sentiment=analysis['sentiment'],
                    keywords=analysis['keywords'],
                    video_count=len(cluster_videos),
                    total_views=total_views,
                    total_likes=total_likes,
                    sample_videos=sample_videos
                )
                trends.append(trend)

                logger.info(f"      → Topic: {trend.topic}")
                logger.info(f"      → Sentiment: {trend.sentiment}")
                logger.info(f"      → Videos: {trend.video_count}, Views: {total_views:,}")

            logger.info(f"✅ Step 5: Analyzed {len(trends)} trends")

            # Step 6: Save to MongoDB
            self.mongo_client.save_trends(trends)
            logger.info(f"✅ Step 6: Saved {len(trends)} trends to MongoDB")

            logger.info(f"{'='*60}")
            logger.info(f"✅ Batch {batch_id} completed successfully")
            logger.info(f"{'='*60}\n")

        except Exception as e:
            logger.error(f"❌ Batch {batch_id} failed: {e}", exc_info=True)
            # Don't raise - continue processing next batch

    def run(self):
        """Start Spark Streaming consumer."""
        logger.info("\n" + "="*60)
        logger.info("🚀 STARTING TIKTOK TREND CONSUMER")
        logger.info("="*60)

        try:
            # Get Kafka stream
            stream_df = self._get_kafka_stream()

            # Start streaming query with foreachBatch
            query = stream_df.writeStream \
                .foreachBatch(self._process_batch) \
                .outputMode("append") \
                .option("checkpointLocation", settings.spark.CHECKPOINT_DIR) \
                .trigger(processingTime=settings.processing.BATCH_INTERVAL) \
                .start()

            logger.info(f"✅ Streaming query started")
            logger.info(f"   Trigger interval: {settings.processing.BATCH_INTERVAL}")
            logger.info(f"   Checkpoint: {settings.spark.CHECKPOINT_DIR}")
            logger.info("   Waiting for data from Kafka...")
            logger.info("   Press Ctrl+C to stop\n")

            # Wait for termination
            query.awaitTermination()

        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping consumer (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Consumer failed: {e}", exc_info=True)
        finally:
            self.spark.stop()
            self.mongo_client.close()
            logger.info("👋 Consumer stopped")


if __name__ == "__main__":
    consumer = TikTokConsumer()
    consumer.run()