"""
Main orchestrator for Social Trend Detector.

Runs the full pipeline every 4 hours:
1. Producer: Scrape data from TikTok, VNExpress, YouTube
2. Consumer: Process data and detect trends
3. Save to MongoDB
"""

import sys
import logging
import signal
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from producer.orchestrator import ProducerOrchestrator
from consumer.batch_consumer import BatchConsumer


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


logger = logging.getLogger(__name__)


def run_pipeline():
    """
    Run full pipeline: Producer -> Consumer.

    This function is called by the scheduler every 4 hours.
    """
    logger.info("\n" + "=" * 80)
    logger.info("SCHEDULED RUN - Starting full pipeline...")
    logger.info("=" * 80)

    try:
        # Step 1: Run producers
        logger.info("\n[STEP 1/2] Running producers...")
        producer_orchestrator = ProducerOrchestrator()
        producer_results = producer_orchestrator.run_all()

        total_produced = sum(producer_results.values())
        logger.info(f"Producers completed: {total_produced} items sent to Kafka")

        if total_produced == 0:
            logger.warning("No items produced, skipping consumer")
            return

        # Wait for Kafka to commit messages
        logger.info("Waiting 10 seconds for Kafka to commit messages...")
        time.sleep(10)

        # Step 2: Run consumer
        logger.info("\n[STEP 2/2] Running consumer...")
        consumer = BatchConsumer()
        consumer.run_once()

        logger.info("\n" + "=" * 80)
        logger.info("Pipeline completed successfully")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)


def main():
    """
    Main entry point with scheduler.

    Runs pipeline immediately on startup, then every 4 hours.
    """
    setup_logging()

    logger.info("=" * 80)
    logger.info("SOCIAL TREND DETECTOR - STARTING")
    logger.info("=" * 80)
    logger.info("Schedule: Initial run + every 4 hours")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80 + "\n")

    # Create scheduler
    scheduler = BlockingScheduler()

    # Schedule job: run every 4 hours
    scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(hours=4),
        id='pipeline_job',
        name='Run full pipeline',
        replace_existing=True,
        max_instances=1
    )

    # Graceful shutdown handler
    def shutdown_handler(signum, frame):
        logger.info("\nReceived shutdown signal, stopping scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped gracefully")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # Run immediately on startup
        logger.info("Running initial pipeline on startup...")
        run_pipeline()

        # Start scheduler for recurring runs
        logger.info("\nStarting scheduler for recurring runs...")
        logger.info("Next run will be in 4 hours\n")
        scheduler.start()

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
