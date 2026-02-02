"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_github_token():
    """Mock GitHub token for tests."""
    return "ghp_test_token_1234567890abcdefghijklmnop"


@pytest.fixture
def sample_python_code():
    """Sample Python code for parser tests."""
    return '''
def hello_world():
    """Say hello."""
    print("Hello, World!")

class MyClass:
    """A sample class."""

    def __init__(self, name):
        self.name = name

    def greet(self):
        """Greet by name."""
        return f"Hello, {self.name}!"

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b
'''


@pytest.fixture
def sample_javascript_code():
    """Sample JavaScript code for parser tests."""
    return '''
function helloWorld() {
    console.log("Hello, World!");
}

class MyClass {
    constructor(name) {
        this.name = name;
    }

    greet() {
        return `Hello, ${this.name}!`;
    }
}

const calculateSum = (a, b) => {
    return a + b;
};

export { helloWorld, MyClass, calculateSum };
'''


@pytest.fixture
def sample_typescript_code():
    """Sample TypeScript code for parser tests."""
    return '''
interface Person {
    name: string;
    age: number;
}

function helloWorld(): void {
    console.log("Hello, World!");
}

class MyClass {
    private name: string;

    constructor(name: string) {
        this.name = name;
    }

    public greet(): string {
        return `Hello, ${this.name}!`;
    }
}

const calculateSum = (a: number, b: number): number => {
    return a + b;
};

export { helloWorld, MyClass, calculateSum };
'''
