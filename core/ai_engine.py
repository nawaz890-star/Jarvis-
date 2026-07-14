"""Enhanced AI Engine with Gemini, OpenAI, and Ollama support with streaming."""

import logging
import copy
import json
from typing import Optional, List, Dict, Any, Generator

from config import (
    GEMINI_API_KEY, OPENAI_API_KEY, SYSTEM_PROMPT, AI_RESPONSE_TIMEOUT,
    OLLAMA_MODEL, OLLAMA_HOST, ENABLE_OLLAMA
)

logger = logging.getLogger(__name__)

# Import AI clients
gemini_client = None
openai_client = None
ollama_available = False

try:
    from google import genai
    if GEMINI_API_KEY:
        try:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("Google Gemini client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
except ImportError:
    logger.warning("google-generativeai not installed")

try:
    from openai import OpenAI
    if OPENAI_API_KEY:
        try:
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
except ImportError:
    logger.warning("openai not installed")

try:
    import requests
    if ENABLE_OLLAMA:
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if response.status_code == 200:
                ollama_available = True
                logger.info(f"Ollama available at {OLLAMA_HOST}")
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
except ImportError:
    logger.warning("requests not installed")


class AIEngine:
    """Unified AI engine with multiple provider support including streaming."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT):
        """Initialize AI engine.
        
        Args:
            system_prompt: System prompt for the AI
        """
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        self.model_in_use: str = "none"
        self.provider_priority = self._get_provider_priority()

    def _get_provider_priority(self) -> List[str]:
        """Get provider priority based on availability.
        
        Returns:
            List of available providers in priority order
        """
        priority = []
        if gemini_client:
            priority.append("gemini")
        if openai_client:
            priority.append("openai")
        if ollama_available:
            priority.append("ollama")
        return priority

    def ask(self, prompt: str, include_history: bool = True, search_context: Optional[str] = None) -> str:
        """Ask the AI a question.
        
        Args:
            prompt: User's question or statement
            include_history: Whether to include conversation history
            search_context: Additional context from web search
            
        Returns:
            AI's response text
        """
        if not prompt or not prompt.strip():
            return "Please provide a valid prompt."

        try:
            # Add search context if provided
            if search_context:
                prompt = f"{prompt}\n\n[Web Search Results]\n{search_context}"

            # Build message history
            history = copy.deepcopy(self.conversation_history) if include_history else [{"role": "system", "content": self.system_prompt}]
            history.append({"role": "user", "content": prompt})

            # Try providers in priority order
            for provider in self.provider_priority:
                if provider == "gemini":
                    response = self._ask_gemini(history)
                elif provider == "openai":
                    response = self._ask_openai(history)
                elif provider == "ollama":
                    response = self._ask_ollama(history)
                else:
                    continue

                if response:
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": response})
                    self.model_in_use = provider.capitalize()
                    return response

            return "AI is not configured. Please set GEMINI_API_KEY, OPENAI_API_KEY, or enable Ollama."

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return f"Error: {str(e)}"

    def _ask_gemini(self, history: List[Dict[str, str]]) -> Optional[str]:
        """Query Google Gemini.
        
        Args:
            history: Conversation history
            
        Returns:
            Response text or None if failed
        """
        try:
            if not gemini_client:
                return None

            # Format for Gemini
            prompt_text = "\n".join(
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in history[-10:]
            )

            response = gemini_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt_text,
            )

            if response and hasattr(response, 'text'):
                text = response.text.strip()
                logger.debug(f"Gemini response: {text[:100]}...")
                return text

            return None
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None

    def _ask_openai(self, history: List[Dict[str, str]]) -> Optional[str]:
        """Query OpenAI GPT.
        
        Args:
            history: Conversation history
            
        Returns:
            Response text or None if failed
        """
        try:
            if not openai_client:
                return None

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=history[-10:],
                max_tokens=2048,
                temperature=0.7,
                timeout=AI_RESPONSE_TIMEOUT
            )

            if response and response.choices:
                text = response.choices[0].message.content.strip()
                logger.debug(f"OpenAI response: {text[:100]}...")
                return text

            return None
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return None

    def _ask_ollama(self, history: List[Dict[str, str]]) -> Optional[str]:
        """Query Ollama local model.
        
        Args:
            history: Conversation history
            
        Returns:
            Response text or None if failed
        """
        try:
            if not ollama_available:
                return None

            import requests

            # Format messages for Ollama
            messages = []
            for msg in history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            response = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                },
                timeout=AI_RESPONSE_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                text = data.get("message", {}).get("content", "").strip()
                if text:
                    logger.debug(f"Ollama response: {text[:100]}...")
                    return text

            return None
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None

    def stream_response(self, prompt: str, include_history: bool = True) -> Generator[str, None, None]:
        """Stream response from AI with real-time output.
        
        Args:
            prompt: User's question
            include_history: Whether to include history
            
        Yields:
            Text chunks as they arrive
        """
        try:
            if not prompt or not prompt.strip():
                yield "Please provide a valid prompt."
                return

            # Build message history
            history = copy.deepcopy(self.conversation_history) if include_history else [{"role": "system", "content": self.system_prompt}]
            history.append({"role": "user", "content": prompt})

            # Try OpenAI streaming first (best support)
            if openai_client:
                try:
                    response = openai_client.chat.completions.create(
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
                    
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": full_response})
                    self.model_in_use = "OpenAI"
                    return
                except Exception as e:
                    logger.debug(f"OpenAI streaming failed: {e}")

            # Fall back to non-streaming response
            response = self.ask(prompt, include_history)
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response})
            yield response

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {str(e)}"

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
        logger.info("Conversation history cleared")

    def set_system_prompt(self, prompt: str) -> None:
        """Update system prompt.
        
        Args:
            prompt: New system prompt
        """
        self.system_prompt = prompt
        self.conversation_history[0] = {"role": "system", "content": prompt}
        logger.info("System prompt updated")

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status.
        
        Returns:
            Status dictionary
        """
        return {
            "current_model": self.model_in_use,
            "gemini_available": bool(gemini_client),
            "openai_available": bool(openai_client),
            "ollama_available": ollama_available,
            "provider_priority": self.provider_priority,
            "history_length": len(self.conversation_history)
        }

    def get_system_prompt_for_coding(self) -> str:
        """Get specialized system prompt for coding tasks.
        
        Returns:
            Coding-focused system prompt
        """
        return """You are an expert software engineer and coding assistant. Your capabilities include:

1. Code Generation:
   - Write complete, production-ready code in any language
   - Support Python, JavaScript, TypeScript, Java, C++, C#, PHP, Go, Rust, SQL, HTML, CSS, React, Vue, Angular, Node.js, Next.js
   - Generate frameworks, libraries, and tools
   - Create unit tests, integration tests, and E2E tests
   - Generate Docker configurations and deployment scripts

2. Code Analysis:
   - Review code for bugs, security issues, performance problems
   - Suggest optimizations and best practices
   - Explain complex code sections
   - Refactor code for readability and efficiency
   - Generate architecture diagrams

3. Documentation:
   - Generate comprehensive documentation
   - Create README files
   - Write API documentation
   - Generate code comments and docstrings
   - Create architecture guides

4. File Operations:
   - Read and analyze existing code files
   - Create new files with proper structure
   - Edit and refactor existing code
   - Generate project structures
   - Create configuration files

Always provide:
- Complete, working code (no pseudocode)
- Explanations of key concepts
- Error handling and edge cases
- Performance considerations
- Security best practices"""

    def get_system_prompt_for_websites(self) -> str:
        """Get specialized system prompt for website generation.
        
        Returns:
            Website generation system prompt
        """
        return """You are an expert web developer specializing in full-stack development. Your capabilities include:

1. Website Generation:
   - Create responsive, modern websites
   - Generate landing pages, portfolios, SaaS platforms
   - Build with HTML, CSS, JavaScript, React, Next.js, Vue, Angular
   - Implement responsive design (mobile-first)
   - Optimize for SEO and performance
   - Generate accessible (a11y) compliant code

2. Frontend:
   - Component-based architecture
   - State management (Redux, Zustand, Vuex, Context API)
   - Modern CSS (Tailwind, Bootstrap, Material-UI)
   - Authentication and authorization UI
   - Form validation and handling
   - Real-time updates (WebSocket, Server-Sent Events)

3. Backend:
   - REST API design
   - Database schemas (SQL, NoSQL)
   - Authentication (JWT, OAuth2, Sessions)
   - Middleware and error handling
   - Caching strategies
   - Rate limiting and security

4. DevOps:
   - Docker containerization
   - Kubernetes configuration
   - CI/CD pipelines (GitHub Actions, GitLab CI)
   - Environment management
   - Monitoring and logging
   - Performance optimization

Always provide:
- Complete, production-ready code
- Responsive design examples
- Security best practices
- Performance optimization
- Scalability considerations"""
