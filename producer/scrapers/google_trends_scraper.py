"""
Google Trends scraper using pytrends library.
"""

import logging
import time
from typing import List
from pytrends.request import TrendReq
from datetime import datetime
from producer.scrapers.base_scraper import BaseScraper
from producer.config.settings import settings
from common.models import TrendsData

logger = logging.getLogger(__name__)


class GoogleTrendsScraper(BaseScraper):
    """
    Google Trends scraper using pytrends (unofficial API).

    Usage:
        scraper = GoogleTrendsScraper()
        trends = scraper.scrape(keywords=["phở"], timeframe="now 7-d", region="VN")
    """

    def __init__(self):
        """Initialize Google Trends scraper."""
        super().__init__()

        # Initialize pytrends client
        self.pytrends = TrendReq(
            hl='vi-VN',
            tz=420,  # UTC+7 (Vietnam timezone)
            timeout=(10, 25),
            retries=3,
            backoff_factor=0.5
        )

        self.logger.info("Google Trends API initialized")

    def scrape(
        self,
        keywords: List[str] = None,
        timeframe: str = "now 7-d",
        region: str = "VN"
    ) -> List[TrendsData]:
        """
        Scrape Google Trends data for keywords.

        Args:
            keywords: List of keywords to track
            timeframe: Time range (e.g., "now 7-d", "now 1-d", "today 3-m")
            region: Region code (VN = Vietnam)

        Returns:
            List of TrendsData objects
        """
        if not keywords:
            self.logger.warning("⚠️  No keywords provided, skipping scrape")
            return []

        self._log_scrape_start(
            keywords=keywords,
            timeframe=timeframe,
            region=region
        )

        try:
            trends_data = []

            # Process keywords in batches of 5 (Google Trends API limit)
            for i in range(0, len(keywords), 5):
                batch = keywords[i:i+5]
                self.logger.info(f"📊 Fetching trends for: {batch}")

                # Add delay to avoid rate limiting (especially after first batch)
                if i > 0:
                    delay = 5
                    self.logger.info(f"⏳ Waiting {delay}s to avoid rate limit...")
                    time.sleep(delay)

                try:
                    # Build payload
                    self.pytrends.build_payload(
                        kw_list=batch,
                        timeframe=timeframe,
                        geo=region
                    )

                    # Get interest over time
                    interest_over_time_df = self.pytrends.interest_over_time()

                    # Get related queries
                    related_queries_dict = self.pytrends.related_queries()

                    # Process each keyword in batch
                    for keyword in batch:
                        try:
                            # Transform interest over time to list of dicts
                            interest_over_time = []
                            if not interest_over_time_df.empty and keyword in interest_over_time_df.columns:
                                for idx, row in interest_over_time_df.iterrows():
                                    interest_over_time.append({
                                        'date': idx.isoformat(),
                                        'value': int(row[keyword])
                                    })

                            # Transform related queries to list of dicts
                            related_queries = []
                            if keyword in related_queries_dict:
                                # Top queries
                                top_df = related_queries_dict[keyword].get('top')
                                if top_df is not None and not top_df.empty:
                                    for _, row in top_df.iterrows():
                                        related_queries.append({
                                            'query': row['query'],
                                            'value': int(row['value']),
                                            'type': 'top'
                                        })

                                # Rising queries
                                rising_df = related_queries_dict[keyword].get('rising')
                                if rising_df is not None and not rising_df.empty:
                                    for _, row in rising_df.iterrows():
                                        related_queries.append({
                                            'query': row['query'],
                                            'value': row['value'],  # May be 'Breakout' string
                                            'type': 'rising'
                                        })

                            trends_obj = TrendsData(
                                query=keyword,
                                interest_over_time=interest_over_time,
                                related_queries=related_queries,
                                region=region,
                                timeframe=timeframe
                            )

                            trends_data.append(trends_obj)

                        except Exception as e:
                            self.logger.warning(f"⚠️  Failed to process keyword '{keyword}': {e}")
                            continue

                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to fetch trends for batch {batch}: {e}")
                    continue

            self._log_scrape_complete(len(trends_data))
            return trends_data

        except Exception as e:
            self._log_scrape_error(e)
            return []
