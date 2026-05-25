"""
Keyword Extractor - Extract trending keywords from news headlines using LLM.
"""

import logging
import feedparser
import json
from datetime import datetime
from typing import List, Dict
from pymongo import MongoClient
from keyword_extractor.config.settings import settings

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Extract trending keywords from news headlines.

    Flow:
    1. Scrape RSS feeds (trending categories only)
    2. Extract titles
    3. Batch LLM call to extract keywords
    4. Save to MongoDB extracted_keywords collection
    """

    def __init__(self):
        """Initialize extractor."""
        self.mongo_client = MongoClient(settings.MONGO_URI)
        self.db = self.mongo_client[settings.MONGO_DB]
        self.collection = self.db[settings.EXTRACTED_KEYWORDS_COLLECTION]

        # Setup LLM client
        if settings.LLM_PROVIDER == "openai":
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:  # gemini
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.llm_client = genai.GenerativeModel('gemini-1.5-flash')

    def run(self):
        """Run keyword extraction pipeline."""
        logger.info("Starting keyword extraction...")

        # 1. Scrape headlines
        headlines = self._scrape_headlines()
        logger.info(f"Scraped {len(headlines)} headlines from {len(settings.rss_feeds)} RSS feeds")

        if not headlines:
            logger.warning("No headlines found, skipping extraction")
            return

        # 2. Limit headlines
        limited_headlines = headlines[:settings.MAX_HEADLINES]
        logger.info(f"Using {len(limited_headlines)} headlines for extraction")

        # 3. Extract keywords using LLM
        keywords = self._extract_keywords_with_llm(limited_headlines)
        logger.info(f"Extracted {len(keywords)} keywords")

        # 4. Save to MongoDB
        self._save_keywords(keywords)
        logger.info("Keywords saved to MongoDB")

        # 5. Cleanup
        self.mongo_client.close()

    def _scrape_headlines(self) -> List[str]:
        """
        Scrape headlines from RSS feeds.

        Returns:
            List of headline strings (title only)
        """
        headlines = []

        for feed_url in settings.rss_feeds:
            try:
                logger.info(f"Fetching RSS: {feed_url}")
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    logger.warning(f"Feed parse error: {feed_url}")
                    continue

                for entry in feed.entries:
                    title = entry.get('title', '').strip()
                    if title:
                        headlines.append(title)

            except Exception as e:
                logger.warning(f"Failed to fetch feed {feed_url}: {e}")
                continue

        return headlines

    def _extract_keywords_with_llm(self, headlines: List[str]) -> List[Dict]:
        """
        Extract keywords from headlines using LLM.

        Args:
            headlines: List of news headlines

        Returns:
            List of keyword dicts with metadata
        """
        # Prepare prompt
        headlines_text = "\n".join([f"- {h}" for h in headlines])

        prompt = f"""Từ các tiêu đề tin tức sau đây, hãy trích xuất {settings.NUM_KEYWORDS} từ khóa/chủ đề TRENDING có tiềm năng viral cao nhất.

Tiêu chí:
- Tập trung vào giải trí, công nghệ, lifestyle, sức khỏe, xe, du lịch, thể thao
- Bỏ qua chính trị, quân sự, pháp luật
- Ưu tiên từ khóa xuất hiện nhiều lần
- Ưu tiên từ khóa có tiềm năng viral (drama, scandal, sản phẩm mới, sự kiện)
- Trả về từ khóa ngắn gọn, dễ search (2-5 từ)

Tiêu đề tin tức:
{headlines_text}

Trả về JSON format:
{{
    "keywords": [
        {{"keyword": "tên từ khóa", "category": "giải trí/công nghệ/lifestyle/...", "reason": "lý do trending"}},
        ...
    ]
}}
"""

        try:
            if settings.LLM_PROVIDER == "openai":
                response = self.llm_client.chat.completions.create(
                    model="gpt-4.1-mini",  # Cheaper model
                    messages=[
                        {"role": "system", "content": "You are a Vietnamese trending keywords expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
            else:  # gemini
                response = self.llm_client.generate_content(prompt)
                result_text = response.text

            # Parse JSON
            result = json.loads(result_text)
            keywords = result.get('keywords', [])

            # Add metadata
            for kw in keywords:
                kw['extracted_at'] = datetime.utcnow().isoformat()
                kw['status'] = 'pending'  # Admin needs to review
                kw['source'] = 'news'
                kw['num_headlines'] = len(headlines)

            return keywords

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []

    def _save_keywords(self, keywords: List[Dict]):
        """
        Save extracted keywords to MongoDB.

        Args:
            keywords: List of keyword dicts
        """
        if not keywords:
            return

        try:
            # Clear old pending keywords (from previous runs)
            self.collection.delete_many({"status": "pending"})

            # Insert new keywords
            self.collection.insert_many(keywords)
            logger.info(f"Inserted {len(keywords)} keywords into {settings.EXTRACTED_KEYWORDS_COLLECTION}")

        except Exception as e:
            logger.error(f"Failed to save keywords to MongoDB: {e}")
