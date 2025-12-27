"""
OpenAI client for embeddings and LLM analysis.
"""

import logging
from typing import List, Dict
from openai import OpenAI
from consumer.config.settings import settings
from .base_llm_client import BaseEmbeddingClient, BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseEmbeddingClient, BaseLLMClient):
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
        logger.info("OpenAI client initialized")

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

            logger.info(f"Embedded {len(texts)} texts → {len(all_embeddings)} vectors")
            return all_embeddings

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    def analyze_cluster(self, prompt: str) -> Dict[str, any]:
        """
        Analyze cluster using custom prompt (multi-source support).

        Args:
            prompt: Custom prompt string with multi-source context

        Returns:
            Dict with keys: topic, summary, sentiment, keywords
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.openai.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia phân tích xu hướng xã hội từ nhiều nguồn (TikTok, YouTube, VNExpress). Luôn trả lời bằng tiếng Việt và format JSON hợp lệ."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            result = json.loads(result_text)

            logger.info(f"Analyzed cluster: {result['topic']} (OpenAI)")
            return result

        except Exception as e:
            logger.error(f"Cluster analysis failed: {e}")
            raise