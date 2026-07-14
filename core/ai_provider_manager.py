"""Multi-provider AI manager with automatic switching and fallback."""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
from dataclasses import dataclass
import copy

from config import (
    GEMINI_API_KEY, OPENAI_API_KEY, OLLAMA_HOST, OLLAMA_MODEL,
    ENABLE_OLLAMA, SYSTEM_PROMPT, AI_RESPONSE_TIMEOUT
)

logger = logging.getLogger(__name__)


@dataclass
class AIProvider:
    """AI provider configuration."""
    name: str
    available: bool
    model: str
    type: str  # "cloud" or "local"


class AIProviderManager:
    """Manage multiple AI providers with intelligent fallback."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        """Initialize provider manager.
        
        Args:
            system_prompt: System prompt for AI
        """
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.current_provider = None
        self.providers = self._initialize_providers()
        self.max_history = 20

    def _initialize_providers(self) -> Dict[str, AIProvider]:
        """Initialize available AI providers."""
        providers = {}

        # Gemini
        try:
            from google import genai
            if GEMINI_API_KEY:
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    # Test connection
                    providers["gemini"] = AIProvider(
                        name="Gemini",
                        available=True,
                        model="gemini-1.5-flash",
                        type="cloud"
                    )
                    self.gemini_client = client
                    logger.info("✓ Gemini initialized")
                except Exception as e:
                    logger.error(f"Gemini initialization failed: {e}")
        except ImportError:
            logger.warning("google-generativeai not installed")

        # OpenAI
        try:
            from openai import OpenAI
            if OPENAI_API_KEY:
                try:
                    client = OpenAI(api_key=OPENAI_API_KEY)
                    providers["openai"] = AIProvider(
                        name="OpenAI",
                        available=True,
                        model="gpt-3.5-turbo",
                        type="cloud"
                    )
                    self.openai_client = client
                    logger.info("✓ OpenAI initialized")
                except Exception as e:
                    logger.error(f"OpenAI initialization failed: {e}")
        except ImportError:
            logger.warning("openai not installed")

        # Ollama (local)
        if ENABLE_OLLAMA:
            try:
                import requests
                response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
                if response.status_code == 200:
                    providers["ollama"] = AIProvider(
                        name="Ollama",
                        available=True,
                        model=OLLAMA_MODEL,
                        type="local"
                    )
                    logger.info(f"✓ Ollama initialized ({OLLAMA_MODEL})")
            except Exception as e:
                logger.debug(f"Ollama not available: {e}")

        return providers

    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            name: {
                "available": provider.available,
                "model": provider.model,
                "type": provider.type
            }
            for name, provider in self.providers.items()
        }

    async def ask(self, prompt: str, include_history: bool = True) -> str:
        """Ask a question to the best available AI.
        
        Args:
            prompt: User prompt
            include_history: Include conversation history
            
        Returns:
            AI response
        """
        if not prompt or not prompt.strip():
            return "Please provide a valid prompt."

        history = self._build_history(include_history)
        history.append({"role": "user", "content": prompt})

        # Try providers in order: Gemini -> OpenAI -> Ollama
        for provider_name in ["gemini", "openai", "ollama"]:
            if provider_name in self.providers and self.providers[provider_name].available:
                try:
                    response = await self._query_provider(provider_name, history)
                    if response:
                        self._update_history(prompt, response)
                        self.current_provider = provider_name
                        return response
                except Exception as e:
                    logger.error(f"Provider {provider_name} failed: {e}")
                    continue

        return "All AI providers are unavailable. Please check configuration."

    async def stream_response(self, prompt: str, include_history: bool = True) -> AsyncGenerator[str, None]:
        """Stream response from AI.
        
        Args:
            prompt: User prompt
            include_history: Include conversation history
            
        Yields:
            Response chunks
        """
        if not prompt or not prompt.strip():
            yield "Please provide a valid prompt."
            return

        history = self._build_history(include_history)
        history.append({"role": "user", "content": prompt})

        # Try OpenAI first (best streaming support)
        if "openai" in self.providers and self.providers["openai"].available:
            try:
                async for chunk in self._stream_openai(history):
                    yield chunk
                self.current_provider = "openai"
                return
            except Exception as e:
                logger.error(f"OpenAI streaming failed: {e}")

        # Fall back to regular response
        response = await self.ask(prompt, include_history)
        yield response

    async def _query_provider(self, provider_name: str, history: List[Dict]) -> Optional[str]:
        """Query a specific provider."""
        if provider_name == "gemini":
            return await self._query_gemini(history)
        elif provider_name == "openai":
            return await self._query_openai(history)
        elif provider_name == "ollama":
            return await self._query_ollama(history)
        return None

    async def _query_gemini(self, history: List[Dict]) -> Optional[str]:
        """Query Gemini API."""
        try:
            prompt_text = "\n".join(
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in history[-10:]
            )

            response = self.gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_text,
            )

            if response and hasattr(response, 'text'):
                return response.text.strip()
            return None
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

    async def _query_openai(self, history: List[Dict]) -> Optional[str]:
        """Query OpenAI API."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history[-10:],
                max_tokens=2048,
                temperature=0.7,
                timeout=AI_RESPONSE_TIMEOUT
            )

            if response and response.choices:
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    async def _query_ollama(self, history: List[Dict]) -> Optional[str]:
        """Query Ollama local model."""
        try:
            import requests

            response = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": history[-10:],
                    "stream": False
                },
                timeout=AI_RESPONSE_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    async def _stream_openai(self, history: List[Dict]) -> AsyncGenerator[str, None]:
        """Stream from OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history[-10:],
                max_tokens=2048,
                temperature=0.7,
                stream=True,
                timeout=AI_RESPONSE_TIMEOUT
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    yield text

            # Update history with full response
            if full_response:
                history_msg = {"role": "user", "content": history[-1]["content"]}
                if history_msg in self.conversation_history:
                    idx = self.conversation_history.index(history_msg)
                    self.conversation_history.insert(idx + 1, {"role": "assistant", "content": full_response})

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Streaming error: {str(e)}"

    def _build_history(self, include_history: bool) -> List[Dict]:
        """Build message history."""
        if include_history:
            return copy.deepcopy(self.conversation_history[-self.max_history:])
        return [{"role": "system", "content": self.system_prompt}]

    def _update_history(self, prompt: str, response: str) -> None:
        """Update conversation history."""
        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response})

        # Trim history if too long
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
        logger.info("Conversation history cleared")

    def set_system_prompt(self, prompt: str) -> None:
        """Set system prompt."""
        self.system_prompt = prompt
        self.conversation_history[0] = {"role": "system", "content": prompt}
