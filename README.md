# 🔍 MCP Codebase Analyser

An intelligent Model Context Protocol (MCP) server that analyzes GitHub repositories and provides AI-powered recommendations for finding the right code sections for your features.

## 🎯 What Does It Do?

This MCP server allows you to ask questions like:

> *"I need to create a product fetch popup modal. Find the best section from jolly-commerce/jolly-sections."*

The server will:
1. **Fetch & analyze** the repository (clones and caches locally)
2. **Parse** source code files (JS/TS only, skips minified bundles)
3. **Extract** functions, classes, and components with full code
4. **Index** sections using semantic embeddings (OpenAI or Ollama)
5. **Search** semantically for relevant code
6. **Provide AI recommendations** with reasoning and implementation advice

## ✨ Features

- 🔎 **Semantic Code Search** - Find code by meaning, not just keywords (0.7+ relevance scores)
- 🤖 **AI-Powered Recommendations** - Get intelligent suggestions with high confidence
- 📁 **Smart Filtering** - Automatically skips minified files (.min.js, .chunk.js, bundles)
- 💻 **JavaScript/TypeScript Focus** - Optimized for modern web development
- 💾 **Persistent Cache** - Repositories and embeddings cached for instant repeated queries
- 🐳 **Docker Ready** - Production-ready containerized deployment
- 🔌 **MCP Compatible** - Works seamlessly with Cursor IDE and other MCP clients
- ⚡ **Production Tested** - Successfully indexes jolly-commerce/jolly-sections (152 sections, 100% success rate)

## 🚀 Quick Start

**Prerequisites:** Docker Desktop, OpenAI API Key

### 1. Setup Environment
```bash
cp env.example .env
# Edit .env and add your OpenAI API key:
# LLM_API_KEY=sk-your-key-here
```

### 2. Start Server
```bash
docker-compose up -d
docker-compose logs -f  # Wait for "All components initialized"
```

### 3. Configure Cursor
Add to Cursor MCP settings (`Cmd/Ctrl + ,` → search "MCP"):
```json
{
  "mcpServers": {
    "codebase-analyser": {
      "url": "http://localhost:8050/sse",
      "transport": {"type": "sse"}
    }
  }
}
```
Restart Cursor.

### 4. Test It
In Cursor, try:
```
Analyze the repository jolly-commerce/jolly-sections
```
Wait 2-3 minutes, then:
```
I need to create a product fetch popup modal. Find the best section.
```
✅ Expected: FetchModalProductPopUp class with code snippet

---

**Alternative: Local Development (without Docker)**
```bash
pip install uv
uv pip install -e .
# Edit .env with your API key
uv run src/main.py
```


## 📖 Usage Examples

### 1. Analyze a Repository

First, analyze the repository you want to search:

```
User: Analyze the repository jolly-commerce/jolly-sections

AI uses: analyze_repository("jolly-commerce/jolly-sections")
```

**Result:**
```json
{
  "success": true,
  "message": "Successfully analyzed jolly-commerce/jolly-sections",
  "indexing": {
    "indexed": 152,
    "errors": 0,
    "total": 152
  },
  "files_analyzed": 43,
  "section_types": {
    "functions": 37,
    "classes": 74,
    "react_component": 32
  }
}
```

### 2. Find the Best Section for Your Feature

```
User: I need to create a product fetch popup modal. 
      Find the best section from jolly-commerce/jolly-sections.

AI uses: find_best_section(
  feature_description="product fetch popup modal",
  repo_identifier="jolly-commerce/jolly-sections"
)
```

**Real Response:**
```json
{
  "found_match": true,
  "best_match": "src/templates/components/g-modal.js",
  "best_match_name": "FetchModalProductPopUp",
  "confidence": "high",
  "score": 0.69,
  "reasoning": "The FetchModalProductPopUp class is specifically designed to handle product fetching in a modal context, which aligns perfectly with the user's request...",
  "usage_advice": "To use this section, instantiate the FetchModalProductPopUp class and call the onTrigger method with the appropriate event and trigger element...",
  "alternatives": ["DynamicModal", "GModal"],
  "code_snippet": "class FetchModalProductPopUp extends FetchModal { ... }"
}
```

### 3. Search for Specific Code Patterns

```
User: Find cart drawer components in jolly-commerce/jolly-sections

AI uses: search_code_sections(
  query="cart drawer shopping cart sidebar",
  repo_identifier="jolly-commerce/jolly-sections",
  limit=10
)
```

**Real Response:**
```json
{
  "success": true,
  "results_count": 3,
  "results": [
    {
      "file": "src/templates/components/g-cart.js",
      "name": "CartDrawer",
      "type": "class",
      "score": 0.72,
      "code": "class CartDrawer extends Cart { ... }"
    },
    {
      "file": "src/templates/components/g-cart.js",
      "name": "CartDrawerItem",
      "type": "class",
      "score": 0.70
    }
  ]
}
```

### 4. Get Repository Structure

```
User: What sections are available in jolly-sections?

Tool: get_repository_structure("jolly-sections/jolly-sections")
```

### 5. List All Analyzed Repositories

```
User: What repositories have been analyzed?

Tool: list_analyzed_repositories()
```

## 🛠️ Available MCP Tools

| Tool | Description | Example |
|------|-------------|---------|
| `analyze_repository` | Index a GitHub repository | `analyze_repository("owner/repo")` |
| `find_best_section` | Get AI recommendation for feature | `find_best_section("hero section", "owner/repo")` |
| `search_code_sections` | Semantic code search | `search_code_sections("button component", "owner/repo")` |
| `get_repository_structure` | View indexed sections | `get_repository_structure("owner/repo")` |
| `list_analyzed_repositories` | List all indexed repos | `list_analyzed_repositories()` |
| `clear_repository_cache` | Clear cached data | `clear_repository_cache("owner/repo")` |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Cursor IDE                           │
│                     (MCP Client)                            │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol (SSE/STDIO)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server (FastMCP)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Repository Fetcher                       │  │
│  │  • Clone GitHub repos                                 │  │
│  │  • Cache locally                                      │  │
│  │  • Handle authentication                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Code Parser                              │  │
│  │  • Parse JS/TS/Python/etc.                           │  │
│  │  • Extract functions/classes/components              │  │
│  │  • Generate metadata                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Embedding System                         │  │
│  │  • Generate embeddings (OpenAI/Ollama)               │  │
│  │  • ChromaDB vector database                          │  │
│  │  • Semantic search                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Recommendation System                       │  │
│  │  • LLM analysis (GPT-4/Ollama)                       │  │
│  │  • Context-aware suggestions                         │  │
│  │  • Implementation advice                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ↓                    ↓                    ↓
   repo_cache/          chroma_db/            GitHub API
```

## 📁 Project Structure

```
mcp-codebase-analyser/
├── src/
│   ├── main.py                    # MCP server & tools
│   ├── repo_fetcher.py            # GitHub repository fetching
│   ├── code_parser.py             # Code parsing & extraction
│   ├── embedding_system.py        # Vector embeddings & search
│   ├── recommendation_system.py   # AI recommendations
│   └── utils.py                   # Utility functions
├── repo_cache/                    # Cached repositories
├── chroma_db/                     # Vector database
├── Dockerfile                     # Docker image
├── docker-compose.yml             # Docker compose config
├── pyproject.toml                 # Python dependencies
├── env.example                    # Environment variables template
└── README.md                      # This file
```

## 🔑 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Server host | `0.0.0.0` | No |
| `PORT` | Server port | `8050` | No |
| `TRANSPORT` | Transport type (`sse` or `stdio`) | `sse` | No |
| `LLM_PROVIDER` | LLM provider (`openai`, `ollama`) | `openai` | Yes |
| `LLM_API_KEY` | API key for LLM | - | Yes (OpenAI) |
| `LLM_MODEL` | Model name | `gpt-4o-mini` | No |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` | No |
| `GITHUB_TOKEN` | GitHub personal access token | - | No |
| `REPO_CACHE_DIR` | Repository cache directory | `./repo_cache` | No |
| `CHROMA_PERSIST_DIR` | ChromaDB directory | `./chroma_db` | No |
| `MAX_FILE_SIZE_KB` | Max file size to parse | `500` | No |
| `SUPPORTED_EXTENSIONS` | File extensions to parse | `.js,.jsx,.ts,.tsx` | No |

**Note:** The system automatically skips:
- Minified files (`.min.js`)
- Bundle files (`.chunk.js`, `bundle-*.js`)
- Assets directory compiled code
- This ensures only source code is indexed for better quality results

## 🧪 Testing

Test the server with the production-tested repository:

```bash
# 1. Start the server
docker-compose up -d

# 2. Check logs for success messages
docker-compose logs -f
# Look for: "Initialized embedding system with openai provider"
# Look for: "All components initialized successfully"

# 3. In Cursor, try these verified examples:
```

**Test 1: Analyze Repository** (2-3 minutes)
```
Analyze the repository jolly-commerce/jolly-sections
```
Expected: 152 sections indexed, 0 errors

**Test 2: Find Specific Component** (10-15 seconds)
```
I need to create a product fetch popup modal. Find the best section.
```
Expected: FetchModalProductPopUp class with high confidence (0.69+)

**Test 3: Search Components** (5-10 seconds)
```
Find cart drawer components in jolly-commerce/jolly-sections
```
Expected: CartDrawer, CartDrawerItem with relevance scores

## 🐛 Troubleshooting

### Server won't start
- Check Docker Desktop is running
- Verify `.env` file exists and has correct values
- Check logs: `docker-compose logs -f`

### Can't clone private repositories
- Add `GITHUB_TOKEN` to `.env`
- Ensure token has `repo` scope

### Out of memory / slow indexing
- Reduce `MAX_FILE_SIZE_KB` in `.env`
- Limit `SUPPORTED_EXTENSIONS` to only needed types
- Increase Docker memory limits

### Embeddings API errors
- Verify `LLM_API_KEY` is correct
- Check OpenAI account has credits
- Try with Ollama for local embeddings

## 🔄 Using with Ollama (Local LLM)

For completely local setup:

1. **Install Ollama**: https://ollama.ai

2. **Pull models**:
   ```bash
   ollama pull qwen2.5-coder:7b
   ollama pull nomic-embed-text
   ```

3. **Update `.env`**:
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=qwen2.5-coder:7b
   LLM_BASE_URL=http://host.docker.internal:11434
   EMBEDDING_MODEL=nomic-embed-text
   ```

4. **Restart server**:
   ```bash
   docker-compose restart
   ```

## 📝 Development

### Adding New File Type Support

Edit `src/code_parser.py` and add patterns for your language:

```python
PATTERNS = {
    "your_language": [
        r"pattern_to_match_functions",
        r"pattern_to_match_classes",
    ]
}
```

### Customizing Recommendations

Edit the system prompt in `src/recommendation_system.py`:

```python
def _get_system_prompt(self) -> str:
    return """Your custom prompt here..."""
```

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## 📊 Performance Stats

**Production Tested on jolly-commerce/jolly-sections:**
- ✅ 152 sections indexed (100% success rate)
- ✅ 0 errors during indexing
- ✅ 43 source files analyzed
- ✅ Average search score: 0.7+ (high relevance)
- ✅ No minified files indexed (smart filtering)
- ✅ Query time: 5-15 seconds
- ✅ Initial indexing: 2-3 minutes

**Code Quality:**
- Only source files indexed (src/templates/)
- Full code content extracted (not just names)
- Semantic search with high accuracy
- AI recommendations with reasoning

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Powered by [ChromaDB](https://www.trychroma.com/)
- Uses [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings) or [Ollama](https://ollama.ai)
- Production tested on [jolly-commerce/jolly-sections](https://github.com/jolly-commerce/jolly-sections)

## 📞 Support

For issues and questions, please open a GitHub issue.

---

**Happy Coding! 🚀**
