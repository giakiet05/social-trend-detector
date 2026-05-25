#!/usr/bin/env python3
"""
Extract and summarize metrics from completed batches.
Run this after each batch processing to generate a metrics report.
"""

import json
import sys
from pathlib import Path
from consumer.utils.metrics_logger import MetricsLogger

def print_batch_metrics(batch_metrics: dict):
    """Print individual batch metrics."""
    print(f"\n{'='*70}")
    print(f"Batch: {batch_metrics['timestamp']}")
    print(f"{'='*70}")

    # Stages breakdown
    if "stages" in batch_metrics:
        print("\n📊 Pipeline Stages:")
        for stage_name, stage_data in batch_metrics["stages"].items():
            input_count = stage_data.get("input_count", "N/A")
            output_count = stage_data.get("output_count", "N/A")
            print(f"  {stage_name}:")
            print(f"    Input: {input_count} items")
            if output_count != "N/A":
                print(f"    Output: {output_count} items")

        # Clustering details
        if "ClusteringStage" in batch_metrics["stages"]:
            clustering = batch_metrics["stages"]["ClusteringStage"]
            print(f"\n  🔗 Clustering Results:")
            print(f"    Clusters detected: {clustering.get('cluster_count', 'N/A')}")
            print(f"    Avg cluster size: {sum(clustering.get('cluster_sizes', [])) / len(clustering.get('cluster_sizes', [1])):.1f}")
            print(f"    Min/Max size: {min(clustering.get('cluster_sizes', [0]))}/{max(clustering.get('cluster_sizes', [0]))}")
            print(f"    Noise items: {clustering.get('noise_count', 'N/A')}")
            print(f"    Noise rate: {clustering.get('noise_rate', 'N/A')}")

        # Deduplication details
        if "DeduplicationStage" in batch_metrics["stages"]:
            dedup = batch_metrics["stages"]["DeduplicationStage"]
            print(f"\n  🔄 Deduplication:")
            print(f"    New trends: {dedup.get('new_trends', 'N/A')}")
            print(f"    Merged trends: {dedup.get('merged_trends', 'N/A')}")

        # Storage details
        if "StorageStage" in batch_metrics["stages"]:
            storage = batch_metrics["stages"]["StorageStage"]
            print(f"\n  💾 Storage:")
            print(f"    Trends saved: {storage.get('saved_count', 'N/A')}")

    # Summary statistics
    if "summary" in batch_metrics:
        summary = batch_metrics["summary"]
        print(f"\n📈 Summary Statistics:")

        if "sentiment" in summary:
            print(f"  Sentiment:")
            for sent, count in summary["sentiment"].items():
                print(f"    {sent}: {count}")

        if "risk_level" in summary:
            print(f"  Risk Level:")
            for risk, count in summary["risk_level"].items():
                print(f"    {risk}: {count}")

        if "content_type" in summary:
            print(f"  Content Type:")
            for ctype, count in summary["content_type"].items():
                print(f"    {ctype}: {count}")

        if "source_distribution" in summary:
            print(f"  Source Distribution:")
            sources = summary["source_distribution"]
            total = sum(sources.values())
            for source, count in sources.items():
                pct = (count / total * 100) if total > 0 else 0
                print(f"    {source}: {count} ({pct:.1f}%)")


def print_summary_report(all_metrics: list):
    """Print overall summary across all batches."""
    if not all_metrics:
        print("❌ No metrics found")
        return

    summary = MetricsLogger.summarize_metrics(all_metrics)

    print(f"\n\n{'='*70}")
    print("📊 OVERALL SUMMARY")
    print(f"{'='*70}")

    print(f"\n📋 Batch Statistics:")
    print(f"  Total batches: {summary['total_batches']}")
    print(f"  Total items processed: {summary['total_items_processed']}")
    print(f"  Total clusters detected: {summary['total_clusters_detected']}")
    print(f"  Total trends saved: {summary['total_trends_saved']}")
    print(f"  Avg cluster size: {summary['avg_cluster_size']:.1f}")

    print(f"\n😊 Sentiment Breakdown:")
    for sentiment, count in summary.get("all_sentiment_counts", {}).items():
        print(f"  {sentiment}: {count}")

    print(f"\n⚠️  Risk Level Breakdown:")
    for risk, count in summary.get("all_risk_counts", {}).items():
        print(f"  {risk}: {count}")

    print(f"\n📱 Source Distribution (across all trends):")
    sources = summary.get("all_source_distribution", {})
    total = sum(sources.values())
    for source, count in sources.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {source}: {count} ({pct:.1f}%)")

    print(f"\n{'='*70}\n")


def main():
    """Load and display metrics."""
    metrics_dir = "consumer/metrics"
    all_metrics = MetricsLogger.load_all_metrics(metrics_dir)

    if not all_metrics:
        print(f"❌ No metrics found in {metrics_dir}")
        print("Run producer and consumer first to generate metrics")
        sys.exit(1)

    # Print individual batch metrics
    for batch_metrics in all_metrics:
        print_batch_metrics(batch_metrics)

    # Print overall summary
    print_summary_report(all_metrics)


if __name__ == "__main__":
    main()
