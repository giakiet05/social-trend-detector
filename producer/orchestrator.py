"""
Producer Orchestrator: Run all producers concurrently.
"""

import logging
import concurrent.futures
from typing import Dict
from producer.producers.tiktok_producer import TikTokProducer
from producer.producers.vnexpress_producer import VNExpressProducer
from producer.producers.youtube_producer import YouTubeProducer

logger = logging.getLogger(__name__)


class ProducerOrchestrator:
    """
    Orchestrator to run multiple producers concurrently.

    Runs TikTok, VNExpress, and YouTube producers in parallel using ThreadPoolExecutor.

    Usage:
        orchestrator = ProducerOrchestrator()
        results = orchestrator.run_all()
    """

    def __init__(self):
        """Initialize orchestrator with all producers."""
        self.producers = {
            'tiktok': TikTokProducer(),
            'vnexpress': VNExpressProducer(),
            'youtube': YouTubeProducer()
        }

        logger.info("✅ ProducerOrchestrator initialized")
        logger.info(f"   Producers: {list(self.producers.keys())}")

    def run_all(self) -> Dict[str, int]:
        """
        Run all producers concurrently.

        Uses ThreadPoolExecutor to run producers in parallel threads.
        Each producer scrapes, saves, and sends data independently.

        Returns:
            Dictionary mapping producer name to number of items sent
            Example: {'tiktok': 20, 'vnexpress': 21, 'youtube': 10}
        """
        logger.info("\n" + "=" * 70)
        logger.info("🚀 PRODUCER ORCHESTRATOR - STARTING ALL PRODUCERS")
        logger.info("=" * 70)

        results = {}

        # Run producers in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all producer tasks
            future_to_producer = {
                executor.submit(producer.run): name
                for name, producer in self.producers.items()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_producer):
                producer_name = future_to_producer[future]

                try:
                    count = future.result()
                    results[producer_name] = count
                    logger.info(f"✅ {producer_name.upper()} completed: {count} items sent")

                except Exception as e:
                    logger.error(f"❌ {producer_name.upper()} failed: {e}", exc_info=True)
                    results[producer_name] = 0

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ PRODUCER ORCHESTRATOR - ALL PRODUCERS COMPLETED")
        logger.info("=" * 70)

        total_items = sum(results.values())
        logger.info(f"📊 Results Summary:")
        for name, count in results.items():
            logger.info(f"   {name.upper()}: {count} items")
        logger.info(f"   TOTAL: {total_items} items")
        logger.info("=" * 70 + "\n")

        return results

    def run_single(self, producer_name: str) -> int:
        """
        Run a single producer by name.

        Args:
            producer_name: Name of producer ('tiktok', 'vnexpress', 'youtube')

        Returns:
            Number of items sent

        Raises:
            ValueError: If producer name not found
        """
        if producer_name not in self.producers:
            raise ValueError(
                f"Producer '{producer_name}' not found. "
                f"Available: {list(self.producers.keys())}"
            )

        logger.info(f"🚀 Running single producer: {producer_name.upper()}")
        producer = self.producers[producer_name]
        return producer.run()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run all producers
    orchestrator = ProducerOrchestrator()
    results = orchestrator.run_single("vnexpress")

    # Exit with error code if no items were sent
    if sum(results.values()) == 0:
        exit(1)
