"""
News Producer: Scrape news from multiple sources and send to Kafka.
"""

import logging
from typing import List
from producer.scrapers.news_scraper import NewsScraper
from producer.producers.base_producer import BaseProducer
from producer.config.settings import settings
from common.models import NewsArticle, KafkaMessage

logger = logging.getLogger(__name__)


class NewsProducer(BaseProducer):
    """
    News producer: scrape news from multiple Vietnamese news sources (RSS) and send to Kafka.

    Supports VNExpress, Tuổi Trẻ, VTC News, and Thanh Niên.
    Extends BaseProducer with news-specific configuration.

    Usage:
        producer = NewsProducer()
        producer.run()
    """

    def _get_scraper(self) -> NewsScraper:
        """Get news scraper instance."""
        return NewsScraper()

    def _get_topic(self) -> str:
        """Get Kafka topic for news data."""
        return settings.kafka.NEWS_TOPIC

    def _get_keywords(self) -> dict:
        """
        Get news scraping keywords from settings.

        Returns:
            Dictionary with keywords and rss_feeds
        """
        return {
            "keywords": settings.keywords.news_keywords,
            "rss_feeds": settings.keywords.news_rss_feeds
        }

    def _scrape_with_config(self, config: dict) -> List[NewsArticle]:
        """
        Call news scraper with configuration.

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
        return "news"


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run producer
    producer = NewsProducer()
    producer.run()
