"""GitHub REST API client with rate limiting."""

import base64
import time
from typing import Any, Dict, List, Optional

import requests

from ..utils.errors import AuthenticationError, NotFoundError, RateLimitError
from ..utils.logger import setup_logger
from .rate_limiter import RateLimiter

logger = setup_logger(__name__)


class GitHubClient:
    """GitHub REST API client with automatic rate limiting."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def _make_request(
        self,
        method: str,
        url: str,
        endpoint_type: str = "general",
        max_retries: int = 3,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting and retries.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            endpoint_type: 'general' or 'search'
            max_retries: Maximum number of retries
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            RateLimitError: If rate limit exceeded
            AuthenticationError: If authentication fails
            NotFoundError: If resource not found
        """
        # Check rate limit before request
        self.rate_limiter.check_limit(endpoint_type)

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=30,
                    **kwargs
                )

                # Update rate limit from headers
                self.rate_limiter.update_from_headers(response.headers, endpoint_type)

                # Handle rate limit responses
                if response.status_code == 403 and "rate limit" in response.text.lower():
                    reset_time = int(response.headers.get("x-ratelimit-reset", 0))
                    wait_time = max(0, reset_time - int(time.time()))
                    raise RateLimitError(
                        f"Rate limit exceeded. Reset in {wait_time} seconds.",
                        reset_time=reset_time
                    )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", 60))
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited, waiting {retry_after}s before retry")
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")

                # Handle authentication errors
                if response.status_code == 401:
                    raise AuthenticationError("Invalid or expired GitHub token")

                # Handle not found
                if response.status_code == 404:
                    raise NotFoundError(url)

                # Raise for other HTTP errors
                response.raise_for_status()

                return response

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise

        raise Exception("Max retries exceeded")

    def get(self, endpoint: str, endpoint_type: str = "general", **params) -> Dict[str, Any]:
        """
        Make GET request to GitHub API.

        Args:
            endpoint: API endpoint (e.g., '/repos/{owner}/{repo}')
            endpoint_type: 'general' or 'search'
            **params: Query parameters

        Returns:
            JSON response as dict
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = self._make_request("GET", url, endpoint_type, params=params)
        return response.json()

    def get_raw(self, url: str) -> str:
        """
        Get raw content from URL (for file contents).

        Args:
            url: Full URL to fetch

        Returns:
            Raw content as string
        """
        response = self._make_request("GET", url, endpoint_type="general")
        return response.text

    def get_tree(self, owner: str, repo: str, tree_sha: str = "HEAD", recursive: bool = True) -> List[Dict]:
        """
        Get repository tree (list of files).

        Args:
            owner: Repository owner
            repo: Repository name
            tree_sha: Tree SHA or branch name
            recursive: Whether to get tree recursively

        Returns:
            List of file/tree objects
        """
        endpoint = f"/repos/{owner}/{repo}/git/trees/{tree_sha}"
        params = {"recursive": "1"} if recursive else {}

        try:
            data = self.get(endpoint, **params)
            return data.get("tree", [])
        except NotFoundError:
            # If HEAD doesn't work, try main branch
            if tree_sha == "HEAD":
                logger.info("HEAD not found, trying main branch")
                return self.get_tree(owner, repo, "main", recursive)
            raise

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = None) -> str:
        """
        Get content of a file from repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            ref: Branch/tag/commit (optional)

        Returns:
            File content as string
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if ref:
            params["ref"] = ref

        try:
            data = self.get(endpoint, **params)

            # Decode base64 content
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            else:
                # Fallback to download_url
                download_url = data.get("download_url")
                if download_url:
                    return self.get_raw(download_url)

            raise Exception("Could not decode file content")

        except Exception as e:
            logger.error(f"Failed to get file content for {owner}/{repo}/{path}: {e}")
            raise

    def search_code(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search code on GitHub.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        endpoint = "/search/code"
        params = {
            "q": query,
            "per_page": min(max_results, 100),
        }

        try:
            data = self.get(endpoint, endpoint_type="search", **params)
            items = data.get("items", [])
            return items[:max_results]

        except Exception as e:
            logger.error(f"Code search failed: {e}")
            raise

    def get_license(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get repository license information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            License info dict or None if not found
        """
        endpoint = f"/repos/{owner}/{repo}/license"

        try:
            return self.get(endpoint)
        except NotFoundError:
            logger.debug(f"No license found for {owner}/{repo}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get license for {owner}/{repo}: {e}")
            return None

    def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository info dict
        """
        endpoint = f"/repos/{owner}/{repo}"
        return self.get(endpoint)
