# 🚀 Quick Start Guide

This guide will help you get the MCP Codebase Analyser up and running in 5 minutes.

## Step 1: Setup Environment

1. **Copy the environment file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` with your credentials:**
   
   **Minimum required (OpenAI):**
   ```env
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-your-openai-api-key-here
   ```

   **Optional but recommended:**
   ```env
   GITHUB_TOKEN=your_github_token_here
   ```
   
   Get a GitHub token at: https://github.com/settings/tokens
   - Select scope: `repo` (for private repos) or leave blank for public only

## Step 2: Start the Server

### Using Docker (Recommended)

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f

# You should see:
# "Initialized embedding system with openai provider"
# "All components initialized successfully"
```

### Using Local Python (Alternative)

```bash
# Install dependencies
pip install uv
uv pip install -e .

# Run server
uv run src/main.py
```

## Step 3: Configure Cursor

### Option A: Via Cursor UI

1. Open **Cursor Settings** → **MCP Settings**
2. Click **"Add Server"**
3. Enter:
   - **Name:** `codebase-analyser`
   - **URL:** `http://localhost:8050/sse`
   - **Transport:** `SSE`

### Option B: Manual Configuration

Create or edit: `~/.cursor/mcp_settings.json`

```json
{
  "mcpServers": {
    "codebase-analyser": {
      "url": "http://localhost:8050/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

### Restart Cursor

Close and reopen Cursor for changes to take effect.

## Step 4: Test It Out! 🎉

In Cursor, try these commands:

### Example 1: Analyze a repository
```
Analyze the vercel/next.js repository
```

### Example 2: Find a section
```
I need to add a hero section with a call-to-action button. 
Check the jolly-sections repository and tell me which section to use.
```

### Example 3: Search for patterns
```
Show me authentication code in a repository
```

## Troubleshooting

### ❌ "Server not responding"
- Check if running: `docker-compose ps`
- Check logs: `docker-compose logs -f`
- Restart: `docker-compose restart`

### ❌ "Authentication failed"
- Verify `LLM_API_KEY` in `.env`
- Check OpenAI account has credits
- Test key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### ❌ "Can't clone repository"
- For private repos, add `GITHUB_TOKEN` to `.env`
- Verify token has `repo` scope
- Check repository name format: `owner/repo`

### ❌ "Cursor can't connect to MCP"
- Verify server is running on port 8050
- Check firewall settings
- Try `http://127.0.0.1:8050/sse` instead of `localhost`

## Common Use Cases

### Use Case 1: Find Similar Code
```
I want to implement a pricing table with toggle between monthly/yearly plans.
Check the stripe/stripe-react repository and recommend the best section.
```

### Use Case 2: Understand Repository Structure
```
What sections are available in the shadcn/ui repository?
```

### Use Case 3: Feature Discovery
```
I need to add dark mode toggle. Search the tailwindcss/tailwindcss repository
and tell me where to look.
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [Architecture](README.md#-architecture) to understand how it works
- Explore [all available tools](README.md#-available-mcp-tools)

---

**Need help?** Open an issue on GitHub!

