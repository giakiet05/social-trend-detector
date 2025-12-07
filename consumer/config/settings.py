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
    STARTING_OFFSETS = "earliest"  # Only read new data (avoid reprocessing)

    # Spark Kafka packages
    SPARK_KAFKA_PACKAGE = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
    # Multiple topics for different sources
    TIKTOK_TOPIC = os.getenv("KAFKA_TIKTOK_TOPIC", "tiktok-raw")
    NEWS_TOPIC = os.getenv("KAFKA_NEWS_TOPIC", "news-raw")
    YOUTUBE_TOPIC = os.getenv("KAFKA_YOUTUBE_TOPIC", "youtube-raw")
    TRENDS_TOPIC = os.getenv("KAFKA_TRENDS_TOPIC", "trends-raw")

class OpenAISettings:
    """OpenAI configuration."""
    API_KEY = os.getenv("OPENAI_API_KEY")

    # Models (customizable via env)
    EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4.1-nano")

    # Params
    EMBEDDING_BATCH_SIZE = 100  # Max texts per API call
    MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))


class GeminiSettings:
    """Gemini configuration."""
    API_KEY = os.getenv("GEMINI_API_KEY")

    # Models (customizable via env)
    EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
    LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")

    # Params (increased to handle thinking tokens + response)
    MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))


class DBSCANSettings:
    """Legacy DBSCAN clustering configuration (deprecated, use HDBSCAN)."""
    EPS = 0.3  # Distance threshold (tune this)
    MIN_SAMPLES = 3  # Min videos for a trend
    METRIC = "cosine"


class HDBSCANSettings:
    """HDBSCAN clustering configuration."""
    MIN_CLUSTER_SIZE = 15         # Minimum size of clusters (relaxed for testing)
    METRIC = "euclidean"          # Distance metric (euclidean works best with embeddings)
    MIN_SAMPLES = None            # Let HDBSCAN auto-determine (None = min_cluster_size)


class MongoDBSettings:
    """MongoDB configuration."""
    CONNECTION_STRING = "mongodb://admin:password@localhost:27017/?authSource=admin"
    DATABASE = "tiktok_trends"
    COLLECTION = "trends"

    # Deduplication  
    SIMILARITY_THRESHOLD = 0.6   # Multi-factor threshold (increased for precision)
    DEDUP_WINDOW_HOURS = 24  # Check trends in last N hours


class ProcessingSettings:
    """Processing configuration."""
    # Batch processing (new)
    MIN_BATCH_SIZE = 40  # Minimum items required to start processing (multi-source)

    MAX_OFFSETS_PER_TRIGGER = 1000  # Max messages per batch

    # Trend analysis
    MIN_CLUSTER_SIZE = 10  # Minimum videos in a cluster to be a valid trend
    SAMPLE_VIDEOS_COUNT = 5  # Number of sample videos to save

    # Noise filtering thresholds (relaxed for testing targeted content)
    MIN_ENGAGEMENT_RATE = 0.001  # 0.1% minimum engagement rate (was 1%) 
    MIN_AUTHOR_FANS = 100  # Minimum author followers (was 500)
    MIN_QUALITY_RATIO = 0.0001  # 0.01% minimum collects/views ratio (was 0.1%)
    MIN_VIEWS = 500  # Minimum views threshold (was 1000)


class LLMProviderSettings:
    """LLM provider selection (split into embedding & analysis)."""
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # "openai" or "gemini"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "gemini"


class Settings:
    """Main settings container."""
    spark = SparkSettings()
    kafka = KafkaSettings()
    openai = OpenAISettings()
    gemini = GeminiSettings()
    llm_provider = LLMProviderSettings()
    # Legacy (use HDBSCAN instead)
    dbscan = DBSCANSettings()
    # Current clustering
    hdbscan = HDBSCANSettings()
    mongodb = MongoDBSettings()
    processing = ProcessingSettings()


# Global settings instance
settings = Settings()
