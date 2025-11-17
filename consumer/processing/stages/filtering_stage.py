"""
Filtering stage: Remove noise (spam, bots, low quality).
"""

from typing import List, Dict
import logging
from .base_stage import BaseStage
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class FilteringStage(BaseStage):
    """Filter out noise: spam accounts, low engagement, low quality."""

    def __init__(self):
        super().__init__("FilteringStage")
        self.min_engagement_rate = settings.processing.MIN_ENGAGEMENT_RATE
        self.min_author_fans = settings.processing.MIN_AUTHOR_FANS
        self.min_quality_ratio = settings.processing.MIN_QUALITY_RATIO
        self.min_views = settings.processing.MIN_VIEWS

    def execute(self, videos: List[Dict]) -> List[Dict]:
        """
        Filter videos based on quality thresholds.

        Args:
            videos: Cleaned videos

        Returns:
            High-quality videos
        """
        self.log_start()

        if not videos:
            self.log_skip("No videos to filter")
            return []

        initial_count = len(videos)
        filtered = []

        for video in videos:
            # Filter 1: Minimum views
            if video.get('views', 0) < self.min_views:
                logger.debug(f"Filtered {video.get('video_id')}: views too low ({video.get('views')})")
                continue

            # Filter 2: Engagement rate (avoid clickbait)
            engagement_rate = self._calculate_engagement_rate(video)
            if engagement_rate < self.min_engagement_rate:
                logger.debug(f"Filtered {video.get('video_id')}: low engagement rate ({engagement_rate:.4f})")
                continue

            # Filter 3: Author credibility (avoid spam/bots)
            if video.get('author_fans', 0) < self.min_author_fans:
                logger.debug(f"Filtered {video.get('video_id')}: author has too few fans ({video.get('author_fans')})")
                continue

            # Filter 4: Quality ratio (collects/views - avoid low value content)
            quality_ratio = self._calculate_quality_ratio(video)
            if quality_ratio < self.min_quality_ratio:
                logger.debug(f"Filtered {video.get('video_id')}: low quality ratio ({quality_ratio:.6f})")
                continue

            filtered.append(video)

        removed = initial_count - len(filtered)
        self.log_complete(f"{len(filtered)}/{initial_count} videos passed, {removed} filtered")

        return filtered

    def _calculate_engagement_rate(self, video: Dict) -> float:
        """
        Calculate engagement rate.

        Formula: (likes + comments + shares) / views
        """
        views = video.get('views', 0)
        if views == 0:
            return 0.0

        engagement = (
            video.get('likes', 0) +
            video.get('comments', 0) +
            video.get('shares', 0)
        )
        return engagement / views

    def _calculate_quality_ratio(self, video: Dict) -> float:
        """
        Calculate quality ratio (collects/views).

        Collects (saves) are strong signal of valuable content.
        """
        views = video.get('views', 0)
        if views == 0:
            return 0.0

        collects = video.get('collects', 0)
        return collects / views
