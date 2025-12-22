"""
YouTube Producer: Scrape YouTube videos and send to Kafka.
"""

import logging
from typing import List
from producer.scrapers.youtube_scraper import YouTubeScraper
from producer.producers.base_producer import BaseProducer
from producer.config.settings import settings
from common.models import YouTubeVideo, KafkaMessage

logger = logging.getLogger(__name__)


class YouTubeProducer(BaseProducer):
    """
    YouTube producer: scrape videos from YouTube and send to Kafka topic.

    Extends BaseProducer with YouTube-specific configuration.

    Usage:
        producer = YouTubeProducer()
        producer.run()
    """

    def _get_scraper(self) -> YouTubeScraper:
        """Get YouTube scraper instance."""
        return YouTubeScraper()

    def _get_topic(self) -> str:
        """Get Kafka topic for YouTube data."""
        return settings.kafka.YOUTUBE_TOPIC

    def _get_keywords(self) -> dict:
        """
        Get YouTube scraping keywords from settings.

        Returns:
            Dictionary with keywords and max_videos
        """
        return {
            "keywords": settings.keywords.youtube_keywords,
            "max_videos": settings.keywords.youtube_max_videos
        }

    def _scrape_with_config(self, config: dict) -> List[YouTubeVideo]:
        """
        Call YouTube scraper with configuration.

        Args:
            config: Configuration dictionary with keywords and max_videos

        Returns:
            List of YouTubeVideo objects
        """
        return self.scraper.scrape(
            keywords=config.get("keywords", []),
            max_videos=config.get("max_videos", 50)
        )

    def _transform_to_kafka_message(self, item: YouTubeVideo) -> KafkaMessage:
        """
        Transform YouTubeVideo to KafkaMessage.

        Args:
            item: YouTubeVideo object

        Returns:
            KafkaMessage instance
        """
        return KafkaMessage.from_youtube(item)

    def _get_item_id(self, item: YouTubeVideo) -> str:
        """
        Get video ID from YouTubeVideo.

        Args:
            item: YouTubeVideo object

        Returns:
            Video ID string
        """
        return item.video_id

    def _get_source_name(self) -> str:
        """Get source name for data saver."""
        return "youtube"


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run producer
    producer = YouTubeProducer()
    producer.run()
