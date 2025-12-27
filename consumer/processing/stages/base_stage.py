"""
Abstract base class for pipeline stages.
"""

from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger(__name__)


class BaseStage(ABC):
    """Abstract base class for pipeline stages."""

    def __init__(self, stage_name: str = None):
        """
        Initialize stage.

        Args:
            stage_name: Name of the stage (for logging)
        """
        self.stage_name = stage_name or self.__class__.__name__

    @abstractmethod
    def execute(self, data: Any) -> Any:
        """
        Execute the stage logic.

        Args:
            data: Input data (type varies by stage)

        Returns:
            Transformed data (type varies by stage)
        """
        pass

    def log_start(self):
        """Log stage start."""
        logger.info(f"▶️  {self.stage_name} started")

    def log_complete(self, message: str = ""):
        """Log stage completion."""
        msg = f"{self.stage_name} completed"
        if message:
            msg += f": {message}"
        logger.info(msg)

    def log_skip(self, reason: str):
        """Log stage skip."""
        logger.warning(f"⏭️  {self.stage_name} skipped: {reason}")
