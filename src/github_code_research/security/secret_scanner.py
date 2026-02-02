"""Secret scanner to detect and redact sensitive information."""

import re
from typing import List, Tuple

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SecretScanner:
    """Scanner to detect and redact secrets in code."""

    # Regex patterns for common secrets
    PATTERNS = [
        # AWS Access Key
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
        # AWS Secret Key (generic pattern)
        (r"(?i)aws[_-]?secret[_-]?access[_-]?key['\"\\s:=]+[a-zA-Z0-9/+=]{40}", "AWS Secret Key"),
        # GitHub Token (Personal Access Token)
        (r"ghp_[0-9a-zA-Z]{36}", "GitHub PAT"),
        # GitHub OAuth Token
        (r"gho_[0-9a-zA-Z]{36}", "GitHub OAuth Token"),
        # GitHub Token (Fine-grained)
        (r"github_pat_[0-9a-zA-Z_]{82}", "GitHub Fine-grained PAT"),
        # Generic API Key patterns
        (r"(?i)(api[_-]?key|apikey)['\"\\s:=]+['\"]?[a-zA-Z0-9\\-_.]{16,100}['\"]?", "API Key"),
        # Generic Secret/Token patterns
        (r"(?i)(secret|token|password)['\"\\s:=]+['\"]?[a-zA-Z0-9\\-_.!@#$%^&*()]{16,100}['\"]?", "Generic Secret"),
        # Private Key headers
        (r"-----BEGIN[A-Z ]+PRIVATE KEY-----", "Private Key"),
        # Bearer tokens
        (r"Bearer\s+[a-zA-Z0-9\\-_.=]+", "Bearer Token"),
        # Basic Auth
        (r"Basic\s+[a-zA-Z0-9+/=]+", "Basic Auth"),
        # Slack Token
        (r"xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Token"),
        # Stripe API Key
        (r"sk_live_[0-9a-zA-Z]{24,}", "Stripe Live Key"),
        # Google API Key
        (r"AIza[0-9A-Za-z\\-_]{35}", "Google API Key"),
        # JWT Token (simple pattern)
        (r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "JWT Token"),
    ]

    def __init__(self):
        """Initialize secret scanner with compiled patterns."""
        self.compiled_patterns: List[Tuple[re.Pattern, str]] = [
            (re.compile(pattern, re.MULTILINE), name)
            for pattern, name in self.PATTERNS
        ]

    def scan(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Scan text for secrets.

        Args:
            text: Text to scan

        Returns:
            List of tuples (secret_type, matched_text, position)
        """
        findings = []

        for pattern, secret_type in self.compiled_patterns:
            for match in pattern.finditer(text):
                findings.append((secret_type, match.group(0), match.start()))

        return findings

    def redact(self, text: str, replacement: str = "[REDACTED]") -> Tuple[str, int]:
        """
        Redact secrets from text.

        Args:
            text: Text to redact
            replacement: Replacement string for secrets

        Returns:
            Tuple of (redacted_text, number_of_redactions)
        """
        if not text:
            return text, 0

        redaction_count = 0
        redacted_text = text

        for pattern, secret_type in self.compiled_patterns:
            matches = list(pattern.finditer(redacted_text))
            if matches:
                redaction_count += len(matches)
                redacted_text = pattern.sub(f"{replacement} ({secret_type})", redacted_text)

        if redaction_count > 0:
            logger.warning(f"Redacted {redaction_count} potential secret(s) from content")

        return redacted_text, redaction_count

    def is_safe(self, text: str) -> bool:
        """
        Check if text contains any secrets.

        Args:
            text: Text to check

        Returns:
            True if no secrets found, False otherwise
        """
        for pattern, _ in self.compiled_patterns:
            if pattern.search(text):
                return False
        return True


# Global scanner instance
_scanner_instance = None


def get_scanner() -> SecretScanner:
    """Get global secret scanner instance."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = SecretScanner()
    return _scanner_instance
