"""
VNExpress Producer: Scrape VNExpress news and send to Kafka.
"""

import logging
from typing import List
from producer.scrapers.vnexpress_scraper import VNExpressScraper
from producer.producers.base_producer import BaseProducer
from producer.config.settings import settings
from common.models import NewsArticle, KafkaMessage

logger = logging.getLogger(__name__)


class VNExpressProducer(BaseProducer):
    """
    VNExpress producer: scrape news from VNExpress RSS and send to Kafka topic.

    Extends BaseProducer with VNExpress-specific configuration.

    Usage:
        producer = VNExpressProducer()
        producer.run()
    """

    def _get_scraper(self) -> VNExpressScraper:
        """Get VNExpress scraper instance."""
        return VNExpressScraper()

    def _get_topic(self) -> str:
        """Get Kafka topic for VNExpress data."""
        return settings.kafka.NEWS_TOPIC

    def _get_keywords(self) -> dict:
        """
        Get VNExpress scraping keywords from settings.

        Returns:
            Dictionary with keywords and rss_feeds
        """
        return {
            "keywords": settings.keywords.vnexpress_keywords,
            "rss_feeds": settings.keywords.vnexpress_rss_feeds
        }

    def _scrape_with_config(self, config: dict) -> List[NewsArticle]:
        """
        Call VNExpress scraper with configuration.

        Args:
            config: Configuration dictionary with keywords and rss_feeds

        Returns:
            List of NewsArticle objects
        """
        return self.scraper.scrape(
            keywords=config.get("keywords"),
            rss_feeds=config.get("rss_feeds", [])
        )

    def _transform_to_kafka_message(self, item: NewsArticle) -> KafkaMessage:
        """
        Transform NewsArticle to KafkaMessage.

        Args:
            item: NewsArticle object

        Returns:
            KafkaMessage instance
        """
        return KafkaMessage.from_news(item)

    def _get_item_id(self, item: NewsArticle) -> str:
        """
        Get article ID from NewsArticle.

        Args:
            item: NewsArticle object

        Returns:
            Article ID string
        """
        return item.article_id

    def _get_source_name(self) -> str:
        """Get source name for data saver."""
        return "vnexpress"


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run producer
    producer = VNExpressProducer()
    producer.run()
