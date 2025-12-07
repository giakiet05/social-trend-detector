"""
Data models for Consumer.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime



@dataclass
class Trend:
    """Trend data model for MongoDB (multi-source + business metrics support)."""
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
    
    # Business Metrics (calculated)
    viral_score: float = 0.0                    # 1-10 scale
    growth_rate: float = 0.0                   # % growth in mentions
    estimated_reach: int = 0                   # Total estimated audience
    engagement_rate: float = 0.0               # Overall engagement rate
    peak_hours: List[str] = field(default_factory=list)  # ["19:00", "20:00"]
    audience_demographics: Optional[Dict] = field(default_factory=dict)
    content_insights: Optional[Dict] = field(default_factory=dict)
    hashtag_performance: List[Dict] = field(default_factory=list)
    
    # Action Planning (marketing recommendations)
    action_plan: Optional[Dict] = field(default_factory=dict)

    def to_dict(self):
        data = asdict(self)
        # Convert datetime to ISO string for MongoDB
        data['timestamp'] = self.timestamp.isoformat()
        return data
