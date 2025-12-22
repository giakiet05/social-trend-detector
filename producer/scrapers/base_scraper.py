"""
Abstract Base Class for all scrapers.
Provides common interface and logging for scrapers.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Any

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.

    All scrapers must implement the scrape() method.
    Provides common logging and error handling.

    Usage:
        class TikTokScraper(BaseScraper):
            def scrape(self, **kwargs) -> List[TikTokVideo]:
                # Implementation here
                pass
    """

    def __init__(self):
        """Initialize scraper with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"✅ {self.__class__.__name__} initialized")

    @abstractmethod
    def scrape(self, **kwargs) -> List[Any]:
        """
        Scrape data from source.

        Args:
            **kwargs: Source-specific parameters

        Returns:
            List of scraped data objects

        Raises:
            Exception: If scraping fails
        """
        pass

    def _log_scrape_start(self, **kwargs) -> None:
        """Log scraping start with parameters."""
        self.logger.info(f"🔍 Starting {self.__class__.__name__}.scrape()...")
        for key, value in kwargs.items():
            if value is not None:
                self.logger.info(f"   {key}: {value}")

    def _log_scrape_complete(self, count: int) -> None:
        """Log scraping completion with count."""
        self.logger.info(f"✅ Scraped {count} items")

    def _log_scrape_error(self, error: Exception) -> None:
        """Log scraping error."""
        self.logger.error(f"❌ Scraping failed: {error}", exc_info=True)
