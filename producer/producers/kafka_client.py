"""
Shared Kafka Producer client for all data sources.
"""

import json
import logging
from typing import Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaClient:
    """
    Shared Kafka producer wrapper for sending messages to Kafka topics.

    Usage:
        kafka = KafkaClient(bootstrap_servers=["localhost:9092"])
        kafka.send(topic="tiktok-raw", message={"video_id": "123", ...})
        kafka.close()
    """

    def __init__(self, bootstrap_servers: list):
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: List of Kafka broker addresses
        """
        self.bootstrap_servers = bootstrap_servers

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # Performance configs
                acks='all',  # Wait for all replicas
                retries=3,   # Retry on failure
                max_in_flight_requests_per_connection=5,
                compression_type='gzip'  # Compress messages
            )
            logger.info(f"Kafka producer connected: {bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def send(self, topic: str, message: Dict[str, Any], key: str = None) -> bool:
        """
        Send a message to Kafka topic.

        Args:
            topic: Kafka topic name
            message: Message dictionary (will be JSON serialized)
            key: Optional message key (for partitioning)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Send message
            future = self.producer.send(
                topic=topic,
                value=message,
                key=key
            )

            # Block until sent (or timeout)
            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Message sent to {topic} "
                f"(partition={record_metadata.partition}, offset={record_metadata.offset})"
            )
            return True

        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False

    def send_batch(self, topic: str, messages: list) -> int:
        """
        Send multiple messages to Kafka topic.

        Args:
            topic: Kafka topic name
            messages: List of message dictionaries

        Returns:
            Number of successfully sent messages
        """
        success_count = 0

        for message in messages:
            if self.send(topic, message):
                success_count += 1

        # Flush to ensure all messages are sent
        self.producer.flush()

        logger.info(f"Sent {success_count}/{len(messages)} messages to {topic}")
        return success_count

    def close(self):
        """Close Kafka producer connection."""
        if hasattr(self, 'producer'):
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")
