"""
Embedding stage: Convert text to vectors using embedding provider.
"""

from typing import List
import logging
from .base_stage import BaseStage
from common.models import ContentItem
from consumer.enrichment.base_llm_client import BaseEmbeddingClient

logger = logging.getLogger(__name__)


class EmbeddingStage(BaseStage):
    """Embed content texts using embedding provider (OpenAI or Gemini)."""

    def __init__(self, embedding_client: BaseEmbeddingClient):
        super().__init__("EmbeddingStage")
        self.embedding_client = embedding_client

    def execute(self, items: List[ContentItem]) -> List[ContentItem]:
        """
        Embed content texts to vectors and store in metadata.

        Args:
            items: Filtered ContentItem objects

        Returns:
            ContentItem objects with embeddings added to metadata
        """
        self.log_start()

        if not items:
            self.log_skip("No items to embed")
            return items

        # Extract combined text (text + hashtags)
        texts = []
        for item in items:
            combined = item.text + " " + " ".join(item.hashtags)
            texts.append(combined)

        # Batch embed
        try:
            embeddings = self.embedding_client.embed_texts(texts)

            # Add embeddings to metadata
            for item, embedding in zip(items, embeddings):
                item.metadata["embedding"] = embedding

            self.log_complete(f"Embedded {len(items)} items (dim={len(embeddings[0])})")
            return items

        except Exception as e:
            logger.error(f"Embedding failed: {e}", exc_info=True)
            raise
