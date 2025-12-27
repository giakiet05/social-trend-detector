"""
Shared data models for Producer and Consumer.

This module defines data models for multi-source social trend detection:
- Source-specific models: TikTokVideo, NewsArticle, YouTubeVideo, TrendsData
- Unified model: ContentItem (for Consumer pipeline)
- Kafka wrapper: KafkaMessage (for Producer → Kafka)
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
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


# ============================================
# NEW MODELS FOR MULTI-SOURCE SUPPORT
# ============================================

@dataclass
class NewsArticle:
    """News article raw data (from RSS feeds)."""
    article_id: str
    title: str
    summary: str
    url: str
    category: str
    published_at: str
    thumbnail: Optional[str] = None
    author: str = "VNExpress"

    def to_dict(self) -> dict:
        """Convert to dictionary for Kafka serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'NewsArticle':
        """Create NewsArticle from dictionary."""
        return cls(
            article_id=data.get("article_id", ""),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            url=data.get("url", ""),
            category=data.get("category", ""),
            published_at=data.get("published_at", ""),
            thumbnail=data.get("thumbnail"),
            author=data.get("author", "VNExpress"),
        )


@dataclass
class YouTubeVideo:
    """YouTube video raw data (from YouTube Data API v3)."""
    video_id: str
    title: str
    description: str
    url: str
    tags: List[str]
    views: int
    likes: int
    comments: int
    channel_name: str
    channel_id: str
    published_at: str
    duration_seconds: int
    thumbnail: str
    category: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for Kafka serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'YouTubeVideo':
        """Create YouTubeVideo from dictionary."""
        return cls(
            video_id=data.get("video_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            tags=data.get("tags", []),
            views=data.get("views", 0),
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            channel_name=data.get("channel_name", ""),
            channel_id=data.get("channel_id", ""),
            published_at=data.get("published_at", ""),
            duration_seconds=data.get("duration_seconds", 0),
            thumbnail=data.get("thumbnail", ""),
            category=data.get("category"),
        )


@dataclass
class TrendsData:
    """Google Trends data (from pytrends)."""
    query: str
    interest_over_time: List[Dict[str, Any]]  # [{"date": "2025-11-23", "interest": 100}]
    related_queries: List[Dict[str, Any]]     # [{"query": "...", "value": 100}]
    region: str = "VN"
    timeframe: str = "now 7-d"

    def to_dict(self) -> dict:
        """Convert to dictionary for Kafka serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TrendsData':
        """Create TrendsData from dictionary."""
        return cls(
            query=data.get("query", ""),
            interest_over_time=data.get("interest_over_time", []),
            related_queries=data.get("related_queries", []),
            region=data.get("region", "VN"),
            timeframe=data.get("timeframe", "now 7-d"),
        )


@dataclass
class ContentItem:
    """
    Unified content item from any source.

    This is the SINGLE SOURCE OF TRUTH for Consumer pipeline.
    All source-specific models are normalized to this schema in NormalizationStage.
    """
    content_id: str
    source: str  # "tiktok", "vnexpress", "youtube", "google_trends"
    collected_at: str

    # Content
    text: str
    url: Optional[str]
    hashtags: List[str]
    published_at: Optional[str]

    # Engagement (nullable for news/trends)
    views: Optional[int]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]

    # Author
    author_name: Optional[str]
    author_followers: Optional[int]

    # Source-specific metadata
    metadata: Dict[str, Any]

    def to_dict(self) -> dict:
        """Convert to dictionary for Spark processing."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ContentItem':
        """Create ContentItem from dictionary."""
        return cls(
            content_id=data.get("content_id", ""),
            source=data.get("source", ""),
            collected_at=data.get("collected_at", ""),
            text=data.get("text", ""),
            url=data.get("url"),
            hashtags=data.get("hashtags", []),
            published_at=data.get("published_at"),
            views=data.get("views"),
            likes=data.get("likes"),
            comments=data.get("comments"),
            shares=data.get("shares"),
            author_name=data.get("author_name"),
            author_followers=data.get("author_followers"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class KafkaMessage:
    """
    Wrapper for all messages sent to Kafka.

    Standard format:
    {
      "source": "tiktok",
      "collected_at": "2025-11-24T10:00:00Z",
      "content_id": "123456",
      "data": {...}  # TikTokVideo/NewsArticle/YouTubeVideo/TrendsData
    }
    """
    source: str
    collected_at: str
    content_id: str
    data: Dict[str, Any]  # Raw data object (varies by source)

    def to_dict(self) -> dict:
        """Convert to dictionary for Kafka serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'KafkaMessage':
        """
        Create KafkaMessage from dictionary (deserialize from Kafka).

        Args:
            data: Dictionary with KafkaMessage structure

        Returns:
            KafkaMessage instance with nested data dict
        """
        return cls(
            source=data.get("source", ""),
            collected_at=data.get("collected_at", ""),
            content_id=data.get("content_id", ""),
            data=data.get("data", {})
        )

    def to_source_model(self):
        """
        Convert nested data to source-specific model.

        Returns:
            TikTokVideo | NewsArticle | YouTubeVideo | TrendsData

        Raises:
            ValueError: If source is unknown
        """
        if self.source == "tiktok":
            return TikTokVideo.from_dict(self.data)
        elif self.source == "vnexpress":
            return NewsArticle.from_dict(self.data)
        elif self.source == "youtube":
            return YouTubeVideo.from_dict(self.data)
        elif self.source == "google_trends":
            return TrendsData.from_dict(self.data)
        else:
            raise ValueError(f"Unknown source: {self.source}")

    @classmethod
    def from_tiktok(cls, video: TikTokVideo) -> 'KafkaMessage':
        """Create KafkaMessage from TikTokVideo."""
        return cls(
            source="tiktok",
            collected_at=datetime.utcnow().isoformat(),
            content_id=video.video_id,
            data=video.to_dict()
        )

    @classmethod
    def from_news(cls, article: NewsArticle) -> 'KafkaMessage':
        """Create KafkaMessage from NewsArticle."""
        return cls(
            source="vnexpress",
            collected_at=datetime.utcnow().isoformat(),
            content_id=article.article_id,
            data=article.to_dict()
        )

    @classmethod
    def from_youtube(cls, video: YouTubeVideo) -> 'KafkaMessage':
        """Create KafkaMessage from YouTubeVideo."""
        return cls(
            source="youtube",
            collected_at=datetime.utcnow().isoformat(),
            content_id=video.video_id,
            data=video.to_dict()
        )

    @classmethod
    def from_trends(cls, trends: TrendsData) -> 'KafkaMessage':
        """Create KafkaMessage from TrendsData."""
        return cls(
            source="google_trends",
            collected_at=datetime.utcnow().isoformat(),
            content_id=f"{trends.query}_{datetime.utcnow().strftime('%Y%m%d')}",
            data=trends.to_dict()
        )


@dataclass
class Trend:
    """
    Detected trend data model for MongoDB (multi-source support).

    Used by Consumer to store detected trends and Dashboard to display them.
    """
    timestamp: datetime
    topic: str
    summary: str
    sentiment: str
    keywords: List[str]
    video_count: int
    total_views: int
    total_likes: int
    sample_videos: List[dict]
    source_counts: dict  # {"tiktok": 15, "youtube": 5, "news": 2}

    # Guideline fields
    content_type: str = "entertainment"  # entertainment, drama, dangerous, social_issue, commercial
    risk_level: str = "safe"  # safe, cautious, high_risk, dangerous
    last_updated: datetime = None  # Last merge/update time (for timeout)

    def __post_init__(self):
        """Initialize guidelines dict and last_updated if not provided."""
        if not hasattr(self, 'guidelines'):
            self.guidelines = {}

        # Initialize last_updated to timestamp if not set (new trends)
        if self.last_updated is None:
            self.last_updated = self.timestamp

    guidelines: Dict = None  # Guidelines for marketers & social managers

    def to_dict(self):
        """Convert to dictionary for MongoDB."""
        from dataclasses import asdict
        data = asdict(self)
        # Convert datetime to ISO string for MongoDB
        data['timestamp'] = self.timestamp.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data
