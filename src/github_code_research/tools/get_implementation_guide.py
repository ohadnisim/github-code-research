"""
Tool 6: Get Implementation Guide

Generates step-by-step implementation guides based on working code from GitHub.
Perfect for AI agents that need to understand how to implement a feature.
"""

from typing import Dict, List, Any
import logging
from ..tools.search_patterns import CodeSearcher

logger = logging.getLogger(__name__)


class ImplementationGuideGenerator:
    """Generate implementation guides from real code"""

    def __init__(self, github_client, cache, secret_scanner, cache_ttl: int = 3600):
        self.github_client = github_client
        self.cache = cache
        self.secret_scanner = secret_scanner
        self.cache_ttl = cache_ttl
        self.code_searcher = CodeSearcher(github_client, cache, cache_ttl)

    def generate_guide(
        self,
        feature: str,
        language: str = None,
        framework: str = None,
        max_examples: int = 3
    ) -> Dict[str, Any]:
        """
        Generate implementation guide for a feature.

        Args:
            feature: Feature to implement (e.g., "user authentication")
            language: Programming language
            framework: Framework name (e.g., "fastapi", "express")
            max_examples: Number of examples to include

        Returns:
            Dict with step-by-step guide and code examples
        """
        try:
            # Build cache key
            cache_key = f"guide_{feature}_{language or 'any'}_{framework or 'any'}"
            cached = self.cache.get(cache_key, self.cache_ttl)
            if cached:
                logger.info(f"Cache hit for implementation guide: {feature}")
                return cached

            logger.info(f"Generating implementation guide for: {feature}")

            # Build search query
            query_parts = [feature]
            if framework:
                query_parts.append(framework)

            query = " ".join(query_parts)

            # Search for implementations
            examples = self.code_searcher.search(
                query=query,
                language=language,
                max_results=max_examples
            )

            # Analyze examples to extract patterns
            guide = self._analyze_examples(feature, examples, language, framework)

            # Cache result
            self.cache.set(cache_key, guide)

            return guide

        except Exception as e:
            logger.error(f"Error generating implementation guide: {e}")
            return {
                "feature": feature,
                "language": language,
                "framework": framework,
                "overview": f"Error generating guide: {str(e)}",
                "error": str(e),
                "dependencies": [],
                "steps": [],
                "patterns": [],
                "examples": [],
                "tips": []
            }

    def _analyze_examples(
        self,
        feature: str,
        examples: List[Dict],
        language: str,
        framework: str
    ) -> Dict[str, Any]:
        """Analyze examples and generate guide"""

        # Common patterns based on language/framework
        steps = self._generate_steps(feature, language, framework, examples)

        # Extract dependencies from examples
        dependencies = self._extract_dependencies(examples, language)

        # Extract common patterns
        patterns = self._extract_patterns(examples)

        return {
            "feature": feature,
            "language": language,
            "framework": framework,
            "overview": f"Implementation guide for {feature} in {language or 'any language'}",
            "dependencies": dependencies,
            "steps": steps,
            "patterns": patterns,
            "examples": examples[:3],  # Include top 3 examples
            "tips": self._generate_tips(feature, language, framework)
        }

    def _generate_steps(
        self,
        feature: str,
        language: str,
        framework: str,
        examples: List[Dict]
    ) -> List[Dict[str, str]]:
        """Generate implementation steps"""

        # Generic steps that apply to most features
        steps = []

        # Step 1: Setup
        steps.append({
            "step": 1,
            "title": "Install Dependencies",
            "description": f"Install required packages for {feature}",
            "details": "Check the examples below for specific packages needed"
        })

        # Step 2: Configuration
        steps.append({
            "step": 2,
            "title": "Configure Settings",
            "description": "Set up configuration files and environment variables",
            "details": "Create config files, set environment variables, and establish secrets management"
        })

        # Step 3: Core Implementation
        steps.append({
            "step": 3,
            "title": "Implement Core Logic",
            "description": f"Write the main {feature} logic",
            "details": "See code examples below for implementation patterns"
        })

        # Step 4: Integration
        steps.append({
            "step": 4,
            "title": "Integrate with Application",
            "description": "Connect the feature to your application",
            "details": "Add endpoints, middleware, or hooks as needed"
        })

        # Step 5: Testing
        steps.append({
            "step": 5,
            "title": "Add Tests",
            "description": "Write tests to verify functionality",
            "details": "Include unit tests and integration tests"
        })

        # Step 6: Error Handling
        steps.append({
            "step": 6,
            "title": "Handle Errors",
            "description": "Add proper error handling and validation",
            "details": "Implement try-catch blocks, validation, and user-friendly error messages"
        })

        return steps

    def _extract_dependencies(self, examples: List[Dict], language: str) -> List[str]:
        """Extract common dependencies from examples"""
        dependencies = set()

        for example in examples:
            content = example.get("content", "")

            # Python imports
            if language == "python":
                import_lines = [line for line in content.split("\n") if line.strip().startswith(("import ", "from "))]
                for line in import_lines[:5]:  # First 5 imports
                    dependencies.add(line.strip())

            # JavaScript/TypeScript imports
            elif language in ["javascript", "typescript"]:
                import_lines = [line for line in content.split("\n") if "import " in line or "require(" in line]
                for line in import_lines[:5]:
                    dependencies.add(line.strip())

        return sorted(list(dependencies))[:10]  # Top 10 dependencies

    def _extract_patterns(self, examples: List[Dict]) -> List[str]:
        """Extract common patterns from examples"""
        patterns = []

        if len(examples) >= 2:
            patterns.append("Multiple implementations found - this is a well-established pattern")

        # Check for common keywords
        all_content = " ".join([ex.get("content", "") for ex in examples]).lower()

        if "async" in all_content or "await" in all_content:
            patterns.append("Uses asynchronous patterns")

        if "test" in all_content:
            patterns.append("Includes test examples")

        if "config" in all_content or "settings" in all_content:
            patterns.append("Uses configuration management")

        if "error" in all_content or "exception" in all_content:
            patterns.append("Implements error handling")

        if "validate" in all_content or "validation" in all_content:
            patterns.append("Includes validation logic")

        return patterns

    def _generate_tips(self, feature: str, language: str, framework: str) -> List[str]:
        """Generate implementation tips"""
        tips = [
            "Start with the simplest working example",
            "Add error handling early in development",
            "Write tests as you implement features",
            "Use environment variables for sensitive data",
            "Follow the patterns used in popular repositories"
        ]

        # Language-specific tips
        if language == "python":
            tips.append("Use type hints for better code clarity")
            tips.append("Consider using Pydantic for validation")

        if language in ["javascript", "typescript"]:
            tips.append("Use async/await for asynchronous operations")
            tips.append("Consider using TypeScript for type safety")

        return tips


async def get_implementation_guide_tool(
    arguments: Dict[str, Any],
    github_client,
    cache,
    secret_scanner,
    cache_ttl: int
) -> Dict:
    """
    MCP tool: Get implementation guide

    Arguments:
        feature: Feature to implement (required)
        language: Programming language (optional)
        framework: Framework name (optional)
        max_examples: Number of examples (default: 3)
    """
    feature = arguments.get("feature")
    language = arguments.get("language")
    framework = arguments.get("framework")
    max_examples = arguments.get("max_examples", 3)

    if not feature:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Please provide a feature to get implementation guide for"
            }],
            "isError": True
        }

    generator = ImplementationGuideGenerator(github_client, cache, secret_scanner, cache_ttl)
    guide = generator.generate_guide(feature, language, framework, max_examples)

    # Format output
    output = []
    output.append(f"# Implementation Guide: {guide['feature']}\n\n")

    if guide['language']:
        output.append(f"Language: {guide['language']}\n")
    if guide['framework']:
        output.append(f"Framework: {guide['framework']}\n")

    output.append("\n" + "=" * 60 + "\n\n")

    # Overview
    output.append(f"## Overview\n{guide['overview']}\n\n")

    # Dependencies
    if guide.get('dependencies'):
        output.append("## Dependencies\n")
        for dep in guide['dependencies']:
            output.append(f"  {dep}\n")
        output.append("\n")

    # Steps
    output.append("## Implementation Steps\n\n")
    for step in guide['steps']:
        output.append(f"### Step {step['step']}: {step['title']}\n")
        output.append(f"{step['description']}\n")
        output.append(f"*{step['details']}*\n\n")

    # Patterns
    if guide.get('patterns'):
        output.append("## Common Patterns\n")
        for pattern in guide['patterns']:
            output.append(f"  - {pattern}\n")
        output.append("\n")

    # Tips
    if guide.get('tips'):
        output.append("## Implementation Tips\n")
        for tip in guide['tips']:
            output.append(f"  - {tip}\n")
        output.append("\n")

    # Examples
    if guide.get('examples'):
        output.append("## Working Examples\n\n")
        for i, example in enumerate(guide['examples'], 1):
            output.append(f"### Example {i}: {example['repo']}\n")
            output.append(f"File: {example['path']}\n")
            output.append(f"URL: {example['url']}\n")
            output.append(f"Stars: {example.get('stars', 0)}\n\n")
            output.append("```\n")
            content = example.get('content', '')[:1000]  # First 1000 chars
            output.append(content)
            if len(example.get('content', '')) > 1000:
                output.append("\n... (truncated)")
            output.append("\n```\n\n")

    return {
        "content": [{
            "type": "text",
            "text": "".join(output)
        }]
    }
