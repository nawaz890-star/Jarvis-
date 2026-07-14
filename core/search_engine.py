"""Web search integration using SerpAPI."""

import logging
from typing import List, Dict, Optional, Any

import requests

from config import SEARCH_API_KEY, MAX_SEARCH_RESULTS, SEARCH_TIMEOUT

logger = logging.getLogger(__name__)


class SearchEngine:
    """Web search engine using SerpAPI."""

    def __init__(self, api_key: Optional[str] = SEARCH_API_KEY):
        """Initialize search engine.
        
        Args:
            api_key: SerpAPI key
        """
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.available = bool(api_key)

    def search(self, query: str, num_results: int = MAX_SEARCH_RESULTS) -> List[Dict[str, Any]]:
        """Perform web search.
        
        Args:
            query: Search query
            num_results: Maximum results to return
            
        Returns:
            List of search results
        """
        if not self.available:
            logger.warning("Search API not configured")
            return []

        if not query or not query.strip():
            logger.warning("Empty search query")
            return []

        try:
            params = {
                "q": query.strip(),
                "api_key": self.api_key,
                "engine": "google",
                "num": num_results
            }

            response = requests.get(
                self.base_url,
                params=params,
                timeout=SEARCH_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            results = []

            # Extract organic results
            for item in data.get("organic_results", [])[:num_results]:
                try:
                    result = {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "position": item.get("position", len(results) + 1)
                    }
                    if result["title"] and result["link"]:
                        results.append(result)
                except (KeyError, ValueError) as e:
                    logger.debug(f"Error parsing result: {e}")
                    continue

            logger.info(f"Found {len(results)} search results for: {query[:50]}")
            return results

        except requests.Timeout:
            logger.error("Search API timeout")
            return []
        except requests.RequestException as e:
            logger.error(f"Search API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            return []

    def should_search(self, text: str) -> bool:
        """Determine if query requires web search.
        
        Args:
            text: User query
            
        Returns:
            True if search should be performed
        """
        if not self.available or not text:
            return False

        # Search triggers
        search_triggers = [
            "search", "google", "find", "look up", "who is", "what is",
            "when", "where", "why", "how", "current", "latest",
            "today", "now", "weather", "news", "stock"
        ]

        text_lower = text.lower()
        return any(trigger in text_lower for trigger in search_triggers)

    def format_results_for_ai(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for AI context.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string for AI context
        """
        if not results:
            return ""

        formatted = "Web Search Results:\n"
        for i, result in enumerate(results[:3], 1):
            formatted += f"\n{i}. {result['title']}\n"
            formatted += f"   {result['snippet'][:200]}...\n"
            formatted += f"   Source: {result['link']}\n"

        return formatted
