"""Base parser interface for tree-sitter parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from tree_sitter import Node, Tree


@dataclass
class Symbol:
    """Represents a code symbol (function, class, etc.)."""
    name: str
    type: str  # 'function', 'class', 'method', 'interface', etc.
    signature: str  # Full signature without body
    start_line: int
    end_line: int
    is_exported: bool = False
    is_public: bool = True
    file_path: Optional[str] = None


@dataclass
class ParseResult:
    """Result of parsing a file."""
    symbols: List[Symbol]
    imports: List[str]
    calls: List[str]
    tree: Optional[Tree] = None


class BaseParser(ABC):
    """Base class for language-specific parsers."""

    def __init__(self, language: str):
        """
        Initialize parser.

        Args:
            language: Language name
        """
        self.language = language

    @abstractmethod
    def parse(self, content: str, file_path: str = "") -> ParseResult:
        """
        Parse source code and extract symbols.

        Args:
            content: Source code content
            file_path: Optional file path for context

        Returns:
            ParseResult with extracted information
        """
        pass

    @abstractmethod
    def extract_signatures(self, tree: Tree) -> List[Symbol]:
        """
        Extract function/class signatures from AST.

        Args:
            tree: Tree-sitter AST

        Returns:
            List of symbols
        """
        pass

    def _node_text(self, node: Node, source: bytes) -> str:
        """
        Get text content of a tree-sitter node.

        Args:
            node: Tree-sitter node
            source: Source code as bytes

        Returns:
            Node text content
        """
        return source[node.start_byte:node.end_byte].decode("utf-8")

    def _find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """
        Recursively find all nodes of a specific type.

        Args:
            node: Root node to search from
            node_type: Node type to find

        Returns:
            List of matching nodes
        """
        results = []

        if node.type == node_type:
            results.append(node)

        for child in node.children:
            results.extend(self._find_nodes_by_type(child, node_type))

        return results
