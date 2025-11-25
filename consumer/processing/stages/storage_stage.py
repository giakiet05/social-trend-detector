"""
Storage stage: Save/update trends to MongoDB.
"""

from typing import List
import logging
from .base_stage import BaseStage
from consumer.storage.mongo_client import MongoDBClient
from consumer.models.schemas import Trend

logger = logging.getLogger(__name__)


class StorageStage(BaseStage):
    """Save trends to MongoDB (insert new or update existing)."""

    def __init__(self, mongo_client: MongoDBClient):
        super().__init__("StorageStage")
        self.mongo = mongo_client

    def execute(self, trends: List[Trend]) -> None:
        """
        Save trends to MongoDB.

        If trend has _id (from deduplication), update existing.
        Else, insert new.

        Args:
            trends: List of trends to save

        Returns:
            None (side effect: save to MongoDB)
        """
        self.log_start()

        if not trends:
            self.log_skip("No trends to save")
            return

        new_count = 0
        updated_count = 0

        for trend in trends:
            try:
                if hasattr(trend, '_id') and trend._id:
                    # Update existing trend
                    self.mongo.upsert_trend(trend)
                    updated_count += 1
                else:
                    # Insert new trend
                    self.mongo.upsert_trend(trend)
                    new_count += 1

            except Exception as e:
                logger.error(f"Failed to save trend '{trend.topic}': {e}", exc_info=True)
                continue

        self.log_complete(f"{new_count} new, {updated_count} updated")
