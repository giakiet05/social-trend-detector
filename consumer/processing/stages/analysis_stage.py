"""
Analysis stage: LLM analysis of clusters to detect trends.
"""

from typing import List, Dict
import logging
from datetime import datetime
from .base_stage import BaseStage
from enrichment.openai_client import OpenAIClient
from models.schemas import Trend
from config.settings import settings

logger = logging.getLogger(__name__)


class AnalysisStage(BaseStage):
    """Analyze clusters using LLM to extract trend information."""

    def __init__(self, openai_client: OpenAIClient):
        super().__init__("AnalysisStage")
        self.openai = openai_client
        self.sample_count = settings.processing.SAMPLE_VIDEOS_COUNT

    def execute(self, clusters: Dict[int, List[Dict]]) -> List[Trend]:
        """
        Analyze each cluster with LLM.

        Args:
            clusters: Dict mapping cluster_id -> videos

        Returns:
            List of Trend objects
        """
        self.log_start()

        if not clusters:
            self.log_skip("No clusters to analyze")
            return []

        trends = []

        for cluster_id, cluster_videos in clusters.items():
            logger.info(f"   Analyzing cluster {cluster_id}: {len(cluster_videos)} videos")

            try:
                # Rank videos by engagement score
                ranked_videos = self._rank_by_engagement(cluster_videos)

                # Select top 10 for LLM analysis (cost optimization)
                top_videos = ranked_videos[:10]

                # LLM analysis
                analysis = self.openai.analyze_cluster(top_videos)

                # Calculate stats from ALL videos in cluster
                total_views = sum(v.get('views', 0) for v in cluster_videos)
                total_likes = sum(v.get('likes', 0) for v in cluster_videos)

                # Sample videos: top N by engagement
                sample_videos = ranked_videos[:self.sample_count]

                # Create Trend object
                trend = Trend(
                    timestamp=datetime.utcnow(),
                    topic=analysis['topic'],
                    summary=analysis['summary'],
                    sentiment=analysis['sentiment'],
                    keywords=analysis['keywords'],
                    video_count=len(cluster_videos),
                    total_views=total_views,
                    total_likes=total_likes,
                    sample_videos=sample_videos
                )

                trends.append(trend)

                logger.info(f"      → Topic: {trend.topic}")
                logger.info(f"      → Sentiment: {trend.sentiment}")
                logger.info(f"      → Videos: {trend.video_count}, Views: {total_views:,}")

            except Exception as e:
                logger.error(f"Failed to analyze cluster {cluster_id}: {e}", exc_info=True)
                continue

        self.log_complete(f"Analyzed {len(trends)} trends")
        return trends

    def _rank_by_engagement(self, videos: List[Dict]) -> List[Dict]:
        """
        Rank videos by engagement score.

        Score = likes*1 + comments*2 + shares*3 + collects*4
        """
        def engagement_score(video):
            return (
                video.get('likes', 0) * 1.0 +
                video.get('comments', 0) * 2.0 +
                video.get('shares', 0) * 3.0 +
                video.get('collects', 0) * 4.0
            )

        return sorted(videos, key=engagement_score, reverse=True)
