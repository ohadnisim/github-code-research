"""TypeScript parser using tree-sitter."""

from tree_sitter_languages import get_parser

from .javascript_parser import JavaScriptParser


class TypeScriptParser(JavaScriptParser):
    """Parser for TypeScript code (extends JavaScript parser)."""

    def __init__(self):
        """Initialize TypeScript parser."""
        # Call BaseParser.__init__ instead of JavaScriptParser.__init__
        super(JavaScriptParser, self).__init__("typescript")
        self.parser = get_parser("typescript")
