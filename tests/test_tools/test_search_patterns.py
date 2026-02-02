"""Tests for search_patterns tool."""

import pytest

from github_code_research.tools.search_patterns import CodeSearcher
from github_code_research.utils.cache import FileCache


class TestCodeSearcher:
    """Test code searcher."""

    def test_initialization(self, mock_github_token, temp_cache_dir):
        """Test searcher initialization."""
        from github_code_research.github.client import GitHubClient

        client = GitHubClient(mock_github_token)
        cache = FileCache(temp_cache_dir)
        searcher = CodeSearcher(client, cache)

        assert searcher.github_client is not None
        assert searcher.cache is not None
        assert searcher.secret_scanner is not None

    # Integration tests would require mocking GitHub API or using real API
    # with proper test fixtures
