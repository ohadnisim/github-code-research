# How to Get a GitHub Personal Access Token

## Step-by-Step Guide

### Step 1: Log into GitHub

Go to [GitHub.com](https://github.com) and log into your account.

### Step 2: Go to Settings

Click on your profile picture in the top-right corner → Select **Settings**

### Step 3: Navigate to Developer Settings

1. Scroll down in the left sidebar
2. Click on **Developer settings** (at the very bottom)

### Step 4: Personal Access Tokens

1. In the left sidebar, click **Personal access tokens**
2. Click **Tokens (classic)**

### Step 5: Generate New Token

1. Click the **Generate new token** button
2. Select **Generate new token (classic)**

### Step 6: Configure Your Token

You'll see a form. Fill it out:

**Note (Token name):**
```
GitHub Code Research MCP Server
```

**Expiration:**
- Select: **90 days** (or choose your preferred duration)
- You can always create a new token when it expires

**Select scopes:**

Check these boxes:
- ✅ **repo** (Full control of private repositories)
  - This includes `public_repo` which is what we need
  - If you only want access to public repos, you can select just `public_repo` instead

**Optional but useful:**
- ✅ **read:org** (if you want to access organization repositories)

**Do NOT select:**
- ❌ admin:org (not needed)
- ❌ delete_repo (not needed)
- ❌ admin:public_key (not needed)

### Step 7: Generate Token

1. Scroll to the bottom
2. Click the green **Generate token** button

### Step 8: Copy Your Token

**IMPORTANT:** This is your only chance to see the token!

1. You'll see a green token that starts with `ghp_`
2. Click the copy icon (📋) next to it
3. **Save it somewhere safe immediately**

Example token format:
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 9: Save the Token Securely

**Option A: Save to a file (temporary)**
```bash
# Create a temporary file (DON'T commit this!)
echo "ghp_your_token_here" > ~/.github_token_temp

# Use it in your terminal
export GITHUB_TOKEN=$(cat ~/.github_token_temp)
```

**Option B: Add to your shell profile (permanent)**
```bash
# For bash users
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.bashrc
source ~/.bashrc

# For zsh users (macOS default)
echo 'export GITHUB_TOKEN=ghp_your_token_here' >> ~/.zshrc
source ~/.zshrc
```

**Option C: Create a .env file (recommended)**
```bash
cd github-code-research

# Create .env file
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_your_token_here
EOF

# Load it when needed
source .env  # or use: export $(cat .env)
```

## Quick Access URLs

If you want to go directly to the token creation page:

**Classic tokens:**
https://github.com/settings/tokens/new

**Fine-grained tokens (alternative):**
https://github.com/settings/personal-access-tokens/new

## Token Security Best Practices

### ✅ DO:
- Keep your token secret (like a password)
- Use environment variables or .env files
- Set appropriate expiration dates
- Revoke tokens you're not using
- Use minimal required scopes

### ❌ DON'T:
- Commit tokens to git repositories
- Share tokens publicly
- Use tokens with more permissions than needed
- Keep expired or unused tokens active

## Verifying Your Token

Once you have your token, test it:

```bash
# Set the token
export GITHUB_TOKEN=ghp_your_token_here

# Test it with curl
curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user

# You should see your GitHub user information in JSON format
```

## Revoking a Token (if needed)

If you need to revoke a token:

1. Go to https://github.com/settings/tokens
2. Find your token in the list
3. Click **Delete** next to it
4. Confirm deletion

## Troubleshooting

### "Token doesn't work"

Make sure:
- You copied the entire token (starts with `ghp_`)
- No extra spaces before/after the token
- The token hasn't expired
- You selected the `public_repo` or `repo` scope

### "I lost my token"

You cannot retrieve a lost token. You must:
1. Delete the old token (optional)
2. Create a new token following the steps above

### "Token expired"

Create a new token using the same steps. Tokens expire based on the expiration date you selected.

## What Scopes Do You Need?

For **GitHub Code Research MCP Server**, you need:

**Minimum (recommended):**
- `public_repo` - Access public repositories only

**For private repos:**
- `repo` - Full control of private repositories (includes public_repo)

**Optional:**
- `read:org` - Read organization membership and teams

## Next Steps

Once you have your token:

1. Set it in your environment:
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```

2. Test the MCP server:
   ```bash
   cd github-code-research
   python3 test_integration.py
   ```

3. Configure Claude Desktop:
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

## Still Need Help?

If you're stuck, you can:
1. Check GitHub's official documentation: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
2. Make sure you're logged into GitHub
3. Try using an incognito/private browser window
