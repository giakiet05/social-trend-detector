"""
Trend detection pipeline orchestration.
"""

import logging
from typing import List
from .stages import (
    CleaningStage,
    FilteringStage,
    EmbeddingStage,
    ClusteringStage,
    AnalysisStage,
    DeduplicationStage,
    StorageStage
)
from consumer.enrichment.openai_client import OpenAIClient
from consumer.storage.mongo_client import MongoDBClient
from consumer.processing.clusterer import TrendClusterer
from consumer.models.schemas import Trend

logger = logging.getLogger(__name__)


class TrendDetectionPipeline:
    """
    Pipeline for trend detection from TikTok videos.

    Stages:
    1. CleaningStage - Remove invalid data
    2. FilteringStage - Remove noise (spam, low quality)
    3. EmbeddingStage - Convert text to vectors
    4. ClusteringStage - DBSCAN clustering
    5. AnalysisStage - LLM analysis of clusters
    6. DeduplicationStage - Merge with existing trends
    7. StorageStage - Save to MongoDB
    """

    def __init__(
        self,
        openai_client: OpenAIClient,
        mongo_client: MongoDBClient,
        clusterer: TrendClusterer
    ):
        """
        Initialize pipeline with dependencies.

        Args:
            openai_client: OpenAI client for embeddings and analysis
            mongo_client: MongoDB client for storage
            clusterer: DBSCAN clusterer
        """
        # Initialize all stages
        self.stages = [
            CleaningStage(),
            FilteringStage(),
            EmbeddingStage(openai_client),
            ClusteringStage(clusterer),
            AnalysisStage(openai_client),
            DeduplicationStage(openai_client, mongo_client),
            StorageStage(mongo_client)
        ]

        logger.info(f"✅ Pipeline initialized with {len(self.stages)} stages")

    def process(self, videos: List[dict]) -> List[Trend]:
        """
        Run full pipeline on a batch of videos.

        Args:
            videos: List of video dictionaries from Spark

        Returns:
            List of detected trends (saved to MongoDB)
        """
        logger.info("\n" + "=" * 60)
        logger.info("🔄 PIPELINE STARTED")
        logger.info("=" * 60)

        data = videos

        try:
            # Run each stage sequentially
            for stage in self.stages:
                data = stage.execute(data)

                # Early exit if no data
                if data is None or (isinstance(data, (list, dict)) and len(data) == 0):
                    logger.warning(f"⚠️  Pipeline stopped early: no data after {stage.stage_name}")
                    return []

            logger.info("=" * 60)
            logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60 + "\n")

            # StorageStage returns None, so return empty list
            # (trends are already saved to MongoDB)
            return []

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            raise
