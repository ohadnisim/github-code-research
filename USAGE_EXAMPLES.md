# Usage Examples

This document provides detailed examples of using the GitHub Code Research MCP Server with Claude Desktop.

## Setup

1. Install the package:
```bash
cd github-code-research
pip install -e .
```

2. Get your GitHub token from https://github.com/settings/tokens

3. Configure Claude Desktop by editing `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "github-code-research": {
      "command": "python",
      "args": ["-m", "github_code_research"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

4. Restart Claude Desktop

## Example Queries

### Code Search Examples

**Find authentication patterns:**
```
Search for "oauth authentication" patterns in Python
```

**Find specific decorators:**
```
Search for fastapi route decorators
```

**Find error handling patterns:**
```
Search for try-except patterns in Python with max 20 results
```

**Language-specific search:**
```
Find dependency injection examples in TypeScript
```

### Repository Map Examples

**Explore a popular framework:**
```
Generate a repository map for fastapi/fastapi showing the top 30 symbols
```

**Understand project structure:**
```
Show me the most important functions and classes in django/django
```

**Quick overview:**
```
What are the key components of flask/flask?
```

### Function Extraction Examples

**Extract specific function:**
```
Extract the "create_app" function from https://github.com/pallets/flask/blob/main/src/flask/app.py
```

**Study implementation:**
```
Show me how the "route" decorator is implemented in FastAPI
```

**Extract with URL:**
```
Extract the function "authenticate_user" from this file: https://github.com/owner/repo/blob/main/auth.py
```

### License Checking Examples

**Check if safe to use:**
```
Is it safe to use code from facebook/react?
```

**Check specific repo:**
```
Check the license for tensorflow/tensorflow
```

**Multiple checks:**
```
Check licenses for these repos:
- fastapi/fastapi
- django/django
- flask/flask
```

## Advanced Usage

### Combining Tools

**Research and understand a repo:**
```
1. First, check the license for fastapi/fastapi
2. Then generate a repo map for fastapi/fastapi
3. Extract the main application setup function
```

**Find and extract:**
```
1. Search for "authentication middleware" in Python
2. Extract the authentication function from the best result
```

### Working with Large Repositories

**Focus on important symbols:**
```
Generate a repo map for tensorflow/tensorflow with max 100 symbols
```

**Targeted search:**
```
Search for "model training" in Python language in tensorflow/tensorflow repository
```

## Tips and Best Practices

1. **Start with repository maps** to understand project structure
2. **Use license checking** before diving deep into a repo
3. **Be specific in searches** to avoid rate limits
4. **Combine tools** for comprehensive research
5. **Cache is automatic** - repeated queries are fast

## Rate Limit Management

The server automatically manages GitHub API rate limits:

- **Code Search**: 30 requests/minute
- **General API**: 5000 requests/hour

Tips to stay within limits:
- Use caching (automatic)
- Be specific with queries
- Limit search results when possible
- Space out large operations

## Troubleshooting

### No Results Found

If searches return no results:
- Try broader search terms
- Check if the repository is public
- Verify your GitHub token has proper permissions

### Rate Limit Exceeded

If you hit rate limits:
- Wait for the reset time (shown in error)
- Cached results will still work
- Consider upgrading to GitHub Pro for higher limits

### Parser Not Found

If a file can't be parsed:
- Check if the language is supported (Python, JS, TS)
- The tool will fall back to regex-based extraction
- Consider requesting support for additional languages

## Example Workflow: Learning a New Framework

```
User: I want to learn how FastAPI works

1. "Check the license for fastapi/fastapi"
   → MIT license, safe to use

2. "Generate a repository map for fastapi/fastapi with top 50 symbols"
   → Shows key classes and functions

3. "Search for 'route decorator' in fastapi"
   → Find examples of route definitions

4. "Extract the 'APIRouter' class from the main file"
   → See the implementation details
```

## Example Workflow: Security Research

```
User: I need to implement authentication

1. "Search for 'jwt authentication' in Python"
   → Find implementations (secrets redacted)

2. "Check licenses for the top 3 repos"
   → Verify they're safe to reference

3. "Generate repo maps for the safest option"
   → Understand the architecture

4. "Extract specific auth functions"
   → Study the implementation
```

## Integration with Other Tools

The MCP server works great with:
- Claude Desktop for AI-assisted research
- Your IDE for quick lookups
- Documentation workflows
- Code review processes

## Privacy and Security

- All secrets are automatically redacted
- No code is stored permanently (cache is local)
- GitHub token is only used for API access
- All operations are read-only
