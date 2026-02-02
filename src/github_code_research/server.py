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
from .tools.find_compatible_patterns import find_compatible_patterns_tool
from .tools.get_implementation_guide import get_implementation_guide_tool
from .tools.find_simpler_alternative import find_simpler_alternative_tool
from .tools.validate_code_snippet import validate_code_snippet_tool
from .tools.find_usage_examples import find_usage_examples_tool
from .utils.cache import FileCache
from .utils.errors import GitHubCodeResearchError
from .utils.logger import setup_logger
from .security.secret_scanner import SecretScanner

logger = setup_logger(__name__)

# Initialize server
app = Server("github-code-research")

# Global state
_github_client = None
_cache = None
_settings = None
_secret_scanner = None


async def initialize_server():
    """Initialize server with configuration and GitHub client."""
    global _github_client, _cache, _settings, _secret_scanner

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

        # Initialize secret scanner
        _secret_scanner = SecretScanner()
        logger.info("Secret scanner initialized")

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
        Tool(
            name="find_compatible_patterns",
            description="Find code patterns that work together in the same codebase. Perfect for AI agents building features that need multiple integrations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of patterns to find together (e.g., ['auth', 'database', 'redis'])"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language filter (optional)"
                    },
                    "min_stars": {
                        "type": "integer",
                        "description": "Minimum repository stars (default: 10)",
                        "minimum": 0
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default: 5)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["patterns"]
            }
        ),
        Tool(
            name="get_implementation_guide",
            description="Generate step-by-step implementation guide based on working code from GitHub. Shows AI agents HOW to implement a feature with real examples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature": {
                        "type": "string",
                        "description": "Feature to implement (e.g., 'user authentication', 'file upload')"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (optional)"
                    },
                    "framework": {
                        "type": "string",
                        "description": "Framework name (optional, e.g., 'fastapi', 'express')"
                    },
                    "max_examples": {
                        "type": "integer",
                        "description": "Number of examples to include (default: 3)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["feature"]
            }
        ),
        Tool(
            name="find_simpler_alternative",
            description="Find simpler implementations of the same feature. Helps AI agents avoid overengineering by showing minimal working examples.",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature": {
                        "type": "string",
                        "description": "Feature to find simpler version of"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (optional)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default: 5)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["feature"]
            }
        ),
        Tool(
            name="validate_code_snippet",
            description="Validate code snippets before using them. Checks for security issues, deprecated APIs, and code quality. Essential for AI agents to verify code quality.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code snippet to validate"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (optional)"
                    },
                    "target_version": {
                        "type": "string",
                        "description": "Target language/framework version (optional)"
                    },
                    "check_secrets": {
                        "type": "boolean",
                        "description": "Check for exposed secrets (default: true)"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="find_usage_examples",
            description="Find real-world usage examples of functions, APIs, or libraries. Shows AI agents HOW to actually use code, not just what it is.",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_or_library": {
                        "type": "string",
                        "description": "Function name or library to find usage of"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (optional)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context (optional, e.g., 'authentication', 'database')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results (default: 5)",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["function_or_library"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    global _github_client, _cache, _settings, _secret_scanner

    if not _github_client or not _cache or not _settings or not _secret_scanner:
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

        elif name == "find_compatible_patterns":
            result = await find_compatible_patterns_tool(
                arguments,
                _github_client,
                _cache,
                _secret_scanner,
                _settings.cache_ttl_search
            )

        elif name == "get_implementation_guide":
            result = await get_implementation_guide_tool(
                arguments,
                _github_client,
                _cache,
                _secret_scanner,
                _settings.cache_ttl_search
            )

        elif name == "find_simpler_alternative":
            result = await find_simpler_alternative_tool(
                arguments,
                _github_client,
                _cache,
                _secret_scanner,
                _settings.cache_ttl_search
            )

        elif name == "validate_code_snippet":
            result = await validate_code_snippet_tool(
                arguments,
                _github_client,
                _cache,
                _secret_scanner,
                _settings.cache_ttl_search
            )

        elif name == "find_usage_examples":
            result = await find_usage_examples_tool(
                arguments,
                _github_client,
                _cache,
                _secret_scanner,
                _settings.cache_ttl_search
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
