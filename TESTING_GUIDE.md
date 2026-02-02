# Testing Guide

## Quick Test

To test the GitHub Code Research MCP Server with your GitHub token:

### Step 1: Get a GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "MCP Server Test"
4. Select scope: **public_repo** (required)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### Step 2: Set Up Environment

```bash
cd github-code-research

# Set your GitHub token (replace with your actual token)
export GITHUB_TOKEN=ghp_your_actual_token_here

# Verify it's set
echo $GITHUB_TOKEN
```

### Step 3: Run Integration Tests

```bash
# Run the comprehensive integration test
python3 test_integration.py
```

This will test:
1. ✓ Configuration loading
2. ✓ GitHub authentication
3. ✓ GitHub API client
4. ✓ Secret scanner
5. ✓ Tree-sitter parsers
6. ✓ Search patterns tool
7. ✓ License checking tool
8. ✓ Function extraction tool
9. ✓ Repository mapping tool

### Step 4: Test Individual Components

If you want to test specific components:

```bash
# Test configuration only
python3 -c "
from github_code_research.config.settings import get_settings
settings = get_settings()
print(f'Config loaded: {settings.max_search_results} max results')
"

# Test authentication
python3 -c "
from github_code_research.config.settings import get_settings
from github_code_research.github.auth import validate_token
settings = get_settings()
user = validate_token(settings.github_token)
print(f'Authenticated as: {user[\"login\"]}')
"

# Test parser
python3 -c "
from github_code_research.parsers.factory import ParserFactory
parser = ParserFactory.get_parser(file_path='test.py')
result = parser.parse('def hello(): pass', 'test.py')
print(f'Parsed {len(result.symbols)} symbols')
"
```

### Expected Output

If everything works correctly, you should see:

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         GitHub Code Research MCP Server - Integration Test   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

============================================================
TEST 1: Configuration Loading
============================================================
✓ Configuration loaded successfully
  - GitHub token: ******************** (hidden)
  - Max search results: 10
  - Cache dir: .cache
  - Log level: INFO
  - Supported languages: python, javascript, typescript, go

============================================================
TEST 2: GitHub Authentication
============================================================
✓ Authentication successful
  - Username: your-username
  - User ID: 12345678
  - Account type: User

... [more tests] ...

============================================================
TEST SUMMARY
============================================================
✓ PASS     - Configuration
✓ PASS     - Authentication
✓ PASS     - GitHub Client
✓ PASS     - Secret Scanner
✓ PASS     - Tree-sitter Parsers
✓ PASS     - Search Tool
✓ PASS     - License Tool
✓ PASS     - Extract Function Tool
✓ PASS     - Repo Map Tool

============================================================
Results: 9/9 tests passed
============================================================

🎉 All tests passed! The MCP server is ready to use.
```

## Troubleshooting

### Error: "GITHUB_TOKEN environment variable not set"

Make sure you've exported the token:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### Error: "Invalid GitHub token"

1. Check that you copied the token correctly
2. Verify the token hasn't expired
3. Ensure it has the `public_repo` scope

### Error: "Rate limit exceeded"

Wait a few minutes and try again. The tests make several API calls.

### Error: "No module named 'mcp'"

Install dependencies:
```bash
pip install -e .
```

### Error: "No module named 'tree_sitter'"

Install tree-sitter:
```bash
pip install tree-sitter tree-sitter-languages
```

## Testing with Claude Desktop

After the integration tests pass:

1. Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "github-code-research": {
      "command": "python3",
      "args": ["-m", "github_code_research"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

2. Restart Claude Desktop

3. Try these queries:
   - "Search for hello world in Python"
   - "Check the license for octocat/Hello-World"
   - "Generate a repo map for a small Python repository"

## Manual Testing

If you prefer manual testing:

```bash
# Start the server
export GITHUB_TOKEN=ghp_your_token_here
python3 -m github_code_research

# The server will wait for MCP messages
# You can test it via Claude Desktop or another MCP client
```

## Security Note

**Never commit your GitHub token!**

The `.gitignore` file is configured to ignore:
- `.env` files
- `config.json` files

Always use environment variables or config files that are gitignored.
