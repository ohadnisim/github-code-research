#!/bin/bash

# Quick Start Script for GitHub Code Research MCP Server
# This script helps you get started quickly

set -e

echo "=================================="
echo "GitHub Code Research MCP Server"
echo "Quick Start Installation"
echo "=================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "   ✓ Found Python $PYTHON_VERSION"

    # Check if version is 3.10+
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        echo "   ✗ Error: Python 3.10 or higher required"
        echo "   Please install Python 3.10+ and try again"
        exit 1
    fi
else
    echo "   ✗ Error: python3 not found"
    echo "   Please install Python 3.10+ and try again"
    exit 1
fi

echo ""

# Check if virtual environment exists
echo "2. Setting up virtual environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo "   ✓ Virtual environment already exists"
fi

echo ""

# Activate virtual environment
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Virtual environment activated"

echo ""

# Install package
echo "4. Installing package..."
pip install -e . > /dev/null 2>&1
echo "   ✓ Package installed"

echo ""

# Check for GitHub token
echo "5. Checking GitHub token..."
if [ -z "$GITHUB_TOKEN" ]; then
    echo "   ! GitHub token not found in environment"
    echo ""
    echo "   Please set your GitHub token:"
    echo "   export GITHUB_TOKEN=ghp_your_token_here"
    echo ""
    echo "   Get a token from: https://github.com/settings/tokens"
    echo "   Required scope: public_repo"
    echo ""
    read -p "   Do you want to enter it now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "   Enter your GitHub token: " TOKEN
        export GITHUB_TOKEN=$TOKEN
        echo "   ✓ Token set for this session"
    else
        echo "   ! Warning: Server will not work without a token"
    fi
else
    echo "   ✓ GitHub token found"
fi

echo ""

# Test installation
echo "6. Testing installation..."
python3 -c "from github_code_research import __version__; print(f'   ✓ Version {__version__} installed')" 2>&1

echo ""
echo "=================================="
echo "Installation Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. If you haven't set GITHUB_TOKEN, do it now:"
echo "   export GITHUB_TOKEN=ghp_your_token_here"
echo ""
echo "2. Test the server (press Ctrl+C to stop):"
echo "   python3 -m github_code_research"
echo ""
echo "3. Configure Claude Desktop:"
echo "   Edit: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "   Add:"
echo '   {'
echo '     "mcpServers": {'
echo '       "github-code-research": {'
echo '         "command": "'$(which python3)'",'
echo '         "args": ["-m", "github_code_research"],'
echo '         "env": {'
echo '           "GITHUB_TOKEN": "ghp_your_token_here"'
echo '         }'
echo '       }'
echo '     }'
echo '   }'
echo ""
echo "4. Read the documentation:"
echo "   - README.md - Overview and features"
echo "   - INSTALLATION.md - Detailed installation guide"
echo "   - USAGE_EXAMPLES.md - Usage examples"
echo ""
echo "Happy coding! 🚀"
echo ""
