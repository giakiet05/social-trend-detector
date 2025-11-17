"""
Clustering stage: DBSCAN clustering with min cluster size filter.
"""

from typing import List, Dict, Tuple
import logging
import numpy as np
from .base_stage import BaseStage
from processing.clusterer import TrendClusterer
from config.settings import settings

logger = logging.getLogger(__name__)


class ClusteringStage(BaseStage):
    """Cluster videos using DBSCAN and filter small clusters."""

    def __init__(self, clusterer: TrendClusterer):
        super().__init__("ClusteringStage")
        self.clusterer = clusterer
        self.min_cluster_size = settings.processing.MIN_CLUSTER_SIZE

    def execute(self, data: Tuple[List[Dict], np.ndarray]) -> Dict[int, List[Dict]]:
        """
        Cluster videos and filter by minimum cluster size.

        Args:
            data: Tuple of (videos, embeddings)

        Returns:
            Dict mapping cluster_id -> list of videos (only valid clusters)
        """
        self.log_start()

        videos, embeddings = data

        if len(videos) == 0:
            self.log_skip("No videos to cluster")
            return {}

        # Run DBSCAN
        labels = self.clusterer.cluster(embeddings)

        # Group by cluster
        clusters = self.clusterer.group_by_cluster(videos, labels)

        if not clusters:
            self.log_skip("No clusters found (all noise)")
            return {}

        # Filter small clusters
        valid_clusters = {}
        filtered_count = 0

        for cluster_id, cluster_videos in clusters.items():
            if len(cluster_videos) >= self.min_cluster_size:
                valid_clusters[cluster_id] = cluster_videos
            else:
                filtered_count += 1
                logger.debug(f"Filtered cluster {cluster_id}: only {len(cluster_videos)} videos (min: {self.min_cluster_size})")

        if filtered_count > 0:
            logger.info(f"   Filtered {filtered_count} small clusters (< {self.min_cluster_size} videos)")

        self.log_complete(f"{len(valid_clusters)} valid clusters (from {len(clusters)} total)")

        return valid_clusters
