"""
Factories for creating embedding and LLM clients based on configuration.
"""

import logging
from consumer.config.settings import settings
from .base_llm_client import BaseEmbeddingClient, BaseLLMClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)


def create_embedding_client() -> BaseEmbeddingClient:
    """
    Create embedding client based on EMBEDDING_PROVIDER env variable.

    Returns:
        BaseEmbeddingClient instance (OpenAI or Gemini)

    Raises:
        ValueError: If unknown provider
    """
    provider = settings.llm_provider.EMBEDDING_PROVIDER.lower()

    if provider == "openai":
        logger.info("🔧 Using OpenAI for embeddings")
        return OpenAIClient()
    elif provider == "gemini":
        logger.info("🔧 Using Gemini for embeddings")
        return GeminiClient()
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. "
            f"Set EMBEDDING_PROVIDER to 'openai' or 'gemini' in .env"
        )


def create_llm_client() -> BaseLLMClient:
    """
    Create LLM client based on LLM_PROVIDER env variable.

    Returns:
        BaseLLMClient instance (OpenAI or Gemini)

    Raises:
        ValueError: If unknown provider
    """
    provider = settings.llm_provider.LLM_PROVIDER.lower()

    if provider == "openai":
        logger.info("🔧 Using OpenAI for LLM analysis")
        return OpenAIClient()
    elif provider == "gemini":
        logger.info("🔧 Using Gemini for LLM analysis")
        return GeminiClient()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Set LLM_PROVIDER to 'openai' or 'gemini' in .env"
        )
