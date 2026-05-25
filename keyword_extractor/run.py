"""
Run keyword extractor to extract trending keywords from news headlines.

Usage:
    python -m keyword_extractor.run
"""

import logging
import sys
from keyword_extractor.extractor import KeywordExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for keyword extraction."""
    try:
        logger.info("=" * 60)
        logger.info("Starting Keyword Extraction Pipeline")
        logger.info("=" * 60)

        # Run extractor
        extractor = KeywordExtractor()
        extractor.run()

        logger.info("=" * 60)
        logger.info("Keyword Extraction Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
