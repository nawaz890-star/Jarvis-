"""AI Engine with Gemini and OpenAI support with fallback."""

import logging
import copy
from typing import Optional, List, Dict, Any, Generator

from config import GEMINI_API_KEY, OPENAI_API_KEY, SYSTEM_PROMPT, AI_RESPONSE_TIMEOUT

logger = logging.getLogger(__name__)

# Import AI clients
gemini_client = None
openai_client = None

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
    from openai import OpenAI, APIError
    if OPENAI_API_KEY:
        try:
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
except ImportError:
    logger.warning("openai not installed")
    APIError = Exception


class AIEngine:
    """Unified AI engine with multiple provider support."""

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

            # Try Gemini first
            if gemini_client:
                response = self._ask_gemini(history)
                if response:
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": response})
                    self.model_in_use = "Gemini"
                    return response

            # Fall back to OpenAI
            if openai_client:
                response = self._ask_openai(history)
                if response:
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": response})
                    self.model_in_use = "OpenAI"
                    return response

            return "AI is not configured. Please set GEMINI_API_KEY or OPENAI_API_KEY."

        except Exception as e:
            logger.error(f"Error generating response: {e}")
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
                for msg in history[-6:]
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
                messages=history,
                max_tokens=1024,
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

    def stream_response(self, prompt: str, include_history: bool = True) -> Generator[str, None, None]:
        """Stream response from AI (for real-time output).
        
        Args:
            prompt: User's question
            include_history: Whether to include history
            
        Yields:
            Text chunks as they arrive
        """
        try:
            # For now, yield the complete response
            # Full streaming would require separate implementation
            response = self.ask(prompt, include_history)
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
            "history_length": len(self.conversation_history)
        }
