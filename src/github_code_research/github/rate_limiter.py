"""GitHub API rate limiter with persistent state."""

import json
import time
from pathlib import Path
from typing import Optional

from ..utils.errors import RateLimitError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Two-tier rate limiter for GitHub API."""

    # Rate limit configurations
    GENERAL_LIMIT = 5000  # requests per hour
    SEARCH_LIMIT = 30     # requests per minute

    def __init__(self, state_file: str = ".rate_limit_cache.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load rate limit state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load rate limit state: {e}")

        return {
            "general": {
                "remaining": self.GENERAL_LIMIT,
                "reset": time.time() + 3600,
                "limit": self.GENERAL_LIMIT,
            },
            "search": {
                "remaining": self.SEARCH_LIMIT,
                "reset": time.time() + 60,
                "limit": self.SEARCH_LIMIT,
            },
        }

    def _save_state(self) -> None:
        """Save rate limit state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save rate limit state: {e}")

    def check_limit(self, endpoint_type: str = "general") -> None:
        """
        Check if we can make a request.

        Args:
            endpoint_type: Either 'general' or 'search'

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        if endpoint_type not in self.state:
            logger.warning(f"Unknown endpoint type: {endpoint_type}, using general")
            endpoint_type = "general"

        limit_info = self.state[endpoint_type]
        current_time = time.time()

        # Reset if window has passed
        if current_time >= limit_info["reset"]:
            if endpoint_type == "general":
                limit_info["remaining"] = self.GENERAL_LIMIT
                limit_info["reset"] = current_time + 3600
            else:  # search
                limit_info["remaining"] = self.SEARCH_LIMIT
                limit_info["reset"] = current_time + 60
            self._save_state()

        # Check if we have remaining requests
        if limit_info["remaining"] <= 0:
            wait_time = int(limit_info["reset"] - current_time)
            raise RateLimitError(
                f"GitHub {endpoint_type} API rate limit exceeded. "
                f"Reset in {wait_time} seconds.",
                reset_time=int(limit_info["reset"])
            )

        # Decrement remaining
        limit_info["remaining"] -= 1
        self._save_state()

        logger.debug(
            f"{endpoint_type.capitalize()} API: "
            f"{limit_info['remaining']}/{limit_info['limit']} remaining"
        )

    def update_from_headers(self, headers: dict, endpoint_type: str = "general") -> None:
        """
        Update rate limit state from GitHub response headers.

        Args:
            headers: Response headers from GitHub API
            endpoint_type: Either 'general' or 'search'
        """
        if endpoint_type not in self.state:
            return

        limit_info = self.state[endpoint_type]

        # GitHub uses different header names for different endpoints
        if endpoint_type == "search":
            remaining_header = "x-ratelimit-remaining"
            limit_header = "x-ratelimit-limit"
            reset_header = "x-ratelimit-reset"
        else:
            remaining_header = "x-ratelimit-remaining"
            limit_header = "x-ratelimit-limit"
            reset_header = "x-ratelimit-reset"

        try:
            if remaining_header in headers:
                limit_info["remaining"] = int(headers[remaining_header])

            if limit_header in headers:
                limit_info["limit"] = int(headers[limit_header])

            if reset_header in headers:
                limit_info["reset"] = int(headers[reset_header])

            self._save_state()

            logger.debug(
                f"Updated {endpoint_type} rate limit from headers: "
                f"{limit_info['remaining']}/{limit_info['limit']}"
            )

        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")

    def get_wait_time(self, endpoint_type: str = "general") -> Optional[int]:
        """
        Get wait time in seconds until rate limit resets.

        Args:
            endpoint_type: Either 'general' or 'search'

        Returns:
            Wait time in seconds, or None if no wait needed
        """
        if endpoint_type not in self.state:
            return None

        limit_info = self.state[endpoint_type]
        current_time = time.time()

        if limit_info["remaining"] <= 0 and current_time < limit_info["reset"]:
            return int(limit_info["reset"] - current_time)

        return None
