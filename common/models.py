"""
Shared data models for Producer and Consumer.

This module defines the canonical schema for TikTok videos
that is used across the entire pipeline.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class TikTokVideo:
    """
    Canonical TikTok video data model (FLAT structure).

    This is the SINGLE SOURCE OF TRUTH for video schema.
    Both Producer and Consumer MUST use this exact structure.

    Fields optimized for trend detection and noise filtering:

    Core Content (3 fields):
        video_id: Unique video identifier
        text: Video caption/description
        hashtags: List of hashtag strings (without #)

    Engagement Metrics (5 fields):
        views: View count (playCount)
        likes: Like count (diggCount)
        comments: Comment count
        shares: Share count
        collects: Save/collect count (STRONG quality signal)

    Author Credibility (3 fields):
        author_username: Author username (for deduplication)
        author_fans: Author follower count (spam filter)
        author_verified: Whether author is verified (quality signal)

    Metadata (3 fields):
        timestamp: Video creation time (ISO format string)
        language: Text language code (for filtering)
        video_url: Web URL to video (optional, for reference)

    Total: 14 fields (optimized balance)
    """
    # Core content
    video_id: str
    text: str
    hashtags: List[str]

    # Engagement metrics
    views: int
    likes: int
    comments: int
    shares: int
    collects: int

    # Author credibility
    author_username: str
    author_fans: int
    author_verified: bool

    # Metadata
    timestamp: str
    language: Optional[str] = None
    video_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for Kafka serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TikTokVideo':
        """
        Create TikTokVideo from dictionary.

        Args:
            data: Dictionary with video data

        Returns:
            TikTokVideo instance
        """
        return cls(
            video_id=data.get("video_id", ""),
            text=data.get("text", ""),
            hashtags=data.get("hashtags", []),
            views=data.get("views", 0),
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            shares=data.get("shares", 0),
            collects=data.get("collects", 0),
            author_username=data.get("author_username", ""),
            author_fans=data.get("author_fans", 0),
            author_verified=data.get("author_verified", False),
            timestamp=data.get("timestamp", ""),
            language=data.get("language"),
            video_url=data.get("video_url"),
        )

    def calculate_engagement_rate(self) -> float:
        """
        Calculate engagement rate.

        Returns:
            Engagement rate (0.0 to 1.0+)
        """
        if self.views == 0:
            return 0.0
        return (self.likes + self.comments + self.shares) / self.views

    def calculate_engagement_score(self) -> float:
        """
        Calculate weighted engagement score.

        Different actions have different weights:
        - Likes: 1.0 (easiest action)
        - Comments: 2.0 (requires effort)
        - Shares: 3.0 (strong signal)
        - Collects: 4.0 (strongest quality signal)

        Returns:
            Weighted engagement score
        """
        return (
            self.likes * 1.0 +
            self.comments * 2.0 +
            self.shares * 3.0 +
            self.collects * 4.0
        )

    def is_quality_content(self, min_engagement_rate: float = 0.01) -> bool:
        """
        Check if this is quality content based on engagement.

        Args:
            min_engagement_rate: Minimum engagement rate threshold (default 1%)

        Returns:
            True if quality content, False otherwise
        """
        return self.calculate_engagement_rate() >= min_engagement_rate

    def is_viral(self, min_share_rate: float = 0.02) -> bool:
        """
        Check if this video is viral based on share rate.

        Args:
            min_share_rate: Minimum share rate threshold (default 2%)

        Returns:
            True if viral, False otherwise
        """
        if self.views == 0:
            return False
        return (self.shares / self.views) >= min_share_rate

    @classmethod
    def from_csv_row(cls, row: dict) -> 'TikTokVideo':
        """
        Parse CSV row from Apify TikTok scraper to TikTokVideo object.

        Args:
            row: Dictionary from csv.DictReader

        Returns:
            TikTokVideo instance

        CSV Field Mapping:
            id → video_id
            text → text
            hashtags/0/name ... hashtags/9/name → hashtags (list)
            playCount → views
            diggCount → likes
            commentCount → comments
            shareCount → shares
            collectCount → collects
            authorMeta/name → author_username
            authorMeta/fans → author_fans
            authorMeta/verified → author_verified
            createTimeISO → timestamp
            textLanguage → language
            webVideoUrl → video_url
        """
        # Parse hashtags (up to 28 possible based on CSV, but typically 10)
        hashtags = []
        for i in range(28):  # CSV has up to hashtags/27/name
            key = f"hashtags/{i}/name"
            if key in row and row[key]:
                hashtags.append(row[key])

        # Parse timestamp
        try:
            create_time = datetime.fromisoformat(row.get("createTimeISO", ""))
            timestamp = create_time.isoformat()
        except:
            timestamp = datetime.now().isoformat()

        # Parse boolean verified
        verified_str = row.get("authorMeta/verified", "false")
        if isinstance(verified_str, str):
            verified = verified_str.lower() == "true"
        else:
            verified = bool(verified_str)

        return cls(
            video_id=row.get("id", ""),
            text=row.get("text", ""),
            hashtags=hashtags,
            views=int(row.get("playCount", 0) or 0),
            likes=int(row.get("diggCount", 0) or 0),
            comments=int(row.get("commentCount", 0) or 0),
            shares=int(row.get("shareCount", 0) or 0),
            collects=int(row.get("collectCount", 0) or 0),
            author_username=row.get("authorMeta/name", ""),
            author_fans=int(row.get("authorMeta/fans", 0) or 0),
            author_verified=verified,
            timestamp=timestamp,
            language=row.get("textLanguage"),
            video_url=row.get("webVideoUrl"),
        )
