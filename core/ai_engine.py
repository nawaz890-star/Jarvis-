"""Advanced AI engine with multi-provider support."""

import logging
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator

from core.ai_provider_manager import AIProviderManager
from core.memory_system import MemorySystem
from core.search_engine import SearchEngine
from config import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AIEngine:
    """Main AI engine coordinating all providers and services."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        """Initialize AI engine.
        
        Args:
            system_prompt: System prompt for AI
        """
        self.provider_manager = AIProviderManager(system_prompt)
        self.memory_system = MemorySystem()
        self.search_engine = SearchEngine()
        logger.info("AI engine initialized")

    async def process_input(self, user_input: str, use_search: bool = True) -> str:
        """Process user input and generate response.
        
        Args:
            user_input: User's input text
            use_search: Use web search if needed
            
        Returns:
            AI response
        """
        if not user_input or not user_input.strip():
            return "Please provide a valid input."

        # Check if web search is needed
        search_context = ""
        if use_search and self._should_search(user_input):
            try:
                results = await self.search_engine.search(user_input, sources=["web"])
                if results:
                    search_context = "\n".join([f"- {r.title}: {r.snippet}" for r in results[:3]])
                    logger.info(f"Found {len(results)} search results")
            except Exception as e:
                logger.error(f"Search failed: {e}")

        # Get AI response
        if search_context:
            prompt = f"{user_input}\n\n[Web Search Results]\n{search_context}"
        else:
            prompt = user_input

        response = await self.provider_manager.ask(prompt, include_history=True)

        # Store in memory
        try:
            provider = self.provider_manager.current_provider or "unknown"
            self.memory_system.add_conversation(user_input, response, provider)
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

        return response

    async def stream_response(self, user_input: str) -> AsyncGenerator[str, None]:
        """Stream response from AI.
        
        Args:
            user_input: User's input text
            
        Yields:
            Response chunks
        """
        if not user_input or not user_input.strip():
            yield "Please provide a valid input."
            return

        # Check if web search is needed
        search_context = ""
        if self._should_search(user_input):
            try:
                results = await self.search_engine.search(user_input, sources=["web"])
                if results:
                    search_context = "\n".join([f"- {r.title}: {r.snippet}" for r in results[:3]])
            except Exception as e:
                logger.debug(f"Search failed: {e}")

        # Get streamed response
        if search_context:
            prompt = f"{user_input}\n\n[Web Search Results]\n{search_context}"
        else:
            prompt = user_input

        full_response = ""
        async for chunk in self.provider_manager.stream_response(prompt, include_history=True):
            full_response += chunk
            yield chunk

        # Store in memory
        try:
            provider = self.provider_manager.current_provider or "unknown"
            self.memory_system.add_conversation(user_input, full_response, provider)
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")

    def _should_search(self, query: str) -> bool:
        """Determine if web search should be performed.
        
        Args:
            query: User query
            
        Returns:
            True if search is needed
        """
        search_keywords = [
            "search", "find", "current", "latest", "today", "now",
            "weather", "news", "stock", "price", "how to", "what is"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in search_keywords)

    def get_status(self) -> Dict[str, Any]:
        """Get AI engine status.
        
        Returns:
            Status dictionary
        """
        return {
            "providers": self.provider_manager.get_provider_status(),
            "current_provider": self.provider_manager.current_provider,
            "conversation_length": len(self.provider_manager.conversation_history),
            "memory_available": True
        }
