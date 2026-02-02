"""Code search patterns tool."""

from typing import Dict, List

from ..github.client import GitHubClient
from ..security.secret_scanner import get_scanner
from ..utils.cache import FileCache
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CodeSearcher:
    """Search for code patterns on GitHub."""

    def __init__(self, github_client: GitHubClient, cache: FileCache, cache_ttl: int = 3600):
        """
        Initialize code searcher.

        Args:
            github_client: GitHub API client
            cache: Cache instance
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.github_client = github_client
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.secret_scanner = get_scanner()

    def search(
        self,
        query: str,
        language: str = None,
        max_results: int = 10
    ) -> List[Dict[str, str]]:
        """
        Search for code patterns.

        Args:
            query: Search query
            language: Programming language filter (optional)
            max_results: Maximum number of results

        Returns:
            List of search results with repo, path, url, score, and content
        """
        # Build cache key
        cache_key = f"search_{query}_{language or 'all'}_{max_results}"

        # Check cache
        cached = self.cache.get(cache_key, ttl=self.cache_ttl)
        if cached:
            logger.debug(f"Search cache hit: {query}")
            return cached

        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"

        logger.info(f"Searching GitHub: {search_query}")

        try:
            # Perform search
            items = self.github_client.search_code(search_query, max_results=max_results)

            results = []
            for item in items:
                result = self._process_search_result(item)
                if result:
                    results.append(result)

            # Cache results
            self.cache.set(cache_key, results)

            logger.info(f"Found {len(results)} search results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise

    def _process_search_result(self, item: Dict) -> Dict[str, str]:
        """Process a single search result item."""
        try:
            repo = item.get("repository", {})
            owner = repo.get("owner", {}).get("login", "")
            repo_name = repo.get("name", "")
            file_path = item.get("path", "")
            html_url = item.get("html_url", "")
            score = item.get("score", 0.0)

            # Get file content
            try:
                content = self.github_client.get_file_content(owner, repo_name, file_path)

                # Redact secrets
                content, redaction_count = self.secret_scanner.redact(content)

                # Limit content length
                if len(content) > 2000:
                    content = content[:2000] + "\n... (truncated)"

            except Exception as e:
                logger.warning(f"Failed to fetch content for {owner}/{repo_name}/{file_path}: {e}")
                content = "[Content unavailable]"

            return {
                "repo": f"{owner}/{repo_name}",
                "path": file_path,
                "url": html_url,
                "score": score,
                "content": content
            }

        except Exception as e:
            logger.warning(f"Failed to process search result: {e}")
            return None


async def search_patterns_tool(
    arguments: Dict[str, str],
    github_client: GitHubClient,
    cache: FileCache,
    cache_ttl: int,
    max_results: int
) -> Dict:
    """
    MCP tool: Search for code patterns on GitHub.

    Args:
        arguments: Tool arguments with 'query', optional 'language', 'max_results'
        github_client: GitHub client instance
        cache: Cache instance
        cache_ttl: Cache TTL
        max_results: Default max results

    Returns:
        Tool result with search results
    """
    try:
        query = arguments.get("query")
        language = arguments.get("language")
        result_limit = arguments.get("max_results", max_results)

        if not query:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'query' parameter is required"
                    }
                ],
                "isError": True
            }

        # Validate max_results
        try:
            result_limit = int(result_limit)
            if result_limit < 1 or result_limit > 30:
                result_limit = min(max(result_limit, 1), 30)
        except (ValueError, TypeError):
            result_limit = max_results

        searcher = CodeSearcher(github_client, cache, cache_ttl)
        results = searcher.search(query, language, result_limit)

        if not results:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"No results found for query: {query}"
                    }
                ]
            }

        # Format output
        output_lines = [f"Found {len(results)} results for: {query}\n"]

        for i, result in enumerate(results, 1):
            output_lines.append(f"\n{'='*60}")
            output_lines.append(f"Result {i}: {result['repo']}")
            output_lines.append(f"File: {result['path']}")
            output_lines.append(f"URL: {result['url']}")
            output_lines.append(f"Score: {result['score']:.2f}")
            output_lines.append(f"\nContent:\n{'-'*60}")
            output_lines.append(result['content'])

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(output_lines)
                }
            ]
        }

    except Exception as e:
        logger.error(f"Search patterns failed: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error searching code: {str(e)}"
                }
            ],
            "isError": True
        }
