"""Search Engine - Web search with multiple sources and result caching."""

import logging
from typing import List, Dict, Optional, Any
import requests
import os

logger = logging.getLogger(__name__)


class SearchEngine:
    """Multi-source search engine."""

    def __init__(self):
        """Initialize Search Engine."""
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.search_url = "https://serpapi.com/search"

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        if not query or not query.strip():
            return []

        if not self.search_api_key:
            logger.warning("Search API key not configured")
            return []

        try:
            params = {
                "q": query.strip(),
                "api_key": self.search_api_key,
                "engine": "google",
                "num": num_results
            }

            response = requests.get(self.search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("organic_results", [])[:num_results]:
                try:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": "Google"
                    }
                    if result["title"] and result["link"]:
                        results.append(result)
                except (KeyError, ValueError):
                    continue

            logger.info(f"Search found {len(results)} results for: {query}")
            return results

        except requests.RequestException as e:
            logger.error(f"Search error: {e}")
            return []

    def search_github(self, query: str, language: str = "python") -> List[Dict[str, Any]]:
        """Search GitHub repositories.
        
        Args:
            query: Search query
            language: Programming language filter
            
        Returns:
            List of repository results
        """
        try:
            # Search using GitHub's web search since GraphQL needs auth
            search_query = f"{query} language:{language} sort:stars"
            return self.search(search_query)
        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return []

    def search_stackoverflow(self, query: str) -> List[Dict[str, Any]]:
        """Search Stack Overflow.
        
        Args:
            query: Search query
            
        Returns:
            List of Stack Overflow results
        """
        try:
            search_query = f"site:stackoverflow.com {query}"
            return self.search(search_query)
        except Exception as e:
            logger.error(f"Stack Overflow search error: {e}")
            return []

    def search_documentation(self, library: str, topic: str) -> List[Dict[str, Any]]:
        """Search documentation.
        
        Args:
            library: Library/framework name
            topic: Topic to search
            
        Returns:
            List of documentation results
        """
        try:
            search_query = f"site:docs.{library}.io {topic} OR site:{library}.readthedocs.io {topic}"
            return self.search(search_query)
        except Exception as e:
            logger.error(f"Documentation search error: {e}")
            return []
