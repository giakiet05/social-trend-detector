"""
Analysis stage: LLM analysis of clusters to detect trends (multi-source).
"""

from typing import List, Dict
import logging
import time
from datetime import datetime
from collections import Counter
from .base_stage import BaseStage
from common.models import ContentItem
from consumer.enrichment.base_llm_client import BaseLLMClient
from consumer.models.schemas import Trend
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class AnalysisStage(BaseStage):
    """Analyze clusters using LLM to extract trend information (multi-source support)."""

    def __init__(self, llm_client: BaseLLMClient):
        super().__init__("AnalysisStage")
        self.llm_client = llm_client
        self.sample_count = settings.processing.SAMPLE_VIDEOS_COUNT

    def execute(self, clusters: Dict[int, List[ContentItem]]) -> List[Trend]:
        """
        Analyze each cluster with LLM (multi-source support).

        Args:
            clusters: Dict mapping cluster_id -> ContentItems

        Returns:
            List of Trend objects
        """
        self.log_start()

        if not clusters:
            self.log_skip("No clusters to analyze")
            return []

        trends = []

        for cluster_id, cluster_items in clusters.items():
            # Count sources
            source_counts = Counter(item.source for item in cluster_items)
            source_str = ", ".join([f"{s}: {c}" for s, c in source_counts.items()])
            logger.info(f"   Analyzing cluster {cluster_id}: {len(cluster_items)} items ({source_str})")

            try:
                start_time = time.time()

                # Rank items by engagement score
                ranked_items = self._rank_by_engagement(cluster_items)

                # Select top 10 for LLM analysis (cost optimization)
                top_items = ranked_items[:10]

                # LLM analysis (with multi-source context)
                analysis = self._analyze_cluster(top_items, source_counts)

                # Rate limiting: ensure minimum 5s between LLM calls
                elapsed = time.time() - start_time
                if elapsed < 5:
                    sleep_time = 5 - elapsed
                    logger.debug(f"   Rate limiting: sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)

                # Calculate stats from ALL items in cluster
                total_views = sum(item.views or 0 for item in cluster_items)
                total_likes = sum(item.likes or 0 for item in cluster_items)

                # Sample items: top N by engagement (convert to dict for MongoDB)
                sample_items = [self._item_to_sample_dict(item) for item in ranked_items[:self.sample_count]]

                # Create Trend object
                trend = Trend(
                    timestamp=datetime.utcnow(),
                    topic=analysis['topic'],
                    summary=analysis['summary'],
                    sentiment=analysis['sentiment'],
                    keywords=analysis['keywords'],
                    video_count=len(cluster_items),
                    total_views=total_views,
                    total_likes=total_likes,
                    sample_videos=sample_items,
                    source_counts=dict(source_counts)
                )

                trends.append(trend)

                logger.info(f"      → Topic: {trend.topic}")
                logger.info(f"      → Sentiment: {trend.sentiment}")
                logger.info(f"      → Items: {trend.video_count}, Views: {total_views:,}")

            except Exception as e:
                logger.error(f"Failed to analyze cluster {cluster_id}: {e}", exc_info=True)
                continue

        self.log_complete(f"Analyzed {len(trends)} trends")
        return trends

    def _analyze_cluster(self, items: List[ContentItem], source_counts: Counter) -> Dict:
        """Analyze cluster with LLM (multi-source prompt)."""

        # Build prompt with multi-source context
        prompt = f"""Analyze this trending topic from multiple sources:

Sources breakdown:
{chr(10).join([f"- {source.upper()}: {count} items" for source, count in source_counts.items()])}

Sample content (first {len(items)} items):
"""

        for i, item in enumerate(items, 1):
            prompt += f"\n{i}. [{item.source.upper()}] {item.text[:200]}"

        prompt += """

Task: Provide JSON with:
1. topic: One-sentence trend name
2. summary: 2-3 sentence explanation
3. sentiment: positive/negative/neutral
4. keywords: 5-10 keywords
"""

        # Call LLM
        return self.llm_client.analyze_cluster(prompt)

    def _rank_by_engagement(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Rank items by engagement score.

        Score = likes*1 + comments*2 + shares*3 + collects*4
        """
        def engagement_score(item: ContentItem):
            score = 0
            score += (item.likes or 0) * 1.0
            score += (item.comments or 0) * 2.0
            score += (item.shares or 0) * 3.0
            score += item.metadata.get('collects', 0) * 4.0
            return score

        return sorted(items, key=engagement_score, reverse=True)

    def _item_to_sample_dict(self, item: ContentItem) -> Dict:
        """Convert ContentItem to sample dict for MongoDB."""
        return {
            "content_id": item.content_id,
            "source": item.source,
            "text": item.text[:500],  # Truncate long text
            "url": item.url,
            "views": item.views,
            "likes": item.likes,
            "comments": item.comments,
            "author_name": item.author_name,
        }
