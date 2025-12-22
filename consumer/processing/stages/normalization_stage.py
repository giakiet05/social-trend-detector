"""
NormalizationStage - Transform source-specific data to unified ContentItem.
"""

import logging
from typing import List, Dict
from datetime import datetime
from .base_stage import BaseStage
from common.models import ContentItem
from common.utils import DataSaver

logger = logging.getLogger(__name__)


class NormalizationStage(BaseStage):
    """
    Normalize multi-source data to unified ContentItem schema.

    Input: List[Dict] (mixed: TikTok + News + YouTube)
    Output: List[ContentItem]
    """

    def __init__(self):
        super().__init__("NormalizationStage")
        self.data_saver = DataSaver(base_dir="data/normalized")

    def execute(self, data: List[Dict]) -> List[ContentItem]:
        """
        Transform source-specific dicts to ContentItems.

        Args:
            data: List of raw dicts from Kafka

        Returns:
            List of ContentItem objects
        """
        self.log_start()

        items = []
        source_counts = {"tiktok": 0, "vnexpress": 0, "youtube": 0, "unknown": 0}

        for raw_data in data:
            try:
                # Detect source by fields and normalize
                item = self._normalize(raw_data)
                if item:
                    items.append(item)
                    source_counts[item.source] = source_counts.get(item.source, 0) + 1
            except Exception as e:
                logger.warning(f"Failed to normalize item: {e}")
                source_counts["unknown"] += 1
                continue

        # Log source breakdown
        breakdown = ", ".join([f"{k}: {v}" for k, v in source_counts.items() if v > 0])

        # Save normalized items to JSON for debugging
        if items:
            try:
                self.data_saver.save(source="items", data=items)
                logger.info(f"   💾 Saved {len(items)} normalized items to data/normalized/items/")
            except Exception as e:
                logger.warning(f"   ⚠️  Failed to save normalized items: {e}")

        self.log_complete(f"{len(items)} items normalized ({breakdown})")

        return items

    def _normalize(self, data: Dict) -> ContentItem:
        """Detect source and normalize to ContentItem."""

        # Detect source by unique fields
        if "video_id" in data and "author_fans" in data:
            return self._from_tiktok(data)
        elif "article_id" in data:
            return self._from_news(data)
        elif "channel_id" in data:
            return self._from_youtube(data)
        else:
            logger.warning(f"Unknown source: {list(data.keys())}")
            return None

    def _from_tiktok(self, data: Dict) -> ContentItem:
        """Transform TikTokVideo to ContentItem."""
        return ContentItem(
            content_id=data.get("video_id", ""),
            source="tiktok",
            collected_at=datetime.utcnow().isoformat(),
            text=data.get("text", ""),
            url=data.get("video_url"),
            hashtags=data.get("hashtags", []),
            published_at=data.get("timestamp"),
            views=data.get("views"),
            likes=data.get("likes"),
            comments=data.get("comments"),
            shares=data.get("shares"),
            author_name=data.get("author_username"),
            author_followers=data.get("author_fans"),
            metadata={
                "collects": data.get("collects"),
                "author_verified": data.get("author_verified"),
                "language": data.get("language"),
            }
        )

    def _from_news(self, data: Dict) -> ContentItem:
        """Transform NewsArticle to ContentItem."""
        # Combine title + summary for text
        title = data.get('title', '')
        summary = data.get('summary', '')
        text = f"{title}. {summary}".strip()

        return ContentItem(
            content_id=data.get("article_id", ""),
            source="vnexpress",
            collected_at=datetime.utcnow().isoformat(),
            text=text,
            url=data.get("url"),
            hashtags=[],  # News không có hashtags
            published_at=data.get("published_at"),
            views=None,  # News không có metrics
            likes=None,
            comments=None,
            shares=None,
            author_name=data.get("author", "VNExpress"),
            author_followers=None,
            metadata={
                "category": data.get("category"),
                "thumbnail": data.get("thumbnail"),
            }
        )

    def _from_youtube(self, data: Dict) -> ContentItem:
        """Transform YouTubeVideo to ContentItem."""
        # Combine title + description
        title = data.get('title', '')
        description = data.get('description', '')
        text = f"{title}. {description}".strip()

        return ContentItem(
            content_id=data.get("video_id", ""),
            source="youtube",
            collected_at=datetime.utcnow().isoformat(),
            text=text,
            url=data.get("url"),
            hashtags=data.get("tags", []),
            published_at=data.get("published_at"),
            views=data.get("views"),
            likes=data.get("likes"),
            comments=data.get("comments"),
            shares=None,  # YouTube không có shares
            author_name=data.get("channel_name"),
            author_followers=None,  # Không có trong data
            metadata={
                "channel_id": data.get("channel_id"),
                "duration_seconds": data.get("duration_seconds"),
                "thumbnail": data.get("thumbnail"),
                "category": data.get("category"),
            }
        )
