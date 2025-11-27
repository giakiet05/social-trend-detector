"""
Spark StructType schemas for data validation.
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    ArrayType, BooleanType
)


# TikTok video schema (14 fields - matches common.models.TikTokVideo)
TIKTOK_VIDEO_SCHEMA = StructType([
    # Core content (3)
    StructField("video_id", StringType(), False),
    StructField("text", StringType(), False),
    StructField("hashtags", ArrayType(StringType()), True),

    # Engagement metrics (5)
    StructField("views", LongType(), False),
    StructField("likes", LongType(), False),
    StructField("comments", LongType(), False),
    StructField("shares", LongType(), False),
    StructField("collects", LongType(), False),

    # Author credibility (3)
    StructField("author_username", StringType(), False),
    StructField("author_fans", LongType(), False),
    StructField("author_verified", BooleanType(), False),

    # Metadata (3)
    StructField("timestamp", StringType(), False),
    StructField("language", StringType(), True),
    StructField("video_url", StringType(), True),
])


# News article schema (8 fields - matches common.models.NewsArticle)
NEWS_ARTICLE_SCHEMA = StructType([
    StructField("article_id", StringType(), False),
    StructField("title", StringType(), False),
    StructField("summary", StringType(), False),
    StructField("url", StringType(), False),
    StructField("category", StringType(), False),
    StructField("published_at", StringType(), False),
    StructField("thumbnail", StringType(), True),
    StructField("author", StringType(), True),
])


# YouTube video schema (14 fields - matches common.models.YouTubeVideo)
YOUTUBE_VIDEO_SCHEMA = StructType([
    StructField("video_id", StringType(), False),
    StructField("title", StringType(), False),
    StructField("description", StringType(), False),
    StructField("url", StringType(), False),
    StructField("tags", ArrayType(StringType()), True),
    StructField("views", LongType(), False),
    StructField("likes", LongType(), False),
    StructField("comments", LongType(), False),
    StructField("channel_name", StringType(), False),
    StructField("channel_id", StringType(), False),
    StructField("published_at", StringType(), False),
    StructField("duration_seconds", LongType(), False),
    StructField("thumbnail", StringType(), False),
    StructField("category", StringType(), True),
])
