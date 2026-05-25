# Metrics Logging Guide

## Overview

Hệ thống tự động log các metrics quan trọng sau mỗi batch processing vào thư mục `consumer/metrics/`.

## Metrics Được Log

Mỗi batch sẽ log các thông tin sau:

### 1. Pipeline Stages
- **Input/Output count** cho mỗi stage:
  - NormalizationStage: raw items → normalized items
  - CleaningStage: normalized → cleaned items
  - FilteringStage: cleaned → filtered (high-quality) items
  - EmbeddingStage: items with embeddings
  - ClusteringStage: clustered items
  - AnalysisStage: analyzed trends
  - DeduplicationStage: deduplicated trends
  - StorageStage: saved trends

### 2. Clustering Details
- Số clusters detected
- Cluster size distribution (min, max, avg)
- Noise rate (% items không vào cụm)

### 3. Deduplication
- Số trends mới
- Số trends merged (gộp với trends cũ)

### 4. Storage & Statistics
- Trends saved
- Sentiment breakdown (positive/negative/neutral)
- Risk level distribution
- Content type breakdown
- Source distribution (TikTok/YouTube/News)

## Chạy Hệ Thống

```bash
# Chạy producer + consumer (sẽ tự động log metrics)
python main.py

# Hoặc chạy riêng
python producer/main.py  # Collect data từ 3 sources
python consumer/batch_consumer.py  # Process & log metrics
```

## Xem Metrics

```bash
# Xem tất cả metrics từ tất cả batches
python extract_metrics.py

# Output sẽ bao gồm:
# - Chi tiết từng batch (input/output, clusters, dedup)
# - Tổng hợp overall (total items, avg cluster size, sentiment distribution, etc.)
```

## Metrics Files

Metrics được lưu dưới dạng JSON tại: `consumer/metrics/batch_YYYYMMDD_HHMMSS.json`

Mỗi file có cấu trúc:
```json
{
  "timestamp": "2025-01-30T...",
  "stages": {
    "NormalizationStage": {
      "input_count": 1850,
      "output_count": 1850
    },
    "CleaningStage": {
      "input_count": 1850,
      "output_count": 1756
    },
    ...
    "ClusteringStage": {
      "cluster_count": 12,
      "cluster_sizes": [78, 65, 45, ...],
      "noise_count": 85,
      "noise_rate": "8.2%"
    },
    ...
  },
  "summary": {
    "sentiment": {"positive": 8, "negative": 3, "neutral": 1},
    "risk_level": {"safe": 10, "careful": 2},
    "content_type": {...},
    "source_distribution": {"tiktok": 450, "youtube": 200, "news": 150}
  }
}
```

## Dùng Metrics Cho Report

Sau khi chạy 2-3 batches, mày có thể:

1. Gọi `python extract_metrics.py` để xem tóm tắt
2. Dùng dữ liệu cho phần **Experiments & Results** của báo cáo
3. Extract các con số như:
   - Total items processed
   - Avg cluster size
   - Noise rate
   - Sentiment/risk breakdown
   - Source distribution

## Lưu Ý

- Metrics tự động save sau mỗi lần chạy
- Mỗi batch là một file riêng biệt
- `extract_metrics.py` tự động aggregate tất cả files
- Có thể xóa `consumer/metrics/` folder nếu muốn reset

---

Tất cả metrics đều tự động được log - không cần setup thêm gì!
