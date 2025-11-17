"""
Abstract base loader for data sources.
"""

from abc import ABC, abstractmethod
from typing import List
from common.models import TikTokVideo


class BaseLoader(ABC):
    """Abstract base class for data loaders."""

    @abstractmethod
    def load(self) -> List[TikTokVideo]:
        """
        Load videos from source.

        Returns:
            List of TikTokVideo objects
        """
        pass
