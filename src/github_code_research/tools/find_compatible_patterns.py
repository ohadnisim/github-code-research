"""
Tool 5: Find Compatible Patterns

Searches for multiple patterns that work together in the same codebase.
This helps AI agents find code where multiple features are integrated.
"""

from typing import Dict, List, Any
import logging
from ..utils.errors import GitHubCodeResearchError

logger = logging.getLogger(__name__)


class CompatiblePatternFinder:
    """Find code patterns that work together"""

    def __init__(self, github_client, cache, secret_scanner, cache_ttl: int = 3600):
        self.github_client = github_client
        self.cache = cache
        self.secret_scanner = secret_scanner
        self.cache_ttl = cache_ttl

    def find_compatible(
        self,
        patterns: List[str],
        language: str = None,
        min_stars: int = 10,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Find repositories that implement multiple patterns together.

        Args:
            patterns: List of patterns to find (e.g., ["auth", "database", "caching"])
            language: Programming language filter
            min_stars: Minimum stars for quality filter
            max_results: Maximum repos to return

        Returns:
            Dict with repos that implement all patterns together
        """
        try:
            # Build cache key
            cache_key = f"compatible_{'_'.join(sorted(patterns))}_{language or 'any'}_{min_stars}"
            cached = self.cache.get(cache_key, self.cache_ttl)
            if cached:
                logger.info(f"Cache hit for compatible patterns: {patterns}")
                return cached

            logger.info(f"Finding repos with patterns: {patterns}")

            # Build search query combining all patterns
            query_parts = patterns.copy()
            if language:
                query_parts.append(f"language:{language}")
            query_parts.append(f"stars:>={min_stars}")

            # Search for repos with all patterns
            query = " ".join(query_parts)

            # Use code search to find files mentioning all patterns
            search_results = self.github_client.search_code(
                query=query,
                max_results=max_results * 3  # Get more to filter
            )

            # Group by repository
            repos_with_patterns = {}
            for result in search_results:
                repo_full_name = result.get("repository", {}).get("full_name", "")
                if not repo_full_name:
                    continue

                if repo_full_name not in repos_with_patterns:
                    repos_with_patterns[repo_full_name] = {
                        "repo": repo_full_name,
                        "stars": result.get("repository", {}).get("stargazers_count", 0),
                        "description": result.get("repository", {}).get("description", ""),
                        "url": result.get("repository", {}).get("html_url", ""),
                        "files": [],
                        "patterns_found": set()
                    }

                # Add file and check which patterns it contains
                file_path = result.get("path", "")
                file_url = result.get("html_url", "")
                repos_with_patterns[repo_full_name]["files"].append({
                    "path": file_path,
                    "url": file_url
                })

                # Check which patterns are in the file content
                try:
                    # Get file content to verify patterns
                    content = self._get_file_content(result)
                    content_lower = content.lower()

                    for pattern in patterns:
                        if pattern.lower() in content_lower:
                            repos_with_patterns[repo_full_name]["patterns_found"].add(pattern)
                except Exception as e:
                    logger.warning(f"Error checking patterns in {file_path}: {e}")

            # Filter repos that have ALL patterns
            compatible_repos = []
            for repo_data in repos_with_patterns.values():
                patterns_found = repo_data["patterns_found"]
                if len(patterns_found) >= len(patterns) * 0.7:  # At least 70% of patterns
                    repo_data["patterns_found"] = list(patterns_found)
                    repo_data["compatibility_score"] = len(patterns_found) / len(patterns)
                    compatible_repos.append(repo_data)

            # Sort by stars and compatibility
            compatible_repos.sort(
                key=lambda x: (x["compatibility_score"], x["stars"]),
                reverse=True
            )

            result = {
                "patterns_searched": patterns,
                "language": language,
                "total_found": len(compatible_repos),
                "repositories": compatible_repos[:max_results]
            }

            # Cache result
            self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error finding compatible patterns: {e}")
            raise GitHubCodeResearchError(f"Failed to find compatible patterns: {e}")

    def _get_file_content(self, search_result: Dict) -> str:
        """Get file content from search result"""
        try:
            repo_full_name = search_result.get("repository", {}).get("full_name", "")
            file_path = search_result.get("path", "")

            if not repo_full_name or not file_path:
                return ""

            owner, repo = repo_full_name.split("/")
            content = self.github_client.get_file_content(owner, repo, file_path)

            # Redact secrets
            content, _ = self.secret_scanner.redact(content)

            return content
        except Exception as e:
            logger.warning(f"Error getting file content: {e}")
            return ""


async def find_compatible_patterns_tool(
    arguments: Dict[str, Any],
    github_client,
    cache,
    secret_scanner,
    cache_ttl: int
) -> Dict:
    """
    MCP tool: Find patterns that work together

    Arguments:
        patterns: List of patterns to find together (e.g., ["auth", "database", "redis"])
        language: Optional language filter
        min_stars: Minimum stars (default: 10)
        max_results: Maximum results (default: 5)
    """
    patterns = arguments.get("patterns", [])
    language = arguments.get("language")
    min_stars = arguments.get("min_stars", 10)
    max_results = arguments.get("max_results", 5)

    if not patterns or len(patterns) < 2:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Please provide at least 2 patterns to find together"
            }],
            "isError": True
        }

    finder = CompatiblePatternFinder(github_client, cache, secret_scanner, cache_ttl)
    result = finder.find_compatible(patterns, language, min_stars, max_results)

    # Format output
    output = []
    output.append(f"Found {result['total_found']} repositories with compatible patterns: {', '.join(result['patterns_searched'])}\n")

    if language:
        output.append(f"Language: {language}\n")

    output.append("=" * 60 + "\n")

    for i, repo in enumerate(result['repositories'], 1):
        output.append(f"\nRepository {i}: {repo['repo']}\n")
        output.append(f"Stars: {repo['stars']}\n")
        output.append(f"Compatibility Score: {repo['compatibility_score']:.0%}\n")
        output.append(f"Patterns Found: {', '.join(repo['patterns_found'])}\n")
        output.append(f"URL: {repo['url']}\n")

        if repo['description']:
            output.append(f"Description: {repo['description']}\n")

        output.append(f"\nKey Files ({len(repo['files'])} total):\n")
        for file_info in repo['files'][:5]:  # Show first 5 files
            output.append(f"  - {file_info['path']}\n")
            output.append(f"    {file_info['url']}\n")

        output.append("-" * 60 + "\n")

    return {
        "content": [{
            "type": "text",
            "text": "".join(output)
        }]
    }
