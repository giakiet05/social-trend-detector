"""
News scraper using RSS feeds from multiple Vietnamese news sources.
"""

import logging
import feedparser
from typing import List
from datetime import datetime
from producer.scrapers.base_scraper import BaseScraper
from producer.config.settings import settings
from common.models import NewsArticle

logger = logging.getLogger(__name__)


class NewsScraper(BaseScraper):
    """
    Generic news scraper using RSS feeds.

    Supports multiple Vietnamese news sources:
    - VNExpress (vnexpress.net)
    - Tuổi Trẻ (tuoitre.vn)
    - VTC News (vtcnews.vn)
    - Thanh Niên (thanhnien.vn)

    Usage:
        scraper = NewsScraper()
        articles = scraper.scrape(keywords=["công nghệ"], rss_feeds=["https://..."])
    """

    def __init__(self):
        """Initialize news scraper."""
        super().__init__()

    def scrape(
        self,
        keywords: List[str] = None,
        rss_feeds: List[str] = None
    ) -> List[NewsArticle]:
        """
        Scrape news articles from RSS feeds.

        Args:
            keywords: Filter keywords (if None, return all articles)
            rss_feeds: List of RSS feed URLs from any supported news source

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
                            article = self._transform_rss_entry(entry, category, feed_url)
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

        Supports VNExpress, Tuổi Trẻ, VTC News, and Thanh Niên URL patterns.

        Args:
            url: RSS feed URL

        Returns:
            Category name (e.g., "Thời sự", "Giải trí")
        """
        url_lower = url.lower()

        # Homepage/Latest news
        if any(x in url_lower for x in ["tin-moi-nhat", "trang-chu", "home"]):
            return "Tin mới nhất"

        # Politics/Current Affairs
        elif any(x in url_lower for x in ["thoi-su", "chinh-tri"]):
            return "Thời sự"

        # Entertainment
        elif "giai-tri" in url_lower:
            return "Giải trí"

        # Business/Economy
        elif any(x in url_lower for x in ["kinh-doanh", "kinh-te"]):
            return "Kinh doanh"

        # World news
        elif "the-gioi" in url_lower:
            return "Thế giới"

        # Sports
        elif "the-thao" in url_lower:
            return "Thể thao"

        # Law
        elif "phap-luat" in url_lower:
            return "Pháp luật"

        # Education
        elif "giao-duc" in url_lower:
            return "Giáo dục"

        # Health
        elif "suc-khoe" in url_lower:
            return "Sức khỏe"

        # Lifestyle
        elif "doi-song" in url_lower:
            return "Đời sống"

        # Travel
        elif "du-lich" in url_lower:
            return "Du lịch"

        # Science
        elif "khoa-hoc" in url_lower:
            return "Khoa học"

        # Technology/Digital
        elif any(x in url_lower for x in ["so-hoa", "nhip-song-so", "cong-nghe", "khoa-hoc-cong-nghe"]):
            return "Công nghệ"

        # Automotive
        elif any(x in url_lower for x in ["xe", "oto-xe-may"]):
            return "Xe"

        # Youth
        elif any(x in url_lower for x in ["nhip-song-tre", "gioi-tre"]):
            return "Giới trẻ"

        # Culture
        elif "van-hoa" in url_lower:
            return "Văn hóa"

        # Real estate
        elif any(x in url_lower for x in ["bat-dong-san", "dia-oc"]):
            return "Bất động sản"

        # Need to know (VTC specific)
        elif "can-biet" in url_lower:
            return "Cần biết"

        else:
            return "Tổng hợp"

    def _detect_author_from_url(self, url: str) -> str:
        """
        Detect news source (author) from RSS feed URL.

        Args:
            url: RSS feed URL

        Returns:
            News source name
        """
        url_lower = url.lower()

        if "vnexpress.net" in url_lower:
            return "VNExpress"
        elif "tuoitre.vn" in url_lower:
            return "Tuổi Trẻ"
        elif "vtcnews.vn" in url_lower:
            return "VTC News"
        elif "thanhnien.vn" in url_lower:
            return "Thanh Niên"
        else:
            return "Unknown"

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

    def _transform_rss_entry(self, entry: dict, category: str, feed_url: str) -> NewsArticle:
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
            feed_url: RSS feed URL (for author detection)

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

        # Detect author from feed URL
        author = self._detect_author_from_url(feed_url)

        return NewsArticle(
            article_id=article_id,
            title=entry.get('title', ''),
            summary=entry.get('summary', ''),
            url=entry.get('link', ''),
            category=category,
            published_at=published_at,
            thumbnail=thumbnail,
            author=author
        )
