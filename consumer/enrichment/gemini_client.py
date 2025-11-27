"""
Gemini client for embeddings and LLM analysis.
"""

import logging
import json
from typing import List, Dict
from google import genai
from google.genai import types
from consumer.config.settings import settings
from .base_llm_client import BaseEmbeddingClient, BaseLLMClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseEmbeddingClient, BaseLLMClient):
    """Gemini client for embeddings and trend analysis."""

    def __init__(self, api_key: str = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (defaults to settings)
        """
        self.api_key = api_key or settings.gemini.API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY in .env")

        # Create Gemini client (new syntax)
        self.client = genai.Client(api_key=self.api_key)

        # Model names
        self.embedding_model = settings.gemini.EMBEDDING_MODEL
        self.llm_model = settings.gemini.LLM_MODEL

        logger.info("✅ Gemini client initialized")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            all_embeddings = []

            # Gemini embedding - process each text individually
            # Note: New Gemini SDK may not have batch embed_content yet
            for text in texts:
                # Using new SDK syntax (if embed API is available via client)
                # Otherwise fallback to individual calls
                result = self.client.models.embed_content(
                    model=self.embedding_model,
                    contents=text
                )
                # Extract embedding from response
                all_embeddings.append(result.embeddings[0].values)

            logger.info(f"✅ Embedded {len(texts)} texts → {len(all_embeddings)} vectors (Gemini)")
            return all_embeddings

        except Exception as e:
            logger.error(f"❌ Gemini embedding failed: {e}")
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
            # Build system instruction for JSON output
            system_instruction = "Bạn là chuyên gia phân tích xu hướng xã hội từ nhiều nguồn (TikTok, YouTube, VNExpress). Trả về kết quả dạng JSON."

            # Generate content with new SDK syntax
            response = self.client.models.generate_content(
                model=self.llm_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=settings.gemini.MAX_TOKENS,
                    system_instruction=system_instruction
                )
            )

            result_text = response.text.strip()

            # Parse JSON response
            result = json.loads(result_text)

            logger.info(f"✅ Analyzed cluster: {result['topic']} (Gemini)")
            return result

        except Exception as e:
            logger.error(f"❌ Cluster analysis failed: {e}")
            raise
