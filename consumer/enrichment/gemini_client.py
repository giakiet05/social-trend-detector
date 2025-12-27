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

        logger.info("Gemini client initialized")

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

            logger.info(f"Embedded {len(texts)} texts → {len(all_embeddings)} vectors (Gemini)")
            return all_embeddings

        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
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
                    system_instruction=system_instruction,
                    response_mime_type="application/json"  # Force JSON response
                )
            )

            # Extract text from response (new SDK structure)
            result_text = None

            # Try different extraction methods
            if hasattr(response, 'text') and response.text:
                result_text = response.text
                logger.debug("Extracted text via response.text")
            elif hasattr(response, 'candidates') and response.candidates:
                logger.debug(f"Response has candidates: {len(response.candidates)}")
                candidate = response.candidates[0]
                logger.debug(f"Candidate type: {type(candidate)}")
                logger.debug(f"Candidate attributes: {dir(candidate)}")

                # Try different paths
                if hasattr(candidate, 'text'):
                    result_text = candidate.text
                    logger.debug("Extracted text via candidate.text")
                elif hasattr(candidate, 'content'):
                    content = candidate.content
                    logger.debug(f"Content type: {type(content)}")
                    logger.debug(f"Content: {content}")

                    if hasattr(content, 'parts') and content.parts:
                        part = content.parts[0]
                        logger.debug(f"Part type: {type(part)}")
                        if hasattr(part, 'text'):
                            result_text = part.text
                            logger.debug("Extracted text via candidate.content.parts[0].text")
                        else:
                            logger.error(f"Part has no text attribute. Part: {part}")
                    else:
                        logger.error(f"Content has no parts (parts={content.parts}). Content: {content}")
                        # Check if response was blocked
                        if hasattr(candidate, 'finish_reason'):
                            logger.error(f"Finish reason: {candidate.finish_reason}")
                        if hasattr(response, 'prompt_feedback'):
                            logger.error(f"Prompt feedback: {response.prompt_feedback}")
                        # Log full response for debugging
                        logger.error(f"Full response object: {response}")
                else:
                    logger.error(f"Candidate has no content. Candidate: {candidate}")
            else:
                logger.error(f"Response structure unknown. Response: {response}")
                logger.error(f"Response type: {type(response)}")
                logger.error(f"Response attributes: {dir(response)}")

            if not result_text:
                raise ValueError("Cannot extract text from Gemini response")

            result_text = result_text.strip()

            # Log raw response for debugging
            logger.debug(f"Raw Gemini response (first 500 chars): {result_text[:500]}")

            # Try to clean up JSON if needed
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Raw response (first 1000 chars): {result_text[:1000]}")

                # Try to extract JSON from markdown code blocks
                if "```json" in result_text:
                    import re
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                    if json_match:
                        result_text = json_match.group(1)
                        result = json.loads(result_text)
                    else:
                        raise
                elif "```" in result_text:
                    # Try to extract any code block
                    import re
                    json_match = re.search(r'```\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                    if json_match:
                        result_text = json_match.group(1)
                        result = json.loads(result_text)
                    else:
                        raise
                else:
                    # Try to fix truncated JSON (common with max_tokens limit)
                    logger.warning("Attempting to fix truncated JSON...")

                    # Try to complete the JSON by adding missing closing brackets
                    fixed_text = result_text

                    # Count open/close braces and brackets
                    open_braces = fixed_text.count('{')
                    close_braces = fixed_text.count('}')
                    open_brackets = fixed_text.count('[')
                    close_brackets = fixed_text.count(']')

                    # Add missing closing brackets/braces
                    if open_brackets > close_brackets:
                        fixed_text += ']' * (open_brackets - close_brackets)
                    if open_braces > close_braces:
                        fixed_text += '}' * (open_braces - close_braces)

                    try:
                        result = json.loads(fixed_text)
                        logger.info("Successfully fixed truncated JSON")
                    except:
                        logger.error("Failed to fix truncated JSON")
                        raise e

            logger.info(f"Analyzed cluster: {result['topic']} (Gemini)")
            return result

        except Exception as e:
            logger.error(f"Cluster analysis failed: {e}")
            raise
