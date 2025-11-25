"""
Producer CLI tool for manual runs.

Run producers manually for development/testing.

Usage:
    python -m producer.cli                 # Run all producers
    python -m producer.cli --source tiktok # Run single producer
"""

import sys
import logging
import argparse
from producer.orchestrator import ProducerOrchestrator


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse arguments
    parser = argparse.ArgumentParser(description='Run TikTok Trend Detector producers')
    parser.add_argument(
        '--source',
        type=str,
        choices=['tiktok', 'vnexpress', 'youtube', 'all'],
        default='all',
        help='Data source to scrape (default: all)'
    )
    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = ProducerOrchestrator()

    try:
        if args.source == 'all':
            # Run all producers
            logger.info("🚀 Running all producers...")
            results = orchestrator.run_all()
        else:
            # Run single producer
            logger.info(f"🚀 Running {args.source} producer...")
            count = orchestrator.run_single(args.source)
            results = {args.source: count}

        # Check if any items were sent
        total_items = sum(results.values())
        if total_items == 0:
            logger.error("❌ No items were sent to Kafka")
            sys.exit(1)
        else:
            logger.info(f"✅ Successfully sent {total_items} items to Kafka")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
