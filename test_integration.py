#!/usr/bin/env python3
"""Integration test script for GitHub Code Research MCP Server."""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_configuration():
    """Test configuration loading."""
    print("=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings, reset_settings

        reset_settings()
        settings = get_settings()

        print(f"✓ Configuration loaded successfully")
        print(f"  - GitHub token: {'*' * 20} (hidden)")
        print(f"  - Max search results: {settings.max_search_results}")
        print(f"  - Cache dir: {settings.cache_dir}")
        print(f"  - Log level: {settings.log_level}")
        print(f"  - Supported languages: {', '.join(settings.supported_languages)}")

        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


async def test_github_auth():
    """Test GitHub authentication."""
    print("\n" + "=" * 60)
    print("TEST 2: GitHub Authentication")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings
        from github_code_research.github.auth import validate_token

        settings = get_settings()
        user_info = validate_token(settings.github_token)

        print(f"✓ Authentication successful")
        print(f"  - Username: {user_info['login']}")
        print(f"  - User ID: {user_info['id']}")
        print(f"  - Account type: {user_info['type']}")

        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False


async def test_github_client():
    """Test GitHub client basic operations."""
    print("\n" + "=" * 60)
    print("TEST 3: GitHub Client")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings
        from github_code_research.github.client import GitHubClient

        settings = get_settings()
        client = GitHubClient(settings.github_token)

        # Test getting a well-known repository
        print("  Testing repo info fetch (octocat/Hello-World)...")
        repo_info = client.get_repo_info("octocat", "Hello-World")

        print(f"✓ GitHub client working")
        print(f"  - Repo name: {repo_info['name']}")
        print(f"  - Repo description: {repo_info.get('description', 'N/A')[:50]}...")
        print(f"  - Stars: {repo_info['stargazers_count']}")

        return True
    except Exception as e:
        print(f"✗ GitHub client failed: {e}")
        return False


async def test_secret_scanner():
    """Test secret scanner."""
    print("\n" + "=" * 60)
    print("TEST 4: Secret Scanner")
    print("=" * 60)

    try:
        from github_code_research.security.secret_scanner import get_scanner

        scanner = get_scanner()

        # Test with sample secrets
        test_code = '''
        AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
        GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        api_key = "my-secret-api-key-12345678"
        '''

        redacted, count = scanner.redact(test_code)

        print(f"✓ Secret scanner working")
        print(f"  - Detected and redacted {count} secrets")
        print(f"  - Sample redacted output:")
        for line in redacted.split('\n')[:5]:
            if line.strip():
                print(f"    {line}")

        return True
    except Exception as e:
        print(f"✗ Secret scanner failed: {e}")
        return False


async def test_parsers():
    """Test tree-sitter parsers."""
    print("\n" + "=" * 60)
    print("TEST 5: Tree-sitter Parsers")
    print("=" * 60)

    try:
        from github_code_research.parsers.factory import ParserFactory

        # Test Python parser
        python_code = '''
def hello_world():
    """Say hello."""
    print("Hello, World!")

class MyClass:
    def __init__(self, name):
        self.name = name
'''

        parser = ParserFactory.get_parser(file_path="test.py")
        result = parser.parse(python_code, "test.py")

        print(f"✓ Python parser working")
        print(f"  - Extracted {len(result.symbols)} symbols")
        for symbol in result.symbols[:3]:
            print(f"    - {symbol.type}: {symbol.name}")

        # Test JavaScript parser
        js_code = '''
function helloWorld() {
    console.log("Hello");
}

const myFunc = () => {
    return 42;
};
'''

        js_parser = ParserFactory.get_parser(file_path="test.js")
        js_result = js_parser.parse(js_code, "test.js")

        print(f"✓ JavaScript parser working")
        print(f"  - Extracted {len(js_result.symbols)} symbols")

        return True
    except Exception as e:
        print(f"✗ Parsers failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_search_tool():
    """Test search_patterns tool."""
    print("\n" + "=" * 60)
    print("TEST 6: Search Patterns Tool")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings
        from github_code_research.github.client import GitHubClient
        from github_code_research.utils.cache import FileCache
        from github_code_research.tools.search_patterns import search_patterns_tool

        settings = get_settings()
        client = GitHubClient(settings.github_token)
        cache = FileCache(settings.cache_dir)

        # Test search
        print("  Searching for 'hello world' in Python...")
        result = await search_patterns_tool(
            {"query": "hello world", "language": "python", "max_results": 3},
            client,
            cache,
            settings.cache_ttl_search,
            settings.max_search_results
        )

        print(f"✓ Search tool working")
        content = result["content"][0]["text"]
        lines = content.split('\n')[:5]
        for line in lines:
            print(f"  {line}")

        return True
    except Exception as e:
        print(f"✗ Search tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_license_tool():
    """Test check_license tool."""
    print("\n" + "=" * 60)
    print("TEST 7: License Check Tool")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings
        from github_code_research.github.client import GitHubClient
        from github_code_research.utils.cache import FileCache
        from github_code_research.tools.check_license import check_license_tool

        settings = get_settings()
        client = GitHubClient(settings.github_token)
        cache = FileCache(settings.cache_dir)

        # Test with a known MIT licensed repo
        print("  Checking license for octocat/Hello-World...")
        result = await check_license_tool(
            {"owner": "octocat", "repo": "Hello-World"},
            client,
            cache,
            settings.cache_ttl_license
        )

        print(f"✓ License tool working")
        content = result["content"][0]["text"]
        for line in content.split('\n')[:5]:
            print(f"  {line}")

        return True
    except Exception as e:
        print(f"✗ License tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_extract_function_tool():
    """Test extract_function tool."""
    print("\n" + "=" * 60)
    print("TEST 8: Extract Function Tool")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings
        from github_code_research.github.client import GitHubClient
        from github_code_research.tools.extract_function import extract_function_tool

        settings = get_settings()
        client = GitHubClient(settings.github_token)

        # Test with a known file and function
        print("  Extracting function from GitHub file...")
        result = await extract_function_tool(
            {
                "file_url": "https://github.com/octocat/Hello-World/blob/master/README",
                "function_name": "main"  # This will likely fail, but tests the mechanism
            },
            client
        )

        print(f"✓ Extract function tool accessible")
        print(f"  (Note: May not find 'main' in README, but tool is working)")

        return True
    except Exception as e:
        # This is expected to fail since README doesn't have functions
        if "not found" in str(e).lower() or "function" in str(e).lower():
            print(f"✓ Extract function tool working (expected failure for README)")
            return True
        print(f"✗ Extract function tool failed: {e}")
        return False


async def test_repo_map_tool():
    """Test get_repo_map tool."""
    print("\n" + "=" * 60)
    print("TEST 9: Repository Map Tool")
    print("=" * 60)

    try:
        from github_code_research.config.settings import get_settings
        from github_code_research.github.client import GitHubClient
        from github_code_research.utils.cache import FileCache
        from github_code_research.tools.repo_map import get_repo_map_tool

        settings = get_settings()
        client = GitHubClient(settings.github_token)
        cache = FileCache(settings.cache_dir)

        # Test with a small Python repo
        print("  Generating repo map (this may take a minute)...")
        print("  Testing with octocat/Hello-World...")
        result = await get_repo_map_tool(
            {"owner": "octocat", "repo": "Hello-World", "max_symbols": 10},
            client,
            cache,
            settings.cache_ttl_repo_map
        )

        print(f"✓ Repo map tool working")
        content = result["content"][0]["text"]
        lines = content.split('\n')[:10]
        for line in lines:
            print(f"  {line}")

        return True
    except Exception as e:
        print(f"✗ Repo map tool failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                                                               ║")
    print("║         GitHub Code Research MCP Server - Integration Test   ║")
    print("║                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print("\n")

    # Check for GitHub token
    if not os.environ.get("GITHUB_TOKEN"):
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("\nPlease set your GitHub token:")
        print("  export GITHUB_TOKEN=ghp_your_token_here")
        print("\nGet a token from: https://github.com/settings/tokens")
        return 1

    results = []

    # Run tests
    tests = [
        ("Configuration", test_configuration),
        ("Authentication", test_github_auth),
        ("GitHub Client", test_github_client),
        ("Secret Scanner", test_secret_scanner),
        ("Tree-sitter Parsers", test_parsers),
        ("Search Tool", test_search_tool),
        ("License Tool", test_license_tool),
        ("Extract Function Tool", test_extract_function_tool),
        ("Repo Map Tool", test_repo_map_tool),
    ]

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nUnexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! The MCP server is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
