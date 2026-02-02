"""
Tool 7: Find Simpler Alternative

Finds simpler implementations of the same feature.
Helps AI agents avoid overengineering by showing minimal working examples.
"""

from typing import Dict, List, Any
import logging
from ..tools.search_patterns import CodeSearcher

logger = logging.getLogger(__name__)


class SimplerAlternativeFinder:
    """Find simpler implementations of features"""

    def __init__(self, github_client, cache, secret_scanner, cache_ttl: int = 3600):
        self.github_client = github_client
        self.cache = cache
        self.secret_scanner = secret_scanner
        self.cache_ttl = cache_ttl
        self.code_searcher = CodeSearcher(github_client, cache, cache_ttl)

    def find_simpler(
        self,
        feature: str,
        language: str = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Find simpler implementations of a feature.

        Args:
            feature: Feature to find simpler version of
            language: Programming language
            max_results: Maximum results to return

        Returns:
            Dict with simpler implementations ranked by simplicity
        """
        try:
            # Build cache key
            cache_key = f"simpler_{feature}_{language or 'any'}"
            cached = self.cache.get(cache_key, self.cache_ttl)
            if cached:
                logger.info(f"Cache hit for simpler alternative: {feature}")
                return cached

            logger.info(f"Finding simpler alternatives for: {feature}")

            # Search for "simple", "minimal", "basic" implementations
            simple_queries = [
                f"{feature} simple",
                f"{feature} minimal",
                f"{feature} basic example"
            ]

            all_results = []
            for query in simple_queries:
                results = self.code_searcher.search(
                    query=query,
                    language=language,
                    max_results=max_results
                )
                all_results.extend(results)

            # Deduplicate by repo/file
            seen = set()
            unique_results = []
            for result in all_results:
                key = f"{result['repo']}:{result['path']}"
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)

            # Score by simplicity
            scored_results = []
            for result in unique_results:
                simplicity_score = self._calculate_simplicity(result)
                result['simplicity_score'] = simplicity_score
                scored_results.append(result)

            # Sort by simplicity (higher is simpler)
            scored_results.sort(key=lambda x: x['simplicity_score'], reverse=True)

            guide = {
                "feature": feature,
                "language": language,
                "total_found": len(scored_results),
                "alternatives": scored_results[:max_results]
            }

            # Cache result
            self.cache.set(cache_key, guide)

            return guide

        except Exception as e:
            logger.error(f"Error finding simpler alternatives: {e}")
            return {
                "feature": feature,
                "language": language,
                "total_found": 0,
                "error": str(e),
                "alternatives": []
            }

    def _calculate_simplicity(self, result: Dict) -> float:
        """
        Calculate simplicity score for code.
        Higher score = simpler code.
        """
        content = result.get("content", "")
        lines = content.split("\n")

        score = 100.0  # Start at 100

        # Shorter code is simpler
        line_count = len([l for l in lines if l.strip()])
        if line_count < 50:
            score += 20
        elif line_count < 100:
            score += 10
        elif line_count > 200:
            score -= 20

        # Fewer imports/dependencies = simpler
        import_count = len([l for l in lines if l.strip().startswith(("import ", "from ", "require("))])
        if import_count < 5:
            score += 15
        elif import_count > 15:
            score -= 15

        # Keywords that suggest simplicity
        content_lower = content.lower()
        simple_keywords = ["simple", "minimal", "basic", "easy", "quick"]
        for keyword in simple_keywords:
            if keyword in content_lower:
                score += 10

        # Keywords that suggest complexity
        complex_keywords = ["advanced", "complex", "enterprise", "production"]
        for keyword in complex_keywords:
            if keyword in content_lower:
                score -= 10

        # Presence of comments/docs = better (simpler to understand)
        comment_lines = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "*", '"""', "'''"))])
        if comment_lines > line_count * 0.2:  # >20% comments
            score += 10

        # Check for test/example indicators
        if "example" in result.get("file", "").lower():
            score += 15

        if "tutorial" in result.get("file", "").lower():
            score += 15

        # Fewer classes/functions = simpler
        class_count = content.count("class ") + content.count("function ") + content.count("def ")
        if class_count < 3:
            score += 10
        elif class_count > 10:
            score -= 10

        return max(0, score)  # Don't go negative


async def find_simpler_alternative_tool(
    arguments: Dict[str, Any],
    github_client,
    cache,
    secret_scanner,
    cache_ttl: int
) -> Dict:
    """
    MCP tool: Find simpler alternatives

    Arguments:
        feature: Feature to find simpler version of (required)
        language: Programming language (optional)
        max_results: Maximum results (default: 5)
    """
    feature = arguments.get("feature")
    language = arguments.get("language")
    max_results = arguments.get("max_results", 5)

    if not feature:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Please provide a feature to find simpler alternatives for"
            }],
            "isError": True
        }

    finder = SimplerAlternativeFinder(github_client, cache, secret_scanner, cache_ttl)
    result = finder.find_simpler(feature, language, max_results)

    # Format output
    output = []
    output.append(f"# Simpler Alternatives for: {result['feature']}\n\n")

    if result.get('language'):
        output.append(f"Language: {result['language']}\n")

    output.append(f"Found {result['total_found']} simpler implementations\n")
    output.append("Sorted by simplicity (simplest first)\n\n")
    output.append("=" * 60 + "\n\n")

    for i, alt in enumerate(result.get('alternatives', []), 1):
        output.append(f"## Alternative {i}: {alt['repo']}\n")
        output.append(f"**Simplicity Score: {alt['simplicity_score']:.0f}/100**\n")
        output.append(f"File: {alt['file']}\n")
        output.append(f"URL: {alt['url']}\n")
        output.append(f"Stars: {alt.get('stars', 0)}\n\n")

        # Show why it's simple
        content = alt.get('content', '')
        line_count = len([l for l in content.split("\n") if l.strip()])
        output.append(f"**Why this is simpler:**\n")
        output.append(f"  - Only {line_count} lines of code\n")

        if "simple" in content.lower() or "minimal" in content.lower():
            output.append(f"  - Described as simple/minimal\n")

        if "example" in alt['file'].lower():
            output.append(f"  - From examples/tutorials\n")

        output.append("\n**Code Preview:**\n")
        output.append("```\n")
        preview = content[:800]  # First 800 chars
        output.append(preview)
        if len(content) > 800:
            output.append("\n... (truncated)")
        output.append("\n```\n\n")
        output.append("-" * 60 + "\n\n")

    if not result.get('alternatives'):
        output.append("No simpler alternatives found. Try broadening your search.\n")

    return {
        "content": [{
            "type": "text",
            "text": "".join(output)
        }]
    }
