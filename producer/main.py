"""
TikTok Producer main entry point.
"""

import time
import logging
from config.settings import settings
from clients.kafka_client import KafkaProducerClient
from loaders.csv_loader import CSVLoader
from utils.logger import setup_logger

# Setup logging
setup_logger(level=getattr(logging, settings.logging.LEVEL))
logger = logging.getLogger(__name__)


class TikTokProducer:
    """Main Producer class."""

    def __init__(self):
        # Initialize Kafka client
        self.kafka_client = KafkaProducerClient(
            bootstrap_servers=settings.kafka.BOOTSTRAP_SERVERS
        )

        # Initialize loader based on mode
        if settings.runtime.MODE == "mock":
            logger.info("🧪 Running in MOCK mode - Loading from CSV")
            self.loader = CSVLoader(csv_path=settings.mock.CSV_PATH)
        else:            # TODO: Implement Apify loader
            raise NotImplementedError("LIVE mode not yet implemented")

    def run_mock_mode(self):
        """Run mock mode - read CSV and send to Kafka."""
        logger.info("=" * 60)
        logger.info("🚀 STARTING PRODUCER - MOCK MODE")
        logger.info("=" * 60)

        # Load videos from CSV
        videos = self.loader.load()

        if not videos:
            logger.warning("❌ No videos to send!")
            return

        logger.info(f"📦 Will send {len(videos)} videos to Kafka topic: {settings.kafka.TOPIC}")

        # Send each video to Kafka
        success_count = 0
        for idx, video in enumerate(videos, start=1):
            try:
                # Convert to dict
                message = video.to_dict()

                # Send to Kafka
                self.kafka_client.send_message(
                    topic=settings.kafka.TOPIC,
                    message=message
                )

                success_count += 1
                logger.info(f"✅ [{idx}/{len(videos)}] Sent video: {video.video_id}")

                # Simulate real-time if enabled
                if settings.mock.SIMULATE_REALTIME and idx < len(videos):
                    time.sleep(settings.mock.DELAY_SECONDS)

            except Exception as e:
                logger.error(f"❌ Failed to send video {video.video_id}: {e}")

        logger.info("=" * 60)
        logger.info(f"🎉 COMPLETED: {success_count}/{len(videos)} videos sent successfully")
        logger.info("=" * 60)

    def run(self):
        """Start producer based on mode."""
        try:
            if settings.runtime.MODE == "mock":
                self.run_mock_mode()
            else:
                # TODO: run_live_mode()
                pass
        finally:
            # Cleanup
            self.kafka_client.close()


if __name__ == "__main__":
    producer = TikTokProducer()
    producer.run()
