# 🎯 COMPLETE STEP-BY-STEP GUIDE
## Get Your MCP Codebase Analyser Running in 10 Minutes

Follow these exact steps. Don't skip any!

---

## ✅ STEP 1: Edit Your Environment File

1. **Open the `.env` file** in your editor:
   ```bash
   open .env
   # Or use your favorite editor: code .env, nano .env, etc.
   ```

2. **You need an OpenAI API key.** Get one here:
   👉 https://platform.openai.com/api-keys
   
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)
   - **IMPORTANT**: Save it somewhere safe (you can't see it again!)

3. **Edit these lines in `.env`:**
   ```env
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-YOUR-ACTUAL-OPENAI-KEY-HERE    # ⬅️ PASTE YOUR KEY HERE
   LLM_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=text-embedding-3-small
   ```

4. **(Optional but recommended)** Get a GitHub token for better rate limits:
   👉 https://github.com/settings/tokens
   
   - Click "Generate new token (classic)"
   - Give it a name: "MCP Codebase Analyser"
   - No scopes needed for public repos (or select "repo" for private repos)
   - Copy the token
   
   Add to `.env`:
   ```env
   GITHUB_TOKEN=ghp_YOUR-GITHUB-TOKEN-HERE    # ⬅️ PASTE YOUR TOKEN HERE
   ```

5. **Save the `.env` file**

**✅ Checkpoint**: Your `.env` file should have at minimum:
- `LLM_API_KEY=sk-...` (your real OpenAI key)
- `LLM_PROVIDER=openai`

---

## ✅ STEP 2: Verify Docker Desktop is Running

1. **Open Docker Desktop application**
   - On macOS: Look for Docker icon in your menu bar (whale icon)
   - Should say "Docker Desktop is running"

2. **If Docker Desktop is not installed:**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install it
   - Launch Docker Desktop
   - Wait until it says "Docker Desktop is running"

3. **Test Docker is working:**
   ```bash
   docker --version
   ```
   
   Should show: `Docker version 24.x.x` or similar

**✅ Checkpoint**: Run `docker ps` - should work without errors

---

## ✅ STEP 3: Build and Start the MCP Server

Now let's build and run your server!

1. **Open Terminal** in your project folder:
   ```bash
   cd /Users/yevhenhryhorenko/Documents/Frontend/mcp-codebase-analyser
   ```

2. **Build the Docker image** (takes 2-3 minutes first time):
   ```bash
   docker-compose build
   ```
   
   You'll see lots of output. Wait for it to finish.
   Should end with: "Successfully tagged mcp-codebase-analyser..."

3. **Start the server**:
   ```bash
   docker-compose up -d
   ```
   
   The `-d` means "detached" (runs in background)

4. **Check if it's running**:
   ```bash
   docker-compose ps
   ```
   
   Should show:
   ```
   NAME                     STATUS
   mcp-codebase-analyser    Up X seconds
   ```

5. **View the logs** to confirm it started:
   ```bash
   docker-compose logs
   ```
   
   Look for these success messages:
   - ✅ "Initialized embedding system with openai provider"
   - ✅ "All components initialized successfully"
   - ✅ "Starting MCP server with sse transport..."

**✅ Checkpoint**: Server is running on `http://localhost:8050`

---

## ✅ STEP 4: Configure Cursor

Now let's connect Cursor to your MCP server!

### **Option A: Via Cursor Settings UI (Easiest)**

1. **Open Cursor**

2. **Open Settings**:
   - Mac: `Cmd + ,`
   - Windows/Linux: `Ctrl + ,`

3. **Search for**: `MCP`

4. **Click**: "MCP Settings" or "Edit MCP Configuration"

5. **Add this JSON** (or copy from `cursor_config.json` file):
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

6. **Save** and **Restart Cursor**

### **Option B: Manual Configuration**

1. **Find your Cursor config file**:
   - Mac: `~/.cursor/mcp_settings.json`
   - Windows: `%APPDATA%\Cursor\mcp_settings.json`
   - Linux: `~/.cursor/mcp_settings.json`

2. **Create/edit the file** with the JSON above

3. **Save** and **Restart Cursor**

**✅ Checkpoint**: After restart, Cursor should connect to your MCP server

---

## ✅ STEP 5: Test with jolly-sections Repository!

Now the fun part - let's use it! 🎉

### **Test 1: Analyze the Repository**

In Cursor, open a new chat and type:

```
Analyze the jolly-commerce/jolly-sections repository
```

**What happens:**
1. MCP server clones the repo
2. Parses all code files
3. Generates embeddings
4. Indexes everything

**Expected response:**
```json
{
  "success": true,
  "message": "Successfully analyzed jolly-commerce/jolly-sections",
  "indexing": {
    "indexed": 50,  // number of sections found
    "total": 50
  }
}
```

⏱️ **Time**: 2-5 minutes (first time only)

---

### **Test 2: Find a Specific Section**

Now ask for recommendations! Try this:

```
I want to add a hero section with call-to-action buttons to my landing page. 
Which section from jolly-commerce/jolly-sections should I use?
```

**What happens:**
1. Searches indexed sections semantically
2. GPT-4 analyzes top matches
3. Provides detailed recommendation

**Expected response:**
```json
{
  "found_match": true,
  "best_match": "src/sections/HeroSection.tsx",
  "best_match_name": "HeroSection",
  "confidence": "high",
  "reasoning": "This section implements a hero with CTA buttons...",
  "usage_advice": "You can customize the buttons by changing...",
  "alternatives": ["src/sections/BannerSection.tsx"]
}
```

---

### **Test 3: Search for Patterns**

```
Show me all pricing-related sections in jolly-commerce/jolly-sections
```

**Expected response:**
List of relevant sections with similarity scores

---

### **Test 4: Get Repository Structure**

```
What sections are available in jolly-commerce/jolly-sections?
```

**Expected response:**
Complete structure showing all indexed sections organized by file

---

## 🎯 YOUR EXACT USE CASE

You can now do exactly what you wanted:

```
Please check the jolly-commerce/jolly-sections repo and tell me 
what section is the best choice if I want to add a {feature example} to my code
```

Replace `{feature example}` with:
- "pricing table with monthly/yearly toggle"
- "testimonials carousel"
- "feature comparison grid"
- "contact form with validation"
- "newsletter signup section"
- etc.

---

## 🔍 Useful Commands

### **Check if server is running:**
```bash
docker-compose ps
```

### **View live logs:**
```bash
docker-compose logs -f
```

### **Restart server:**
```bash
docker-compose restart
```

### **Stop server:**
```bash
docker-compose down
```

### **Start server again:**
```bash
docker-compose up -d
```

### **Rebuild after code changes:**
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### **Clear all cached data:**
```bash
docker-compose down
rm -rf repo_cache/ chroma_db/
docker-compose up -d
```

---

## 🐛 Troubleshooting

### ❌ "Server not responding"
```bash
# Check if running
docker-compose ps

# Check logs for errors
docker-compose logs

# Restart
docker-compose restart
```

### ❌ "Authentication failed" / "OpenAI API error"
```bash
# Check your API key is correct
grep LLM_API_KEY .env

# Make sure it starts with "sk-"
# Make sure you have credits in your OpenAI account
```

### ❌ "Can't clone jolly-commerce/jolly-sections"
```bash
# Add GitHub token to .env
# Even for public repos, it helps with rate limits

# Or try full URL:
# "Analyze the https://github.com/jolly-commerce/jolly-sections repository"
```

### ❌ Cursor can't connect to MCP
```bash
# Verify server is running
docker-compose ps

# Check the URL in Cursor settings:
# http://localhost:8050/sse (not https, not /api, etc.)

# Try restarting Cursor completely
```

### ❌ Docker build fails
```bash
# Make sure Docker Desktop is running
# Try building with no cache:
docker-compose build --no-cache
```

---

## 📊 What Data is Stored?

When you run the server, these directories are created:

- **`repo_cache/`** - Cloned repositories (can delete anytime)
- **`chroma_db/`** - Vector database with embeddings (persists between restarts)

Both are gitignored and can be safely deleted if you want to start fresh.

---

## 💰 Cost Estimate

For jolly-commerce/jolly-sections (assuming ~50 sections):

- **One-time indexing**: ~$0.05 (embeddings)
- **Each query**: ~$0.01-0.02 (GPT-4-mini)
- **Subsequent queries**: Only GPT cost (embeddings cached)

Very affordable! 💰

---

## 🎉 You're Done!

Follow the 5 steps above, and you'll have:
✅ MCP server running in Docker
✅ Connected to Cursor
✅ Analyzing jolly-sections repository
✅ Getting AI-powered recommendations

**Next message in Cursor:**
```
Analyze the jolly-commerce/jolly-sections repository
```

**Then ask:**
```
What's the best section for a pricing table?
```

Have fun! 🚀

