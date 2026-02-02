"""License checking tool."""

import re
from typing import Dict, Optional

from ..github.client import GitHubClient
from ..utils.cache import FileCache
from ..utils.errors import GitHubCodeResearchError, NotFoundError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class LicenseChecker:
    """Check repository licenses and categorize safety."""

    # Safe licenses (permissive)
    SAFE_LICENSES = {
        "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause",
        "isc", "cc0-1.0", "unlicense", "0bsd"
    }

    # Viral licenses (copyleft)
    VIRAL_LICENSES = {
        "gpl-2.0", "gpl-3.0", "agpl-3.0", "lgpl-2.1", "lgpl-3.0",
        "mpl-2.0", "epl-1.0", "epl-2.0", "eupl-1.1", "eupl-1.2"
    }

    # License patterns for text detection
    LICENSE_PATTERNS = {
        "MIT": r"MIT License|Permission is hereby granted, free of charge",
        "Apache-2.0": r"Apache License.*Version 2\.0",
        "GPL-3.0": r"GNU GENERAL PUBLIC LICENSE.*Version 3",
        "GPL-2.0": r"GNU GENERAL PUBLIC LICENSE.*Version 2",
        "BSD": r"BSD.*Clause License|Redistribution and use in source and binary forms",
        "ISC": r"ISC License|Permission to use, copy, modify.*ISC",
    }

    def __init__(self, github_client: GitHubClient, cache: FileCache, cache_ttl: int = 604800):
        """
        Initialize license checker.

        Args:
            github_client: GitHub API client
            cache: Cache instance
            cache_ttl: Cache TTL in seconds (default: 7 days)
        """
        self.github_client = github_client
        self.cache = cache
        self.cache_ttl = cache_ttl

    def check_license(self, owner: str, repo: str) -> Dict[str, str]:
        """
        Check repository license and categorize safety.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dict with keys:
                - license: License SPDX ID or "UNKNOWN"
                - safety: "SAFE_TO_USE", "VIRAL_LICENSE_WARNING", or "REVIEW_REQUIRED"
                - source: "api" or "file_detection"
                - details: Additional information
        """
        cache_key = f"license_{owner}_{repo}"

        # Check cache
        cached = self.cache.get(cache_key, ttl=self.cache_ttl)
        if cached:
            logger.debug(f"License cache hit: {owner}/{repo}")
            return cached

        result = {
            "license": "UNKNOWN",
            "safety": "REVIEW_REQUIRED",
            "source": "none",
            "details": ""
        }

        try:
            # Try GitHub License API
            license_data = self.github_client.get_license(owner, repo)

            if license_data:
                license_info = license_data.get("license", {})
                spdx_id = license_info.get("spdx_id", "").lower()

                if spdx_id and spdx_id != "noassertion":
                    result["license"] = spdx_id.upper()
                    result["source"] = "api"
                    result["safety"] = self._categorize_license(spdx_id)
                    result["details"] = license_info.get("name", "")

                    logger.info(f"License for {owner}/{repo}: {result['license']} ({result['safety']})")

                    # Cache result
                    self.cache.set(cache_key, result)
                    return result

        except NotFoundError:
            logger.debug(f"No license API data for {owner}/{repo}, trying file detection")
        except Exception as e:
            logger.warning(f"Failed to get license from API for {owner}/{repo}: {e}")

        # Try detecting from LICENSE file
        try:
            license_from_file = self._detect_from_file(owner, repo)
            if license_from_file:
                result.update(license_from_file)
                result["source"] = "file_detection"

                logger.info(f"License detected from file for {owner}/{repo}: {result['license']}")

        except Exception as e:
            logger.warning(f"Failed to detect license from file for {owner}/{repo}: {e}")

        # Cache result even if unknown
        self.cache.set(cache_key, result)
        return result

    def _categorize_license(self, spdx_id: str) -> str:
        """Categorize license by safety."""
        spdx_lower = spdx_id.lower()

        if spdx_lower in self.SAFE_LICENSES:
            return "SAFE_TO_USE"
        elif spdx_lower in self.VIRAL_LICENSES:
            return "VIRAL_LICENSE_WARNING"
        else:
            return "REVIEW_REQUIRED"

    def _detect_from_file(self, owner: str, repo: str) -> Optional[Dict[str, str]]:
        """Detect license from LICENSE file content."""
        # Try common license file names
        license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "COPYING.txt"]

        for filename in license_files:
            try:
                content = self.github_client.get_file_content(owner, repo, filename)

                # Try to match license patterns
                for license_name, pattern in self.LICENSE_PATTERNS.items():
                    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                        spdx_id = license_name.upper()
                        return {
                            "license": spdx_id,
                            "safety": self._categorize_license(spdx_id),
                            "details": f"Detected from {filename}"
                        }

                # If we found a LICENSE file but couldn't match it
                return {
                    "license": "CUSTOM",
                    "safety": "REVIEW_REQUIRED",
                    "details": f"Custom license in {filename}"
                }

            except NotFoundError:
                continue
            except Exception as e:
                logger.debug(f"Error reading {filename}: {e}")
                continue

        return None


async def check_license_tool(
    arguments: Dict[str, str],
    github_client: GitHubClient,
    cache: FileCache,
    cache_ttl: int
) -> Dict:
    """
    MCP tool: Check repository license.

    Args:
        arguments: Tool arguments with 'owner' and 'repo'
        github_client: GitHub client instance
        cache: Cache instance
        cache_ttl: Cache TTL

    Returns:
        Tool result with license information
    """
    try:
        owner = arguments.get("owner")
        repo = arguments.get("repo")

        if not owner or not repo:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'owner' and 'repo' are required parameters"
                    }
                ],
                "isError": True
            }

        checker = LicenseChecker(github_client, cache, cache_ttl)
        result = checker.check_license(owner, repo)

        # Format output
        output_lines = [
            f"Repository: {owner}/{repo}",
            f"License: {result['license']}",
            f"Safety: {result['safety']}",
            f"Source: {result['source']}",
        ]

        if result.get("details"):
            output_lines.append(f"Details: {result['details']}")

        # Add safety explanation
        if result['safety'] == "SAFE_TO_USE":
            output_lines.append("\nThis is a permissive license. You can generally use this code freely.")
        elif result['safety'] == "VIRAL_LICENSE_WARNING":
            output_lines.append(
                "\nWARNING: This is a copyleft license. "
                "Using this code may require you to open-source your own code. "
                "Review the license terms carefully."
            )
        elif result['safety'] == "REVIEW_REQUIRED":
            output_lines.append(
                "\nThis license requires review. "
                "Check the license terms before using this code."
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(output_lines)
                }
            ]
        }

    except Exception as e:
        logger.error(f"License check failed: {e}", exc_info=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error checking license: {str(e)}"
                }
            ],
            "isError": True
        }
