"""Configuration settings with multiple sources (env, file, defaults)."""

import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..utils.errors import ConfigurationError


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GitHub authentication
    github_token: str = Field(default="", description="GitHub personal access token")

    # Search settings
    max_search_results: int = Field(default=10, ge=1, le=30, description="Max search results")

    # Cache settings
    cache_dir: str = Field(default=".cache", description="Cache directory path")
    cache_ttl_search: int = Field(default=3600, description="Search cache TTL (seconds)")
    cache_ttl_repo_map: int = Field(default=86400, description="Repo map cache TTL (seconds)")
    cache_ttl_license: int = Field(default=604800, description="License cache TTL (seconds)")

    # Language support
    supported_languages: List[str] = Field(
        default=["python", "javascript", "typescript", "go"],
        description="Supported programming languages"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator("github_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate GitHub token format."""
        if not v:
            return v  # Will be caught by get_settings()
        if not (v.startswith("ghp_") or v.startswith("github_pat_") or v.startswith("gho_")):
            raise ValueError("GitHub token must start with 'ghp_', 'github_pat_', or 'gho_'")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper


_settings_instance: Optional[Settings] = None


def get_settings(config_file: Optional[str] = None) -> Settings:
    """
    Get settings instance (singleton pattern).

    Priority order:
    1. Environment variables
    2. Config file (if provided)
    3. Default values

    Args:
        config_file: Optional path to JSON config file

    Returns:
        Settings instance

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _settings_instance

    if _settings_instance is not None:
        return _settings_instance

    # Start with defaults and env vars
    config_data = {}

    # Load from config file if provided
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path) as f:
                    file_config = json.load(f)
                    config_data.update(file_config)
            except Exception as e:
                raise ConfigurationError(f"Failed to load config file: {e}")
    elif Path("config.json").exists():
        # Try default config.json
        try:
            with open("config.json") as f:
                file_config = json.load(f)
                config_data.update(file_config)
        except Exception:
            pass  # Config file is optional

    try:
        # Create settings (env vars will override file config)
        _settings_instance = Settings(**config_data)

        # Validate GitHub token is provided
        if not _settings_instance.github_token:
            raise ConfigurationError(
                "GitHub token not found. Set GITHUB_TOKEN environment variable or add it to config.json"
            )

        return _settings_instance

    except Exception as e:
        raise ConfigurationError(f"Configuration error: {e}")


def reset_settings():
    """Reset settings instance (for testing)."""
    global _settings_instance
    _settings_instance = None
