import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

class KafkaProducerClient:
    """
    A Kafka client for sending messages with serialization and logging.
    """
    def __init__(self, bootstrap_servers: list):
        """
        Initialize Kafka Producer.

        Args:
            bootstrap_servers: List of Kafka broker addresses, e.g., ['localhost:9092']
        """
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                # Serialize message value to JSON bytes
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                # Configuration for reliability and performance
                acks='all',              # Wait for all replicas to acknowledge
                retries=3,               # Retry 3 times on failure
                retry_backoff_ms=1000    # Wait 1 second between retries
            )
            logger.info(f"Successfully connected to Kafka brokers at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}", exc_info=True)
            raise

    def _on_send_success(self, record_metadata):
        """Callback for successful message send."""
        logger.debug(
            f"Message sent to topic '{record_metadata.topic}' "
            f"[partition {record_metadata.partition}, offset {record_metadata.offset}]"
        )

    def _on_send_error(self, excp):
        """Callback for failed message send."""
        logger.error("Failed to send message", exc_info=excp)

    def send_message(self, topic: str, message: dict):
        """
        Send a message (dict) to a specific Kafka topic.

        Args:
            topic: Topic name
            message: Message content (Python dictionary)
        """
        try:
            future = self.producer.send(topic, value=message)
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
        except KafkaError as e:
            logger.error(f"Kafka error while sending message to topic '{topic}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error while sending message: {e}", exc_info=True)

    def close(self):
        """
        Ensure all messages are sent and close the producer connection.
        Important to call this when shutting down.
        """
        if self.producer:
            logger.info("Flushing remaining messages and closing Kafka producer...")
            # flush() blocks until all messages are sent or timeout
            self.producer.flush(timeout=10)  # Wait max 10 seconds
            self.producer.close()
            logger.info("Kafka producer closed successfully")

