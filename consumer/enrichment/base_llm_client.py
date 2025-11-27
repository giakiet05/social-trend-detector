"""
Abstract Base Classes for LLM clients (split into embedding & analysis).
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseEmbeddingClient(ABC):
    """
    Abstract base class for embedding providers (OpenAI, Gemini, etc.).

    Handles text-to-vector conversion.
    """

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        pass


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM providers (OpenAI, Gemini, etc.).

    Handles text generation and analysis.
    """

    @abstractmethod
    def analyze_cluster(self, prompt: str) -> Dict[str, any]:
        """
        Analyze cluster using custom prompt (multi-source support).

        Args:
            prompt: Custom prompt string with multi-source context

        Returns:
            Dict with keys: topic, summary, sentiment, keywords
        """
        pass
