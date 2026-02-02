"""Python parser using tree-sitter."""

from typing import List

from tree_sitter import Language, Parser, Tree
from tree_sitter_languages import get_language, get_parser

from ..utils.logger import setup_logger
from .base import BaseParser, ParseResult, Symbol

logger = setup_logger(__name__)


class PythonParser(BaseParser):
    """Parser for Python code."""

    def __init__(self):
        """Initialize Python parser."""
        super().__init__("python")
        self.parser = get_parser("python")
        self.language = get_language("python")

    def parse(self, content: str, file_path: str = "") -> ParseResult:
        """
        Parse Python source code.

        Args:
            content: Python source code
            file_path: Optional file path

        Returns:
            ParseResult with extracted symbols
        """
        try:
            source_bytes = content.encode("utf-8")
            tree = self.parser.parse(source_bytes)

            symbols = self.extract_signatures(tree, source_bytes, file_path)
            imports = self._extract_imports(tree.root_node, source_bytes)
            calls = self._extract_calls(tree.root_node, source_bytes)

            return ParseResult(
                symbols=symbols,
                imports=imports,
                calls=calls,
                tree=tree
            )

        except Exception as e:
            logger.error(f"Failed to parse Python file {file_path}: {e}")
            return ParseResult(symbols=[], imports=[], calls=[])

    def extract_signatures(self, tree: Tree, source_bytes: bytes, file_path: str = "") -> List[Symbol]:
        """
        Extract function and class signatures from Python AST.

        Args:
            tree: Tree-sitter AST
            source_bytes: Source code as bytes
            file_path: Optional file path

        Returns:
            List of symbols
        """
        symbols = []

        # Find all function and class definitions
        functions = self._find_nodes_by_type(tree.root_node, "function_definition")
        classes = self._find_nodes_by_type(tree.root_node, "class_definition")

        # Extract functions
        for func_node in functions:
            symbol = self._extract_function_symbol(func_node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

        # Extract classes
        for class_node in classes:
            symbol = self._extract_class_symbol(class_node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

                # Extract methods from class
                for child in class_node.children:
                    if child.type == "block":
                        methods = self._find_nodes_by_type(child, "function_definition")
                        for method_node in methods:
                            method_symbol = self._extract_function_symbol(
                                method_node, source_bytes, file_path, parent_class=symbol.name
                            )
                            if method_symbol:
                                symbols.append(method_symbol)

        return symbols

    def _extract_function_symbol(
        self,
        node: 'Node',
        source_bytes: bytes,
        file_path: str,
        parent_class: str = None
    ) -> Symbol:
        """Extract function/method symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = self._node_text(name_node, source_bytes)

        # Get parameters
        params_node = node.child_by_field_name("parameters")
        params = self._node_text(params_node, source_bytes) if params_node else "()"

        # Get return type if present
        return_type = ""
        for child in node.children:
            if child.type == "->":
                # Find the type annotation
                idx = node.children.index(child)
                if idx + 1 < len(node.children):
                    type_node = node.children[idx + 1]
                    if type_node.type != ":":
                        return_type = f" -> {self._node_text(type_node, source_bytes).strip()}"
                break

        # Build signature
        if parent_class:
            signature = f"def {parent_class}.{name}{params}{return_type}"
            symbol_type = "method"
        else:
            signature = f"def {name}{params}{return_type}"
            symbol_type = "function"

        # Check if public (not starting with _)
        is_public = not name.startswith("_") or name.startswith("__") and name.endswith("__")

        return Symbol(
            name=name,
            type=symbol_type,
            signature=signature,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_public=is_public,
            is_exported=is_public,  # In Python, public symbols are effectively exported
            file_path=file_path
        )

    def _extract_class_symbol(self, node: 'Node', source_bytes: bytes, file_path: str) -> Symbol:
        """Extract class symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = self._node_text(name_node, source_bytes)

        # Get base classes
        bases = []
        superclasses_node = node.child_by_field_name("superclasses")
        if superclasses_node:
            bases_text = self._node_text(superclasses_node, source_bytes)
            signature = f"class {name}{bases_text}"
        else:
            signature = f"class {name}"

        # Check if public
        is_public = not name.startswith("_")

        return Symbol(
            name=name,
            type="class",
            signature=signature,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_public=is_public,
            is_exported=is_public,
            file_path=file_path
        )

    def _extract_imports(self, node: 'Node', source_bytes: bytes) -> List[str]:
        """Extract import statements."""
        imports = []

        # Find import and from...import statements
        import_nodes = self._find_nodes_by_type(node, "import_statement")
        from_import_nodes = self._find_nodes_by_type(node, "import_from_statement")

        for imp_node in import_nodes + from_import_nodes:
            import_text = self._node_text(imp_node, source_bytes).strip()
            imports.append(import_text)

        return imports

    def _extract_calls(self, node: 'Node', source_bytes: bytes) -> List[str]:
        """Extract function calls."""
        calls = []

        call_nodes = self._find_nodes_by_type(node, "call")

        for call_node in call_nodes:
            func_node = call_node.child_by_field_name("function")
            if func_node:
                func_name = self._node_text(func_node, source_bytes).strip()
                # Only include simple names or attribute access (avoid complex expressions)
                if func_name and not func_name.startswith("("):
                    calls.append(func_name)

        return list(set(calls))  # Remove duplicates
