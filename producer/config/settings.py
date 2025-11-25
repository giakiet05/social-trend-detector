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


class YouTube:
    """YouTube Data API v3 configuration."""
    def __init__(self):
        self.API_KEY = os.getenv("YOUTUBE_API_KEY")


class KeywordsConfig:
    """
    Scraping keywords configuration loaded from YAML file.

    Edit keywords in: producer/config/scraping_keywords.yaml
    """
    def __init__(self):
        self._config = self._load_yaml()

    def _load_yaml(self) -> Dict:
        """Load keywords from YAML file."""
        try:
            with open(Paths.KEYWORDS_CONFIG, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Keywords config not found: {Paths.KEYWORDS_CONFIG}")
            return {}
        except yaml.YAMLError as e:
            print(f"⚠️  Failed to parse YAML: {e}")
            return {}

    # TikTok
    @property
    def tiktok_keywords(self) -> List[str]:
        return self._config.get('tiktok', {}).get('keywords', [])

    @property
    def tiktok_hashtags(self) -> List[str]:
        return self._config.get('tiktok', {}).get('hashtags', [])

    @property
    def tiktok_max_videos(self) -> int:
        return self._config.get('tiktok', {}).get('max_videos_per_query', 100)

    # VNExpress
    @property
    def vnexpress_keywords(self) -> List[str]:
        return self._config.get('vnexpress', {}).get('keywords', [])

    @property
    def vnexpress_rss_feeds(self) -> List[str]:
        return self._config.get('vnexpress', {}).get('rss_feeds', [])

    # YouTube
    @property
    def youtube_keywords(self) -> List[str]:
        return self._config.get('youtube', {}).get('keywords', [])

    @property
    def youtube_max_videos(self) -> int:
        return self._config.get('youtube', {}).get('max_videos_per_keyword', 50)

    # Google Trends
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
        self.keywords = KeywordsConfig()

        # Dynamic configs (load from environment)
        self.runtime = Runtime()
        self.mock = MockMode()
        self.kafka = Kafka()
        self.apify = Apify()
        self.youtube = YouTube()
        self.logging = Logging()


# Singleton instance
settings = Settings()
