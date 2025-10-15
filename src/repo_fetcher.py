"""
Repository fetcher module for cloning and managing GitHub repositories.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import git
from git import Repo
import logging

logger = logging.getLogger(__name__)


class RepositoryFetcher:
    """Handles fetching and managing GitHub repositories."""
    
    def __init__(self, cache_dir: str = "./repo_cache", github_token: Optional[str] = None):
        """
        Initialize the repository fetcher.
        
        Args:
            cache_dir: Directory to cache cloned repositories
            github_token: Optional GitHub personal access token for authentication
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.github_token = github_token
        
    def _parse_repo_url(self, repo_identifier: str) -> Dict[str, str]:
        """
        Parse repository identifier into owner and repo name.
        
        Args:
            repo_identifier: Can be:
                - Full URL: https://github.com/owner/repo
                - Short form: owner/repo
                - With branch: owner/repo@branch
        
        Returns:
            Dict with owner, repo, branch, and url
        """
        branch = "main"  # Default branch
        
        # Handle branch specification
        if "@" in repo_identifier:
            repo_identifier, branch = repo_identifier.split("@", 1)
        
        # Handle full URL
        if repo_identifier.startswith("http"):
            # Extract owner/repo from URL
            parts = repo_identifier.rstrip("/").split("/")
            if len(parts) >= 2:
                repo = parts[-1].replace(".git", "")
                owner = parts[-2]
            else:
                raise ValueError(f"Invalid repository URL: {repo_identifier}")
        else:
            # Handle owner/repo format
            if "/" not in repo_identifier:
                raise ValueError(
                    f"Invalid repository identifier: {repo_identifier}. "
                    "Use format: owner/repo or https://github.com/owner/repo"
                )
            owner, repo = repo_identifier.split("/", 1)
            repo = repo.replace(".git", "")
        
        # Build authenticated URL if token is available
        if self.github_token:
            url = f"https://{self.github_token}@github.com/{owner}/{repo}.git"
        else:
            url = f"https://github.com/{owner}/{repo}.git"
        
        return {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "url": url,
            "cache_key": f"{owner}_{repo}_{branch}"
        }
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the cache directory path for a repository."""
        return self.cache_dir / cache_key
    
    def fetch_repository(
        self, 
        repo_identifier: str, 
        force_refresh: bool = False
    ) -> Path:
        """
        Fetch a repository, cloning if necessary or using cached version.
        
        Args:
            repo_identifier: Repository identifier (owner/repo, URL, or owner/repo@branch)
            force_refresh: If True, delete cache and clone fresh
        
        Returns:
            Path to the local repository directory
        
        Raises:
            Exception: If cloning or fetching fails
        """
        try:
            repo_info = self._parse_repo_url(repo_identifier)
            cache_path = self._get_cache_path(repo_info["cache_key"])
            
            # Remove cache if force refresh
            if force_refresh and cache_path.exists():
                logger.info(f"Force refresh: removing cached repo at {cache_path}")
                shutil.rmtree(cache_path)
            
            # Check if repository is already cached
            if cache_path.exists() and (cache_path / ".git").exists():
                logger.info(f"Using cached repository: {cache_path}")
                try:
                    # Try to pull latest changes
                    repo = Repo(cache_path)
                    origin = repo.remote("origin")
                    origin.pull(repo_info["branch"])
                    logger.info(f"Updated repository to latest {repo_info['branch']}")
                except Exception as e:
                    logger.warning(f"Failed to pull latest changes: {e}. Using cached version.")
                
                return cache_path
            
            # Clone the repository
            logger.info(f"Cloning repository from {repo_info['url']}")
            logger.info(f"Branch: {repo_info['branch']}")
            logger.info(f"Cache path: {cache_path}")
            
            Repo.clone_from(
                repo_info["url"],
                cache_path,
                branch=repo_info["branch"],
                depth=1  # Shallow clone for faster download
            )
            
            logger.info(f"Successfully cloned repository to {cache_path}")
            return cache_path
            
        except git.exc.GitCommandError as e:
            error_msg = str(e)
            if "Authentication failed" in error_msg or "authentication" in error_msg.lower():
                raise Exception(
                    f"GitHub authentication failed. The repository may be private. "
                    f"Please provide a valid GITHUB_TOKEN in your .env file."
                ) from e
            elif "Repository not found" in error_msg or "not found" in error_msg.lower():
                raise Exception(
                    f"Repository not found: {repo_identifier}. "
                    f"Please check the repository name and ensure it exists."
                ) from e
            else:
                raise Exception(f"Git error while fetching repository: {error_msg}") from e
        except Exception as e:
            raise Exception(f"Failed to fetch repository {repo_identifier}: {str(e)}") from e
    
    def get_repository_info(self, repo_path: Path) -> Dict[str, Any]:
        """
        Get information about a cloned repository.
        
        Args:
            repo_path: Path to the local repository
        
        Returns:
            Dictionary containing repository metadata
        """
        try:
            repo = Repo(repo_path)
            
            # Get current commit info
            commit = repo.head.commit
            
            # Count files by extension
            file_counts = {}
            total_files = 0
            
            for file_path in repo_path.rglob("*"):
                if file_path.is_file() and ".git" not in str(file_path):
                    ext = file_path.suffix or "no_extension"
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                    total_files += 1
            
            return {
                "path": str(repo_path),
                "branch": repo.active_branch.name,
                "commit_hash": commit.hexsha[:8],
                "commit_message": commit.message.strip(),
                "commit_author": str(commit.author),
                "commit_date": commit.committed_datetime.isoformat(),
                "total_files": total_files,
                "file_counts": file_counts,
            }
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return {
                "path": str(repo_path),
                "error": str(e)
            }
    
    def clear_cache(self, repo_identifier: Optional[str] = None):
        """
        Clear repository cache.
        
        Args:
            repo_identifier: If provided, clear only this repository. 
                           If None, clear all cached repositories.
        """
        if repo_identifier:
            repo_info = self._parse_repo_url(repo_identifier)
            cache_path = self._get_cache_path(repo_info["cache_key"])
            if cache_path.exists():
                shutil.rmtree(cache_path)
                logger.info(f"Cleared cache for {repo_identifier}")
        else:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared all repository caches")

