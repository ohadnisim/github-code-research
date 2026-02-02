"""JavaScript parser using tree-sitter."""

from typing import List

from tree_sitter import Tree
from tree_sitter_languages import get_parser

from ..utils.logger import setup_logger
from .base import BaseParser, ParseResult, Symbol

logger = setup_logger(__name__)


class JavaScriptParser(BaseParser):
    """Parser for JavaScript code."""

    def __init__(self):
        """Initialize JavaScript parser."""
        super().__init__("javascript")
        self.parser = get_parser("javascript")

    def parse(self, content: str, file_path: str = "") -> ParseResult:
        """Parse JavaScript source code."""
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
            logger.error(f"Failed to parse JavaScript file {file_path}: {e}")
            return ParseResult(symbols=[], imports=[], calls=[])

    def extract_signatures(self, tree: Tree, source_bytes: bytes, file_path: str = "") -> List[Symbol]:
        """Extract function and class signatures."""
        symbols = []

        # Function declarations
        func_declarations = self._find_nodes_by_type(tree.root_node, "function_declaration")
        for node in func_declarations:
            symbol = self._extract_function(node, source_bytes, file_path, "function")
            if symbol:
                symbols.append(symbol)

        # Arrow functions (variable assignments)
        arrow_funcs = self._find_nodes_by_type(tree.root_node, "arrow_function")
        for node in arrow_funcs:
            # Get variable name if assigned
            parent = node.parent
            if parent and parent.type == "variable_declarator":
                name_node = parent.child_by_field_name("name")
                if name_node:
                    symbol = self._extract_arrow_function(node, name_node, source_bytes, file_path)
                    if symbol:
                        symbols.append(symbol)

        # Class declarations
        class_declarations = self._find_nodes_by_type(tree.root_node, "class_declaration")
        for node in class_declarations:
            symbol = self._extract_class(node, source_bytes, file_path)
            if symbol:
                symbols.append(symbol)

        return symbols

    def _extract_function(self, node, source_bytes: bytes, file_path: str, symbol_type: str) -> Symbol:
        """Extract function symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = self._node_text(name_node, source_bytes)
        params_node = node.child_by_field_name("parameters")
        params = self._node_text(params_node, source_bytes) if params_node else "()"

        signature = f"function {name}{params}"

        return Symbol(
            name=name,
            type=symbol_type,
            signature=signature,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_public=True,
            is_exported=self._is_exported(node),
            file_path=file_path
        )

    def _extract_arrow_function(self, node, name_node, source_bytes: bytes, file_path: str) -> Symbol:
        """Extract arrow function symbol."""
        name = self._node_text(name_node, source_bytes)
        params_node = node.child_by_field_name("parameters") or node.child_by_field_name("parameter")

        if params_node:
            params = self._node_text(params_node, source_bytes)
        else:
            params = "()"

        signature = f"const {name} = {params} =>"

        return Symbol(
            name=name,
            type="function",
            signature=signature,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_public=True,
            is_exported=self._is_exported(node.parent.parent),
            file_path=file_path
        )

    def _extract_class(self, node, source_bytes: bytes, file_path: str) -> Symbol:
        """Extract class symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = self._node_text(name_node, source_bytes)
        signature = f"class {name}"

        return Symbol(
            name=name,
            type="class",
            signature=signature,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_public=True,
            is_exported=self._is_exported(node),
            file_path=file_path
        )

    def _is_exported(self, node) -> bool:
        """Check if node is exported."""
        if not node:
            return False

        # Check for export keyword
        parent = node.parent
        while parent:
            if parent.type in ["export_statement", "export_specifier"]:
                return True
            parent = parent.parent

        return False

    def _extract_imports(self, node, source_bytes: bytes) -> List[str]:
        """Extract import statements."""
        imports = []
        import_nodes = self._find_nodes_by_type(node, "import_statement")

        for imp_node in import_nodes:
            import_text = self._node_text(imp_node, source_bytes).strip()
            imports.append(import_text)

        return imports

    def _extract_calls(self, node, source_bytes: bytes) -> List[str]:
        """Extract function calls."""
        calls = []
        call_nodes = self._find_nodes_by_type(node, "call_expression")

        for call_node in call_nodes:
            func_node = call_node.child_by_field_name("function")
            if func_node:
                func_name = self._node_text(func_node, source_bytes).strip()
                if func_name:
                    calls.append(func_name)

        return list(set(calls))
