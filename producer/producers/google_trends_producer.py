"""
Google Trends Producer: Scrape Google Trends data and send to Kafka.
"""

import logging
from typing import List
from producer.scrapers.google_trends_scraper import GoogleTrendsScraper
from producer.producers.base_producer import BaseProducer
from producer.config.settings import settings
from common.models import TrendsData, KafkaMessage

logger = logging.getLogger(__name__)


class GoogleTrendsProducer(BaseProducer):
    """
    Google Trends producer: scrape trends data and send to Kafka topic.

    Extends BaseProducer with Google Trends-specific configuration.

    Usage:
        producer = GoogleTrendsProducer()
        producer.run()
    """

    def _get_scraper(self) -> GoogleTrendsScraper:
        """Get Google Trends scraper instance."""
        return GoogleTrendsScraper()

    def _get_topic(self) -> str:
        """Get Kafka topic for Google Trends data."""
        return settings.kafka.TRENDS_TOPIC

    def _get_keywords(self) -> dict:
        """
        Get Google Trends keywords from settings.

        Returns:
            Dictionary with keywords, timeframe, and region
        """
        return {
            "keywords": settings.keywords.trends_keywords,
            "timeframe": settings.keywords.trends_timeframe,
            "region": settings.keywords.trends_region
        }

    def _scrape_with_config(self, config: dict) -> List[TrendsData]:
        """
        Call Google Trends scraper with configuration.

        Args:
            config: Configuration dictionary with keywords, timeframe, region

        Returns:
            List of TrendsData objects
        """
        return self.scraper.scrape(
            keywords=config.get("keywords", []),
            timeframe=config.get("timeframe", "now 7-d"),
            region=config.get("region", "VN")
        )

    def _transform_to_kafka_message(self, item: TrendsData) -> KafkaMessage:
        """
        Transform TrendsData to KafkaMessage.

        Args:
            item: TrendsData object

        Returns:
            KafkaMessage instance
        """
        return KafkaMessage.from_trends(item)

    def _get_item_id(self, item: TrendsData) -> str:
        """
        Get query as ID from TrendsData.

        Args:
            item: TrendsData object

        Returns:
            Query string as ID
        """
        return item.query

    def _get_source_name(self) -> str:
        """Get source name for data saver."""
        return "google_trends"


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run producer
    producer = GoogleTrendsProducer()
    producer.run()
