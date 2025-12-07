"""
Filtering stage: Remove noise (spam, bots, low quality).
"""

from typing import List
import logging
from .base_stage import BaseStage
from common.models import ContentItem
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class FilteringStage(BaseStage):
    """Filter out noise: spam accounts, low engagement, low quality (source-specific)."""

    def __init__(self):
        super().__init__("FilteringStage")
        self.min_engagement_rate = settings.processing.MIN_ENGAGEMENT_RATE
        self.min_author_fans = settings.processing.MIN_AUTHOR_FANS
        self.min_quality_ratio = settings.processing.MIN_QUALITY_RATIO
        self.min_views = settings.processing.MIN_VIEWS

    def execute(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Filter content based on source-specific quality thresholds.

        Args:
            items: Cleaned ContentItem objects

        Returns:
            High-quality ContentItem objects
        """
        self.log_start()

        if not items:
            self.log_skip("No items to filter")
            return []

        initial_count = len(items)
        filtered = []

        for item in items:
            # Source-specific filtering
            if item.source == "tiktok":
                if not self._is_quality_tiktok(item):
                    continue
            elif item.source == "youtube":
                if not self._is_quality_youtube(item):
                    continue
            elif item.source == "vnexpress":
                # News: no filtering for now (accept all)
                pass

            filtered.append(item)

        removed = initial_count - len(filtered)
        self.log_complete(f"{len(filtered)}/{initial_count} items passed, {removed} filtered")

        return filtered

    def _is_quality_tiktok(self, item: ContentItem) -> bool:
        """Check TikTok quality based on engagement & author credibility."""

        # Filter 1: Minimum views
        if item.views and item.views < self.min_views:
            logger.debug(f"Filtered {item.content_id}: views too low ({item.views})")
            return False

        # Filter 2: Engagement rate
        if item.views and item.views > 0:
            engagement = (item.likes or 0) + (item.comments or 0) + (item.shares or 0)
            engagement_rate = engagement / item.views
            if engagement_rate < self.min_engagement_rate:
                logger.debug(f"Filtered {item.content_id}: low engagement rate ({engagement_rate:.4f})")
                return False

        # Filter 3: Author credibility
        if item.author_followers and item.author_followers < self.min_author_fans:
            logger.debug(f"Filtered {item.content_id}: author has too few fans ({item.author_followers})")
            return False

        # Filter 4: Quality ratio (collects/views)
        collects = item.metadata.get("collects", 0)
        if item.views and item.views > 0:
            quality_ratio = collects / item.views
            if quality_ratio < self.min_quality_ratio:
                logger.debug(f"Filtered {item.content_id}: low quality ratio ({quality_ratio:.6f})")
                return False

        return True

    def _is_quality_youtube(self, item: ContentItem) -> bool:
        """Check YouTube quality based on engagement (relaxed)."""

        # Min views (relaxed)
        if item.views and item.views < 500:  # was 1000
            logger.debug(f"Filtered {item.content_id}: YouTube views too low ({item.views})")
            return False

        # Min engagement rate (relaxed)
        if item.views and item.views > 0:
            engagement = (item.likes or 0) + (item.comments or 0)
            engagement_rate = engagement / item.views
            if engagement_rate < 0.001:  # 0.1% for YouTube (was 1%)
                logger.debug(f"Filtered {item.content_id}: YouTube low engagement ({engagement_rate:.4f})")
                return False

        return True
