"""GitHub authentication utilities."""

import requests

from ..utils.errors import AuthenticationError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def validate_token(token: str) -> dict:
    """
    Validate GitHub token and get authenticated user info.

    Args:
        token: GitHub personal access token

    Returns:
        User info dict with 'login', 'id', 'type' fields

    Raises:
        AuthenticationError: If token is invalid
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)

        if response.status_code == 401:
            raise AuthenticationError("Invalid GitHub token")

        if response.status_code == 403:
            raise AuthenticationError("GitHub token does not have sufficient permissions")

        response.raise_for_status()
        user_data = response.json()

        logger.info(f"Authenticated as GitHub user: {user_data.get('login')}")

        return {
            "login": user_data.get("login"),
            "id": user_data.get("id"),
            "type": user_data.get("type"),
        }

    except requests.RequestException as e:
        raise AuthenticationError(f"Failed to validate GitHub token: {e}")
