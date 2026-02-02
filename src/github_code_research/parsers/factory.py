"""Parser factory for creating language-specific parsers."""

from typing import Dict, Optional, Type

from ..utils.logger import setup_logger
from .base import BaseParser
from .javascript_parser import JavaScriptParser
from .python_parser import PythonParser
from .typescript_parser import TypeScriptParser

logger = setup_logger(__name__)


class ParserFactory:
    """Factory for creating language-specific parsers."""

    # Map file extensions to parser classes
    EXTENSION_MAP: Dict[str, Type[BaseParser]] = {
        ".py": PythonParser,
        ".js": JavaScriptParser,
        ".jsx": JavaScriptParser,
        ".mjs": JavaScriptParser,
        ".cjs": JavaScriptParser,
        ".ts": TypeScriptParser,
        ".tsx": TypeScriptParser,
        ".mts": TypeScriptParser,
        ".cts": TypeScriptParser,
    }

    # Map language names to parser classes
    LANGUAGE_MAP: Dict[str, Type[BaseParser]] = {
        "python": PythonParser,
        "javascript": JavaScriptParser,
        "typescript": TypeScriptParser,
    }

    _parser_cache: Dict[str, BaseParser] = {}

    @classmethod
    def get_parser(cls, file_path: str = None, language: str = None) -> Optional[BaseParser]:
        """
        Get parser for a file or language.

        Args:
            file_path: File path (used to detect language by extension)
            language: Language name (overrides file_path detection)

        Returns:
            Parser instance or None if language not supported
        """
        parser_class = None

        # Try language name first
        if language:
            parser_class = cls.LANGUAGE_MAP.get(language.lower())

        # Try file extension
        elif file_path:
            for ext, parser in cls.EXTENSION_MAP.items():
                if file_path.endswith(ext):
                    parser_class = parser
                    break

        if not parser_class:
            logger.debug(f"No parser found for file_path={file_path}, language={language}")
            return None

        # Return cached parser instance
        parser_name = parser_class.__name__
        if parser_name not in cls._parser_cache:
            try:
                cls._parser_cache[parser_name] = parser_class()
                logger.debug(f"Created parser: {parser_name}")
            except Exception as e:
                logger.error(f"Failed to create parser {parser_name}: {e}")
                return None

        return cls._parser_cache[parser_name]

    @classmethod
    def is_supported(cls, file_path: str = None, language: str = None) -> bool:
        """
        Check if a file or language is supported.

        Args:
            file_path: File path
            language: Language name

        Returns:
            True if supported
        """
        if language and language.lower() in cls.LANGUAGE_MAP:
            return True

        if file_path:
            for ext in cls.EXTENSION_MAP.keys():
                if file_path.endswith(ext):
                    return True

        return False

    @classmethod
    def get_supported_extensions(cls) -> list:
        """Get list of supported file extensions."""
        return list(cls.EXTENSION_MAP.keys())

    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of supported language names."""
        return list(cls.LANGUAGE_MAP.keys())
