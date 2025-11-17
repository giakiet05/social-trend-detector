"""
Cleaning stage: Remove invalid/null data.
"""

from typing import List, Dict
import logging
from .base_stage import BaseStage

logger = logging.getLogger(__name__)


class CleaningStage(BaseStage):
    """Clean and validate video data."""

    def __init__(self):
        super().__init__("CleaningStage")

    def execute(self, videos: List[Dict]) -> List[Dict]:
        """
        Remove videos with null/invalid data.

        Args:
            videos: List of video dictionaries

        Returns:
            Cleaned videos
        """
        self.log_start()

        if not videos:
            self.log_skip("No videos to clean")
            return []

        initial_count = len(videos)
        cleaned = []

        for video in videos:
            # Check required fields
            if not video.get('video_id'):
                logger.debug(f"Skipping video: missing video_id")
                continue

            if not video.get('text') or not isinstance(video.get('text'), str):
                logger.debug(f"Skipping video {video.get('video_id')}: invalid text")
                continue

            # Ensure hashtags is list
            if not isinstance(video.get('hashtags'), list):
                video['hashtags'] = []

            # Ensure numeric fields are valid
            for field in ['views', 'likes', 'comments', 'shares', 'collects', 'author_fans']:
                if video.get(field) is None:
                    video[field] = 0

            cleaned.append(video)

        removed = initial_count - len(cleaned)
        self.log_complete(f"{len(cleaned)}/{initial_count} videos valid, {removed} removed")

        return cleaned
