"""
Centralized configuration management for TikTok Producer.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class Paths:
    """Static path configurations."""
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_DIR = ROOT_DIR / "data"


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
        self.TOPIC = os.getenv("KAFKA_TOPIC", "tiktok-raw-data")


class Apify:
    """Apify API configuration (for live scraping)."""
    def __init__(self):
        self.API_TOKEN = os.getenv("APIFY_API_TOKEN")
        self.ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "clockworks/tiktok-scraper")


class ScrapingStrategy:
    """Scraping keywords and hashtags configuration."""

    # General keywords (for current random test data)
    GENERAL_KEYWORDS = [
        "review phim", "drama", "biến căng", "unboxing", "daily vlog",
        "outfit ideas", "goc lam dep", "make up", "skincare", "funny",
        "dance trend", "cover", "game", "the thao", "am thuc",
        "du lich", "learn on tiktok", "startup", "AI", "technology"
    ]

    # Tech-specific keywords (for future phase 2)
    TECH_KEYWORDS = [
        "iphone review", "smartphone review", "laptop review", "tech review",
        "unboxing", "tech news", "technology", "gadget", "android",
        "macbook", "ipad", "airpods", "tech tips", "software",
        "app review", "AI", "đánh giá điện thoại", "review laptop",
        "công nghệ", "mở hộp", "smartphone", "điện thoại"
    ]

    # General hashtags
    GENERAL_HASHTAGS = [
        "xuhuong", "fyp", "viral", "trending", "thinhhanh"
    ]

    # Tech-specific hashtags (for future use)
    TECH_HASHTAGS = [
        "tech", "technology", "unboxing", "review", "techreview",
        "smartphone", "iphone", "android", "laptop", "gadget",
        "congnghe", "dienThoai", "technews", "techtok"
    ]


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
        self.scraping = ScrapingStrategy()

        # Dynamic configs (load from environment)
        self.runtime = Runtime()
        self.mock = MockMode()
        self.kafka = Kafka()
        self.apify = Apify()
        self.logging = Logging()


# Singleton instance
settings = Settings()
