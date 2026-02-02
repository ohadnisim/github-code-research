"""CLI entry point for GitHub Code Research MCP Server."""

import asyncio
import sys

from .server import main


def cli():
    """CLI entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped.", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()
