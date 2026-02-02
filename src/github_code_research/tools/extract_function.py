"""Function extraction tool."""

import re
from typing import Dict, Optional

from ..github.client import GitHubClient
from ..parsers.factory import ParserFactory
from ..security.secret_scanner import get_scanner
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FunctionExtractor:
    """Extract specific functions from GitHub files."""

    def __init__(self, github_client: GitHubClient):
        """
        Initialize function extractor.

        Args:
            github_client: GitHub API client
        """
        self.github_client = github_client
        self.secret_scanner = get_scanner()

    def extract_function(self, file_url: str, function_name: str) -> Dict[str, str]:
        """
        Extract a specific function from a GitHub file.

        Args:
            file_url: GitHub file URL
            function_name: Name of function to extract

        Returns:
            Dict with function code, line numbers, and metadata
        """
        # Parse GitHub URL
        parsed = self._parse_github_url(file_url)
        if not parsed:
            raise ValueError(f"Invalid GitHub URL: {file_url}")

        owner, repo, file_path = parsed

        logger.info(f"Extracting function '{function_name}' from {owner}/{repo}/{file_path}")

        # Get file content
        try:
            content = self.github_client.get_file_content(owner, repo, file_path)
        except Exception as e:
            raise Exception(f"Failed to fetch file: {e}")

        # Get parser for file
        parser = ParserFactory.get_parser(file_path=file_path)

        if parser:
            # Use tree-sitter for precise extraction
            result = self._extract_with_parser(content, function_name, parser, file_path)
        else:
            # Fallback to regex-based extraction
            logger.warning(f"No parser for {file_path}, using regex fallback")
            result = self._extract_with_regex(content, function_name)

        if not result:
            raise Exception(f"Function '{function_name}' not found in {file_path}")

        # Redact secrets
        code, redaction_count = self.secret_scanner.redact(result["code"])
        result["code"] = code

        if redaction_count > 0:
            result["warning"] = f"Redacted {redaction_count} potential secret(s)"

        return result

    def _parse_github_url(self, url: str) -> Optional[tuple]:
        """Parse GitHub URL to extract owner, repo, and file path."""
        # Match: https://github.com/owner/repo/blob/branch/path/to/file.py
        pattern = r"github\.com/([^/]+)/([^/]+)/(?:blob|tree)/[^/]+/(.+)"
        match = re.search(pattern, url)

        if match:
            return match.group(1), match.group(2), match.group(3)

        # Match: github.com/owner/repo/path/to/file.py (raw format)
        pattern = r"github\.com/([^/]+)/([^/]+)/([^?#]+)"
        match = re.search(pattern, url)

        if match:
            return match.group(1), match.group(2), match.group(3)

        return None

    def _extract_with_parser(
        self,
        content: str,
        function_name: str,
        parser,
        file_path: str
    ) -> Optional[Dict[str, str]]:
        """Extract function using tree-sitter parser."""
        try:
            parse_result = parser.parse(content, file_path)

            # Find function in symbols
            target_symbol = None
            for symbol in parse_result.symbols:
                if symbol.name == function_name or symbol.name.endswith(f".{function_name}"):
                    target_symbol = symbol
                    break

            if not target_symbol:
                return None

            # Extract function with context
            lines = content.split("\n")
            start_line = max(0, target_symbol.start_line - 4)  # 3 lines before
            end_line = min(len(lines), target_symbol.end_line + 3)  # 3 lines after

            # Get code with line numbers
            code_lines = []
            for line_num in range(start_line, end_line):
                if line_num < len(lines):
                    code_lines.append(f"{line_num + 1:4d} | {lines[line_num]}")

            return {
                "code": "\n".join(code_lines),
                "start_line": target_symbol.start_line,
                "end_line": target_symbol.end_line,
                "signature": target_symbol.signature,
                "type": target_symbol.type,
                "context_lines": 3
            }

        except Exception as e:
            logger.error(f"Parser extraction failed: {e}")
            return None

    def _extract_with_regex(self, content: str, function_name: str) -> Optional[Dict[str, str]]:
        """Fallback: Extract function using regex patterns."""
        lines = content.split("\n")

        # Common patterns for function definitions
        patterns = [
            rf"^\s*(def|function|func|fn)\s+{re.escape(function_name)}\s*[\(\[]",  # Python, JS, Go
            rf"^\s*(public|private|protected)?\s*\w*\s*{re.escape(function_name)}\s*[\(\[]",  # Java, C++
            rf"^\s*const\s+{re.escape(function_name)}\s*=",  # JS const/arrow
            rf"^\s*let\s+{re.escape(function_name)}\s*=",  # JS let/arrow
        ]

        # Find function start
        start_line = None
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    start_line = i
                    break
            if start_line is not None:
                break

        if start_line is None:
            return None

        # Find function end (simple heuristic: find next function or end of indentation)
        indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        end_line = start_line + 1

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip():  # Non-empty line
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_level and not line.strip().startswith((")", "]", "}")):
                    # Found a line at same or less indentation (likely next function/block)
                    end_line = i
                    break
            end_line = i + 1

        # Add context
        context_start = max(0, start_line - 3)
        context_end = min(len(lines), end_line + 3)

        # Build code with line numbers
        code_lines = []
        for line_num in range(context_start, context_end):
            code_lines.append(f"{line_num + 1:4d} | {lines[line_num]}")

        return {
            "code": "\n".join(code_lines),
            "start_line": start_line + 1,
            "end_line": end_line,
            "signature": lines[start_line].strip(),
            "type": "function",
            "context_lines": 3
        }


async def extract_function_tool(
    arguments: Dict[str, str],
    github_client: GitHubClient
) -> Dict:
    """
    MCP tool: Extract a specific function from a GitHub file.

    Args:
        arguments: Tool arguments with 'file_url' and 'function_name'
        github_client: GitHub client instance

    Returns:
        Tool result with function code
    """
    try:
        file_url = arguments.get("file_url")
        function_name = arguments.get("function_name")

        if not file_url or not function_name:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'file_url' and 'function_name' are required parameters"
                    }
                ],
                "isError": True
            }

        extractor = FunctionExtractor(github_client)
        result = extractor.extract_function(file_url, function_name)

        # Format output
        output_lines = [
            f"Function: {function_name}",
            f"Type: {result['type']}",
            f"Lines: {result['start_line']}-{result['end_line']}",
            f"Signature: {result['signature']}",
        ]

        if result.get("warning"):
            output_lines.append(f"\nWarning: {result['warning']}")

        output_lines.append(f"\nCode (with {result['context_lines']} lines context):")
        output_lines.append("=" * 60)
        output_lines.append(result["code"])

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(output_lines)
                }
            ]
        }

    except Exception as e:
        logger.error(f"Function extraction failed: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error extracting function: {str(e)}"
                }
            ],
            "isError": True
        }
