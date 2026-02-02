"""
Tool 9: Find Usage Examples

Finds real-world usage examples of functions, APIs, or libraries.
Shows AI agents HOW to actually use code, not just what it is.
"""

from typing import Dict, List, Any
import logging
from ..tools.search_patterns import CodeSearcher

logger = logging.getLogger(__name__)


class UsageExampleFinder:
    """Find real-world usage examples"""

    def __init__(self, github_client, cache, secret_scanner, cache_ttl: int = 3600):
        self.github_client = github_client
        self.cache = cache
        self.secret_scanner = secret_scanner
        self.cache_ttl = cache_ttl
        self.code_searcher = CodeSearcher(github_client, cache, cache_ttl)

    def find_usage(
        self,
        function_or_library: str,
        language: str = None,
        context: str = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Find usage examples of a function or library.

        Args:
            function_or_library: Function name or library to find usage of
            language: Programming language
            context: Additional context (e.g., "authentication", "database")
            max_results: Maximum results to return

        Returns:
            Dict with usage examples from real code
        """
        try:
            # Build cache key
            cache_key = f"usage_{function_or_library}_{language or 'any'}_{context or 'none'}"
            cached = self.cache.get(cache_key, self.cache_ttl)
            if cached:
                logger.info(f"Cache hit for usage examples: {function_or_library}")
                return cached

            logger.info(f"Finding usage examples for: {function_or_library}")

            # Build search queries
            queries = [
                function_or_library,
                f"{function_or_library} example",
            ]

            if context:
                queries.append(f"{function_or_library} {context}")

            # Search for usage examples
            all_examples = []
            for query in queries:
                results = self.code_searcher.search(
                    query=query,
                    language=language,
                    max_results=max_results
                )
                all_examples.extend(results)

            # Deduplicate
            seen = set()
            unique_examples = []
            for example in all_examples:
                key = f"{example['repo']}:{example['path']}"
                if key not in seen:
                    seen.add(key)
                    unique_examples.append(example)

            # Analyze and score examples
            scored_examples = []
            for example in unique_examples:
                usage_score = self._calculate_usage_score(example, function_or_library)
                example['usage_score'] = usage_score
                example['usage_patterns'] = self._extract_usage_patterns(example, function_or_library)
                scored_examples.append(example)

            # Sort by usage score
            scored_examples.sort(key=lambda x: x['usage_score'], reverse=True)

            result = {
                "function_or_library": function_or_library,
                "language": language,
                "context": context,
                "total_found": len(scored_examples),
                "examples": scored_examples[:max_results]
            }

            # Cache result
            self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error finding usage examples: {e}")
            return {
                "function_or_library": function_or_library,
                "language": language,
                "context": context,
                "total_found": 0,
                "error": str(e),
                "examples": []
            }

    def _calculate_usage_score(self, example: Dict, target: str) -> float:
        """Calculate how good this usage example is"""
        score = 50.0  # Base score

        content = example.get('content', '')
        content_lower = content.lower()
        target_lower = target.lower()

        # Count occurrences of target
        occurrence_count = content_lower.count(target_lower)
        score += min(occurrence_count * 5, 20)  # Up to +20

        # Check for example/tutorial indicators
        file_path = example.get('file', '').lower()
        if any(keyword in file_path for keyword in ['example', 'tutorial', 'demo', 'sample']):
            score += 15

        # Check for documentation/comments
        lines = content.split('\n')
        comment_ratio = len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))]) / max(len(lines), 1)
        score += comment_ratio * 20  # Up to +20

        # Check for common usage patterns
        if 'import ' in content or 'require(' in content:
            score += 5

        if 'def ' in content or 'function ' in content:
            score += 5

        # Check for test indicators (tests show real usage)
        if any(keyword in file_path for keyword in ['test', 'spec']):
            score += 10

        # Repository stars (popularity indicator)
        stars = example.get('stars', 0)
        if stars > 100:
            score += 10
        elif stars > 1000:
            score += 15

        return min(score, 100)  # Cap at 100

    def _extract_usage_patterns(self, example: Dict, target: str) -> List[str]:
        """Extract common usage patterns from the example"""
        patterns = []
        content = example.get('content', '')
        lines = content.split('\n')

        # Find lines that use the target
        target_lower = target.lower()
        usage_lines = []
        for i, line in enumerate(lines):
            if target_lower in line.lower():
                # Get context (line before and after)
                context_start = max(0, i - 1)
                context_end = min(len(lines), i + 2)
                context_lines = lines[context_start:context_end]
                usage_lines.extend(context_lines)

        # Analyze patterns
        usage_text = '\n'.join(usage_lines).lower()

        if 'import' in usage_text or 'from' in usage_text:
            patterns.append("Import statement")

        if '(' in usage_text and ')' in usage_text:
            patterns.append("Function call")

        if '=' in usage_text:
            patterns.append("Variable assignment")

        if 'async' in usage_text or 'await' in usage_text:
            patterns.append("Async usage")

        if 'try:' in usage_text or 'catch' in usage_text:
            patterns.append("With error handling")

        if 'test' in example.get('file', '').lower():
            patterns.append("Test example")

        return patterns


async def find_usage_examples_tool(
    arguments: Dict[str, Any],
    github_client,
    cache,
    secret_scanner,
    cache_ttl: int
) -> Dict:
    """
    MCP tool: Find usage examples

    Arguments:
        function_or_library: Function/library to find usage of (required)
        language: Programming language (optional)
        context: Additional context (optional)
        max_results: Maximum results (default: 5)
    """
    function_or_library = arguments.get("function_or_library")
    language = arguments.get("language")
    context = arguments.get("context")
    max_results = arguments.get("max_results", 5)

    if not function_or_library:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Please provide a function or library to find usage examples for"
            }],
            "isError": True
        }

    finder = UsageExampleFinder(github_client, cache, secret_scanner, cache_ttl)
    result = finder.find_usage(function_or_library, language, context, max_results)

    # Format output
    output = []
    output.append(f"# Usage Examples: {result['function_or_library']}\n\n")

    if result.get('language'):
        output.append(f"Language: {result['language']}\n")
    if result.get('context'):
        output.append(f"Context: {result['context']}\n")

    output.append(f"\nFound {result['total_found']} usage examples\n")
    output.append("Sorted by relevance (most relevant first)\n\n")
    output.append("=" * 60 + "\n\n")

    for i, example in enumerate(result.get('examples', []), 1):
        output.append(f"## Example {i}: {example['repo']}\n")
        output.append(f"**Usage Score: {example.get('usage_score', 0):.0f}/100**\n")
        output.append(f"File: {example['path']}\n")
        output.append(f"URL: {example['url']}\n")
        output.append(f"Stars: {example.get('stars', 0)}\n\n")

        # Show usage patterns
        patterns = example.get('usage_patterns', [])
        if patterns:
            output.append("**Usage Patterns:**\n")
            for pattern in patterns:
                output.append(f"  - {pattern}\n")
            output.append("\n")

        # Show code
        output.append("**Code:**\n")
        output.append("```\n")
        code_preview = example.get('content', '')[:1000]  # First 1000 chars
        output.append(code_preview)
        if len(example.get('content', '')) > 1000:
            output.append("\n... (truncated)")
        output.append("\n```\n\n")
        output.append("-" * 60 + "\n\n")

    if not result.get('examples'):
        output.append("No usage examples found. Try:\n")
        output.append("  - Checking the function/library name spelling\n")
        output.append("  - Using a more specific search term\n")
        output.append("  - Adding context to narrow the search\n")

    return {
        "content": [{
            "type": "text",
            "text": "".join(output)
        }]
    }
