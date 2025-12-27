"""
Trend detection pipeline orchestration (multi-source support).
"""

import logging
from typing import List
from .stages import (
    NormalizationStage,
    CleaningStage,
    FilteringStage,
    EmbeddingStage,
    ClusteringStage,
    AnalysisStage,
    DeduplicationStage,
    StorageStage
)
from consumer.enrichment.base_llm_client import BaseEmbeddingClient, BaseLLMClient
from consumer.storage.mongo_client import MongoDBClient
from consumer.processing.clusterer import TrendClusterer
from common.models import Trend

logger = logging.getLogger(__name__)


class TrendDetectionPipeline:
    """
    Pipeline for trend detection from multiple sources (TikTok, VNExpress, YouTube).

    Stages:
    0. NormalizationStage - Transform to unified ContentItem
    1. CleaningStage - Remove invalid data
    2. FilteringStage - Remove noise (spam, low quality)
    3. EmbeddingStage - Convert text to vectors
    4. ClusteringStage - HDBSCAN clustering
    5. AnalysisStage - LLM analysis of clusters
    6. DeduplicationStage - Merge with existing trends
    7. StorageStage - Save to MongoDB
    """

    def __init__(
        self,
        embedding_client: BaseEmbeddingClient,
        llm_client: BaseLLMClient,
        mongo_client: MongoDBClient,
        clusterer: TrendClusterer
    ):
        """
        Initialize pipeline with dependencies.

        Args:
            embedding_client: Embedding client (OpenAI or Gemini) for text-to-vector
            llm_client: LLM client (OpenAI or Gemini) for analysis
            mongo_client: MongoDB client for storage
            clusterer: DBSCAN clusterer
        """
        # Initialize all stages (multi-source pipeline with separate providers)
        self.stages = [
            NormalizationStage(),
            CleaningStage(),
            FilteringStage(),
            EmbeddingStage(embedding_client),
            ClusteringStage(clusterer),
            AnalysisStage(llm_client),
            DeduplicationStage(embedding_client, mongo_client),
            StorageStage(mongo_client)
        ]

        logger.info(f"Pipeline initialized with {len(self.stages)} stages (multi-source)")

    def process(self, videos: List[dict]) -> List[Trend]:
        """
        Run full pipeline on a batch of videos.

        Args:
            videos: List of video dictionaries from Spark

        Returns:
            List of detected trends (saved to MongoDB)
        """
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE STARTED")
        logger.info("=" * 60)

        data = videos

        try:
            # Run each stage sequentially
            for stage in self.stages:
                data = stage.execute(data)

                # Early exit if no data
                if data is None or (isinstance(data, (list, dict)) and len(data) == 0):
                    logger.warning(f"Pipeline stopped early: no data after {stage.stage_name}")
                    return []

            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60 + "\n")

            # StorageStage returns None, so return empty list
            # (trends are already saved to MongoDB)
            return []

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
