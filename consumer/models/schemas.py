"""
Data models for Consumer.
"""

from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime



@dataclass
class Trend:
    """Trend data model for MongoDB."""
    timestamp: datetime
    topic: str
    summary: str
    sentiment: str
    keywords: List[str]
    video_count: int
    total_views: int
    total_likes: int
    sample_videos: List[dict]

    def to_dict(self):
        data = asdict(self)
        # Convert datetime to ISO string for MongoDB
        data['timestamp'] = self.timestamp.isoformat()
        return data
