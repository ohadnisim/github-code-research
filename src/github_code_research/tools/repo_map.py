"""Repository mapping tool with PageRank-based symbol ranking."""

from collections import defaultdict
from typing import Dict, List

from ..github.client import GitHubClient
from ..parsers.factory import ParserFactory
from ..parsers.pagerank import SymbolRanker
from ..security.secret_scanner import get_scanner
from ..utils.cache import FileCache
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RepositoryMapper:
    """Generate repository maps with ranked symbols."""

    def __init__(self, github_client: GitHubClient, cache: FileCache, cache_ttl: int = 86400):
        """
        Initialize repository mapper.

        Args:
            github_client: GitHub API client
            cache: Cache instance
            cache_ttl: Cache TTL in seconds (default: 24 hours)
        """
        self.github_client = github_client
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.secret_scanner = get_scanner()
        self.symbol_ranker = SymbolRanker()

    def generate_map(self, owner: str, repo: str, max_symbols: int = 50) -> Dict:
        """
        Generate repository map with top symbols.

        Args:
            owner: Repository owner
            repo: Repository name
            max_symbols: Maximum number of symbols to include

        Returns:
            Dict with repository map and metadata
        """
        # Get repo info for commit SHA
        repo_info = self.github_client.get_repo_info(owner, repo)
        default_branch = repo_info.get("default_branch", "main")

        # Try to get the latest commit SHA
        try:
            # Get the branch info to get the latest commit
            branch_endpoint = f"/repos/{owner}/{repo}/branches/{default_branch}"
            branch_info = self.github_client.get(branch_endpoint)
            commit_sha = branch_info.get("commit", {}).get("sha", "HEAD")
        except Exception:
            commit_sha = "HEAD"

        # Check cache
        cache_key = f"{owner}_{repo}@{commit_sha}"
        cached = self.cache.get(cache_key, ttl=self.cache_ttl)
        if cached:
            logger.info(f"Repo map cache hit: {owner}/{repo}")
            return cached

        logger.info(f"Generating repo map for {owner}/{repo}")

        # Get repository tree
        try:
            tree = self.github_client.get_tree(owner, repo, commit_sha, recursive=True)
        except Exception as e:
            logger.error(f"Failed to get repo tree: {e}")
            raise Exception(f"Failed to get repository tree: {e}")

        # Filter to code files
        code_files = self._filter_code_files(tree)

        if not code_files:
            return {
                "repo": f"{owner}/{repo}",
                "files": 0,
                "symbols": [],
                "map": "No supported code files found in repository."
            }

        logger.info(f"Found {len(code_files)} code files")

        # Limit number of files to process (avoid timeout)
        if len(code_files) > 100:
            logger.warning(f"Limiting to 100 files (found {len(code_files)})")
            code_files = code_files[:100]

        # Parse files and extract symbols
        all_symbols = []
        all_imports = []
        all_calls = []

        for file_info in code_files:
            file_path = file_info["path"]

            try:
                # Get file content
                content = self.github_client.get_file_content(owner, repo, file_path)

                # Get parser
                parser = ParserFactory.get_parser(file_path=file_path)
                if not parser:
                    continue

                # Parse file
                parse_result = parser.parse(content, file_path)

                # Collect symbols
                for symbol in parse_result.symbols:
                    symbol.file_path = file_path
                    all_symbols.append(symbol)

                # Collect imports and calls
                all_imports.extend(parse_result.imports)
                all_calls.extend(parse_result.calls)

            except Exception as e:
                logger.debug(f"Failed to parse {file_path}: {e}")
                continue

        if not all_symbols:
            return {
                "repo": f"{owner}/{repo}",
                "files": len(code_files),
                "symbols": [],
                "map": "No symbols found in repository."
            }

        logger.info(f"Extracted {len(all_symbols)} symbols")

        # Rank symbols using PageRank
        symbol_scores = self.symbol_ranker.rank_symbols(all_symbols, all_imports, all_calls)

        # Sort symbols by score
        ranked_symbols = sorted(
            all_symbols,
            key=lambda s: symbol_scores.get(s.name, 0.0),
            reverse=True
        )

        # Take top N symbols
        top_symbols = ranked_symbols[:max_symbols]

        logger.info(f"Selected top {len(top_symbols)} symbols")

        # Format as map
        map_text = self._format_map(top_symbols, symbol_scores)

        result = {
            "repo": f"{owner}/{repo}",
            "files": len(code_files),
            "total_symbols": len(all_symbols),
            "displayed_symbols": len(top_symbols),
            "map": map_text
        }

        # Cache result
        self.cache.set(cache_key, result)

        return result

    def _filter_code_files(self, tree: List[Dict]) -> List[Dict]:
        """Filter tree to only code files."""
        code_files = []

        for item in tree:
            if item.get("type") != "blob":
                continue

            path = item.get("path", "")

            # Skip non-code files
            if any(skip in path for skip in [
                "node_modules/", "vendor/", ".git/", "__pycache__/",
                "dist/", "build/", ".egg-info/", "venv/", "env/",
                "test/", "tests/", "spec/", ".test.", ".spec.",
                ".min.", ".bundle.", ".map"
            ]):
                continue

            # Check if supported
            if ParserFactory.is_supported(file_path=path):
                code_files.append(item)

        return code_files

    def _format_map(self, symbols: List, scores: Dict[str, float]) -> str:
        """Format symbols as a compact repository map."""
        # Group symbols by file
        by_file = defaultdict(list)
        for symbol in symbols:
            by_file[symbol.file_path].append((symbol, scores.get(symbol.name, 0.0)))

        # Sort files by highest symbol score
        sorted_files = sorted(
            by_file.items(),
            key=lambda x: max(score for _, score in x[1]),
            reverse=True
        )

        lines = []
        lines.append("Repository Map (Top Symbols by Importance)")
        lines.append("=" * 60)

        for file_path, file_symbols in sorted_files:
            lines.append(f"\n{file_path}")

            # Sort symbols in file by score
            sorted_symbols = sorted(file_symbols, key=lambda x: x[1], reverse=True)

            for symbol, score in sorted_symbols:
                # Format: "  [score] signature"
                lines.append(f"  [{score:.2f}] {symbol.signature}")

        return "\n".join(lines)


async def get_repo_map_tool(
    arguments: Dict[str, str],
    github_client: GitHubClient,
    cache: FileCache,
    cache_ttl: int
) -> Dict:
    """
    MCP tool: Generate repository map with ranked symbols.

    Args:
        arguments: Tool arguments with 'owner', 'repo', optional 'max_symbols'
        github_client: GitHub client instance
        cache: Cache instance
        cache_ttl: Cache TTL

    Returns:
        Tool result with repository map
    """
    try:
        owner = arguments.get("owner")
        repo = arguments.get("repo")
        max_symbols = arguments.get("max_symbols", 50)

        if not owner or not repo:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'owner' and 'repo' are required parameters"
                    }
                ],
                "isError": True
            }

        # Validate max_symbols
        try:
            max_symbols = int(max_symbols)
            if max_symbols < 1:
                max_symbols = 50
        except (ValueError, TypeError):
            max_symbols = 50

        mapper = RepositoryMapper(github_client, cache, cache_ttl)
        result = mapper.generate_map(owner, repo, max_symbols)

        # Format output
        output_lines = [
            f"Repository: {result['repo']}",
            f"Files analyzed: {result['files']}",
            f"Total symbols: {result.get('total_symbols', 0)}",
            f"Displayed symbols: {result.get('displayed_symbols', 0)}",
            "",
            result['map']
        ]

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(output_lines)
                }
            ]
        }

    except Exception as e:
        logger.error(f"Repo map generation failed: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error generating repository map: {str(e)}"
                }
            ],
            "isError": True
        }
