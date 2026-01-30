"""
Metrics logger for trend detection pipeline.
Logs structured metrics to JSON file for analysis and reporting.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class MetricsLogger:
    """Log pipeline metrics to JSON file."""

    def __init__(self, metrics_dir: str = "consumer/metrics"):
        """
        Initialize metrics logger.

        Args:
            metrics_dir: Directory to save metrics files
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Current batch metrics
        self.batch_timestamp = datetime.now().isoformat()
        self.batch_file = self.metrics_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Initialize batch metrics
        self.metrics = {
            "timestamp": self.batch_timestamp,
            "stages": {},
            "summary": {}
        }

    def log_stage_input(self, stage_name: str, count: int):
        """Log items count before stage."""
        if stage_name not in self.metrics["stages"]:
            self.metrics["stages"][stage_name] = {}

        self.metrics["stages"][stage_name]["input_count"] = count
        logger.info(f"   [{stage_name}] Input: {count} items")

    def log_stage_output(self, stage_name: str, count: int):
        """Log items count after stage."""
        if stage_name not in self.metrics["stages"]:
            self.metrics["stages"][stage_name] = {}

        self.metrics["stages"][stage_name]["output_count"] = count
        dropped = self.metrics["stages"][stage_name].get("input_count", 0) - count
        logger.info(f"   [{stage_name}] Output: {count} items (dropped: {dropped})")

    def log_clustering(self, cluster_count: int, cluster_sizes: List[int], noise_count: int):
        """Log clustering results."""
        if "ClusteringStage" not in self.metrics["stages"]:
            self.metrics["stages"]["ClusteringStage"] = {}

        self.metrics["stages"]["ClusteringStage"]["cluster_count"] = cluster_count
        self.metrics["stages"]["ClusteringStage"]["cluster_sizes"] = cluster_sizes
        self.metrics["stages"]["ClusteringStage"]["noise_count"] = noise_count
        self.metrics["stages"]["ClusteringStage"]["noise_rate"] = (
            f"{(noise_count / (sum(cluster_sizes) + noise_count) * 100):.1f}%"
            if (sum(cluster_sizes) + noise_count) > 0 else "0%"
        )

        avg_size = sum(cluster_sizes) / len(cluster_sizes) if cluster_sizes else 0
        logger.info(f"   [ClusteringStage] {cluster_count} clusters, "
                   f"avg size: {avg_size:.1f}, "
                   f"noise: {noise_count} ({self.metrics['stages']['ClusteringStage']['noise_rate']})")

    def log_deduplication(self, new_trends_count: int, merged_count: int):
        """Log deduplication results."""
        if "DeduplicationStage" not in self.metrics["stages"]:
            self.metrics["stages"]["DeduplicationStage"] = {}

        self.metrics["stages"]["DeduplicationStage"]["new_trends"] = new_trends_count
        self.metrics["stages"]["DeduplicationStage"]["merged_trends"] = merged_count

        logger.info(f"   [DeduplicationStage] New trends: {new_trends_count}, "
                   f"Merged: {merged_count}")

    def log_storage(self, saved_count: int, stats: Dict[str, Any]):
        """Log storage results and trend statistics."""
        if "StorageStage" not in self.metrics["stages"]:
            self.metrics["stages"]["StorageStage"] = {}

        self.metrics["stages"]["StorageStage"]["saved_count"] = saved_count
        self.metrics["stages"]["StorageStage"]["stats"] = stats

        # Extract sentiment and risk distribution
        sentiment_counts = {}
        risk_counts = {}
        content_type_counts = {}
        source_distribution = {"tiktok": 0, "youtube": 0, "news": 0}

        for trend in stats.get("trends", []):
            # Sentiment
            sentiment = trend.get("sentiment", "unknown")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

            # Risk level
            risk = trend.get("risk_level", "unknown")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

            # Content type
            content_type = trend.get("content_type", "unknown")
            content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1

            # Source distribution
            sources = trend.get("source_counts", {})
            for source, count in sources.items():
                if source.lower() in source_distribution:
                    source_distribution[source.lower()] += count

        self.metrics["summary"]["sentiment"] = sentiment_counts
        self.metrics["summary"]["risk_level"] = risk_counts
        self.metrics["summary"]["content_type"] = content_type_counts
        self.metrics["summary"]["source_distribution"] = source_distribution

        logger.info(f"   [StorageStage] Saved: {saved_count} trends")
        logger.info(f"   Sentiment: {sentiment_counts}")
        logger.info(f"   Risk level: {risk_counts}")
        logger.info(f"   Content type: {content_type_counts}")
        logger.info(f"   Source distribution: {source_distribution}")

    def log_source_distribution(self, source_counts: Dict[str, int]):
        """Log input data source distribution."""
        if "source_distribution" not in self.metrics["summary"]:
            self.metrics["summary"]["source_distribution"] = {}

        self.metrics["summary"]["source_distribution"].update(source_counts)
        logger.info(f"   Input sources: {source_counts}")

    def save(self):
        """Save metrics to JSON file."""
        try:
            with open(self.batch_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
            logger.info(f"Metrics saved to {self.batch_file}")
            return str(self.batch_file)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
            return None

    @staticmethod
    def load_all_metrics(metrics_dir: str = "consumer/metrics") -> List[Dict]:
        """Load all metrics files."""
        metrics_path = Path(metrics_dir)
        if not metrics_path.exists():
            return []

        all_metrics = []
        for file in sorted(metrics_path.glob("batch_*.json")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    all_metrics.append(json.load(f))
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")

        return all_metrics

    @staticmethod
    def summarize_metrics(all_metrics: List[Dict]) -> Dict[str, Any]:
        """Summarize metrics across multiple batches."""
        if not all_metrics:
            return {}

        summary = {
            "total_batches": len(all_metrics),
            "total_items_processed": 0,
            "total_clusters_detected": 0,
            "total_trends_saved": 0,
            "avg_cluster_size": [],
            "all_sentiment_counts": {},
            "all_risk_counts": {},
            "all_source_distribution": {"tiktok": 0, "youtube": 0, "news": 0}
        }

        for batch in all_metrics:
            # Items count
            if "NormalizationStage" in batch["stages"]:
                summary["total_items_processed"] += batch["stages"]["NormalizationStage"].get("input_count", 0)

            # Clustering
            if "ClusteringStage" in batch["stages"]:
                cluster_count = batch["stages"]["ClusteringStage"].get("cluster_count", 0)
                cluster_sizes = batch["stages"]["ClusteringStage"].get("cluster_sizes", [])
                summary["total_clusters_detected"] += cluster_count
                summary["avg_cluster_size"].extend(cluster_sizes)

            # Storage
            if "StorageStage" in batch["stages"]:
                summary["total_trends_saved"] += batch["stages"]["StorageStage"].get("saved_count", 0)

            # Summary stats
            if "summary" in batch:
                for sentiment, count in batch["summary"].get("sentiment", {}).items():
                    summary["all_sentiment_counts"][sentiment] = summary["all_sentiment_counts"].get(sentiment, 0) + count

                for risk, count in batch["summary"].get("risk_level", {}).items():
                    summary["all_risk_counts"][risk] = summary["all_risk_counts"].get(risk, 0) + count

                sources = batch["summary"].get("source_distribution", {})
                for source, count in sources.items():
                    if source.lower() in summary["all_source_distribution"]:
                        summary["all_source_distribution"][source.lower()] += count

        # Calculate average cluster size
        if summary["avg_cluster_size"]:
            summary["avg_cluster_size"] = sum(summary["avg_cluster_size"]) / len(summary["avg_cluster_size"])
        else:
            summary["avg_cluster_size"] = 0

        return summary
