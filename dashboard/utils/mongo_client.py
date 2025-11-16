"""
MongoDB client for Dashboard - Read trends data.
"""

from pymongo import MongoClient
from typing import List, Dict
import streamlit as st


class DashboardMongoClient:
    """MongoDB client for reading trends."""

    def __init__(self, connection_string: str = "mongodb://admin:password@localhost:27017/?authSource=admin"):
        """Initialize MongoDB client."""
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.collection = None

    @st.cache_resource
    def connect(_self):
        """Establish MongoDB connection (cached)."""
        _self.client = MongoClient(_self.connection_string)
        _self.db = _self.client['tiktok_trends']
        _self.collection = _self.db['trends']
        return _self

    def get_all_trends(self, limit: int = 100) -> List[Dict]:
        """
        Get all trends sorted by timestamp (newest first).

        Args:
            limit: Maximum number of trends to return

        Returns:
            List of trend documents
        """
        if self.collection is None:
            self.connect()

        trends = list(
            self.collection.find()
            .sort('timestamp', -1)
            .limit(limit)
        )

        # Convert ObjectId to string for Streamlit
        for trend in trends:
            trend['_id'] = str(trend['_id'])

        return trends

    def get_trend_by_id(self, trend_id: str) -> Dict:
        """Get a single trend by ID."""
        if self.collection is None:
            self.connect()

        from bson import ObjectId
        trend = self.collection.find_one({'_id': ObjectId(trend_id)})

        if trend:
            trend['_id'] = str(trend['_id'])

        return trend

    def get_trends_stats(self) -> Dict:
        """
        Get aggregate statistics about trends.

        Returns:
            Dict with total_trends, total_videos, sentiments breakdown
        """
        if self.collection is None:
            self.connect()

        total_trends = self.collection.count_documents({})

        # Aggregate total videos
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_videos': {'$sum': '$video_count'},
                    'total_views': {'$sum': '$total_views'},
                    'total_likes': {'$sum': '$total_likes'}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        totals = result[0] if result else {'total_videos': 0, 'total_views': 0, 'total_likes': 0}

        # Sentiment breakdown
        sentiment_pipeline = [
            {
                '$group': {
                    '_id': '$sentiment',
                    'count': {'$sum': 1}
                }
            }
        ]

        sentiment_result = list(self.collection.aggregate(sentiment_pipeline))
        sentiments = {item['_id']: item['count'] for item in sentiment_result}

        return {
            'total_trends': total_trends,
            'total_videos': totals.get('total_videos', 0),
            'total_views': totals.get('total_views', 0),
            'total_likes': totals.get('total_likes', 0),
            'sentiments': sentiments
        }
