"""
Data models for Consumer.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime



@dataclass
class Trend:
    """Trend data model for MongoDB (multi-source support)."""
    timestamp: datetime
    topic: str
    summary: str
    sentiment: str
    keywords: List[str]
    video_count: int
    total_views: int
    total_likes: int
    sample_videos: List[dict]
    source_counts: dict  # {"tiktok": 15, "youtube": 5, "vnexpress": 2}

    # Guideline fields
    content_type: str = "entertainment"  # entertainment, drama, dangerous, social_issue, commercial
    risk_level: str = "safe"  # safe, cautious, high_risk, dangerous
    guidelines: Dict = field(default_factory=dict)  # Guidelines for marketers & social managers

    def to_dict(self):
        data = asdict(self)
        # Convert datetime to ISO string for MongoDB
        data['timestamp'] = self.timestamp.isoformat()
        return data
