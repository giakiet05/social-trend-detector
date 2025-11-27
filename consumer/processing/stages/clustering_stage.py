"""
Clustering stage: DBSCAN clustering with min cluster size filter.
"""

from typing import List, Dict
import logging
import numpy as np
from .base_stage import BaseStage
from common.models import ContentItem
from consumer.processing.clusterer import TrendClusterer
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class ClusteringStage(BaseStage):
    """Cluster content items using DBSCAN and filter small clusters."""

    def __init__(self, clusterer: TrendClusterer):
        super().__init__("ClusteringStage")
        self.clusterer = clusterer
        self.min_cluster_size = settings.processing.MIN_CLUSTER_SIZE

    def execute(self, items: List[ContentItem]) -> Dict[int, List[ContentItem]]:
        """
        Cluster content items and filter by minimum cluster size.

        Args:
            items: ContentItem objects with embeddings in metadata

        Returns:
            Dict mapping cluster_id -> list of ContentItems (only valid clusters)
        """
        self.log_start()

        if len(items) == 0:
            self.log_skip("No items to cluster")
            return {}

        # Extract embeddings from metadata
        embeddings = np.array([item.metadata["embedding"] for item in items])

        # Run DBSCAN
        labels = self.clusterer.cluster(embeddings)

        # Group by cluster (skip noise = -1)
        clusters: Dict[int, List[ContentItem]] = {}
        noise_count = 0

        for item, label in zip(items, labels):
            if label == -1:
                noise_count += 1
                continue

            if label not in clusters:
                clusters[label] = []
            clusters[label].append(item)

        if not clusters:
            self.log_skip(f"No clusters found ({noise_count} noise items)")
            return {}

        # Filter small clusters
        valid_clusters = {}
        filtered_count = 0

        for cluster_id, cluster_items in clusters.items():
            if len(cluster_items) >= self.min_cluster_size:
                valid_clusters[cluster_id] = cluster_items
            else:
                filtered_count += 1
                logger.debug(f"Filtered cluster {cluster_id}: only {len(cluster_items)} items (min: {self.min_cluster_size})")

        if filtered_count > 0:
            logger.info(f"   Filtered {filtered_count} small clusters (< {self.min_cluster_size} items)")
        if noise_count > 0:
            logger.info(f"   Noise items: {noise_count}")

        self.log_complete(f"{len(valid_clusters)} valid clusters (from {len(clusters)} total)")

        return valid_clusters
