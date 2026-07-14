"""AI Provider Manager - Handles Gemini, OpenAI, and Ollama with automatic switching."""

import asyncio
import logging
import copy
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Available AI providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    OLLAMA = "ollama"
    NONE = "none"


@dataclass
class AIResponse:
    """AI Response data class."""
    content: str
    provider: AIProvider
    tokens_input: int = 0
    tokens_output: int = 0
    model: str = ""
    streaming: bool = False


class AIProviderManager:
    """Manage multiple AI providers with automatic fallback and switching."""

    def __init__(self):
        """Initialize AI Provider Manager."""
        self.gemini_client = None
        self.openai_client = None
        self.ollama_available = False
        self.current_provider = AIProvider.NONE
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._get_system_prompt()
        self.provider_priority = []
        
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize all available AI providers."""
        try:
            from google import genai
            import os
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                self.gemini_client = genai.Client(api_key=gemini_key)
                logger.info("✓ Gemini API initialized")
        except Exception as e:
            logger.debug(f"Gemini initialization failed: {e}")

        try:
            from openai import OpenAI
            import os
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("✓ OpenAI API initialized")
        except Exception as e:
            logger.debug(f"OpenAI initialization failed: {e}")

        try:
            import requests
            import os
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            response = requests.get(f"{ollama_host}/api/tags", timeout=2)
            if response.status_code == 200:
                self.ollama_available = True
                logger.info(f"✓ Ollama available at {ollama_host}")
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")

        # Set provider priority: Gemini -> OpenAI -> Ollama
        if self.gemini_client:
            self.provider_priority.append(AIProvider.GEMINI)
        if self.openai_client:
            self.provider_priority.append(AIProvider.OPENAI)
        if self.ollama_available:
            self.provider_priority.append(AIProvider.OLLAMA)

    async def ask(self, prompt: str, include_history: bool = True) -> AIResponse:
        """Ask AI a question with automatic provider switching.
        
        Args:
            prompt: User question
            include_history: Whether to include conversation history
            
        Returns:
            AIResponse with content and provider info
        """
        if not prompt or not prompt.strip():
            return AIResponse(content="Please provide a valid prompt.", provider=AIProvider.NONE)

        try:
            # Build history
            history = copy.deepcopy(self.conversation_history) if include_history else []
            history.append({"role": "user", "content": prompt})

            # Try providers in priority order
            for provider in self.provider_priority:
                try:
                    if provider == AIProvider.GEMINI:
                        response = await self._ask_gemini(history)
                    elif provider == AIProvider.OPENAI:
                        response = await self._ask_openai(history)
                    elif provider == AIProvider.OLLAMA:
                        response = await self._ask_ollama(history)
                    else:
                        continue

                    if response and response.content:
                        # Update history
                        self.conversation_history.append({"role": "user", "content": prompt})
                        self.conversation_history.append({"role": "assistant", "content": response.content})
                        self.current_provider = provider
                        return response
                except Exception as e:
                    logger.debug(f"Provider {provider.value} failed: {e}")
                    continue

            return AIResponse(
                content="All AI providers failed. Please check your API keys and configuration.",
                provider=AIProvider.NONE
            )

        except Exception as e:
            logger.error(f"Error in ask: {e}")
            return AIResponse(content=f"Error: {str(e)}", provider=AIProvider.NONE)

    async def stream(self, prompt: str, include_history: bool = True) -> AsyncGenerator[str, None]:
        """Stream AI response with automatic provider switching.
        
        Args:
            prompt: User question
            include_history: Whether to include history
            
        Yields:
            Response chunks
        """
        try:
            history = copy.deepcopy(self.conversation_history) if include_history else []
            history.append({"role": "user", "content": prompt})

            # Try OpenAI streaming first
            if AIProvider.OPENAI in self.provider_priority:
                async for chunk in self._stream_openai(history):
                    yield chunk
                return

            # Fallback to regular response
            response = await self.ask(prompt, include_history)
            yield response.content

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {str(e)}"

    async def _ask_gemini(self, history: List[Dict[str, str]]) -> Optional[AIResponse]:
        """Query Gemini API."""
        try:
            if not self.gemini_client:
                return None

            prompt_text = "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in history[-10:])
            
            response = self.gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_text,
            )

            if response and hasattr(response, 'text'):
                return AIResponse(
                    content=response.text.strip(),
                    provider=AIProvider.GEMINI,
                    model="gemini-1.5-flash"
                )
            return None
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

    async def _ask_openai(self, history: List[Dict[str, str]]) -> Optional[AIResponse]:
        """Query OpenAI API."""
        try:
            if not self.openai_client:
                return None

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history[-10:],
                max_tokens=2048,
                temperature=0.7,
            )

            if response and response.choices:
                return AIResponse(
                    content=response.choices[0].message.content.strip(),
                    provider=AIProvider.OPENAI,
                    tokens_input=response.usage.prompt_tokens,
                    tokens_output=response.usage.completion_tokens,
                    model="gpt-3.5-turbo"
                )
            return None
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    async def _ask_ollama(self, history: List[Dict[str, str]]) -> Optional[AIResponse]:
        """Query Ollama local model."""
        try:
            import requests
            import os
            
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
            
            if not self.ollama_available:
                return None

            response = requests.post(
                f"{ollama_host}/api/chat",
                json={
                    "model": ollama_model,
                    "messages": history[-10:],
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "").strip()
                if content:
                    return AIResponse(
                        content=content,
                        provider=AIProvider.OLLAMA,
                        model=ollama_model
                    )
            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    async def _stream_openai(self, history: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream OpenAI responses."""
        try:
            if not self.openai_client:
                return

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history[-10:],
                max_tokens=2048,
                temperature=0.7,
                stream=True,
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    yield text

            # Update history after streaming
            if full_response:
                user_prompt = history[-1]["content"] if history else ""
                if user_prompt:
                    self.conversation_history.append({"role": "user", "content": user_prompt})
                    self.conversation_history.append({"role": "assistant", "content": full_response})
                    self.current_provider = AIProvider.OPENAI

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_status(self) -> Dict[str, Any]:
        """Get current provider status."""
        return {
            "current_provider": self.current_provider.value,
            "gemini_available": bool(self.gemini_client),
            "openai_available": bool(self.openai_client),
            "ollama_available": self.ollama_available,
            "provider_priority": [p.value for p in self.provider_priority],
            "history_length": len(self.conversation_history)
        }

    @staticmethod
    def _get_system_prompt() -> str:
        """Get system prompt for JARVIS."""
        return """You are JARVIS, an advanced AI personal software engineer and operating system.

Capabilities:
- Write production-ready code in any programming language
- Generate complete websites, applications, and APIs
- Analyze and fix code bugs
- Manage projects and files
- Execute system commands safely
- Access real-time information via web search
- Remember conversations and user preferences
- Explain complex technical concepts
- Generate documentation and guides
- Optimize code for performance

Behavior:
- Be proactive and anticipate user needs
- Provide complete, working code (no pseudocode)
- Always consider security and best practices
- Be honest about limitations
- Ask clarifying questions when needed
- Provide step-by-step explanations
- Use markdown for code formatting
- Maintain context across conversations"""
