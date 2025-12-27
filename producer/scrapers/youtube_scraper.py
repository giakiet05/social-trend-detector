"""
YouTube scraper using YouTube Data API v3.
"""

import logging
from typing import List
from googleapiclient.discovery import build
from datetime import datetime
import isodate
from producer.scrapers.base_scraper import BaseScraper
from producer.config.settings import settings
from common.models import YouTubeVideo

logger = logging.getLogger(__name__)


class YouTubeScraper(BaseScraper):
    """
    YouTube video scraper using YouTube Data API v3.

    Usage:
        scraper = YouTubeScraper()
        videos = scraper.scrape(keywords=["trend"], max_videos=50)
    """

    def __init__(self):
        """Initialize YouTube scraper with API client."""
        super().__init__()

        api_key = settings.youtube_config.API_KEY
        if not api_key:
            raise ValueError(
                "YouTube API key is required. "
                "Please set YOUTUBE_API_KEY in .env file"
            )

        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.logger.info(f"YouTube Data API v3 initialized")

    def scrape(
        self,
        keywords: List[str] = None,
        max_videos: int = 50
    ) -> List[YouTubeVideo]:
        """
        Scrape YouTube videos by keywords.

        Args:
            keywords: List of search keywords
            max_videos: Max videos per keyword

        Returns:
            List of YouTubeVideo objects
        """
        if not keywords:
            self.logger.warning("⚠️  No keywords provided, skipping scrape")
            return []

        self._log_scrape_start(
            keywords=keywords,
            max_videos=max_videos
        )

        try:
            videos = []

            for keyword in keywords:
                self.logger.info(f"🔍 Searching YouTube for: {keyword}")

                try:
                    video_ids = []
                    page_token = None
                    pages_fetched = 0

                    # Pagination loop to get max_videos
                    while len(video_ids) < max_videos:
                        search_response = self.youtube.search().list(
                            q=keyword,
                            type='video',
                            part='id,snippet',
                            maxResults=min(50, max_videos - len(video_ids)),  # API limit: 50 per request
                            pageToken=page_token,
                            order='relevance',
                            regionCode='VN',
                            relevanceLanguage='vi'
                        ).execute()

                        page_video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                        video_ids.extend(page_video_ids)
                        pages_fetched += 1

                        self.logger.debug(f"   Page {pages_fetched}: {len(page_video_ids)} videos (total: {len(video_ids)})")

                        # Check if there's a next page
                        page_token = search_response.get('nextPageToken')
                        if not page_token:
                            self.logger.debug(f"   No more pages available")
                            break

                    if not video_ids:
                        self.logger.warning(f"⚠️  No videos found for: {keyword}")
                        continue

                    self.logger.info(f"   Found {len(video_ids)} videos across {pages_fetched} pages")

                    # Get video details (views, likes, etc.) - batch by 50 (API limit)
                    for i in range(0, len(video_ids), 50):
                        batch_ids = video_ids[i:i+50]

                        videos_response = self.youtube.videos().list(
                            id=','.join(batch_ids),
                            part='snippet,statistics,contentDetails'
                        ).execute()

                        for item in videos_response.get('items', []):
                            try:
                                video = self._transform_youtube_item(item)
                                videos.append(video)
                            except Exception as e:
                                self.logger.warning(f"⚠️  Failed to transform item: {e}")
                                continue

                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to search for '{keyword}': {e}")
                    continue

            self._log_scrape_complete(len(videos))
            return videos

        except Exception as e:
            self._log_scrape_error(e)
            return []

    def _transform_youtube_item(self, item: dict) -> YouTubeVideo:
        """
        Transform YouTube API response to YouTubeVideo model.

        Args:
            item: YouTube API video item

        Returns:
            YouTubeVideo instance
        """
        snippet = item.get('snippet', {})
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})

        video_id = item['id']

        # Parse duration (ISO 8601 format like PT15M33S)
        duration_str = content_details.get('duration', 'PT0S')
        try:
            duration = isodate.parse_duration(duration_str)
            duration_seconds = int(duration.total_seconds())
        except:
            duration_seconds = 0

        # Parse published date
        published_at = snippet.get('publishedAt', datetime.utcnow().isoformat())

        # Extract tags
        tags = snippet.get('tags', [])

        # Parse statistics (may not exist for some videos)
        views = int(statistics.get('viewCount', 0))
        likes = int(statistics.get('likeCount', 0))
        comments = int(statistics.get('commentCount', 0))

        # Get thumbnails (prefer high quality)
        thumbnails = snippet.get('thumbnails', {})
        thumbnail = (
            thumbnails.get('high', {}).get('url') or
            thumbnails.get('medium', {}).get('url') or
            thumbnails.get('default', {}).get('url') or
            ''
        )

        return YouTubeVideo(
            video_id=video_id,
            title=snippet.get('title', ''),
            description=snippet.get('description', ''),
            url=f"https://www.youtube.com/watch?v={video_id}",
            tags=tags,
            views=views,
            likes=likes,
            comments=comments,
            channel_name=snippet.get('channelTitle', ''),
            channel_id=snippet.get('channelId', ''),
            published_at=published_at,
            duration_seconds=duration_seconds,
            thumbnail=thumbnail,
            category=snippet.get('categoryId')
        )
