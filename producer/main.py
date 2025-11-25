"""
Producer main entry point with scheduler.

Runs all producers on a schedule for Docker container.
Designed to run continuously as a long-lived process.

Schedule:
    - Initial run on startup
    - Repeat every 4 hours

Usage:
    python -m producer.main
"""

import sys
import logging
import signal
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from producer.orchestrator import ProducerOrchestrator


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


logger = logging.getLogger(__name__)


def run_producers():
    """
    Run all producers via orchestrator.

    This function is called by the scheduler.
    """
    logger.info("\n" + "=" * 80)
    logger.info("⏰ SCHEDULED RUN - Starting producers...")
    logger.info("=" * 80)

    try:
        orchestrator = ProducerOrchestrator()
        results = orchestrator.run_all()

        total_items = sum(results.values())
        if total_items > 0:
            logger.info(f"✅ Scheduled run completed: {total_items} items sent")
        else:
            logger.warning("⚠️  Scheduled run completed but no items were sent")

    except Exception as e:
        logger.error(f"❌ Scheduled run failed: {e}", exc_info=True)


def main():
    """
    Main entry point with scheduler.

    Runs producers immediately on startup, then every 4 hours.
    """
    setup_logging()

    logger.info("=" * 80)
    logger.info("🚀 PRODUCER SCHEDULER - STARTING")
    logger.info("=" * 80)
    logger.info("Schedule: Initial run + every 4 hours")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80 + "\n")

    # Create scheduler
    scheduler = BlockingScheduler()

    # Schedule job: run every 4 hours
    scheduler.add_job(
        run_producers,
        trigger=IntervalTrigger(hours=4),
        id='producer_job',
        name='Run all producers',
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )

    # Graceful shutdown handler
    def shutdown_handler(signum, frame):
        logger.info("\n⚠️  Received shutdown signal, stopping scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("✅ Scheduler stopped gracefully")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    try:
        # Run immediately on startup
        logger.info("🏃 Running initial scrape on startup...")
        run_producers()

        # Start scheduler for recurring runs
        logger.info("\n⏰ Starting scheduler for recurring runs...")
        logger.info("Next run will be in 4 hours\n")
        scheduler.start()

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
