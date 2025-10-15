# 🔍 MCP Codebase Analyser

An intelligent Model Context Protocol (MCP) server that analyzes GitHub repositories and provides AI-powered recommendations for finding the right code sections for your features.

## 🎯 What Does It Do?

This MCP server allows you to ask questions like:

> *"Check the jolly-sections repo and tell me what section is the best choice if I want to add a hero section with call-to-action buttons"*

The server will:
1. **Fetch & analyze** the repository
2. **Parse** all code files (JS/TS/Python/etc.)
3. **Index** sections using semantic embeddings
4. **Search** for relevant code sections
5. **Provide AI recommendations** with specific file names and implementation advice

## ✨ Features

- 🔎 **Semantic Code Search** - Find code by meaning, not just keywords
- 🤖 **AI-Powered Recommendations** - Get intelligent suggestions with reasoning
- 📁 **Multi-Language Support** - JavaScript, TypeScript, Python, Go, Rust, C++, and more
- 💾 **Persistent Cache** - Repositories and embeddings are cached for fast repeated queries
- 🐳 **Docker Ready** - Easy deployment with Docker Desktop
- 🔌 **MCP Compatible** - Works seamlessly with Cursor and other MCP clients

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (for containerized deployment)
- **OpenAI API Key** (or Ollama for local LLM)
- **GitHub Token** (optional, but recommended for private repos and rate limits)

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd mcp-codebase-analyser
   ```

2. **Create `.env` file**
   ```bash
   cp env.example .env
   ```

3. **Edit `.env` with your credentials**
   ```env
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-your-openai-api-key
   LLM_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=text-embedding-3-small
   GITHUB_TOKEN=your_github_token  # Optional
   ```

4. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Check if running**
   ```bash
   docker-compose logs -f
   ```

The server will be running at `http://localhost:8050`

### Option 2: Local Development

1. **Install dependencies**
   ```bash
   # Install uv (if not already installed)
   pip install uv
   
   # Install project dependencies
   uv pip install -e .
   ```

2. **Create `.env` file** (same as above)

3. **Run the server**
   ```bash
   uv run src/main.py
   ```

## 🔧 Configuration for Cursor

To use this MCP server in Cursor, add it to your MCP settings:

### For SSE Transport (Recommended)

Add to your Cursor MCP settings (`~/.cursor/mcp_settings.json` or via Cursor settings):

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

### For Docker Deployment

If running via Docker:

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

## 📖 Usage Examples

### 1. Analyze a Repository

First, analyze the repository you want to search:

```
User: Analyze the jolly-sections repository

Tool: analyze_repository("jolly-sections/jolly-sections")
```

This will:
- Clone the repository
- Parse all code files
- Extract functions, classes, components
- Generate embeddings
- Index in vector database

### 2. Find the Best Section for Your Feature

```
User: I want to add a pricing section with monthly/yearly toggle. 
      Which section from jolly-sections should I use?

Tool: find_best_section(
  feature_description="pricing section with monthly/yearly toggle",
  repo_identifier="jolly-sections/jolly-sections"
)
```

**Response Example:**
```json
{
  "found_match": true,
  "best_match": "src/sections/PricingSection.tsx",
  "best_match_name": "PricingSection",
  "confidence": "high",
  "reasoning": "This section implements a pricing display with tier options...",
  "usage_advice": "You can extend this section by adding a toggle component...",
  "alternatives": ["src/sections/FeatureComparison.tsx"],
  "considerations": ["Consider responsive design for mobile", "Add animation for toggle"]
}
```

### 3. Search for Specific Code Patterns

```
User: Show me all authentication-related code in the repo

Tool: search_code_sections(
  query="authentication login user session",
  repo_identifier="owner/repo",
  limit=10
)
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
| `SUPPORTED_EXTENSIONS` | File extensions to parse | `.js,.jsx,.ts,.tsx,...` | No |

## 🧪 Testing

Test the server manually:

```bash
# 1. Start the server
docker-compose up -d

# 2. Check logs
docker-compose logs -f

# 3. In Cursor, try:
# "Analyze the facebook/react repository"
# "Find the best component for a button with loading state in facebook/react"
```

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

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Powered by [ChromaDB](https://www.trychroma.com/)
- Uses [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings) or [Ollama](https://ollama.ai)

## 📞 Support

For issues and questions, please open a GitHub issue.

---

**Happy Coding! 🚀**
