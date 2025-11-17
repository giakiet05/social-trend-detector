"""
CSV-based data loader for testing.
"""

import csv
import logging
from typing import List
from pathlib import Path
from .base_loader import BaseLoader
from common.models import TikTokVideo

logger = logging.getLogger(__name__)


class CSVLoader(BaseLoader):
    """Load TikTok videos from CSV file (for testing)."""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)

        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

    def load(self) -> List[TikTokVideo]:
        """Load all videos from CSV."""
        videos = []

        logger.info(f"Reading CSV file: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader, start=1):
                try:
                    video = TikTokVideo.from_csv_row(row)
                    videos.append(video)

                    if idx % 5 == 0:
                        logger.info(f"Parsed {idx} videos...")

                except Exception as e:
                    logger.warning(f"Failed to parse row {idx}: {e}")
                    continue

        logger.info(f"Successfully loaded {len(videos)} videos from CSV")
        return videos
