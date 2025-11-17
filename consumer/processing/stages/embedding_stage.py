"""
Embedding stage: Convert text to vectors using OpenAI.
"""

from typing import List, Dict, Tuple
import logging
import numpy as np
from .base_stage import BaseStage
from enrichment.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class EmbeddingStage(BaseStage):
    """Embed video texts using OpenAI API."""

    def __init__(self, openai_client: OpenAIClient):
        super().__init__("EmbeddingStage")
        self.openai = openai_client

    def execute(self, videos: List[Dict]) -> Tuple[List[Dict], np.ndarray]:
        """
        Embed video texts to vectors.

        Args:
            videos: Filtered videos

        Returns:
            Tuple of (videos, embeddings array)
        """
        self.log_start()

        if not videos:
            self.log_skip("No videos to embed")
            return videos, np.array([])

        # Extract combined text (text + hashtags)
        texts = []
        for video in videos:
            text = video.get('text', '')
            hashtags = video.get('hashtags', [])
            combined = text + " " + " ".join(hashtags)
            texts.append(combined)

        # Batch embed
        try:
            embeddings = self.openai.embed_texts(texts)
            embeddings_array = np.array(embeddings)

            self.log_complete(f"Embedded {len(videos)} videos → shape {embeddings_array.shape}")
            return videos, embeddings_array

        except Exception as e:
            logger.error(f"Embedding failed: {e}", exc_info=True)
            raise
