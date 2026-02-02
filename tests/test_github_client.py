"""Tests for GitHub client."""

import os

import pytest

from github_code_research.github.client import GitHubClient
from github_code_research.utils.errors import NotFoundError


class TestGitHubClient:
    """Test GitHub client functionality."""

    def test_client_initialization(self, mock_github_token):
        """Test client can be initialized."""
        client = GitHubClient(mock_github_token)
        assert client.token == mock_github_token
        assert client.BASE_URL == "https://api.github.com"

    def test_rate_limiter_initialization(self, mock_github_token):
        """Test rate limiter is initialized."""
        client = GitHubClient(mock_github_token)
        assert client.rate_limiter is not None
        assert hasattr(client.rate_limiter, "check_limit")

    # Note: Integration tests requiring real GitHub API calls should be marked
    # and only run when a real token is available

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("GITHUB_TOKEN"),
        reason="Requires GITHUB_TOKEN environment variable"
    )
    def test_get_repo_info_real(self):
        """Integration test: Get real repo info."""
        token = os.environ.get("GITHUB_TOKEN")
        client = GitHubClient(token)

        # Test with a known public repo
        info = client.get_repo_info("octocat", "Hello-World")
        assert info["name"] == "Hello-World"
        assert info["owner"]["login"] == "octocat"
