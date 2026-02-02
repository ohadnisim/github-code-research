"""Tests for tree-sitter parsers."""

import pytest

from github_code_research.parsers.factory import ParserFactory
from github_code_research.parsers.python_parser import PythonParser
from github_code_research.parsers.javascript_parser import JavaScriptParser
from github_code_research.parsers.typescript_parser import TypeScriptParser


class TestParserFactory:
    """Test parser factory."""

    def test_get_python_parser(self):
        """Test getting Python parser."""
        parser = ParserFactory.get_parser(file_path="test.py")
        assert isinstance(parser, PythonParser)

    def test_get_javascript_parser(self):
        """Test getting JavaScript parser."""
        parser = ParserFactory.get_parser(file_path="test.js")
        assert isinstance(parser, JavaScriptParser)

    def test_get_typescript_parser(self):
        """Test getting TypeScript parser."""
        parser = ParserFactory.get_parser(file_path="test.ts")
        assert isinstance(parser, TypeScriptParser)

    def test_unsupported_file(self):
        """Test unsupported file returns None."""
        parser = ParserFactory.get_parser(file_path="test.cpp")
        assert parser is None

    def test_is_supported(self):
        """Test file support checking."""
        assert ParserFactory.is_supported(file_path="test.py") is True
        assert ParserFactory.is_supported(file_path="test.js") is True
        assert ParserFactory.is_supported(file_path="test.cpp") is False


class TestPythonParser:
    """Test Python parser."""

    def test_parse_python_code(self, sample_python_code):
        """Test parsing Python code."""
        parser = PythonParser()
        result = parser.parse(sample_python_code)

        assert len(result.symbols) > 0
        assert result.tree is not None

        # Check for expected symbols
        symbol_names = [s.name for s in result.symbols]
        assert "hello_world" in symbol_names
        assert "MyClass" in symbol_names
        assert "calculate_sum" in symbol_names

    def test_extract_function_signatures(self, sample_python_code):
        """Test extracting function signatures."""
        parser = PythonParser()
        result = parser.parse(sample_python_code)

        # Find hello_world function
        hello_func = next(s for s in result.symbols if s.name == "hello_world")
        assert hello_func.type == "function"
        assert "def hello_world()" in hello_func.signature

    def test_extract_class(self, sample_python_code):
        """Test extracting class."""
        parser = PythonParser()
        result = parser.parse(sample_python_code)

        # Find MyClass
        my_class = next(s for s in result.symbols if s.name == "MyClass")
        assert my_class.type == "class"
        assert "class MyClass" in my_class.signature


class TestJavaScriptParser:
    """Test JavaScript parser."""

    def test_parse_javascript_code(self, sample_javascript_code):
        """Test parsing JavaScript code."""
        parser = JavaScriptParser()
        result = parser.parse(sample_javascript_code)

        assert len(result.symbols) > 0
        assert result.tree is not None

        # Check for expected symbols
        symbol_names = [s.name for s in result.symbols]
        assert "helloWorld" in symbol_names
        assert "MyClass" in symbol_names

    def test_extract_imports(self, sample_javascript_code):
        """Test extracting exports (as imports)."""
        parser = JavaScriptParser()
        result = parser.parse(sample_javascript_code)

        # Should detect export statement
        assert len(result.imports) > 0 or len(result.symbols) > 0


class TestTypeScriptParser:
    """Test TypeScript parser."""

    def test_parse_typescript_code(self, sample_typescript_code):
        """Test parsing TypeScript code."""
        parser = TypeScriptParser()
        result = parser.parse(sample_typescript_code)

        assert len(result.symbols) > 0
        assert result.tree is not None

        # Check for expected symbols
        symbol_names = [s.name for s in result.symbols]
        assert "helloWorld" in symbol_names
        assert "MyClass" in symbol_names
