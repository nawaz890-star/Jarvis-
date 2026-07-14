"""Integrated search functionality for documentation, GitHub, Stack Overflow, and web."""

import logging
from typing import List, Dict, Any, Optional
import asyncio

import requests
from pydantic import BaseModel

from config import SEARCH_API_KEY, MAX_SEARCH_RESULTS, SEARCH_TIMEOUT

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Search result model."""
    title: str
    url: str
    snippet: str
    source: str  # "web", "github", "stackoverflow", "docs"
    relevance: float = 1.0


class SearchEngine:
    """Multi-source search engine."""

    def __init__(self, api_key: Optional[str] = SEARCH_API_KEY):
        """Initialize search engine.
        
        Args:
            api_key: Search API key (SerpAPI)
        """
        self.api_key = api_key
        self.search_url = "https://serpapi.com/search"
        logger.info("Search engine initialized")

    async def search(self, query: str, sources: Optional[List[str]] = None) -> List[SearchResult]:
        """Search across multiple sources.
        
        Args:
            query: Search query
            sources: List of sources to search ("web", "github", "stackoverflow", "docs")
            
        Returns:
            List of search results
        """
        if not query or not query.strip():
            return []

        sources = sources or ["web"]
        results = []

        for source in sources:
            if source == "web":
                web_results = await self._search_web(query)
                results.extend(web_results)
            elif source == "github":
                gh_results = await self._search_github(query)
                results.extend(gh_results)
            elif source == "stackoverflow":
                so_results = await self._search_stackoverflow(query)
                results.extend(so_results)
            elif source == "docs":
                doc_results = await self._search_docs(query)
                results.extend(doc_results)

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:MAX_SEARCH_RESULTS]

    async def _search_web(self, query: str) -> List[SearchResult]:
        """Search the web using SerpAPI.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        if not self.api_key:
            logger.warning("Search API key not configured")
            return []

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "num": MAX_SEARCH_RESULTS
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.search_url, params=params, timeout=SEARCH_TIMEOUT)
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("organic_results", [])[:MAX_SEARCH_RESULTS]:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="web",
                    relevance=1.0
                )
                results.append(result)

            logger.debug(f"Web search: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    async def _search_github(self, query: str) -> List[SearchResult]:
        """Search GitHub repositories.
        
        Args:
            query: Search query
            
        Returns:
            List of GitHub results
        """
        try:
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": MAX_SEARCH_RESULTS
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    "https://api.github.com/search/repositories",
                    params=params,
                    timeout=SEARCH_TIMEOUT
                )
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("items", [])[:MAX_SEARCH_RESULTS]:
                result = SearchResult(
                    title=item.get("name", ""),
                    url=item.get("html_url", ""),
                    snippet=item.get("description", ""),
                    source="github",
                    relevance=min(1.0, item.get("stargazers_count", 0) / 1000)  # Normalize by stars
                )
                results.append(result)

            logger.debug(f"GitHub search: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"GitHub search error: {e}")
            return []

    async def _search_stackoverflow(self, query: str) -> List[SearchResult]:
        """Search Stack Overflow.
        
        Args:
            query: Search query
            
        Returns:
            List of Stack Overflow results
        """
        try:
            params = {
                "intitle": query,
                "site": "stackoverflow.com",
                "sort": "relevance",
                "order": "desc",
                "pagesize": MAX_SEARCH_RESULTS
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    "https://api.stackexchange.com/2.3/search/advanced",
                    params=params,
                    timeout=SEARCH_TIMEOUT
                )
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get("items", [])[:MAX_SEARCH_RESULTS]:
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=f"Score: {item.get('score', 0)}",
                    source="stackoverflow",
                    relevance=min(1.0, item.get("score", 0) / 100)  # Normalize by score
                )
                results.append(result)

            logger.debug(f"Stack Overflow search: {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Stack Overflow search error: {e}")
            return []

    async def _search_docs(self, query: str) -> List[SearchResult]:
        """Search common documentation sites.
        
        Args:
            query: Search query
            
        Returns:
            List of documentation results
        """
        results = []
        doc_sites = [
            "python.org",
            "docs.python.org",
            "developer.mozilla.org",
            "nodejs.org",
            "react.dev",
            "nextjs.org",
            "docs.djangoproject.com"
        ]

        for site in doc_sites:
            try:
                params = {
                    "q": f"{query} site:{site}",
                    "api_key": self.api_key,
                    "engine": "google",
                    "num": 1
                }

                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(self.search_url, params=params, timeout=SEARCH_TIMEOUT)
                )

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("organic_results", [])[:1]:
                        result = SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source="docs",
                            relevance=1.0
                        )
                        results.append(result)
                        break
            except Exception as e:
                logger.debug(f"Doc search for {site} failed: {e}")

        logger.debug(f"Docs search: {len(results)} results")
        return results
