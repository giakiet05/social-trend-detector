"""
Centralized configuration management for Multi-Source Social Trend Producer.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict


class Paths:
    """Static path configurations."""
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT_DIR / "data"
    CONFIG_DIR = Path(__file__).resolve().parent
    KEYWORDS_CONFIG = CONFIG_DIR / "scraping_keywords.yaml"
    RSS_FEEDS_CONFIG = CONFIG_DIR / "rss_feeds.yaml"


# Load .env from project root (only once)
load_dotenv(dotenv_path=Paths.ROOT_DIR / ".env")


class Runtime:
    """Runtime mode configuration."""
    def __init__(self):
        self.MODE = os.getenv("RUN_MODE", "mock")  # "mock" or "live"


class MockMode:
    """Configuration for mock mode (CSV-based testing)."""
    def __init__(self):
        self.CSV_PATH = os.getenv(
            "MOCK_CSV_PATH",
            "data/raw_tiktok_data.csv"
        )
        self.SIMULATE_REALTIME = os.getenv("MOCK_SIMULATE_REALTIME", "true").lower() == "true"
        self.DELAY_SECONDS = float(os.getenv("MOCK_DELAY_SECONDS", "1"))


class Kafka:
    """Kafka broker configuration."""
    def __init__(self):
        self.BOOTSTRAP_SERVERS = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        ).split(",")

        # Multiple topics for different sources
        self.TIKTOK_TOPIC = os.getenv("KAFKA_TIKTOK_TOPIC", "tiktok-raw")
        self.NEWS_TOPIC = os.getenv("KAFKA_NEWS_TOPIC", "news-raw")
        self.YOUTUBE_TOPIC = os.getenv("KAFKA_YOUTUBE_TOPIC", "youtube-raw")
        self.TRENDS_TOPIC = os.getenv("KAFKA_TRENDS_TOPIC", "trends-raw")


class Apify:
    """Apify API configuration (for TikTok scraping)."""
    def __init__(self):
        self.API_TOKEN = os.getenv("APIFY_API_TOKEN")
        self.ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "GdWCkxBtKWOsKjdch")  # clockworks/tiktok-scraper


class TikTokConfig:
    """Static TikTok scraper configuration."""
    def __init__(self):
        self.MAX_VIDEOS_PER_QUERY = int(os.getenv("TIKTOK_MAX_VIDEOS", "100"))


class YouTubeConfig:
    """Static YouTube scraper configuration."""
    def __init__(self):
        self.API_KEY = os.getenv("YOUTUBE_API_KEY")
        self.MAX_VIDEOS_PER_KEYWORD = int(os.getenv("YOUTUBE_MAX_VIDEOS", "200"))


class NewsConfig:
    """Static News scraper configuration."""
    pass  # No static config needed currently


class KeywordsConfig:
    """
    Scraping keywords configuration with dual-mode support.

    Modes (controlled by KEYWORDS_SOURCE env var):
    - yaml: Read keywords from scraping_keywords.yaml (dev/test)
    - mongodb: Read keywords from MongoDB (production)

    Usage:
        # Development/Testing
        KEYWORDS_SOURCE=yaml

        # Production
        KEYWORDS_SOURCE=mongodb
    """

    def __init__(self):
        self.source = os.getenv("KEYWORDS_SOURCE", "yaml")  # Default: yaml
        self._config = self._load_yaml() if self.source == "yaml" else {}
        self._mongo_client = None

        # Load RSS feeds from separate file (used in both modes)
        self._rss_feeds = self._load_rss_feeds()

    def _load_yaml(self) -> Dict:
        """Load keywords from YAML file (dev/test mode)."""
        try:
            with open(Paths.KEYWORDS_CONFIG, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Keywords config not found: {Paths.KEYWORDS_CONFIG}")
            return {}
        except yaml.YAMLError as e:
            print(f"⚠️  Failed to parse YAML: {e}")
            return {}

    def _load_rss_feeds(self) -> Dict:
        """Load RSS feeds from separate YAML file."""
        try:
            with open(Paths.RSS_FEEDS_CONFIG, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  RSS feeds config not found: {Paths.RSS_FEEDS_CONFIG}")
            return {}
        except yaml.YAMLError as e:
            print(f"⚠️  Failed to parse RSS feeds YAML: {e}")
            return {}

    def _get_mongo_client(self):
        """Lazy load MongoDB client (production mode)."""
        if self._mongo_client is None:
            from pymongo import MongoClient
            mongo_uri = os.getenv(
                "MONGO_URI",
                "mongodb://admin:password@localhost:27017/?authSource=admin"
            )
            self._mongo_client = MongoClient(mongo_uri)
        return self._mongo_client

    def _load_from_mongodb(self, source: str) -> List[str]:
        """Load keywords from MongoDB (production mode)."""
        try:
            db = self._get_mongo_client()["social_trends"]
            keywords = db.active_keywords.find({
                "status": "active",
                "sources": source
            })
            return [k["keyword"] for k in keywords]
        except Exception as e:
            print(f"⚠️  Failed to load keywords from MongoDB: {e}")
            return []

    # --- TikTok ---
    @property
    def tiktok_keywords(self) -> List[str]:
        """Get TikTok keywords (from YAML or MongoDB)."""
        if self.source == "yaml":
            return self._config.get('tiktok', {}).get('keywords', [])
        else:  # mongodb
            return self._load_from_mongodb('tiktok')

    @property
    def tiktok_hashtags(self) -> List[str]:
        """Get TikTok hashtags (static, from YAML)."""
        return self._config.get('tiktok', {}).get('hashtags', [])

    # --- News ---
    @property
    def news_keywords(self) -> List[str]:
        """Get News keywords (from YAML or MongoDB)."""
        if self.source == "yaml":
            return self._config.get('news', {}).get('keywords', [])
        else:  # mongodb
            return self._load_from_mongodb('news')

    @property
    def news_rss_feeds(self) -> List[str]:
        """Get News RSS feeds (from rss_feeds.yaml)."""
        return self._rss_feeds.get('news', {}).get('feeds', [])

    # --- YouTube ---
    @property
    def youtube_keywords(self) -> List[str]:
        """Get YouTube keywords (from YAML or MongoDB)."""
        if self.source == "yaml":
            return self._config.get('youtube', {}).get('keywords', [])
        else:  # mongodb
            return self._load_from_mongodb('youtube')

    # --- Google Trends (legacy, still from YAML) ---
    @property
    def trends_keywords(self) -> List[str]:
        return self._config.get('google_trends', {}).get('keywords', [])

    @property
    def trends_timeframe(self) -> str:
        return self._config.get('google_trends', {}).get('timeframe', 'now 7-d')

    @property
    def trends_region(self) -> str:
        return self._config.get('google_trends', {}).get('region', 'VN')


class Logging:
    """Logging configuration."""
    def __init__(self):
        self.LEVEL = os.getenv("LOG_LEVEL", "INFO")


class Settings:
    """
    Main settings singleton that holds all configuration objects.
    """
    def __init__(self):
        # Static configs
        self.paths = Paths()

        # Scraper-specific static configs
        self.tiktok_config = TikTokConfig()
        self.youtube_config = YouTubeConfig()
        self.news_config = NewsConfig()

        # Keywords (dynamic, dual-mode)
        self.keywords = KeywordsConfig()

        # API configs
        self.apify = Apify()

        # Runtime configs
        self.runtime = Runtime()
        self.mock = MockMode()
        self.kafka = Kafka()
        self.logging = Logging()


# Singleton instance
settings = Settings()
