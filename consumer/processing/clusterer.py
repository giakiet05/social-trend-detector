"""
DBSCAN clustering for trend detection.
"""

import logging
import numpy as np
from sklearn.cluster import DBSCAN
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class TrendClusterer:
    """DBSCAN-based trend clustering."""

    def __init__(self, eps: float = None, min_samples: int = None, metric: str = None):
        """
        Initialize DBSCAN clusterer.

        Args:
            eps: Maximum distance between samples (defaults to settings)
            min_samples: Minimum samples for a cluster (defaults to settings)
            metric: Distance metric (defaults to settings)
        """
        self.eps = eps or settings.dbscan.EPS
        self.min_samples = min_samples or settings.dbscan.MIN_SAMPLES
        self.metric = metric or settings.dbscan.METRIC

        self.dbscan = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric=self.metric
        )

        logger.info(f"✅ DBSCAN initialized: eps={self.eps}, min_samples={self.min_samples}, metric={self.metric}")

    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Cluster embeddings using DBSCAN.

        Args:
            embeddings: Numpy array of shape (n_videos, embedding_dim)

        Returns:
            Numpy array of cluster labels (shape: n_videos)
            Label -1 means noise (no cluster)
        """
        if len(embeddings) == 0:
            logger.warning("No embeddings to cluster")
            return np.array([])

        try:
            labels = self.dbscan.fit_predict(embeddings)

            # Count clusters (excluding noise)
            unique_labels = set(labels)
            n_clusters = len(unique_labels - {-1})
            n_noise = list(labels).count(-1)

            logger.info(f"✅ Clustering complete: {n_clusters} trends, {n_noise} noise videos")
            logger.debug(f"   Cluster distribution: {dict(zip(*np.unique(labels, return_counts=True)))}")

            return labels

        except Exception as e:
            logger.error(f"❌ Clustering failed: {e}")
            raise

    def group_by_cluster(self, videos: list, labels: np.ndarray) -> dict:
        """
        Group videos by cluster label.

        Args:
            videos: List of video dicts
            labels: Cluster labels from DBSCAN

        Returns:
            Dict mapping cluster_id -> list of videos
            (excludes noise cluster -1)
        """
        if len(videos) != len(labels):
            raise ValueError(f"Mismatch: {len(videos)} videos but {len(labels)} labels")

        clusters = {}
        for video, label in zip(videos, labels):
            if label == -1:
                continue  # Skip noise

            if label not in clusters:
                clusters[label] = []

            clusters[label].append(video)

        logger.info(f"✅ Grouped {len(videos)} videos into {len(clusters)} clusters")
        return clusters