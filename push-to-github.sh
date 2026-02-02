#!/bin/bash

# Script to push to GitHub
# Run this AFTER creating the repository on GitHub

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         Push GitHub Code Research to GitHub                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if username is provided
if [ -z "$1" ]; then
    echo "❌ Error: GitHub username required"
    echo ""
    echo "Usage: ./push-to-github.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "Example: ./push-to-github.sh ohadnisim"
    exit 1
fi

USERNAME=$1
REPO_URL="https://github.com/$USERNAME/github-code-research.git"

echo "📋 Configuration:"
echo "   Username: $USERNAME"
echo "   Repository: $REPO_URL"
echo ""

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    echo "ℹ️  Remote 'origin' already exists, removing..."
    git remote remove origin
fi

echo "🔗 Adding remote..."
git remote add origin "$REPO_URL"

echo "📌 Setting main branch..."
git branch -M main

echo "🚀 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ SUCCESS!                                ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🎉 Your repository is now live at:"
    echo "   https://github.com/$USERNAME/github-code-research"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Visit your repo and check it looks good"
    echo "   2. Add topics: mcp, ai, github, code-search, claude"
    echo "   3. Share it with the community!"
    echo ""
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Common issues:"
    echo "   1. Repository doesn't exist on GitHub yet"
    echo "      → Go to https://github.com/new and create it"
    echo ""
    echo "   2. Authentication failed"
    echo "      → Run: git config --global credential.helper osxkeychain"
    echo ""
    echo "   3. Repository name is wrong"
    echo "      → Make sure it's named 'github-code-research'"
fi
