"""
MCP Server for Intelligent Codebase Analysis
Provides tools to analyze GitHub repositories and find relevant code sections.
"""
import os
import asyncio
import json
import logging
from typing import Optional

# Load environment first
from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from dataclasses import dataclass

from repo_fetcher import RepositoryFetcher
from code_parser import CodeParser, CodeSection
from embedding_system import EmbeddingSystem
from recommendation_system import RecommendationSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CodebaseAnalyserContext:
    """Context for the Codebase Analyser MCP server."""
    repo_fetcher: RepositoryFetcher
    code_parser: CodeParser
    embedding_system: EmbeddingSystem
    recommendation_system: RecommendationSystem

# Global context - will be initialized on startup
_context: Optional[CodebaseAnalyserContext] = None

def get_context() -> CodebaseAnalyserContext:
    """Get the global context."""
    if _context is None:
        raise RuntimeError("Context not initialized. Server startup may have failed.")
    return _context

async def initialize_context():
    """Initialize the global context."""
    global _context
    
    # Get configuration from environment
    github_token = os.getenv("GITHUB_TOKEN")
    repo_cache_dir = os.getenv("REPO_CACHE_DIR", "./repo_cache")
    chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    chroma_collection = os.getenv("CHROMA_COLLECTION_NAME", "codebase_sections")
    
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    max_file_size_kb = int(os.getenv("MAX_FILE_SIZE_KB", "500"))
    supported_extensions = os.getenv("SUPPORTED_EXTENSIONS", 
                                    ".js,.jsx,.ts,.tsx,.py,.java,.go,.rs,.cpp,.c,.h")
    supported_ext_list = [ext.strip() for ext in supported_extensions.split(",")]
    
    # Initialize components
    logger.info("Initializing Codebase Analyser MCP Server...")
    
    repo_fetcher = RepositoryFetcher(
        cache_dir=repo_cache_dir,
        github_token=github_token
    )
    
    code_parser = CodeParser(
        max_file_size_kb=max_file_size_kb,
        supported_extensions=supported_ext_list
    )
    
    embedding_system = EmbeddingSystem(
        persist_dir=chroma_persist_dir,
        collection_name=chroma_collection,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        embedding_model=embedding_model
    )
    
    recommendation_system = RecommendationSystem(
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model=llm_model
    )
    
    logger.info("All components initialized successfully")
    
    _context = CodebaseAnalyserContext(
        repo_fetcher=repo_fetcher,
        code_parser=code_parser,
        embedding_system=embedding_system,
        recommendation_system=recommendation_system
    )

# Initialize FastMCP server with lifespan
@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for FastMCP server."""
    # Startup
    logger.info("Starting up MCP server...")
    await initialize_context()
    logger.info("Server startup complete")
    yield
    # Shutdown
    logger.info("Shutting down MCP server...")

mcp = FastMCP("codebase-analyser", lifespan=lifespan)

@mcp.tool()
async def analyze_repository(
    ctx: Context,
    repo_identifier: str,
    force_refresh: bool = False
) -> str:
    """
    Analyze a GitHub repository and index its code sections.
    
    This tool fetches a repository, parses all code files, and indexes them for semantic search.
    Use this before searching for specific sections or features.
    
    Args:
        ctx: The MCP server context
        repo_identifier: Repository to analyze (e.g., "owner/repo" or "owner/repo@branch")
        force_refresh: If True, re-clone and re-index the repository (default: False)
    
    Returns:
        JSON string with analysis results including number of sections indexed
    
    Examples:
        - analyze_repository("facebook/react")
        - analyze_repository("vercel/next.js@main")
        - analyze_repository("owner/private-repo", force_refresh=True)
    """
    try:
        context = get_context()
        
        logger.info(f"Analyzing repository: {repo_identifier}")
        
        # Step 1: Fetch repository
        repo_path = context.repo_fetcher.fetch_repository(
            repo_identifier,
            force_refresh=force_refresh
        )
        
        # Get repository info
        repo_info = context.repo_fetcher.get_repository_info(repo_path)
        
        # Step 2: Parse code sections
        code_sections = context.code_parser.parse_repository(repo_path)
        
        if not code_sections:
            return json.dumps({
                "success": False,
                "message": "No code sections found in repository",
                "repo": repo_identifier,
                "repo_info": repo_info
            }, indent=2)
        
        # Convert CodeSection objects to dictionaries
        sections_dict = [section.to_dict() for section in code_sections]
        
        # Step 3: Index in vector database
        if force_refresh:
            # Delete existing data for this repo
            context.embedding_system.delete_repository(repo_identifier)
        
        index_result = context.embedding_system.index_code_sections(
            repo_identifier,
            sections_dict
        )
        
        # Get summary
        summary = context.recommendation_system.summarize_repository(
            repo_identifier,
            sections_dict
        )
        
        result = {
            "success": True,
            "message": f"Successfully analyzed {repo_identifier}",
            "repo": repo_identifier,
            "repo_info": repo_info,
            "indexing": index_result,
            "summary": summary
        }
        
        logger.info(f"Analysis complete for {repo_identifier}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "repo": repo_identifier
        }, indent=2)

@mcp.tool()
async def find_best_section(
    ctx: Context,
    feature_description: str,
    repo_identifier: str,
    top_n: int = 5
) -> str:
    """
    Find the best code section for implementing a specific feature.
    
    This is the main tool for getting recommendations. It searches indexed repositories
    and uses AI to recommend the most suitable code sections for your needs.
    
    Args:
        ctx: The MCP server context
        feature_description: Description of the feature you want to implement
        repo_identifier: Repository to search (e.g., "owner/repo")
        top_n: Number of candidate sections to analyze (default: 5)
    
    Returns:
        JSON string with recommendation including best match, reasoning, and advice
    
    Examples:
        - find_best_section("hero section with call-to-action buttons", "jolly-sections")
        - find_best_section("user authentication form", "owner/repo")
        - find_best_section("pricing table with monthly/yearly toggle", "company/website")
    """
    try:
        context = get_context()
        
        logger.info(f"Finding best section for: {feature_description}")
        
        # Search for relevant sections
        search_results = context.embedding_system.search_sections(
            query=feature_description,
            repo_filter=repo_identifier,
            limit=top_n
        )
        
        # Get intelligent recommendation
        recommendation = context.recommendation_system.analyze_and_recommend(
            user_request=feature_description,
            search_results=search_results,
            repo_name=repo_identifier
        )
        
        logger.info(f"Recommendation generated for {repo_identifier}")
        return json.dumps(recommendation, indent=2)
        
    except Exception as e:
        logger.error(f"Error finding best section: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "feature": feature_description,
            "repo": repo_identifier
        }, indent=2)

@mcp.tool()
async def search_code_sections(
    ctx: Context,
    query: str,
    repo_identifier: str = None,
    limit: int = 10
) -> str:
    """
    Search for code sections using semantic search.
    
    Returns raw search results without AI analysis. Useful for exploring
    what's available in a repository.
    
    Args:
        ctx: The MCP server context
        query: Search query describing what you're looking for
        repo_identifier: Optional repository filter (e.g., "owner/repo")
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        JSON string with list of matching code sections and their similarity scores
    
    Examples:
        - search_code_sections("button component")
        - search_code_sections("authentication", "owner/repo", 5)
    """
    try:
        context = get_context()
        
        search_results = context.embedding_system.search_sections(
            query=query,
            repo_filter=repo_identifier,
            limit=limit
        )
        
        result = {
            "success": True,
            "query": query,
            "repo_filter": repo_identifier,
            "results_count": len(search_results),
            "results": search_results
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching code sections: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": query
        }, indent=2)

@mcp.tool()
async def get_repository_structure(
    ctx: Context,
    repo_identifier: str
) -> str:
    """
    Get the structure and summary of an analyzed repository.
    
    Shows what sections have been indexed, file organization, and section types.
    
    Args:
        ctx: The MCP server context
        repo_identifier: Repository identifier (e.g., "owner/repo")
    
    Returns:
        JSON string with repository structure and statistics
    
    Examples:
        - get_repository_structure("jolly-sections")
        - get_repository_structure("facebook/react")
    """
    try:
        context = get_context()
        
        # Get all sections for the repository
        sections = context.embedding_system.get_repository_sections(repo_identifier)
        
        if not sections:
            return json.dumps({
                "success": False,
                "message": f"No indexed data found for {repo_identifier}. Run analyze_repository first.",
                "repo": repo_identifier
            }, indent=2)
        
        # Generate summary
        summary = context.recommendation_system.summarize_repository(
            repo_identifier,
            sections
        )
        
        result = {
            "success": True,
            "repo": repo_identifier,
            **summary
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting repository structure: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "repo": repo_identifier
        }, indent=2)

@mcp.tool()
async def list_analyzed_repositories(ctx: Context) -> str:
    """
    List all repositories that have been analyzed and indexed.
    
    Shows which repositories are available for searching and their statistics.
    
    Args:
        ctx: The MCP server context
    
    Returns:
        JSON string with list of analyzed repositories and their stats
    """
    try:
        context = get_context()
        
        stats = context.embedding_system.get_stats()
        
        return json.dumps({
            "success": True,
            **stats
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def clear_repository_cache(
    ctx: Context,
    repo_identifier: str = None
) -> str:
    """
    Clear cached repository data.
    
    Removes both the cloned repository files and indexed sections from the database.
    
    Args:
        ctx: The MCP server context
        repo_identifier: Optional repository to clear. If None, clears all cached data.
    
    Returns:
        JSON string with result of the clear operation
    
    Examples:
        - clear_repository_cache("owner/repo")
        - clear_repository_cache()  # Clears everything
    """
    try:
        context = get_context()
        
        if repo_identifier:
            # Clear specific repository
            context.repo_fetcher.clear_cache(repo_identifier)
            deleted_count = context.embedding_system.delete_repository(repo_identifier)
            
            return json.dumps({
                "success": True,
                "message": f"Cleared cache for {repo_identifier}",
                "repo": repo_identifier,
                "sections_deleted": deleted_count
            }, indent=2)
        else:
            # Clear all
            context.repo_fetcher.clear_cache()
            context.embedding_system.clear_all()
            
            return json.dumps({
                "success": True,
                "message": "Cleared all cached repositories and indexed data"
            }, indent=2)
            
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def health_check(ctx: Context) -> str:
    """
    Check if the MCP server is healthy and operational.
    
    Returns server status and initialization state.
    
    Args:
        ctx: The MCP server context
    
    Returns:
        JSON string with health status
    """
    try:
        context = get_context()
        stats = context.embedding_system.get_stats()
        
        return json.dumps({
            "status": "healthy",
            "server": "codebase-analyser",
            "initialized": True,
            "stats": stats
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "unhealthy",
            "server": "codebase-analyser",
            "initialized": False,
            "error": str(e)
        }, indent=2)

def main():
    """Main entry point for the MCP server."""
    transport = os.getenv("TRANSPORT", "sse")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting MCP server with {transport} transport on {host}:{port}...")
    
    if transport == 'sse':
        # Run SSE server with proper host/port binding
        import uvicorn
        uvicorn.run(
            mcp.sse_app(),
            host=host,
            port=port,
            log_level="info"
        )
    else:
        # Run stdio transport
        mcp.run()

if __name__ == "__main__":
    main()
