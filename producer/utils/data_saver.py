"""
Universal data saver for all scraping sources.
Saves raw scraped data as timestamped JSON files for backup/testing.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Any, Literal, Dict

logger = logging.getLogger(__name__)


class DataSaver:
    """
    Universal data saver for all producers.

    Saves scraped data as timestamped JSON files for:
    - Backup/replay without calling expensive APIs
    - Testing and debugging
    - Data auditing

    Usage:
        saver = DataSaver(base_dir="data/raw")
        saver.save(source="tiktok", data=videos)
    """

    def __init__(self, base_dir: str = "data/raw"):
        """
        Initialize DataSaver.

        Args:
            base_dir: Base directory for all raw data (default: data/raw)
        """
        self.base_dir = Path(base_dir)
        logger.info(f"DataSaver initialized (base_dir: {self.base_dir})")

    def save(
        self,
        source: str,
        data: List[Any],
        format: Literal["json"] = "json"
    ) -> Path:
        """
        Save data to timestamped file.

        Args:
            source: Data source name (tiktok, vnexpress, youtube, google_trends)
            data: List of data objects (must have to_dict() method)
            format: Output format (currently only json supported)

        Returns:
            Path to saved file

        Raises:
            ValueError: If data is empty or invalid
            IOError: If file write fails
        """
        if not data:
            logger.warning(f"No data to save for source: {source}")
            raise ValueError(f"Cannot save empty data for source: {source}")

        # Create source directory
        source_dir = self.base_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = source_dir / f"{timestamp}.{format}"

        try:
            if format == "json":
                self._save_json(filename, data)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Saved {len(data)} items to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save data: {e}", exc_info=True)
            raise IOError(f"Failed to save data to {filename}: {e}")

    def _save_json(self, filepath: Path, data: List[Any]) -> None:
        """
        Save data as JSON file.

        Args:
            filepath: Output file path
            data: List of data objects (must have to_dict() method)
        """
        # Convert objects to dictionaries
        serialized_data = []
        for item in data:
            if hasattr(item, 'to_dict'):
                serialized_data.append(item.to_dict())
            elif isinstance(item, dict):
                serialized_data.append(item)
            else:
                raise ValueError(f"Item must have to_dict() method or be a dict: {type(item)}")

        # Write to file with pretty formatting
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                serialized_data,
                f,
                ensure_ascii=False,
                indent=2
            )

    def append_to_aggregate(
        self,
        source: str,
        data: List[Any],
        format: Literal["json"] = "json"
    ) -> Path:
        """
        Append new data to aggregate file for this source.

        Creates/updates a single aggregate file per source (e.g., tiktok_all.json)
        that accumulates all scraped data over time.

        Args:
            source: Data source name (tiktok, vnexpress, youtube, google_trends)
            data: List of new data objects to append
            format: Output format (currently only json supported)

        Returns:
            Path to aggregate file

        Raises:
            ValueError: If data is empty
            IOError: If file operation fails
        """
        if not data:
            logger.warning(f"No data to append for source: {source}")
            raise ValueError(f"Cannot append empty data for source: {source}")

        # Aggregate file path
        filename = f"{source}_all.{format}"
        filepath = self.base_dir / filename

        try:
            if format == "json":
                self._append_json(filepath, data)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Appended {len(data)} items to aggregate: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to append to aggregate: {e}", exc_info=True)
            raise IOError(f"Failed to append data to {filepath}: {e}")

    def _append_json(self, filepath: Path, new_data: List[Any]) -> None:
        """
        Append new data to existing JSON aggregate file.

        Deduplicates based on unique ID field (video_id, article_id, query).

        Args:
            filepath: Path to aggregate JSON file
            new_data: List of new items to append
        """
        # Serialize new data
        serialized_new = []
        for item in new_data:
            if hasattr(item, 'to_dict'):
                serialized_new.append(item.to_dict())
            elif isinstance(item, dict):
                serialized_new.append(item)
            else:
                raise ValueError(f"Item must have to_dict() method or be a dict: {type(item)}")

        # Read existing data if file exists
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        logger.warning(f"Existing file is not a list, overwriting")
                        existing_data = []
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse existing file, overwriting")
                existing_data = []
        else:
            existing_data = []

        # Deduplicate: extract existing IDs
        existing_ids = set()
        for item in existing_data:
            # Try different ID fields (video_id, article_id, query)
            item_id = item.get('video_id') or item.get('article_id') or item.get('query')
            if item_id:
                existing_ids.add(item_id)

        # Filter out duplicates from new data
        serialized_new_unique = []
        duplicates_count = 0
        for item in serialized_new:
            item_id = item.get('video_id') or item.get('article_id') or item.get('query')
            if item_id and item_id in existing_ids:
                duplicates_count += 1
                continue  # Skip duplicate
            serialized_new_unique.append(item)
            if item_id:
                existing_ids.add(item_id)  # Track new ID

        # Log deduplication stats
        if duplicates_count > 0:
            logger.info(f"   Skipped {duplicates_count} duplicate items")

        # Append unique new data
        combined_data = existing_data + serialized_new_unique

        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                combined_data,
                f,
                ensure_ascii=False,
                indent=2
            )
