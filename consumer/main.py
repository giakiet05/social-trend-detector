"""
TikTok Trend Consumer - Spark Streaming Application
"""

import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json

from consumer.config.settings import settings
from consumer.models.spark_schemas import TIKTOK_VIDEO_SCHEMA
from consumer.enrichment.openai_client import OpenAIClient
from consumer.processing.clusterer import TrendClusterer
from consumer.processing.pipeline import TrendDetectionPipeline
from consumer.storage.mongo_client import MongoDBClient

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

        # Initialize clients
        self.openai_client = OpenAIClient()
        self.clusterer = TrendClusterer()
        self.mongo_client = MongoDBClient()

        # Initialize pipeline
        self.pipeline = TrendDetectionPipeline(
            openai_client=self.openai_client,
            mongo_client=self.mongo_client,
            clusterer=self.clusterer
        )

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
        # Read from Kafka
        kafka_df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", settings.kafka.BOOTSTRAP_SERVERS) \
            .option("subscribe", settings.kafka.TOPIC) \
            .option("startingOffsets", settings.kafka.STARTING_OFFSETS) \
            .option("failOnDataLoss", "true") \
            .load()

        # Parse JSON from Kafka value using updated schema (14 fields)
        parsed_df = kafka_df.select(
            from_json(col("value").cast("string"), TIKTOK_VIDEO_SCHEMA).alias("data")
        ).select("data.*")

        logger.info(f"✅ Kafka stream configured: topic={settings.kafka.TOPIC}")
        return parsed_df

    def _process_batch(self, batch_df, batch_id):
        """
        Process each micro-batch from Kafka using Pipeline.

        Args:
            batch_df: Spark DataFrame for this batch
            batch_id: Batch ID number
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 BATCH {batch_id}")
        logger.info(f"{'='*60}")

        # Check if batch is empty
        count = batch_df.count()
        if count == 0:
            logger.warning("⚠️  Empty batch, skipping")
            return

        logger.info(f"📊 Batch size: {count} videos")

        try:
            # Collect to Python (small batch, OK to collect)
            videos = [row.asDict() for row in batch_df.collect()]

            # Run pipeline
            self.pipeline.process(videos)

            logger.info(f"{'='*60}")
            logger.info(f"✅ BATCH {batch_id} COMPLETED")
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