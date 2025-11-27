"""
Deduplication stage: Merge similar trends across batches.
"""

from typing import List
import logging
import numpy as np
from datetime import datetime
from .base_stage import BaseStage
from consumer.enrichment.base_llm_client import BaseEmbeddingClient
from consumer.storage.mongo_client import MongoDBClient
from consumer.models.schemas import Trend
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class DeduplicationStage(BaseStage):
    """Deduplicate trends against existing trends in MongoDB."""

    def __init__(self, embedding_client: BaseEmbeddingClient, mongo_client: MongoDBClient):
        super().__init__("DeduplicationStage")
        self.embedding_client = embedding_client
        self.mongo = mongo_client
        self.similarity_threshold = settings.mongodb.SIMILARITY_THRESHOLD
        self.window_hours = settings.mongodb.DEDUP_WINDOW_HOURS

    def execute(self, new_trends: List[Trend]) -> List[Trend]:
        """
        Deduplicate new trends against existing trends.

        Strategy:
        1. Query MongoDB for recent trends (last 24h)
        2. Embed all trend topics
        3. Calculate cosine similarity
        4. Merge if similarity >= threshold, else keep as new

        Args:
            new_trends: Trends detected in current batch

        Returns:
            Deduplicated trends (merged or new)
        """
        self.log_start()

        if not new_trends:
            self.log_skip("No new trends to deduplicate")
            return []

        # Get existing trends from MongoDB
        existing_trends = self.mongo.get_recent_trends(hours=self.window_hours)

        if not existing_trends:
            logger.info(f"   No existing trends in last {self.window_hours}h, all trends are new")
            self.log_complete(f"{len(new_trends)} new trends")
            return new_trends

        logger.info(f"   Comparing with {len(existing_trends)} existing trends")

        # Embed topics
        existing_topics = [t['topic'] for t in existing_trends]
        new_topics = [t.topic for t in new_trends]

        try:
            existing_embeddings = self.embedding_client.embed_texts(existing_topics)
            new_embeddings = self.embedding_client.embed_texts(new_topics)
        except Exception as e:
            logger.error(f"Embedding failed during deduplication: {e}")
            # Fallback: return new trends without deduplication
            return new_trends

        # Deduplicate
        deduplicated = []
        merged_count = 0
        new_count = 0

        for i, new_trend in enumerate(new_trends):
            new_emb = new_embeddings[i]

            # Find most similar existing trend
            max_similarity = 0
            best_match = None

            for j, existing_trend in enumerate(existing_trends):
                existing_emb = existing_embeddings[j]
                similarity = self._cosine_similarity(new_emb, existing_emb)

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = existing_trend

            # Merge or keep new
            if max_similarity >= self.similarity_threshold:
                # MERGE
                merged_trend = self._merge_trends(best_match, new_trend)
                deduplicated.append(merged_trend)
                merged_count += 1
                logger.info(f"   🔗 Merged: '{new_trend.topic}' → '{best_match['topic']}' (similarity: {max_similarity:.3f})")
            else:
                # NEW TREND
                deduplicated.append(new_trend)
                new_count += 1
                logger.info(f"   ✨ New trend: '{new_trend.topic}' (max similarity: {max_similarity:.3f})")

        self.log_complete(f"{merged_count} merged, {new_count} new")
        return deduplicated

    def _cosine_similarity(self, emb1, emb2):
        """Calculate cosine similarity between two embeddings."""
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    def _merge_trends(self, existing_trend: dict, new_trend: Trend) -> Trend:
        """
        Merge new trend into existing trend.

        Strategy:
        - Keep existing topic name (more established)
        - Increment video_count
        - Add views/likes
        - Merge keywords (unique)
        - Update sample_videos (top by engagement)
        - Update timestamp to latest
        - Keep MongoDB _id for upsert
        """
        # Merge keywords (unique)
        merged_keywords = list(set(existing_trend['keywords'] + new_trend.keywords))

        # Merge sample videos
        old_samples = existing_trend.get('sample_videos', [])
        new_samples = new_trend.sample_videos
        merged_samples = self._merge_sample_videos(old_samples, new_samples)

        return Trend(
            timestamp=datetime.utcnow(),  # Latest update time
            topic=existing_trend['topic'],  # Keep original name
            summary=existing_trend['summary'],  # Keep original summary
            sentiment=existing_trend['sentiment'],  # Keep original sentiment
            keywords=merged_keywords,
            video_count=existing_trend['video_count'] + new_trend.video_count,
            total_views=existing_trend['total_views'] + new_trend.total_views,
            total_likes=existing_trend['total_likes'] + new_trend.total_likes,
            sample_videos=merged_samples,
            _id=existing_trend['_id']  # Keep MongoDB _id for update
        )

    def _merge_sample_videos(self, old_samples, new_samples, top_k=10):
        """
        Merge sample videos and rank by engagement.

        Args:
            old_samples: Existing sample videos
            new_samples: New sample videos
            top_k: Number of top videos to keep

        Returns:
            Top K videos by engagement score
        """
        all_samples = old_samples + new_samples

        # Deduplicate by video_id
        seen = set()
        unique = []
        for v in all_samples:
            if v['video_id'] not in seen:
                seen.add(v['video_id'])
                unique.append(v)

        # Sort by engagement score
        sorted_samples = sorted(unique, key=self._engagement_score, reverse=True)
        return sorted_samples[:top_k]

    def _engagement_score(self, video):
        """Calculate engagement score."""
        return (
            video.get('likes', 0) * 1.0 +
            video.get('comments', 0) * 2.0 +
            video.get('shares', 0) * 3.0 +
            video.get('collects', 0) * 4.0
        )
