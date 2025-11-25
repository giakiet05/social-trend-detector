"""
VNExpress scraper using RSS feeds.
"""

import logging
import feedparser
from typing import List
from datetime import datetime
from producer.scrapers.base_scraper import BaseScraper
from producer.config.settings import settings
from common.models import NewsArticle

logger = logging.getLogger(__name__)


class VNExpressScraper(BaseScraper):
    """
    VNExpress news scraper using RSS feeds.

    Scrapes articles from VNExpress RSS feeds and filters by keywords.

    Usage:
        scraper = VNExpressScraper()
        articles = scraper.scrape(keywords=["công nghệ"], rss_feeds=["https://..."])
    """

    def __init__(self):
        """Initialize VNExpress scraper."""
        super().__init__()

    def scrape(
        self,
        keywords: List[str] = None,
        rss_feeds: List[str] = None
    ) -> List[NewsArticle]:
        """
        Scrape VNExpress articles from RSS feeds.

        Args:
            keywords: Filter keywords (if None, return all articles)
            rss_feeds: List of RSS feed URLs

        Returns:
            List of NewsArticle objects
        """
        if not rss_feeds:
            self.logger.warning("⚠️  No RSS feeds provided, skipping scrape")
            return []

        self._log_scrape_start(
            keywords=keywords or "All articles",
            rss_feeds_count=len(rss_feeds)
        )

        try:
            articles = []

            for feed_url in rss_feeds:
                self.logger.info(f"📡 Fetching RSS feed: {feed_url}")

                try:
                    # Parse RSS feed
                    feed = feedparser.parse(feed_url)

                    if feed.bozo:
                        self.logger.warning(f"⚠️  Feed parse error: {feed_url}")
                        continue

                    # Infer category from RSS URL
                    category = self._infer_category_from_url(feed_url)

                    # Process entries
                    for entry in feed.entries:
                        # Filter by keywords if provided
                        if keywords:
                            if not self._matches_keywords(entry, keywords):
                                continue

                        try:
                            article = self._transform_rss_entry(entry, category)
                            articles.append(article)
                        except Exception as e:
                            self.logger.warning(f"⚠️  Failed to transform entry: {e}")
                            continue

                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to fetch feed {feed_url}: {e}")
                    continue

            self._log_scrape_complete(len(articles))
            return articles

        except Exception as e:
            self._log_scrape_error(e)
            return []

    def _infer_category_from_url(self, url: str) -> str:
        """
        Infer category from RSS feed URL.

        Args:
            url: RSS feed URL

        Returns:
            Category name (e.g., "Thời sự", "Giải trí")
        """
        url_lower = url.lower()

        if "tin-moi-nhat" in url_lower:
            return "Tin mới nhất"
        elif "thoi-su" in url_lower:
            return "Thời sự"
        elif "giai-tri" in url_lower:
            return "Giải trí"
        elif "kinh-doanh" in url_lower:
            return "Kinh doanh"
        elif "the-gioi" in url_lower:
            return "Thế giới"
        elif "the-thao" in url_lower:
            return "Thể thao"
        elif "phap-luat" in url_lower:
            return "Pháp luật"
        elif "giao-duc" in url_lower:
            return "Giáo dục"
        elif "suc-khoe" in url_lower:
            return "Sức khỏe"
        elif "doi-song" in url_lower:
            return "Đời sống"
        elif "du-lich" in url_lower:
            return "Du lịch"
        elif "khoa-hoc" in url_lower:
            return "Khoa học"
        elif "so-hoa" in url_lower:
            return "Số hóa"
        elif "xe" in url_lower:
            return "Xe"
        else:
            return "Tổng hợp"

    def _matches_keywords(self, entry: dict, keywords: List[str]) -> bool:
        """
        Check if RSS entry matches any keyword.

        Args:
            entry: RSS feed entry
            keywords: List of keywords to match

        Returns:
            True if entry matches any keyword
        """
        # Combine title and summary for matching
        text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()

        for keyword in keywords:
            if keyword.lower() in text:
                return True

        return False

    def _transform_rss_entry(self, entry: dict, category: str) -> NewsArticle:
        """
        Transform RSS entry to NewsArticle model.

        RSS field mapping:
            id → article_id
            title → title
            summary → summary
            link → url
            published → published_at
            media_thumbnail → thumbnail

        Args:
            entry: RSS feed entry
            category: Inferred category

        Returns:
            NewsArticle instance
        """
        # Parse published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            except:
                published_at = datetime.utcnow().isoformat()
        else:
            published_at = datetime.utcnow().isoformat()

        # Extract thumbnail
        thumbnail = None
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            thumbnail = entry.media_thumbnail[0].get('url')
        elif hasattr(entry, 'media_content') and entry.media_content:
            thumbnail = entry.media_content[0].get('url')

        # Generate article ID from link
        article_id = entry.get('id') or entry.get('link', '').split('/')[-1].split('.')[0]

        return NewsArticle(
            article_id=article_id,
            title=entry.get('title', ''),
            summary=entry.get('summary', ''),
            url=entry.get('link', ''),
            category=category,
            published_at=published_at,
            thumbnail=thumbnail,
            author="VNExpress"
        )
