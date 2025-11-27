"""
Cleaning stage: Remove invalid/null data.
"""

from typing import List
import logging
from .base_stage import BaseStage
from common.models import ContentItem

logger = logging.getLogger(__name__)


class CleaningStage(BaseStage):
    """Clean and validate content items from all sources."""

    def __init__(self):
        super().__init__("CleaningStage")

    def execute(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Remove items with null/invalid data.

        Args:
            items: List of ContentItem objects

        Returns:
            Cleaned ContentItem objects
        """
        self.log_start()

        if not items:
            self.log_skip("No items to clean")
            return []

        initial_count = len(items)
        cleaned = []

        for item in items:
            # Check required fields (universal)
            if not item.content_id:
                logger.debug(f"Skipping item: missing content_id")
                continue

            if not item.text or not isinstance(item.text, str):
                logger.debug(f"Skipping item {item.content_id}: invalid text")
                continue

            if not item.source:
                logger.debug(f"Skipping item {item.content_id}: missing source")
                continue

            # Text length check
            if len(item.text.strip()) < 10:
                logger.debug(f"Skipping item {item.content_id}: text too short")
                continue

            # Ensure hashtags is list
            if item.hashtags is None:
                item.hashtags = []

            cleaned.append(item)

        removed = initial_count - len(cleaned)
        self.log_complete(f"{len(cleaned)}/{initial_count} items valid, {removed} removed")

        return cleaned
