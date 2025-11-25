"""
Abstract Base Class for all producers.
Provides template method pattern for producer pipeline.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Any
from producer.producers.kafka_client import KafkaClient
from producer.utils.data_saver import DataSaver
from producer.config.settings import settings
from common.models import KafkaMessage

logger = logging.getLogger(__name__)


class BaseProducer(ABC):
    """
    Abstract base class for all producers.

    Implements the producer pipeline as a template method:
    1. Load configuration
    2. Scrape data
    3. Save raw data (backup)
    4. Send to Kafka

    All producers must implement:
    - _get_scraper() -> scraper instance
    - _get_topic() -> Kafka topic name
    - _get_keywords() -> scraping keywords
    - _transform_to_kafka_message() -> convert data to KafkaMessage

    Usage:
        class TikTokProducer(BaseProducer):
            def _get_scraper(self):
                return TikTokScraper()

            def _get_topic(self) -> str:
                return settings.kafka.TIKTOK_TOPIC

            # ... implement other abstract methods
    """

    def __init__(self):
        """Initialize Kafka client and DataSaver."""
        self.kafka = KafkaClient(
            bootstrap_servers=settings.kafka.BOOTSTRAP_SERVERS
        )
        self.data_saver = DataSaver(base_dir="data/raw")
        self.scraper = self._get_scraper()
        self.topic = self._get_topic()

        logger.info(f"✅ {self.__class__.__name__} initialized (topic: {self.topic})")

    @abstractmethod
    def _get_scraper(self):
        """
        Get scraper instance for this producer.

        Returns:
            Scraper instance (e.g., TikTokScraper)
        """
        pass

    @abstractmethod
    def _get_topic(self) -> str:
        """
        Get Kafka topic name for this producer.

        Returns:
            Kafka topic name (e.g., "tiktok-raw")
        """
        pass

    @abstractmethod
    def _get_keywords(self) -> dict:
        """
        Get scraping keywords/parameters from settings.

        Returns:
            Dictionary with source-specific parameters
            Example: {"keywords": [...], "hashtags": [...], "max_videos": 10}
        """
        pass

    @abstractmethod
    def _transform_to_kafka_message(self, item: Any) -> KafkaMessage:
        """
        Transform scraped item to KafkaMessage.

        Args:
            item: Scraped data object (e.g., TikTokVideo)

        Returns:
            KafkaMessage instance
        """
        pass

    @abstractmethod
    def _get_item_id(self, item: Any) -> str:
        """
        Extract unique ID from scraped item (used as Kafka key).

        Args:
            item: Scraped data object

        Returns:
            Unique identifier string
        """
        pass

    @abstractmethod
    def _get_source_name(self) -> str:
        """
        Get source name for data saver.

        Returns:
            Source name (e.g., "tiktok", "vnexpress")
        """
        pass

    def run(self) -> int:
        """
        Run producer pipeline (template method).

        Pipeline steps:
        1. Load keywords/config
        2. Scrape data
        3. Save raw data (backup)
        4. Send to Kafka

        Returns:
            Number of successfully sent items
        """
        logger.info("\n" + "=" * 60)
        logger.info(f"🚀 {self.__class__.__name__.upper()} - STARTING")
        logger.info("=" * 60)

        try:
            # Step 1: Load configuration
            config = self._get_keywords()

            if not config or not any(config.values()):
                logger.error(f"❌ No configuration found in scraping_keywords.yaml")
                logger.info(f"   Please edit: producer/config/scraping_keywords.yaml")
                return 0

            logger.info(f"📋 Configuration:")
            for key, value in config.items():
                logger.info(f"   {key}: {value}")

            # Step 2: Scrape data
            scraped_data = self._scrape_with_config(config)

            if not scraped_data:
                logger.warning("⚠️  No data scraped, nothing to send")
                return 0

            logger.info(f"📦 Scraped {len(scraped_data)} items")

            # Step 3: Save raw data (backup)
            try:
                # Save timestamped file
                saved_path = self.data_saver.save(
                    source=self._get_source_name(),
                    data=scraped_data
                )
                logger.info(f"💾 Raw data saved to: {saved_path}")

                # Append to aggregate file
                aggregate_path = self.data_saver.append_to_aggregate(
                    source=self._get_source_name(),
                    data=scraped_data
                )
                logger.info(f"📝 Appended to aggregate: {aggregate_path}")

            except Exception as e:
                logger.warning(f"⚠️  Failed to save raw data: {e}")
                # Continue even if save fails

            # Step 4: Send to Kafka
            success_count = self._send_to_kafka(scraped_data)

            logger.info("=" * 60)
            logger.info(f"✅ {self.__class__.__name__.upper()} - COMPLETED")
            logger.info(f"   Sent: {success_count}/{len(scraped_data)} items")
            logger.info("=" * 60 + "\n")

            return success_count

        except Exception as e:
            logger.error(f"❌ {self.__class__.__name__} failed: {e}", exc_info=True)
            return 0

        finally:
            # Always close Kafka connection
            self.kafka.close()

    @abstractmethod
    def _scrape_with_config(self, config: dict) -> List[Any]:
        """
        Call scraper with configuration.

        Args:
            config: Configuration dictionary from _get_keywords()

        Returns:
            List of scraped items
        """
        pass

    def _send_to_kafka(self, items: List[Any]) -> int:
        """
        Send scraped items to Kafka topic.

        Args:
            items: List of scraped data objects

        Returns:
            Number of successfully sent items
        """
        success_count = 0

        for idx, item in enumerate(items, 1):
            try:
                # Transform to KafkaMessage
                kafka_message = self._transform_to_kafka_message(item)
                item_id = self._get_item_id(item)

                # Send to Kafka
                if self.kafka.send(
                    topic=self.topic,
                    message=kafka_message.to_dict(),
                    key=item_id
                ):
                    success_count += 1
                    logger.info(f"✅ [{idx}/{len(items)}] Sent: {item_id}")
                else:
                    logger.error(f"❌ [{idx}/{len(items)}] Failed: {item_id}")

            except Exception as e:
                logger.error(f"❌ [{idx}/{len(items)}] Error: {e}")

        return success_count
