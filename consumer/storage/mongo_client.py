"""
MongoDB client for saving trends.
"""

import logging
from typing import List
from datetime import datetime, timedelta
from pymongo import MongoClient, errors
from consumer.config.settings import settings
from consumer.models.schemas import Trend

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

    def upsert_trend(self, trend: Trend):
        """
        Upsert a trend into MongoDB.

        If trend has _id (merged trend), update existing document.
        Else, insert new document.

        Args:
            trend: Trend object
        """
        if self.collection is None:
            self.connect()

        try:
            if hasattr(trend, '_id') and trend._id:
                # Update existing
                self.collection.update_one(
                    {'_id': trend._id},
                    {'$set': trend.to_dict()}
                )
                logger.debug(f"Updated trend: {trend.topic}")
            else:
                # Insert new
                result = self.collection.insert_one(trend.to_dict())
                logger.debug(f"Inserted new trend: {trend.topic} (ID: {result.inserted_id})")

        except Exception as e:
            logger.error(f"Failed to upsert trend '{trend.topic}': {e}")
            raise

    def get_recent_trends(self, hours: int = 24) -> List[dict]:
        """
        Get trends from last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of trend documents (as dicts)
        """
        if self.collection is None:
            self.connect()

        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            trends = list(self.collection.find({
                'timestamp': {'$gte': cutoff.isoformat()}
            }))

            logger.debug(f"Retrieved {len(trends)} trends from last {hours}h")
            return trends

        except Exception as e:
            logger.error(f"Failed to query recent trends: {e}")
            return []

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")