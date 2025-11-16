"""
OpenAI client for embeddings and LLM analysis.
"""

import logging
from typing import List, Dict
from openai import OpenAI
from config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for embeddings and trend analysis."""

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to settings)
        """
        self.api_key = api_key or settings.openai.API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env")

        self.client = OpenAI(api_key=self.api_key)
        logger.info("✅ OpenAI client initialized")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (1536 dimensions each)
        """
        if not texts:
            return []

        try:
            # OpenAI supports batching up to 2048 texts
            batch_size = settings.openai.EMBEDDING_BATCH_SIZE
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = self.client.embeddings.create(
                    model=settings.openai.EMBEDDING_MODEL,
                    input=batch
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Embedded {len(batch)} texts (batch {i // batch_size + 1})")

            logger.info(f"✅ Embedded {len(texts)} texts → {len(all_embeddings)} vectors")
            return all_embeddings

        except Exception as e:
            logger.error(f"❌ Embedding failed: {e}")
            raise

    def analyze_cluster(self, videos: List[Dict]) -> Dict[str, any]:
        """
        Analyze a cluster of videos to extract topic, summary, sentiment.

        Args:
            videos: List of video dicts (each with 'text', 'hashtags', etc.)

        Returns:
            Dict with keys: topic, summary, sentiment, keywords
        """
        if not videos:
            return {
                "topic": "Unknown",
                "summary": "No videos in cluster",
                "sentiment": "neutral",
                "keywords": []
            }

        try:
            # Prepare prompt with sample videos
            sample_size = min(5, len(videos))
            sample_videos = videos[:sample_size]

            # Build prompt
            video_texts = []
            for i, video in enumerate(sample_videos, 1):
                text = video.get('text', '')
                hashtags = video.get('hashtags', [])
                video_texts.append(
                    f"{i}. Text: {text[:200]}...\n"
                    f"   Hashtags: {', '.join(hashtags[:5])}"
                )

            prompt = f"""Analyze these {len(videos)} TikTok videos about TECH trends.

Sample videos:
{chr(10).join(video_texts)}

Extract:
1. Topic (concise title, 3-7 words)
2. Summary (1-2 sentences describing the trend)
3. Sentiment (positive/negative/neutral)
4. Keywords (5-10 relevant keywords)

Respond in JSON format:
{{
  "topic": "...",
  "summary": "...",
  "sentiment": "...",
  "keywords": ["...", "..."]
}}"""

            response = self.client.chat.completions.create(
                model=settings.openai.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a TikTok trend analyst specializing in tech content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.openai.MAX_TOKENS,
                temperature=0.7
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            result = json.loads(result_text)

            logger.info(f"✅ Analyzed cluster: {result['topic']}")
            return result

        except Exception as e:
            logger.error(f"❌ Cluster analysis failed: {e}")
            # Return fallback
            return {
                "topic": "Tech Trend (Analysis Failed)",
                "summary": f"Cluster of {len(videos)} videos about tech",
                "sentiment": "neutral",
                "keywords": []
            }