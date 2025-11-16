"""
Consumer configuration settings.
Load from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")


class SparkSettings:
    """Spark configuration."""
    APP_NAME = "TikTokTrendConsumer"
    MASTER = "local[*]"  # Use all cores
    CHECKPOINT_DIR = "./consumer/checkpoints"
    LOG_LEVEL = "WARN"  # Reduce Spark logs


class KafkaSettings:
    """Kafka configuration."""
    BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    TOPIC = os.getenv("KAFKA_TOPIC", "tiktok-raw-data")
    STARTING_OFFSETS = "earliest"  # Read from beginning for testing

    # Spark Kafka packages
    SPARK_KAFKA_PACKAGE = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"


class OpenAISettings:
    """OpenAI configuration."""
    API_KEY = os.getenv("OPENAI_API_KEY")

    # Models
    EMBEDDING_MODEL = "text-embedding-3-small"
    LLM_MODEL = "gpt-4.1-nano"

    # Params
    EMBEDDING_BATCH_SIZE = 100  # Max texts per API call
    MAX_TOKENS = 500  # For LLM response


class DBSCANSettings:
    """DBSCAN clustering configuration."""
    EPS = 0.3  # Distance threshold (tune this)
    MIN_SAMPLES = 3  # Min videos for a trend
    METRIC = "cosine"


class MongoDBSettings:
    """MongoDB configuration."""
    CONNECTION_STRING = "mongodb://admin:password@localhost:27017/?authSource=admin"
    DATABASE = "tiktok_trends"
    COLLECTION = "trends"


class ProcessingSettings:
    """Processing configuration."""
    BATCH_INTERVAL = "10 seconds"  # Trigger interval
    MAX_OFFSETS_PER_TRIGGER = 1000  # Max messages per batch

    # Trend analysis
    MIN_VIDEOS_FOR_TREND = 3  # Same as DBSCAN min_samples
    SAMPLE_VIDEOS_COUNT = 5  # Number of sample videos to save


class Settings:
    """Main settings container."""
    spark = SparkSettings()
    kafka = KafkaSettings()
    openai = OpenAISettings()
    dbscan = DBSCANSettings()
    mongodb = MongoDBSettings()
    processing = ProcessingSettings()


# Global settings instance
settings = Settings()
