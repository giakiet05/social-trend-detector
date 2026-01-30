"""
Trend detection pipeline orchestration (multi-source support).
"""

import logging
from typing import List, Dict
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
from consumer.utils.metrics_logger import MetricsLogger
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
        # Initialize metrics logger
        self.metrics = MetricsLogger()

        # Initialize all stages (multi-source pipeline with separate providers)
        self.stages = [
            NormalizationStage(),
            CleaningStage(),
            FilteringStage(),
            EmbeddingStage(embedding_client),
            ClusteringStage(clusterer, metrics_logger=self.metrics),
            AnalysisStage(llm_client),
            DeduplicationStage(embedding_client, mongo_client, metrics_logger=self.metrics),
            StorageStage(mongo_client, metrics_logger=self.metrics)
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
        self.metrics.log_stage_input("NormalizationStage", len(videos))

        try:
            # Run each stage sequentially
            for i, stage in enumerate(self.stages):
                data = stage.execute(data)

                # Early exit if no data
                if data is None or (isinstance(data, (list, dict)) and len(data) == 0):
                    logger.warning(f"Pipeline stopped early: no data after {stage.stage_name}")
                    self.metrics.save()
                    return []

                # Log stage output (different formats for different stages)
                if stage.stage_name == "ClusteringStage" and isinstance(data, dict):
                    # ClusteringStage returns Dict[cluster_id -> items]
                    clusters = data
                    total_items = sum(len(items) for items in clusters.values())
                    cluster_sizes = [len(items) for items in clusters.values()]

                    # Count noise (items before clustering minus items in clusters)
                    # Note: This is approximate, actual noise count is in the stage
                    self.metrics.log_clustering(len(clusters), cluster_sizes, 0)
                elif stage.stage_name == "DeduplicationStage" and isinstance(data, list):
                    # DeduplicationStage returns List[Trend]
                    # This is logged in the stage itself
                    pass
                else:
                    # Other stages return list of items
                    if isinstance(data, list):
                        self.metrics.log_stage_output(stage.stage_name, len(data))
                    elif isinstance(data, dict):
                        self.metrics.log_stage_output(stage.stage_name, sum(len(v) for v in data.values()) if data else 0)

            logger.info("=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60 + "\n")

            # Save metrics before returning
            self.metrics.save()

            # StorageStage returns None, so return empty list
            # (trends are already saved to MongoDB)
            return []

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.metrics.save()
            raise
