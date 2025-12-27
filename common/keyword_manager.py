"""
MongoDB Keyword Manager for user submissions and keyword management.
"""

from pymongo import MongoClient
from datetime import datetime
from typing import Optional, List, Dict
import os


class MongoKeywordManager:
    """
    Manager class for keyword submissions and active keywords in MongoDB.

    Collections:
    - user_submissions: Keywords submitted by public users
    - active_keywords: Active keywords used by producers
    - keyword_history: Audit log of all keyword actions
    """

    def __init__(self, mongo_uri: str = None):
        """
        Initialize MongoDB connection.

        Args:
            mongo_uri: MongoDB connection string (default: from env)
        """
        if mongo_uri is None:
            mongo_uri = os.getenv(
                "MONGO_URI",
                "mongodb://admin:password@localhost:27017/?authSource=admin"
            )

        self.client = MongoClient(mongo_uri)
        self.db = self.client["social_trends"]

        # Collections
        self.user_submissions = self.db.user_submissions
        self.active_keywords = self.db.active_keywords
        self.keyword_history = self.db.keyword_history

        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create MongoDB indexes for performance."""
        # User submissions
        self.user_submissions.create_index("keyword")
        self.user_submissions.create_index([("status", 1), ("created_at", -1)])

        # Active keywords
        self.active_keywords.create_index("keyword", unique=True)
        self.active_keywords.create_index([("status", 1), ("sources", 1)])

    # --- User Submissions ---

    def submit_keyword(
        self,
        keyword: str,
        reason: Optional[str] = None,
        submitted_by: Optional[str] = None
    ) -> Dict:
        """
        Submit a new keyword from public user.

        Args:
            keyword: The keyword to submit
            reason: Why user thinks it's trending (optional)
            submitted_by: User name/email (optional)

        Returns:
            Dict with submission result
        """
        # Check if already submitted
        existing = self.user_submissions.find_one({
            "keyword": keyword,
            "status": "pending"
        })

        if existing:
            return {
                "success": False,
                "message": "Từ khóa này đã được đề xuất trước đó và đang chờ duyệt"
            }

        # Check if already active
        active = self.active_keywords.find_one({"keyword": keyword})
        if active:
            return {
                "success": False,
                "message": "Từ khóa này đã có trong hệ thống"
            }

        # Insert submission
        submission = {
            "keyword": keyword.strip(),
            "reason": reason.strip() if reason else None,
            "submitted_by": submitted_by.strip() if submitted_by else "Anonymous",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "reviewed_at": None,
            "reviewed_by": None,
            "notes": None
        }

        result = self.user_submissions.insert_one(submission)

        return {
            "success": True,
            "message": "Cảm ơn bạn! Từ khóa đã được gửi và sẽ được xem xét.",
            "submission_id": str(result.inserted_id)
        }

    def get_pending_submissions(self, limit: int = 100) -> List[Dict]:
        """
        Get all pending user submissions.

        Args:
            limit: Maximum number of submissions to return

        Returns:
            List of pending submissions
        """
        return list(self.user_submissions.find(
            {"status": "pending"}
        ).sort("created_at", -1).limit(limit))

    def approve_submission(
        self,
        submission_id: str,
        sources: List[str],
        reviewed_by: str = "admin"
    ) -> Dict:
        """
        Approve a user submission and add to active keywords.

        Args:
            submission_id: MongoDB ObjectId of submission
            sources: List of sources to use keyword (tiktok, news, youtube)
            reviewed_by: Admin username

        Returns:
            Dict with result
        """
        from bson import ObjectId

        # Get submission
        submission = self.user_submissions.find_one({"_id": ObjectId(submission_id)})
        if not submission:
            return {"success": False, "message": "Submission not found"}

        keyword = submission["keyword"]

        # Add to active keywords
        self.active_keywords.insert_one({
            "keyword": keyword,
            "sources": sources,
            "status": "active",
            "added_at": datetime.utcnow(),
            "added_by": reviewed_by,
            "origin": "user_submission"
        })

        # Update submission status
        self.user_submissions.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "status": "approved",
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": reviewed_by
                }
            }
        )

        # Log to history
        self.keyword_history.insert_one({
            "keyword": keyword,
            "action": "approved",
            "performed_by": reviewed_by,
            "performed_at": datetime.utcnow(),
            "details": {
                "origin": "user_submission",
                "sources": sources
            }
        })

        return {"success": True, "message": f"Keyword '{keyword}' approved"}

    def reject_submission(
        self,
        submission_id: str,
        reason: Optional[str] = None,
        reviewed_by: str = "admin"
    ) -> Dict:
        """
        Reject a user submission.

        Args:
            submission_id: MongoDB ObjectId of submission
            reason: Reason for rejection (optional)
            reviewed_by: Admin username

        Returns:
            Dict with result
        """
        from bson import ObjectId

        # Update submission status
        result = self.user_submissions.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "status": "rejected",
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": reviewed_by,
                    "notes": reason
                }
            }
        )

        if result.modified_count == 0:
            return {"success": False, "message": "Submission not found"}

        return {"success": True, "message": "Submission rejected"}

    # --- Active Keywords ---

    def get_active_keywords(self, source: Optional[str] = None) -> List[Dict]:
        """
        Get all active keywords.

        Args:
            source: Filter by source (tiktok, news, youtube) or None for all

        Returns:
            List of active keywords
        """
        query = {"status": "active"}
        if source:
            query["sources"] = source

        return list(self.active_keywords.find(query).sort("added_at", -1))

    def add_keyword(
        self,
        keyword: str,
        sources: List[str],
        added_by: str = "admin"
    ) -> Dict:
        """
        Manually add a keyword (admin action).

        Args:
            keyword: The keyword to add
            sources: List of sources (tiktok, news, youtube)
            added_by: Admin username

        Returns:
            Dict with result
        """
        # Check if already exists
        existing = self.active_keywords.find_one({"keyword": keyword})
        if existing:
            return {
                "success": False,
                "message": "Keyword already exists"
            }

        # Insert keyword
        self.active_keywords.insert_one({
            "keyword": keyword.strip(),
            "sources": sources,
            "status": "active",
            "added_at": datetime.utcnow(),
            "added_by": added_by,
            "origin": "manual"
        })

        # Log to history
        self.keyword_history.insert_one({
            "keyword": keyword,
            "action": "added",
            "performed_by": added_by,
            "performed_at": datetime.utcnow(),
            "details": {
                "origin": "manual",
                "sources": sources
            }
        })

        return {"success": True, "message": f"Keyword '{keyword}' added"}

    def remove_keyword(self, keyword: str, removed_by: str = "admin") -> Dict:
        """
        Remove a keyword from active keywords.

        Args:
            keyword: The keyword to remove
            removed_by: Admin username

        Returns:
            Dict with result
        """
        result = self.active_keywords.delete_one({"keyword": keyword})

        if result.deleted_count == 0:
            return {"success": False, "message": "Keyword not found"}

        # Log to history
        self.keyword_history.insert_one({
            "keyword": keyword,
            "action": "removed",
            "performed_by": removed_by,
            "performed_at": datetime.utcnow()
        })

        return {"success": True, "message": f"Keyword '{keyword}' removed"}

    def close(self):
        """Close MongoDB connection."""
        self.client.close()
