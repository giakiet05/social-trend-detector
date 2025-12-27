"""
TikTok scraper using Apify TikTok Video Scraper actor.
"""

import logging
from typing import List
from apify_client import ApifyClient
from common.models import TikTokVideo
from datetime import datetime
from producer.config.settings import settings
from producer.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TikTokScraper(BaseScraper):
    """
    TikTok video scraper using Apify (clockworks/tiktok-scraper).

    Usage:
        scraper = TikTokScraper()
        videos = scraper.scrape(keywords=["trend"], hashtags=["fyp"], max_videos=100)
    """

    def __init__(self):
        """
        Initialize TikTok scraper with Apify client.

        API token and actor ID are loaded from settings/environment variables.
        """
        super().__init__()  # Initialize BaseScraper

        api_token = settings.apify.API_TOKEN
        if not api_token:
            raise ValueError(
                "Apify API token is required. "
                "Please set APIFY_API_TOKEN in .env file"
            )

        self.client = ApifyClient(api_token)
        self.actor_id = settings.apify.ACTOR_ID

        self.logger.info(f"Actor ID: {self.actor_id}")

    def scrape(
        self,
        keywords: List[str] = None,
        hashtags: List[str] = None,
        max_videos: int = 10
    ) -> List[TikTokVideo]:
        """
        Scrape TikTok videos by keywords and/or hashtags.

        Args:
            keywords: List of search keywords (searchQueries param)
            hashtags: List of hashtags (hashtags param, without #)
            max_videos: Max videos per query

        Returns:
            List of TikTokVideo objects
        """
        if not keywords and not hashtags:
            self.logger.warning("No keywords or hashtags provided, skipping scrape")
            return []

        # Use BaseScraper logging helper
        self._log_scrape_start(
            keywords=keywords,
            hashtags=hashtags,
            max_videos=max_videos
        )

        try:
            # Prepare actor input (based on your provided code)
            run_input = {
                "searchQueries": keywords if keywords else [],
                "hashtags": hashtags if hashtags else [],
                "resultsPerPage": max_videos,

                # Other params (minimal required fields only)
                "profiles": [],
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
                "shouldDownloadSubtitles": False,
            }

            # Run Apify actor
            self.logger.info("Running Apify actor...")
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            # Fetch results from dataset
            self.logger.info("Fetching results from dataset...")
            videos = []

            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                try:
                    video = self._transform_apify_item(item)
                    videos.append(video)
                except Exception as e:
                    self.logger.warning(f"Failed to transform item: {e}")
                    continue

            # Use BaseScraper logging helper
            self._log_scrape_complete(len(videos))
            return videos

        except Exception as e:
            # Use BaseScraper logging helper
            self._log_scrape_error(e)
            return []

    def _transform_apify_item(self, item: dict) -> TikTokVideo:
        """
        Transform Apify output to TikTokVideo model.

        Apify field mapping:
            id → video_id
            text → text
            hashtags → hashtags (list of objects with 'name' field)
            playCount → views
            diggCount → likes
            commentCount → comments
            shareCount → shares
            collectCount → collects
            authorMeta → author info (name, fans, verified)
            createTimeISO → timestamp
            textExtra → language detection
            webVideoUrl → video_url
        """
        # Extract hashtags from list of objects
        hashtags = []
        if 'hashtags' in item and isinstance(item['hashtags'], list):
            for tag in item['hashtags']:
                if isinstance(tag, dict) and 'name' in tag:
                    hashtags.append(tag['name'])
                elif isinstance(tag, str):
                    hashtags.append(tag)

        # Parse author metadata
        author_meta = item.get('authorMeta', {})

        # Parse timestamp
        timestamp_str = item.get('createTimeISO') or item.get('createTime')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).isoformat()
            except:
                timestamp = datetime.utcnow().isoformat()
        else:
            timestamp = datetime.utcnow().isoformat()

        # Detect language (Apify may provide this in textExtra)
        language = None
        if 'textExtra' in item and isinstance(item['textExtra'], list) and len(item['textExtra']) > 0:
            # Sometimes language is in first textExtra item
            language = item.get('textExtra', [{}])[0].get('languageCode')

        return TikTokVideo(
            video_id=str(item.get('id', '')),
            text=item.get('text', ''),
            hashtags=hashtags,

            # Engagement metrics
            views=int(item.get('playCount', 0) or 0),
            likes=int(item.get('diggCount', 0) or 0),
            comments=int(item.get('commentCount', 0) or 0),
            shares=int(item.get('shareCount', 0) or 0),
            collects=int(item.get('collectCount', 0) or 0),

            # Author info
            author_username=author_meta.get('name', ''),
            author_fans=int(author_meta.get('fans', 0) or 0),
            author_verified=bool(author_meta.get('verified', False)),

            # Metadata
            timestamp=timestamp,
            language=language,
            video_url=item.get('webVideoUrl', '')
        )
