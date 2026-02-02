# Installation Guide

Complete step-by-step installation instructions for the GitHub Code Research MCP Server.

## Prerequisites

### Required
- Python 3.10 or higher
- pip (Python package manager)
- GitHub Personal Access Token

### System Requirements
- macOS, Linux, or Windows with WSL
- 100MB free disk space
- Internet connection

## Quick Start

```bash
# 1. Clone or download the repository
cd github-code-research

# 2. Install the package
pip install -e .

# 3. Set up your GitHub token
export GITHUB_TOKEN=ghp_your_token_here

# 4. Test the installation
python3 -m github_code_research --help
```

## Detailed Installation

### Step 1: Verify Python Version

```bash
python3 --version
```

You should see Python 3.10 or higher. If not, install a newer version:

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip
```

**Windows:**
Download from https://www.python.org/downloads/

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install the Package

```bash
# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Step 4: Get GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "GitHub Code Research MCP"
4. Select scopes:
   - ✅ `public_repo` (access public repositories)
   - ✅ `read:org` (optional, for organization repos)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

### Step 5: Configure Authentication

Choose one of these methods:

#### Method A: Environment Variable (Recommended for testing)

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Add to your shell profile (~/.bashrc, ~/.zshrc) to make it permanent:
```bash
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.zshrc
source ~/.zshrc
```

#### Method B: Configuration File (Recommended for production)

```bash
cp config.example.json config.json
```

Edit `config.json`:
```json
{
  "github_token": "ghp_your_token_here",
  "max_search_results": 10,
  "cache_dir": ".cache",
  "log_level": "INFO"
}
```

#### Method C: .env File

```bash
cp .env.example .env
```

Edit `.env`:
```
GITHUB_TOKEN=ghp_your_token_here
MAX_SEARCH_RESULTS=10
CACHE_DIR=.cache
LOG_LEVEL=INFO
```

### Step 6: Verify Installation

```bash
# Test import
python3 -c "from github_code_research import __version__; print(__version__)"

# Should output: 0.1.0
```

## Claude Desktop Integration

### Step 1: Locate Configuration File

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Add MCP Server Configuration

Edit the configuration file:

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

Or if using a virtual environment:

```json
{
  "mcpServers": {
    "github-code-research": {
      "command": "/path/to/venv/bin/python3",
      "args": ["-m", "github_code_research"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

### Step 4: Verify in Claude

Open Claude Desktop and try:
```
Search for "hello world" in Python
```

You should see the MCP server respond with search results!

## Troubleshooting

### Import Error: No module named 'mcp'

```bash
pip install mcp
```

### Import Error: No module named 'tree_sitter'

```bash
pip install tree-sitter tree-sitter-languages
```

### Authentication Error

Verify your token:
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
```

Should return your GitHub user info.

### Command Not Found: github-code-research

Install in editable mode:
```bash
pip install -e .
```

Or use the module form:
```bash
python3 -m github_code_research
```

### Permission Denied

On macOS/Linux, you might need to make files executable:
```bash
chmod +x src/github_code_research/__main__.py
```

### Claude Desktop Not Connecting

1. Check the configuration file path
2. Verify JSON syntax (use https://jsonlint.com/)
3. Check logs in Claude Desktop (Help → View Logs)
4. Restart Claude Desktop completely

## Updating

To update to a newer version:

```bash
cd github-code-research
git pull  # if using git
pip install -e . --upgrade
```

## Uninstalling

```bash
pip uninstall github-code-research
```

To completely remove:
```bash
rm -rf .cache
rm config.json
rm .env
```

## Development Installation

For contributors:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Docker Installation (Advanced)

Create a Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -e .

ENV GITHUB_TOKEN=""

CMD ["python3", "-m", "github_code_research"]
```

Build and run:
```bash
docker build -t github-code-research .
docker run -e GITHUB_TOKEN=your_token github-code-research
```

## Next Steps

After installation:
1. Read [README.md](README.md) for feature overview
2. Check [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for usage examples
3. Start researching code with Claude!

## Support

If you encounter issues:
1. Check this guide first
2. Review the troubleshooting section
3. Check GitHub issues
4. Create a new issue with:
   - Your Python version
   - Installation method
   - Error messages
   - Steps to reproduce
