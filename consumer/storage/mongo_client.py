"""
MongoDB client for saving trends.
"""

import logging
from typing import List
from pymongo import MongoClient, errors
from config.settings import settings
from models import Trend

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for trend storage."""

    def __init__(self, connection_string: str = None):
        """
        Initialize MongoDB client.

        Args:
            connection_string: MongoDB connection string (defaults to settings)
        """
        self.connection_string = connection_string or settings.mongodb.CONNECTION_STRING
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        """Establish MongoDB connection."""
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')

            self.db = self.client[settings.mongodb.DATABASE]
            self.collection = self.db[settings.mongodb.COLLECTION]

            logger.info(f"✅ Connected to MongoDB: {settings.mongodb.DATABASE}.{settings.mongodb.COLLECTION}")
        except errors.ConnectionError as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise

    def save_trend(self, trend: Trend):
        """
        Save a single trend to MongoDB.

        Args:
            trend: Trend object
        """
        if self.collection is None:
            self.connect()

        try:
            result = self.collection.insert_one(trend.to_dict())
            logger.info(f"✅ Saved trend: {trend.topic} (ID: {result.inserted_id})")
        except Exception as e:
            logger.error(f"❌ Failed to save trend: {e}")
            raise

    def save_trends(self, trends: List[Trend]):
        """
        Save multiple trends to MongoDB.

        Args:
            trends: List of Trend objects
        """
        if not trends:
            logger.warning("No trends to save")
            return

        if self.collection is None:
            self.connect()

        try:
            docs = [trend.to_dict() for trend in trends]
            result = self.collection.insert_many(docs)
            logger.info(f"✅ Saved {len(result.inserted_ids)} trends to MongoDB")
        except Exception as e:
            logger.error(f"❌ Failed to save trends: {e}")
            raise

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")