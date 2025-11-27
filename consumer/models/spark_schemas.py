"""
Spark StructType schemas for data validation.

NOTE: Producer sends KafkaMessage wrapper format:
{
  "source": "tiktok",
  "collected_at": "...",
  "content_id": "...",
  "data": {...actual data...}
}

These schemas wrap the inner data schemas.
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    ArrayType, BooleanType
)


# Inner schemas (actual data objects)
_TIKTOK_VIDEO_INNER = StructType([
    # Core content (3)
    StructField("video_id", StringType(), True),
    StructField("text", StringType(), True),
    StructField("hashtags", ArrayType(StringType()), True),

    # Engagement metrics (5)
    StructField("views", LongType(), True),
    StructField("likes", LongType(), True),
    StructField("comments", LongType(), True),
    StructField("shares", LongType(), True),
    StructField("collects", LongType(), True),

    # Author credibility (3)
    StructField("author_username", StringType(), True),
    StructField("author_fans", LongType(), True),
    StructField("author_verified", BooleanType(), True),

    # Metadata (3)
    StructField("timestamp", StringType(), True),
    StructField("language", StringType(), True),
    StructField("video_url", StringType(), True),
])

# KafkaMessage wrapper for TikTok
TIKTOK_VIDEO_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("collected_at", StringType(), True),
    StructField("content_id", StringType(), True),
    StructField("data", _TIKTOK_VIDEO_INNER, True),
])


_NEWS_ARTICLE_INNER = StructType([
    StructField("article_id", StringType(), True),
    StructField("title", StringType(), True),
    StructField("summary", StringType(), True),
    StructField("url", StringType(), True),
    StructField("category", StringType(), True),
    StructField("published_at", StringType(), True),
    StructField("thumbnail", StringType(), True),
    StructField("author", StringType(), True),
])

# KafkaMessage wrapper for News
NEWS_ARTICLE_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("collected_at", StringType(), True),
    StructField("content_id", StringType(), True),
    StructField("data", _NEWS_ARTICLE_INNER, True),
])


_YOUTUBE_VIDEO_INNER = StructType([
    StructField("video_id", StringType(), True),
    StructField("title", StringType(), True),
    StructField("description", StringType(), True),
    StructField("url", StringType(), True),
    StructField("tags", ArrayType(StringType()), True),
    StructField("views", LongType(), True),
    StructField("likes", LongType(), True),
    StructField("comments", LongType(), True),
    StructField("channel_name", StringType(), True),
    StructField("channel_id", StringType(), True),
    StructField("published_at", StringType(), True),
    StructField("duration_seconds", LongType(), True),
    StructField("thumbnail", StringType(), True),
    StructField("category", StringType(), True),
])

# KafkaMessage wrapper for YouTube
YOUTUBE_VIDEO_SCHEMA = StructType([
    StructField("source", StringType(), True),
    StructField("collected_at", StringType(), True),
    StructField("content_id", StringType(), True),
    StructField("data", _YOUTUBE_VIDEO_INNER, True),
])
