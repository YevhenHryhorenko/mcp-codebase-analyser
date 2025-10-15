"""
Intelligent recommendation system using LLM to analyze code sections.
"""
import os
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
import json

logger = logging.getLogger(__name__)


class RecommendationSystem:
    """Provides intelligent recommendations using LLM analysis."""
    
    def __init__(
        self,
        llm_provider: str = "openai",
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4o-mini"
    ):
        """
        Initialize the recommendation system.
        
        Args:
            llm_provider: LLM provider (openai, ollama)
            llm_api_key: API key for the LLM provider
            llm_model: Model to use for recommendations
        """
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        
        # Initialize OpenAI client
        if llm_provider == "openai":
            self.client = OpenAI(api_key=llm_api_key or os.getenv("LLM_API_KEY"))
        else:
            # For Ollama or other providers
            base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
            self.client = OpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"
            )
        
        logger.info(f"Initialized recommendation system with {llm_provider} provider")
    
    def analyze_and_recommend(
        self,
        user_request: str,
        search_results: List[Dict[str, Any]],
        repo_name: str
    ) -> Dict[str, Any]:
        """
        Analyze search results and provide intelligent recommendations.
        
        Args:
            user_request: The user's feature request or question
            search_results: List of relevant code sections from search
            repo_name: Name of the repository being analyzed
        
        Returns:
            Dictionary containing recommendations and analysis
        """
        if not search_results:
            return {
                "found_match": False,
                "message": f"No relevant sections found in {repo_name} for your request.",
                "recommendation": "This functionality might not exist in the repository yet. You may need to implement it from scratch.",
                "suggestions": [
                    "Check if there are similar patterns in the codebase",
                    "Look for base components that could be extended",
                    "Consider creating a new section based on existing conventions"
                ]
            }
        
        # Prepare context for LLM
        context = self._prepare_context(user_request, search_results, repo_name)
        
        # Get LLM recommendation
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            recommendation_text = response.choices[0].message.content
            
            # Parse the recommendation
            return self._parse_recommendation(recommendation_text, search_results)
            
        except Exception as e:
            logger.error(f"Error getting LLM recommendation: {e}")
            # Fallback to simple recommendation
            return self._create_fallback_recommendation(search_results)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are an expert code analyst helping developers find the best code sections for their needs.

Analyze the provided code sections and user request, then provide:
1. Whether a good match was found (true/false)
2. The best matching section(s) with file paths
3. Clear reasoning for your recommendation
4. Practical advice on how to use or extend the code
5. Any potential limitations or considerations

Format your response as JSON with these fields:
{
  "found_match": true/false,
  "best_match": "file/path/to/section.tsx",
  "best_match_name": "SectionName",
  "confidence": "high/medium/low",
  "reasoning": "Why this section is the best match...",
  "usage_advice": "How to use or extend this section...",
  "alternatives": ["Alternative section 1", "Alternative section 2"],
  "considerations": ["Things to consider..."],
  "code_snippet": "Brief relevant code snippet if helpful"
}

Be specific, practical, and helpful. If no good match exists, be honest about it."""
    
    def _prepare_context(
        self,
        user_request: str,
        search_results: List[Dict[str, Any]],
        repo_name: str
    ) -> str:
        """Prepare context for LLM analysis."""
        context = f"# User Request\n{user_request}\n\n"
        context += f"# Repository: {repo_name}\n\n"
        context += "# Found Code Sections\n\n"
        
        for i, result in enumerate(search_results[:5], 1):  # Top 5 results
            metadata = result.get("metadata", {})
            context += f"## Section {i} (Relevance: {result.get('score', 0):.2%})\n"
            context += f"- **File**: {metadata.get('file_path', 'unknown')}\n"
            context += f"- **Name**: {metadata.get('name', 'unknown')}\n"
            context += f"- **Type**: {metadata.get('type', 'unknown')}\n"
            context += f"- **Lines**: {metadata.get('start_line', 0)}-{metadata.get('end_line', 0)}\n\n"
            
            code = result.get("code", "")
            if code:
                context += f"```\n{code[:800]}\n```\n\n"  # Limit code length
        
        context += "\nProvide your analysis and recommendation in JSON format."
        
        return context
    
    def _parse_recommendation(
        self,
        recommendation_text: str,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Parse LLM recommendation response."""
        try:
            # Try to extract JSON from the response
            # Sometimes LLM wraps JSON in markdown code blocks
            if "```json" in recommendation_text:
                start = recommendation_text.find("```json") + 7
                end = recommendation_text.find("```", start)
                recommendation_text = recommendation_text[start:end].strip()
            elif "```" in recommendation_text:
                start = recommendation_text.find("```") + 3
                end = recommendation_text.find("```", start)
                recommendation_text = recommendation_text[start:end].strip()
            
            recommendation = json.loads(recommendation_text)
            
            # Add search results for reference
            recommendation["search_results"] = [
                {
                    "file": r.get("metadata", {}).get("file_path"),
                    "name": r.get("metadata", {}).get("name"),
                    "type": r.get("metadata", {}).get("type"),
                    "score": r.get("score")
                }
                for r in search_results[:5]
            ]
            
            return recommendation
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using text format")
            # Return as text if JSON parsing fails
            return {
                "found_match": len(search_results) > 0,
                "recommendation": recommendation_text,
                "search_results": [
                    {
                        "file": r.get("metadata", {}).get("file_path"),
                        "name": r.get("metadata", {}).get("name"),
                        "score": r.get("score")
                    }
                    for r in search_results[:5]
                ]
            }
    
    def _create_fallback_recommendation(
        self,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a simple recommendation without LLM."""
        if not search_results:
            return {
                "found_match": False,
                "message": "No relevant sections found"
            }
        
        best_match = search_results[0]
        metadata = best_match.get("metadata", {})
        
        return {
            "found_match": True,
            "best_match": metadata.get("file_path", "unknown"),
            "best_match_name": metadata.get("name", "unknown"),
            "confidence": "medium" if best_match.get("score", 0) > 0.7 else "low",
            "score": best_match.get("score", 0),
            "reasoning": f"This section has the highest semantic similarity ({best_match.get('score', 0):.2%}) to your request.",
            "search_results": [
                {
                    "file": r.get("metadata", {}).get("file_path"),
                    "name": r.get("metadata", {}).get("name"),
                    "type": r.get("metadata", {}).get("type"),
                    "score": r.get("score")
                }
                for r in search_results[:5]
            ]
        }
    
    def summarize_repository(
        self,
        repo_name: str,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a summary of the repository structure.
        
        Args:
            repo_name: Name of the repository
            sections: List of all code sections
        
        Returns:
            Dictionary containing repository summary
        """
        # Group sections by file and type
        by_file = {}
        by_type = {}
        
        for section in sections:
            # Fields are at top level in section dict from CodeSection.to_dict()
            file_path = section.get("file_path", "unknown")
            section_type = section.get("type", "unknown")
            section_name = section.get("name", "unknown")
            
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(section_name)
            
            if section_type not in by_type:
                by_type[section_type] = 0
            by_type[section_type] += 1
        
        return {
            "repository": repo_name,
            "total_sections": len(sections),
            "files_analyzed": len(by_file),
            "section_types": by_type,
            "file_structure": {
                file: names for file, names in sorted(by_file.items())[:20]  # Top 20 files
            }
        }

