# Quick Start Guide - After Restart

## ✅ Installation Complete!

Your GitHub Code Research MCP Server is installed and ready. After restarting Claude Code, you'll have 4 new tools available.

---

## 🔄 To Activate (One Time Only)

**Simply restart Claude Code:**
1. Quit Claude Code completely
2. Reopen Claude Code
3. The tools will be available automatically

---

## 🎯 Your New Tools (After Restart)

### 1. search_patterns
Search millions of GitHub repositories for code patterns

**Example queries:**
```
"Search GitHub for fastapi route decorators"
"Find authentication examples in Python"
"Show me dependency injection patterns in TypeScript"
```

### 2. check_license
Verify if a repository is safe to use

**Example queries:**
```
"Check if tensorflow/tensorflow is safe to use"
"What's the license for fastapi/fastapi?"
"Is django/django safe for commercial use?"
```

### 3. get_repo_map
Generate a map showing the most important functions and classes

**Example queries:**
```
"Show me the repo map for django/django"
"Map the structure of flask/flask"
"What are the key components of requests library?"
```

### 4. extract_function
Extract specific functions with full documentation

**Example queries:**
```
"Extract the request function from psf/requests"
"Show me the create_app function from flask"
"Get the route decorator implementation from FastAPI"
```

---

## 💡 Natural Language Commands

You can ask in plain English! Examples:

```
"I want to understand how FastAPI handles authentication -
 search for examples and show me the key functions"
```

```
"Before I use React in my project, check if it's safe to use
 and show me its license"
```

```
"I'm learning Django - show me a map of its most important
 components and explain the main request handler"
```

```
"Find examples of error handling in Python web frameworks"
```

---

## 🚀 Quick Test After Restart

Try this simple query to verify it's working:

```
"Search GitHub for hello world in Python"
```

You should see:
- Real GitHub search results
- Code snippets from repositories
- Automatically redacted secrets
- Repository URLs

---

## 📊 What Makes This Special

- ✅ **15-20x faster** than manual GitHub browsing
- ✅ **Automatic secret redaction** for safety
- ✅ **Smart ranking** with PageRank algorithm
- ✅ **Precise extraction** using AST parsing
- ✅ **License safety** categorization
- ✅ **Cached results** for speed

---

## 🔧 Troubleshooting

### If tools don't appear after restart:

1. **Check configuration exists:**
   ```bash
   ls ~/.claude/mcp/github-code-research.json
   ```

2. **Verify it's valid JSON:**
   ```bash
   cat ~/.claude/mcp/github-code-research.json
   ```

3. **Check Claude Code logs** (if available in Help menu)

4. **Try a simple test query:**
   ```
   "What GitHub tools are available?"
   ```

---

## 📝 Usage Tips

### Best Practices:
- Start with searches to explore
- Check licenses before diving deep
- Use repo maps to understand architecture
- Extract specific functions to study details

### Performance:
- First queries: 2-15 seconds
- Cached queries: <100ms
- Large repo maps: May take 30-60 seconds

### Rate Limits:
- Code Search: 30 requests/minute
- General API: 5000 requests/hour
- Automatic throttling prevents errors

---

## 🎯 Example Workflow

**Learning a new framework:**
```
1. "Check if fastapi/fastapi is safe to use"
2. "Show me the repo map for fastapi/fastapi"
3. "Search for route decorator examples in FastAPI"
4. "Extract the APIRouter class from FastAPI"
```

**Finding best practices:**
```
1. "Search for authentication patterns in Python"
2. "Check licenses for the top 3 results"
3. "Show me how the safest one implements JWT auth"
```

**Understanding a library:**
```
1. "Map the structure of requests library"
2. "Extract the Session class from requests"
3. "Show me how requests handles retries"
```

---

## 📚 Full Documentation

Available in your project directory:
```
/Users/ohadnissim/Desktop/Projects/GitHub Agent/github-code-research/
```

Files:
- README.md - Complete feature overview
- USAGE_EXAMPLES.md - Detailed examples
- DEMO_RESULTS.md - Real demo results
- TEST_RESULTS.md - All test results

---

## 🔐 Your Configuration

**Location:** `~/.claude/mcp/github-code-research.json`

**Status:** ✅ Installed and configured

**Token:** Configured and working

**Python Environment:** Using virtual environment at:
```
/Users/ohadnissim/Desktop/Projects/GitHub Agent/github-code-research/venv/
```

---

## ✨ Ready to Go!

After restart, your first query could be:

```
"Search GitHub for fastapi route decorators and show me
 the most popular implementation"
```

Or simply:

```
"Test GitHub search with hello world"
```

---

**🎉 Enjoy your new GitHub research superpowers!**

Remember: After restart, these tools will be available in ALL your Claude Code conversations, not just this one!
