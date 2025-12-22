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

        # Adaptive min cluster size based on batch size (more sensitive)
        batch_size = len(items)
        adaptive_min_size = max(15, batch_size // 60)  # 1.7% or min 15 (was 2.5%)
        logger.info(f"   Adaptive min_cluster_size: {adaptive_min_size} (batch: {batch_size})")

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

        # Two-pass clustering: assign noise items to nearest clusters
        labels = self._assign_noise_to_clusters(items, labels, embeddings)
        
        # Re-group by cluster with updated labels
        clusters = {}
        noise_count = 0

        for item, label in zip(items, labels):
            if label == -1:
                noise_count += 1
                continue

            if label not in clusters:
                clusters[label] = []
            clusters[label].append(item)

        logger.info(f"   After noise assignment: {len(clusters)} clusters, {noise_count} noise items")
        if noise_count > 0:
            new_noise_ratio = noise_count / len(items)
            logger.info(f"   Improved noise ratio: {new_noise_ratio:.1%}")

        # Filter small clusters (use adaptive size)
        valid_clusters = {}
        filtered_count = 0

        for cluster_id, cluster_items in clusters.items():
            if len(cluster_items) >= adaptive_min_size:
                valid_clusters[cluster_id] = cluster_items
            else:
                filtered_count += 1
                logger.debug(f"Filtered cluster {cluster_id}: only {len(cluster_items)} items (min: {adaptive_min_size})")

        if filtered_count > 0:
            logger.info(f"   Filtered {filtered_count} small clusters (< {adaptive_min_size} items)")

        self.log_complete(f"{len(valid_clusters)} valid clusters (from {len(clusters)} total)")

        return valid_clusters

    def _assign_noise_to_clusters(self, items: List[ContentItem], labels: np.ndarray, 
                                  embeddings: np.ndarray) -> np.ndarray:
        """
        Two-pass clustering: assign noise items to nearest clusters.
        
        Args:
            items: ContentItem objects  
            labels: Cluster labels from HDBSCAN
            embeddings: Item embeddings
            
        Returns:
            Updated labels with some noise items assigned to clusters
        """
        # Find unique cluster IDs (excluding noise = -1)
        cluster_ids = [label for label in set(labels) if label != -1]
        
        if len(cluster_ids) == 0:
            logger.warning("No clusters found for noise assignment")
            return labels
            
        # Calculate cluster centroids
        cluster_centroids = {}
        for cluster_id in cluster_ids:
            cluster_mask = labels == cluster_id
            cluster_embeddings = embeddings[cluster_mask]
            centroid = np.mean(cluster_embeddings, axis=0)
            cluster_centroids[cluster_id] = centroid
            
        # Distance threshold for assignment (tunable)
        distance_threshold = 0.5  # Cosine distance threshold
        
        # Process noise items
        updated_labels = labels.copy()
        assigned_count = 0
        
        noise_indices = np.where(labels == -1)[0]
        logger.info(f"   Attempting to assign {len(noise_indices)} noise items to clusters...")
        
        for idx in noise_indices:
            item_embedding = embeddings[idx]
            
            # Find nearest cluster centroid
            min_distance = float('inf')
            nearest_cluster = -1
            
            for cluster_id, centroid in cluster_centroids.items():
                # Calculate cosine distance
                distance = 1.0 - np.dot(item_embedding, centroid) / (
                    np.linalg.norm(item_embedding) * np.linalg.norm(centroid)
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_cluster = cluster_id
            
            # Assign to nearest cluster if within threshold
            if min_distance <= distance_threshold:
                updated_labels[idx] = nearest_cluster
                assigned_count += 1
                
        logger.info(f"   Assigned {assigned_count}/{len(noise_indices)} noise items to clusters")
        logger.info(f"   Remaining noise: {len(noise_indices) - assigned_count} items")
        
        return updated_labels
