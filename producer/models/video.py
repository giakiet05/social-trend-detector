"""
TikTok video data model.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class TikTokVideo:
    """Schema for TikTok video from Apify CSV."""

    # Core fields
    video_id: str
    text: str
    author_username: str
    author_nickname: str
    create_time: datetime

    # Engagement metrics
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    collects: int = 0

    # Additional info
    hashtags: List[str] = field(default_factory=list)
    music_name: Optional[str] = None
    music_author: Optional[str] = None
    video_url: Optional[str] = None
    language: Optional[str] = None

    # Author info
    author_fans: int = 0
    author_verified: bool = False

    # Metadata
    scraped_at: datetime = field(default_factory=datetime.now)
    niche: str = "general"

    def to_dict(self) -> dict:
        """Convert to dict for Kafka message."""
        return {
            "video_id": self.video_id,
            "text": self.text,
            "author": {
                "username": self.author_username,
                "nickname": self.author_nickname,
                "fans": self.author_fans,
                "verified": self.author_verified
            },
            "create_time": self.create_time.isoformat(),
            "engagement": {
                "likes": self.likes,
                "comments": self.comments,
                "shares": self.shares,
                "views": self.views,
                "collects": self.collects
            },
            "hashtags": self.hashtags,
            "music": {
                "name": self.music_name,
                "author": self.music_author
            },
            "video_url": self.video_url,
            "language": self.language,
            "metadata": {
                "scraped_at": self.scraped_at.isoformat(),
                "niche": self.niche
            }
        }

    @classmethod
    def from_csv_row(cls, row: dict) -> 'TikTokVideo':
        """
        Parse CSV row to TikTokVideo object.

        Args:
            row: Dictionary from csv.DictReader

        Returns:
            TikTokVideo instance
        """
        # Parse hashtags (up to 10 possible)
        hashtags = []
        for i in range(10):
            key = f"hashtags/{i}/name"
            if key in row and row[key]:
                hashtags.append(row[key])

        # Parse timestamp
        try:
            create_time = datetime.fromisoformat(row.get("createTimeISO", ""))
        except:
            create_time = datetime.now()

        # Parse boolean
        verified = row.get("authorMeta/verified", "false").lower() == "true"

        return cls(
            video_id=row.get("id", ""),
            text=row.get("text", ""),
            author_username=row.get("authorMeta/name", ""),
            author_nickname=row.get("authorMeta/nickName", ""),
            create_time=create_time,
            likes=int(row.get("diggCount", 0) or 0),
            comments=int(row.get("commentCount", 0) or 0),
            shares=int(row.get("shareCount", 0) or 0),
            views=int(row.get("playCount", 0) or 0),
            collects=int(row.get("collectCount", 0) or 0),
            hashtags=hashtags,
            music_name=row.get("musicMeta/musicName"),
            music_author=row.get("musicMeta/musicAuthor"),
            video_url=row.get("webVideoUrl"),
            language=row.get("textLanguage"),
            author_fans=int(row.get("authorMeta/fans", 0) or 0),
            author_verified=verified,
            scraped_at=datetime.now(),
            niche="general"
        )
