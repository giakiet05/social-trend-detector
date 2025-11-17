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
