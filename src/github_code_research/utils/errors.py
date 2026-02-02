"""Custom exceptions for GitHub Code Research."""


class GitHubCodeResearchError(Exception):
    """Base exception for all GitHub Code Research errors."""
    pass


class RateLimitError(GitHubCodeResearchError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, message: str, reset_time: int = None):
        super().__init__(message)
        self.reset_time = reset_time


class AuthenticationError(GitHubCodeResearchError):
    """Raised when GitHub authentication fails."""
    pass


class ParseError(GitHubCodeResearchError):
    """Raised when parsing code fails."""

    def __init__(self, file: str, line: int = None, message: str = ""):
        self.file = file
        self.line = line
        super().__init__(f"Parse error in {file}" + (f" at line {line}" if line else "") + f": {message}")


class NotFoundError(GitHubCodeResearchError):
    """Raised when a GitHub resource is not found."""

    def __init__(self, resource: str):
        self.resource = resource
        super().__init__(f"Resource not found: {resource}")


class ConfigurationError(GitHubCodeResearchError):
    """Raised when configuration is invalid."""
    pass
