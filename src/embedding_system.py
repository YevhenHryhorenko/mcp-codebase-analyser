"""
Embedding system for semantic code search using vector database.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger(__name__)


class EmbeddingSystem:
    """Handles embedding generation and vector database operations."""
    
    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        collection_name: str = "codebase_sections",
        llm_provider: str = "openai",
        llm_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize the embedding system.
        
        Args:
            persist_dir: Directory to persist ChromaDB
            collection_name: Name of the collection in ChromaDB
            llm_provider: LLM provider (openai, ollama)
            llm_api_key: API key for the LLM provider
            embedding_model: Model to use for embeddings
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        self.llm_provider = llm_provider
        self.embedding_model = embedding_model
        
        # Initialize OpenAI client
        if llm_provider == "openai":
            self.openai_client = OpenAI(api_key=llm_api_key or os.getenv("LLM_API_KEY"))
        else:
            # For Ollama or other providers
            base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
            self.openai_client = OpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"  # Ollama doesn't need real API key
            )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Initialized embedding system with {llm_provider} provider")
        logger.info(f"Collection: {collection_name}, items: {self.collection.count()}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            # Truncate text if too long (OpenAI limit is 8191 tokens, ~6000 chars safe)
            # For text-embedding-3-small, we need to stay well under the limit
            max_chars = 6000
            if len(text) > max_chars:
                logger.debug(f"Text too long ({len(text)} chars), truncating to {max_chars}")
                text = text[:max_chars] + "\n... (truncated)"
            
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in parallel.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors (None if failed)
        """
        results = [None] * len(texts)
        
        def generate_one(index: int, text: str):
            try:
                embedding = self._generate_embedding(text)
                results[index] = embedding
            except Exception as e:
                logger.error(f"Failed to generate embedding {index}: {e}")
                results[index] = None
        
        # Process up to 10 embeddings in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i, text in enumerate(texts):
                future = executor.submit(generate_one, i, text)
                futures.append(future)
            
            # Wait for all to complete
            for future in futures:
                future.result()
        
        return results
    
    def _generate_id(self, repo_identifier: str, file_path: str, section_name: str, start_line: int = 0, end_line: int = 0, code_hash: str = "") -> str:
        """Generate unique ID for a code section including code hash for absolute uniqueness."""
        unique_string = f"{repo_identifier}::{file_path}::{section_name}::{start_line}::{end_line}::{code_hash}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess search query to improve results.
        
        - Removes common stop words
        - Expands common abbreviations
        - Cleans up formatting
        
        Args:
            query: Raw search query
        
        Returns:
            Preprocessed query
        """
        # Common stop words to remove (keep technical ones like "async", "static")
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 
            'that', 'the', 'to', 'was', 'will', 'with'
        }
        
        # Common programming abbreviations to expand
        abbreviations = {
            'auth': 'authentication',
            'config': 'configuration',
            'ctx': 'context',
            'db': 'database',
            'func': 'function',
            'impl': 'implementation',
            'params': 'parameters',
            'props': 'properties',
            'repo': 'repository',
            'res': 'response',
            'req': 'request',
            'util': 'utility',
            'btn': 'button',
            'msg': 'message',
            'init': 'initialize',
            'async': 'asynchronous',
        }
        
        # Clean up query
        query = query.lower().strip()
        
        # Expand abbreviations
        words = query.split()
        expanded_words = []
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w\s-]', '', word)
            if clean_word in abbreviations:
                # Keep both the abbreviation and expansion for better matching
                expanded_words.append(clean_word)
                expanded_words.append(abbreviations[clean_word])
            elif clean_word not in stop_words or len(clean_word) > 3:
                # Keep word if it's not a stop word, or if it's a longer stop word
                expanded_words.append(clean_word)
        
        processed_query = ' '.join(expanded_words)
        
        # Log if query was significantly changed
        if processed_query != query:
            logger.debug(f"Query preprocessing: '{query}' -> '{processed_query}'")
        
        return processed_query if processed_query else query  # Fallback to original if empty
    
    def index_code_sections(
        self,
        repo_identifier: str,
        code_sections: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Index code sections into the vector database.
        
        Args:
            repo_identifier: Repository identifier (owner/repo)
            code_sections: List of code section dictionaries
            batch_size: Number of sections to process at once
        
        Returns:
            Dictionary with indexing statistics
        """
        logger.info(f"Indexing {len(code_sections)} code sections for {repo_identifier}")
        
        indexed_count = 0
        skipped_count = 0
        error_count = 0
        
        # Get existing IDs to avoid duplicates
        try:
            existing_data = self.collection.get()
            existing_ids = set(existing_data.get("ids", []))
            logger.info(f"Found {len(existing_ids)} existing sections in database")
        except:
            existing_ids = set()
        
        # Track IDs within this indexing run to avoid duplicates in the same batch
        seen_ids_this_run = set()
        
        # Process in batches with parallel embedding generation
        for i in range(0, len(code_sections), batch_size):
            batch = code_sections[i:i + batch_size]
            
            # Log progress every 50 sections
            if i % 50 == 0 and i > 0:
                progress_pct = (i / len(code_sections)) * 100
                logger.info(f"Progress: {i}/{len(code_sections)} sections ({progress_pct:.1f}%) - Indexed: {indexed_count}, Skipped: {skipped_count}, Errors: {error_count}")
            
            # Prepare all data for this batch first
            batch_data = []
            
            for section in batch:
                try:
                    # Generate unique ID with full content hash + line numbers + pattern type
                    code_content = section.get("code", "")
                    pattern_type = section.get("metadata", {}).get("pattern_type", "")
                    
                    # Include pattern_type in the ID to distinguish different patterns matching the same code
                    full_id_string = f"{code_content}{pattern_type}{section.get('start_line', 0)}{section.get('end_line', 0)}"
                    code_hash = hashlib.md5(full_id_string.encode()).hexdigest()[:12]
                    
                    section_id = self._generate_id(
                        repo_identifier,
                        section["file_path"],
                        section["name"],
                        section.get("start_line", 0),
                        section.get("end_line", 0),
                        code_hash
                    )
                    
                    # Skip if already exists in DB or already seen this run
                    if section_id in existing_ids or section_id in seen_ids_this_run:
                        skipped_count += 1
                        continue
                    
                    # Mark as seen for this run
                    seen_ids_this_run.add(section_id)
                    
                    # Prepare context for embedding - include full code up to embedding limit
                    context = section.get("context", "")
                    if not context:
                        # Build rich context with full code (truncation happens in _generate_embedding)
                        context = f"File: {section['file_path']}\n"
                        context += f"Type: {section['type']}\n"
                        context += f"Name: {section['name']}\n"
                        context += f"Code:\n{section.get('code', '')}"  # Full code, not truncated here
                    
                    # Prepare metadata
                    metadata = {
                        "repo": repo_identifier,
                        "file_path": section["file_path"],
                        "name": section["name"],
                        "type": section["type"],
                        "start_line": section.get("start_line", 0),
                        "end_line": section.get("end_line", 0),
                        **section.get("metadata", {})
                    }
                    
                    # Store more of the document for retrieval (was 2000, now 4000)
                    document = section.get("code", "")[:4000]
                    
                    batch_data.append({
                        "id": section_id,
                        "context": context,
                        "metadata": metadata,
                        "document": document
                    })
                    
                except Exception as e:
                    logger.error(f"Error preparing section {section.get('name', 'unknown')}: {e}")
                    error_count += 1
            
            if not batch_data:
                continue
            
            # Generate embeddings in parallel
            contexts = [item["context"] for item in batch_data]
            embeddings = self._generate_embeddings_batch(contexts)
            
            # Add successful ones to collection
            ids = []
            valid_embeddings = []
            metadatas = []
            documents = []
            
            for item, embedding in zip(batch_data, embeddings):
                if embedding is not None:
                    ids.append(item["id"])
                    valid_embeddings.append(embedding)
                    metadatas.append(item["metadata"])
                    documents.append(item["document"])
                    indexed_count += 1
                    existing_ids.add(item["id"])  # Track for future batches
                else:
                    error_count += 1
            
            # Add batch to collection
            if ids:
                try:
                    self.collection.add(
                        ids=ids,
                        embeddings=valid_embeddings,
                        metadatas=metadatas,
                        documents=documents
                    )
                except Exception as e:
                    logger.error(f"Error adding batch to collection: {e}")
                    error_count += len(ids)
                    indexed_count -= len(ids)
        
        result = {
            "indexed": indexed_count,
            "skipped": skipped_count,
            "errors": error_count,
            "total": len(code_sections),
            "collection_size": self.collection.count()
        }
        
        logger.info(f"✅ Indexing complete: Indexed {indexed_count}, Skipped {skipped_count}, Errors {error_count} out of {len(code_sections)} total sections")
        return result
    
    def search_sections(
        self,
        query: str,
        repo_filter: Optional[str] = None,
        limit: int = 20,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for code sections using semantic search.
        
        Args:
            query: Search query
            repo_filter: Optional repository filter (owner/repo)
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of matching code sections with scores
        """
        try:
            # Preprocess query for better search results
            processed_query = self._preprocess_query(query)
            
            # Generate query embedding
            query_embedding = self._generate_embedding(processed_query)
            
            # Build where filter
            where_filter = None
            if repo_filter:
                where_filter = {"repo": repo_filter}
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Format results
            formatted_results = []
            
            if results and results.get("ids") and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    # Calculate similarity score (1 - distance for cosine)
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    score = 1 - distance  # Convert distance to similarity
                    
                    if score < min_score:
                        continue
                    
                    result = {
                        "id": results["ids"][0][i],
                        "score": round(score, 4),
                        "metadata": results["metadatas"][0][i],
                        "code": results["documents"][0][i] if results.get("documents") else "",
                    }
                    formatted_results.append(result)
            
            logger.info(f"Search found {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching sections: {e}")
            return []
    
    def get_repository_sections(
        self,
        repo_identifier: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all indexed sections for a repository.
        
        Args:
            repo_identifier: Repository identifier (owner/repo)
            limit: Optional limit on number of results
        
        Returns:
            List of code sections
        """
        try:
            results = self.collection.get(
                where={"repo": repo_identifier},
                limit=limit
            )
            
            formatted_results = []
            if results and results.get("ids"):
                for i in range(len(results["ids"])):
                    result = {
                        "id": results["ids"][i],
                        "metadata": results["metadatas"][i],
                        "code": results["documents"][i] if results.get("documents") else "",
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting repository sections: {e}")
            return []
    
    def delete_repository(self, repo_identifier: str) -> int:
        """
        Delete all sections for a repository.
        
        Args:
            repo_identifier: Repository identifier (owner/repo)
        
        Returns:
            Number of sections deleted
        """
        try:
            # Get all sections for the repo
            sections = self.get_repository_sections(repo_identifier)
            
            if sections:
                ids = [s["id"] for s in sections]
                self.collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} sections for {repo_identifier}")
                return len(ids)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting repository sections: {e}")
            return 0
    
    def clear_all(self):
        """Delete all data from the collection."""
        try:
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Cleared all data from collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed data."""
        try:
            total_count = self.collection.count()
            
            # Get unique repositories
            all_data = self.collection.get()
            repos = set()
            if all_data and all_data.get("metadatas"):
                repos = {m.get("repo", "unknown") for m in all_data["metadatas"]}
            
            return {
                "total_sections": total_count,
                "repositories": list(repos),
                "repository_count": len(repos),
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

