"""File-based caching for GitHub API responses."""

import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Optional

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FileCache:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized cache at {self.cache_dir}")

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace(":", "_").replace("@", "_")
        return self.cache_dir / f"{safe_key}.pkl"

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds. If None, no expiration check.

        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {key}")
            return None

        try:
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            cached_at = data.get("cached_at", 0)
            value = data.get("value")

            # Check TTL if provided
            if ttl is not None:
                age = time.time() - cached_at
                if age > ttl:
                    logger.debug(f"Cache expired: {key} (age: {age:.0f}s, ttl: {ttl}s)")
                    return None

            logger.debug(f"Cache hit: {key}")
            return value

        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)

        try:
            data = {
                "cached_at": time.time(),
                "value": value,
            }

            with open(cache_path, "wb") as f:
                pickle.dump(data, f)

            logger.debug(f"Cached: {key}")

        except Exception as e:
            logger.warning(f"Failed to write cache for {key}: {e}")

    def invalidate(self, key: str) -> None:
        """
        Invalidate a cache entry.

        Args:
            key: Cache key to invalidate
        """
        cache_path = self._get_cache_path(key)

        try:
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Invalidated cache: {key}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache for {key}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Cleared all cache entries")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
