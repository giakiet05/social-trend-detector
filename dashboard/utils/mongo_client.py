"""
MongoDB client for Dashboard - Read trends data.
"""

import os
from pymongo import MongoClient
from typing import List, Dict
import streamlit as st


class DashboardMongoClient:
    """MongoDB client for reading trends."""

    def __init__(self, connection_string: str = None):
        """Initialize MongoDB client."""
        if connection_string is None:
            connection_string = os.getenv(
                "MONGO_URI",
                "mongodb://admin:password@localhost:27017/?authSource=admin"
            )
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.collection = None

    @st.cache_resource
    def connect(_self):
        """Establish MongoDB connection (cached)."""
        _self.client = MongoClient(_self.connection_string)
        _self.db = _self.client['social_trends']
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

    def delete_trend(self, trend_id: str) -> bool:
        """
        Delete a trend by ID (admin only).

        Args:
            trend_id: MongoDB ObjectId string

        Returns:
            True if deleted successfully, False otherwise
        """
        if self.collection is None:
            self.connect()

        try:
            from bson import ObjectId
            result = self.collection.delete_one({'_id': ObjectId(trend_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting trend: {e}")
            return False

    def get_extracted_keywords(self, status: str = 'pending', limit: int = 100) -> List[Dict]:
        """
        Get extracted keywords from keyword extractor service.

        Args:
            status: Filter by status (pending/approved/rejected), or 'all' for no filter
            limit: Maximum number of keywords to return

        Returns:
            List of extracted keyword documents
        """
        if self.db is None:
            self.connect()

        extracted_collection = self.db['extracted_keywords']

        if status == 'all':
            keywords = list(
                extracted_collection.find()
                .sort('extracted_at', -1)
                .limit(limit)
            )
        else:
            keywords = list(
                extracted_collection.find({'status': status})
                .sort('extracted_at', -1)
                .limit(limit)
            )

        for kw in keywords:
            kw['_id'] = str(kw['_id'])

        return keywords

    def approve_extracted_keyword(self, keyword_id: str, keyword_text: str, approved_by: str = "admin") -> Dict:
        """
        Approve an extracted keyword and add to active keywords.

        Args:
            keyword_id: MongoDB ObjectId string of extracted keyword
            keyword_text: The keyword text to add
            approved_by: Who approved the keyword

        Returns:
            Dict with success status and message
        """
        if self.db is None:
            self.connect()

        try:
            from bson import ObjectId
            from datetime import datetime

            extracted_collection = self.db['extracted_keywords']

            result = extracted_collection.update_one(
                {'_id': ObjectId(keyword_id)},
                {
                    '$set': {
                        'status': 'approved',
                        'approved_at': datetime.utcnow().isoformat(),
                        'approved_by': approved_by
                    }
                }
            )

            if result.modified_count > 0:
                return {
                    'success': True,
                    'message': f"Đã duyệt từ khóa: {keyword_text}"
                }
            else:
                return {
                    'success': False,
                    'message': "Không tìm thấy từ khóa hoặc đã được duyệt"
                }

        except Exception as e:
            return {
                'success': False,
                'message': f"Lỗi: {str(e)}"
            }

    def reject_extracted_keyword(self, keyword_id: str, rejected_by: str = "admin", reason: str = "") -> Dict:
        """
        Reject an extracted keyword.

        Args:
            keyword_id: MongoDB ObjectId string of extracted keyword
            rejected_by: Who rejected the keyword
            reason: Reason for rejection

        Returns:
            Dict with success status and message
        """
        if self.db is None:
            self.connect()

        try:
            from bson import ObjectId
            from datetime import datetime

            extracted_collection = self.db['extracted_keywords']

            result = extracted_collection.update_one(
                {'_id': ObjectId(keyword_id)},
                {
                    '$set': {
                        'status': 'rejected',
                        'rejected_at': datetime.utcnow().isoformat(),
                        'rejected_by': rejected_by,
                        'rejection_reason': reason
                    }
                }
            )

            if result.modified_count > 0:
                return {
                    'success': True,
                    'message': "Đã từ chối từ khóa"
                }
            else:
                return {
                    'success': False,
                    'message': "Không tìm thấy từ khóa"
                }

        except Exception as e:
            return {
                'success': False,
                'message': f"Lỗi: {str(e)}"
            }
