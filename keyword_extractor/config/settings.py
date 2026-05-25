"""
Configuration for Keyword Extractor.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load .env
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=ROOT_DIR / ".env")

# Paths
CONFIG_DIR = Path(__file__).resolve().parent
RSS_FEEDS_CONFIG = CONFIG_DIR / "rss_feeds.yaml"


class Settings:
    """Keyword Extractor Settings."""

    def __init__(self):
        # MongoDB
        self.MONGO_URI = os.getenv(
            "MONGO_URI",
            "mongodb://admin:password@localhost:27017/?authSource=admin"
        )
        self.MONGO_DB = "social_trends"
        self.EXTRACTED_KEYWORDS_COLLECTION = "extracted_keywords"

        # LLM
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai or gemini
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        # Extraction settings
        self.MAX_HEADLINES = int(os.getenv("EXTRACT_MAX_HEADLINES", "1000"))  # Limit headlines
        self.NUM_KEYWORDS = int(os.getenv("EXTRACT_NUM_KEYWORDS", "30"))      # Number of keywords to extract

        # RSS Feeds (load from YAML)
        self.rss_feeds = self._load_rss_feeds()

    def _load_rss_feeds(self):
        """Load RSS feeds from YAML."""
        try:
            with open(RSS_FEEDS_CONFIG, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('news', {}).get('feeds', [])
        except Exception as e:
            print(f"Failed to load RSS feeds: {e}")
            return []


# Singleton
settings = Settings()
