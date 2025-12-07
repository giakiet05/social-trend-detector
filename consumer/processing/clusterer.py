"""
HDBSCAN clustering for trend detection.
"""

import logging
import numpy as np
import hdbscan
from consumer.config.settings import settings

logger = logging.getLogger(__name__)


class TrendClusterer:
    """HDBSCAN-based trend clustering."""

    def __init__(self, min_cluster_size: int = None, metric: str = None, min_samples: int = None):
        """
        Initialize HDBSCAN clusterer.

        Args:
            min_cluster_size: Minimum size of clusters (defaults to settings)
            metric: Distance metric (defaults to settings)
            min_samples: Min samples for core points (defaults to settings, None = auto)
        """
        self.min_cluster_size = min_cluster_size or settings.hdbscan.MIN_CLUSTER_SIZE
        self.metric = metric or settings.hdbscan.METRIC
        self.min_samples = min_samples if min_samples is not None else settings.hdbscan.MIN_SAMPLES

        self.hdbscan = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            metric=self.metric,
            min_samples=self.min_samples,
            cluster_selection_method='eom'  # Excess of Mass (better for varying densities)
        )

        logger.info(f"✅ HDBSCAN initialized: min_cluster_size={self.min_cluster_size}, metric={self.metric}, min_samples={self.min_samples}")

    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Cluster embeddings using HDBSCAN.

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
            labels = self.hdbscan.fit_predict(embeddings)

            # Count clusters (excluding noise)
            unique_labels = set(labels)
            n_clusters = len(unique_labels - {-1})
            n_noise = list(labels).count(-1)

            logger.info(f"✅ Clustering complete: {n_clusters} trends, {n_noise} noise videos")
            
            # Debug: cluster size distribution
            label_counts = {}
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
            
            # Sort by size (excluding noise)
            cluster_sizes = [(k, v) for k, v in label_counts.items() if k != -1]
            cluster_sizes.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"   Cluster sizes: {cluster_sizes}")
            logger.info(f"   Noise ratio: {n_noise/len(embeddings):.1%}")

            # Log cluster strength scores (unique to HDBSCAN)
            if hasattr(self.hdbscan, 'cluster_persistence_'):
                logger.debug(f"   Cluster strengths: {self.hdbscan.cluster_persistence_}")

            return labels

        except Exception as e:
            logger.error(f"❌ Clustering failed: {e}")
            raise

    def group_by_cluster(self, videos: list, labels: np.ndarray) -> dict:
        """
        Group videos by cluster label.

        Args:
            videos: List of video dicts
            labels: Cluster labels from HDBSCAN

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