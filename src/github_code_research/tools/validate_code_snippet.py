"""
Tool 8: Validate Code Snippet

Validates code snippets before AI agents use them.
Checks for common issues, deprecated APIs, and compatibility.
"""

from typing import Dict, List, Any
import logging
import re

logger = logging.getLogger(__name__)


class CodeValidator:
    """Validate code snippets for quality and compatibility"""

    def __init__(self, github_client, secret_scanner):
        self.github_client = github_client
        self.secret_scanner = secret_scanner

    def validate(
        self,
        code: str,
        language: str = None,
        target_version: str = None,
        check_secrets: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a code snippet.

        Args:
            code: Code snippet to validate
            language: Programming language
            target_version: Target language/framework version
            check_secrets: Whether to check for secrets

        Returns:
            Dict with validation results
        """
        try:
            logger.info(f"Validating code snippet ({len(code)} chars)")

            issues = []
            warnings = []
            suggestions = []
            score = 100.0

            # Check for secrets
            if check_secrets:
                redacted_code, secret_count = self.secret_scanner.redact(code)
                if secret_count > 0:
                    issues.append({
                        "type": "SECURITY",
                        "severity": "CRITICAL",
                        "message": f"Found {secret_count} potential secret(s) in code",
                        "fix": "Remove hardcoded secrets and use environment variables"
                    })
                    score -= 30

            # Language-specific validation
            if language == "python":
                python_issues = self._validate_python(code, target_version)
                issues.extend(python_issues)
                score -= len(python_issues) * 5

            elif language in ["javascript", "typescript"]:
                js_issues = self._validate_javascript(code, target_version)
                issues.extend(js_issues)
                score -= len(js_issues) * 5

            # General code quality checks
            quality_issues = self._check_code_quality(code)
            warnings.extend(quality_issues)
            score -= len(quality_issues) * 2

            # Check for best practices
            practice_suggestions = self._check_best_practices(code, language)
            suggestions.extend(practice_suggestions)

            # Calculate final score
            final_score = max(0, min(100, score))

            # Determine status
            if final_score >= 90:
                status = "EXCELLENT"
            elif final_score >= 75:
                status = "GOOD"
            elif final_score >= 60:
                status = "ACCEPTABLE"
            elif final_score >= 40:
                status = "NEEDS_IMPROVEMENT"
            else:
                status = "POOR"

            return {
                "valid": len([i for i in issues if i.get("severity") == "CRITICAL"]) == 0,
                "score": final_score,
                "status": status,
                "issues": issues,
                "warnings": warnings,
                "suggestions": suggestions,
                "summary": self._generate_summary(final_score, issues, warnings)
            }

        except Exception as e:
            logger.error(f"Error validating code: {e}")
            return {
                "valid": False,
                "error": str(e),
                "issues": [],
                "warnings": [],
                "suggestions": []
            }

    def _validate_python(self, code: str, target_version: str = None) -> List[Dict]:
        """Python-specific validation"""
        issues = []

        # Check for deprecated imports
        deprecated_imports = {
            "imp": "Use importlib instead",
            "optparse": "Use argparse instead",
            "popen2": "Use subprocess instead"
        }

        for dep_import, suggestion in deprecated_imports.items():
            if f"import {dep_import}" in code or f"from {dep_import}" in code:
                issues.append({
                    "type": "DEPRECATED",
                    "severity": "WARNING",
                    "message": f"Using deprecated module: {dep_import}",
                    "fix": suggestion
                })

        # Check for common anti-patterns
        if "except:" in code or "except :" in code:
            issues.append({
                "type": "ANTI_PATTERN",
                "severity": "WARNING",
                "message": "Bare except clause catches all exceptions",
                "fix": "Specify exception types explicitly"
            })

        # Check for Python 2 vs 3 issues
        if "print " in code and "print(" not in code:
            issues.append({
                "type": "COMPATIBILITY",
                "severity": "ERROR",
                "message": "Python 2 style print statement",
                "fix": "Use print() function for Python 3"
            })

        return issues

    def _validate_javascript(self, code: str, target_version: str = None) -> List[Dict]:
        """JavaScript/TypeScript-specific validation"""
        issues = []

        # Check for deprecated APIs
        if "var " in code:
            issues.append({
                "type": "DEPRECATED",
                "severity": "WARNING",
                "message": "Using 'var' instead of 'let' or 'const'",
                "fix": "Use 'let' for mutable variables or 'const' for constants"
            })

        # Check for common mistakes
        if "== " in code or " ==" in code:
            issues.append({
                "type": "ANTI_PATTERN",
                "severity": "WARNING",
                "message": "Using loose equality (==) instead of strict (===)",
                "fix": "Use === for type-safe comparisons"
            })

        return issues

    def _check_code_quality(self, code: str) -> List[Dict]:
        """Check general code quality"""
        warnings = []

        lines = code.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]

        # Check line length
        long_lines = [i for i, l in enumerate(lines, 1) if len(l) > 120]
        if long_lines:
            warnings.append({
                "type": "STYLE",
                "severity": "INFO",
                "message": f"Found {len(long_lines)} lines longer than 120 characters",
                "fix": "Consider breaking long lines for readability"
            })

        # Check for TODO/FIXME comments
        todo_count = len([l for l in lines if "TODO" in l or "FIXME" in l])
        if todo_count > 0:
            warnings.append({
                "type": "INCOMPLETE",
                "severity": "INFO",
                "message": f"Found {todo_count} TODO/FIXME comment(s)",
                "fix": "Address incomplete implementations"
            })

        # Check for hardcoded values
        if re.search(r'[\'"]\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[\'"]', code):
            warnings.append({
                "type": "HARDCODED",
                "severity": "WARNING",
                "message": "Found hardcoded IP address",
                "fix": "Use configuration or environment variables"
            })

        return warnings

    def _check_best_practices(self, code: str, language: str) -> List[Dict]:
        """Check for best practices"""
        suggestions = []

        # Check for error handling
        if language == "python":
            if "try:" in code and "except" in code:
                suggestions.append({
                    "type": "GOOD_PRACTICE",
                    "message": "✓ Includes error handling"
                })
            else:
                suggestions.append({
                    "type": "SUGGESTION",
                    "message": "Consider adding try-except for error handling"
                })

        # Check for documentation
        if '"""' in code or "'''" in code or "/**" in code:
            suggestions.append({
                "type": "GOOD_PRACTICE",
                "message": "✓ Includes documentation"
            })

        # Check for type hints (Python)
        if language == "python" and "->" in code:
            suggestions.append({
                "type": "GOOD_PRACTICE",
                "message": "✓ Uses type hints"
            })

        return suggestions

    def _generate_summary(self, score: float, issues: List, warnings: List) -> str:
        """Generate validation summary"""
        critical_count = len([i for i in issues if i.get("severity") == "CRITICAL"])
        error_count = len([i for i in issues if i.get("severity") == "ERROR"])
        warning_count = len(warnings)

        if critical_count > 0:
            return f"Code has {critical_count} critical issue(s) that must be fixed"
        elif error_count > 0:
            return f"Code has {error_count} error(s) that should be fixed"
        elif warning_count > 0:
            return f"Code has {warning_count} warning(s) to consider"
        else:
            return "Code looks good with no major issues"


async def validate_code_snippet_tool(
    arguments: Dict[str, Any],
    github_client,
    cache,
    secret_scanner,
    cache_ttl: int
) -> List[Dict[str, Any]]:
    """
    MCP tool: Validate code snippet

    Arguments:
        code: Code snippet to validate (required)
        language: Programming language (optional)
        target_version: Target version (optional)
        check_secrets: Check for secrets (default: true)
    """
    code = arguments.get("code")
    language = arguments.get("language")
    target_version = arguments.get("target_version")
    check_secrets = arguments.get("check_secrets", True)

    if not code:
        return [{
            "type": "text",
            "text": "Error: Please provide code to validate"
        }]

    validator = CodeValidator(github_client, secret_scanner)
    result = validator.validate(code, language, target_version, check_secrets)

    # Format output
    output = []
    output.append("# Code Validation Results\n\n")

    # Status
    status_emoji = {
        "EXCELLENT": "✅",
        "GOOD": "✓",
        "ACCEPTABLE": "⚠️",
        "NEEDS_IMPROVEMENT": "⚠️",
        "POOR": "❌"
    }
    emoji = status_emoji.get(result.get('status', 'UNKNOWN'), "?")

    output.append(f"{emoji} **Status: {result.get('status', 'UNKNOWN')}**\n")
    output.append(f"**Score: {result.get('score', 0):.0f}/100**\n")
    output.append(f"**Valid: {'Yes' if result.get('valid') else 'No'}**\n\n")

    output.append(f"**Summary:** {result.get('summary', 'N/A')}\n\n")

    output.append("=" * 60 + "\n\n")

    # Issues
    issues = result.get('issues', [])
    if issues:
        output.append("## Issues\n\n")
        for issue in issues:
            severity_emoji = {"CRITICAL": "🔴", "ERROR": "🟠", "WARNING": "🟡"}
            emoji = severity_emoji.get(issue.get('severity', 'INFO'), "ℹ️")
            output.append(f"{emoji} **{issue.get('severity')}** - {issue.get('message')}\n")
            if issue.get('fix'):
                output.append(f"   *Fix: {issue.get('fix')}*\n")
            output.append("\n")

    # Warnings
    warnings = result.get('warnings', [])
    if warnings:
        output.append("## Warnings\n\n")
        for warning in warnings:
            output.append(f"⚠️  {warning.get('message')}\n")
            if warning.get('fix'):
                output.append(f"   *{warning.get('fix')}*\n")
            output.append("\n")

    # Suggestions
    suggestions = result.get('suggestions', [])
    if suggestions:
        output.append("## Suggestions\n\n")
        for suggestion in suggestions:
            output.append(f"💡 {suggestion.get('message')}\n")

    if not issues and not warnings:
        output.append("\n✅ **No issues found! Code looks good.**\n")

    return [{"type": "text", "text": "".join(output)}]
