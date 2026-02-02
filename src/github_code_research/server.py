"""Main MCP server for GitHub code research."""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config.settings import get_settings
from .github.auth import validate_token
from .github.client import GitHubClient
from .tools.check_license import check_license_tool
from .tools.extract_function import extract_function_tool
from .tools.repo_map import get_repo_map_tool
from .tools.search_patterns import search_patterns_tool
from .utils.cache import FileCache
from .utils.errors import GitHubCodeResearchError
from .utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize server
app = Server("github-code-research")

# Global state
_github_client = None
_cache = None
_settings = None


async def initialize_server():
    """Initialize server with configuration and GitHub client."""
    global _github_client, _cache, _settings

    try:
        # Load settings
        _settings = get_settings()
        logger.info("Configuration loaded successfully")

        # Setup logger with configured level
        logger.setLevel(_settings.log_level)

        # Validate GitHub token
        user_info = validate_token(_settings.github_token)
        logger.info(f"GitHub authentication successful: {user_info['login']}")

        # Initialize GitHub client
        _github_client = GitHubClient(_settings.github_token)
        logger.info("GitHub client initialized")

        # Initialize cache
        _cache = FileCache(_settings.cache_dir)
        logger.info(f"Cache initialized at {_settings.cache_dir}")

    except Exception as e:
        logger.error(f"Server initialization failed: {e}", exc_info=True)
        raise


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_patterns",
            description="Search for code patterns on GitHub. Returns matching code snippets with secrets redacted.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'fastapi route decorator')"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language filter (optional, e.g., 'python', 'javascript')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (1-30, default: 10)",
                        "minimum": 1,
                        "maximum": 30
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_repo_map",
            description="Generate a repository map showing the most important symbols (functions, classes) ranked by PageRank algorithm. Useful for understanding repository structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (GitHub username or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "max_symbols": {
                        "type": "integer",
                        "description": "Maximum number of symbols to include (default: 50)",
                        "minimum": 1
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        Tool(
            name="extract_function",
            description="Extract a specific function from a GitHub file with precise tree-sitter parsing. Returns the function code with context lines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_url": {
                        "type": "string",
                        "description": "GitHub file URL (e.g., 'https://github.com/owner/repo/blob/main/path/to/file.py')"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function to extract"
                    }
                },
                "required": ["file_url", "function_name"]
            }
        ),
        Tool(
            name="check_license",
            description="Check repository license and categorize as SAFE_TO_USE, VIRAL_LICENSE_WARNING, or REVIEW_REQUIRED.",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    global _github_client, _cache, _settings

    if not _github_client or not _cache or not _settings:
        await initialize_server()

    try:
        logger.info(f"Tool call: {name}")

        if name == "search_patterns":
            result = await search_patterns_tool(
                arguments,
                _github_client,
                _cache,
                _settings.cache_ttl_search,
                _settings.max_search_results
            )

        elif name == "get_repo_map":
            result = await get_repo_map_tool(
                arguments,
                _github_client,
                _cache,
                _settings.cache_ttl_repo_map
            )

        elif name == "extract_function":
            result = await extract_function_tool(
                arguments,
                _github_client
            )

        elif name == "check_license":
            result = await check_license_tool(
                arguments,
                _github_client,
                _cache,
                _settings.cache_ttl_license
            )

        else:
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {name}"
                    }
                ],
                "isError": True
            }

        # Convert to MCP response format
        return result.get("content", [])

    except GitHubCodeResearchError as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    except Exception as e:
        logger.error(f"Unexpected error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Unexpected error: {str(e)}")]


async def main():
    """Run the MCP server."""
    try:
        # Initialize server
        await initialize_server()

        # Run stdio server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("GitHub Code Research MCP Server started")
            await app.run(read_stream, write_stream, app.create_initialization_options())

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
