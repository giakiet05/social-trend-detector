"""
TikTok Producer: Scrape TikTok videos and send to Kafka.
"""

import logging
from typing import List, Any
from producer.scrapers.tiktok_scraper import TikTokScraper
from producer.producers.base_producer import BaseProducer
from producer.config.settings import settings
from common.models import TikTokVideo, KafkaMessage

logger = logging.getLogger(__name__)


class TikTokProducer(BaseProducer):
    """
    TikTok producer: scrape videos from TikTok and send to Kafka topic.

    Extends BaseProducer with TikTok-specific configuration.

    Usage:
        producer = TikTokProducer()
        producer.run()
    """

    def _get_scraper(self) -> TikTokScraper:
        """Get TikTok scraper instance."""
        return TikTokScraper()

    def _get_topic(self) -> str:
        """Get Kafka topic for TikTok data."""
        return settings.kafka.TIKTOK_TOPIC

    def _get_keywords(self) -> dict:
        """
        Get TikTok scraping keywords from settings.

        Returns:
            Dictionary with keywords, hashtags, and max_videos
        """
        return {
            "keywords": settings.keywords.tiktok_keywords,
            "hashtags": settings.keywords.tiktok_hashtags,
            "max_videos": settings.keywords.tiktok_max_videos
        }

    def _scrape_with_config(self, config: dict) -> List[TikTokVideo]:
        """
        Call TikTok scraper with configuration.

        Args:
            config: Configuration dictionary with keywords, hashtags, max_videos

        Returns:
            List of TikTokVideo objects
        """
        return self.scraper.scrape(
            keywords=config.get("keywords"),
            hashtags=config.get("hashtags"),
            max_videos=config.get("max_videos", 10)
        )

    def _transform_to_kafka_message(self, item: TikTokVideo) -> KafkaMessage:
        """
        Transform TikTokVideo to KafkaMessage.

        Args:
            item: TikTokVideo object

        Returns:
            KafkaMessage instance
        """
        return KafkaMessage.from_tiktok(item)

    def _get_item_id(self, item: TikTokVideo) -> str:
        """
        Get video ID from TikTokVideo.

        Args:
            item: TikTokVideo object

        Returns:
            Video ID string
        """
        return item.video_id

    def _get_source_name(self) -> str:
        """Get source name for data saver."""
        return "tiktok"


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run producer
    producer = TikTokProducer()
    producer.run()
