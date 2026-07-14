"""Advanced voice processing with continuous listening and reliable TTS."""

import logging
import threading
import queue
import asyncio
from typing import Optional, Callable, List

import speech_recognition as sr
from pydantic import BaseModel

from config import (
    WAKE_WORD, ENABLE_WAKE_WORD, VOICE_NAME, MIC_DEVICE_INDEX,
    VOICE_TIMEOUT, VOICE_PHRASE_LIMIT, VOICE_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class VoiceConfig(BaseModel):
    """Voice configuration."""
    wake_word: str = WAKE_WORD
    enable_wake_word: bool = ENABLE_WAKE_WORD
    voice_name: str = VOICE_NAME
    mic_index: int = MIC_DEVICE_INDEX
    timeout: int = VOICE_TIMEOUT
    phrase_limit: int = VOICE_PHRASE_LIMIT
    confidence_threshold: float = VOICE_CONFIDENCE_THRESHOLD


class VoiceProcessor:
    """Handle speech recognition and text-to-speech."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        """Initialize voice processor.
        
        Args:
            config: Voice configuration
        """
        self.config = config or VoiceConfig()
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.recognition_callbacks: List[Callable] = []
        self.listener_thread = None
        self._setup_tts()
        logger.info(f"Voice processor initialized - Wake word: {self.config.wake_word}")

    def _setup_tts(self) -> None:
        """Setup text-to-speech engine."""
        try:
            import edge_tts
            self.tts = edge_tts
            logger.info("Edge TTS initialized")
        except ImportError:
            logger.warning("edge_tts not installed, TTS disabled")
            self.tts = None

    def start_listening(self) -> None:
        """Start continuous voice listening in background thread."""
        if self.is_listening:
            logger.warning("Already listening")
            return

        self.is_listening = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        logger.info("Voice listening started")

    def stop_listening(self) -> None:
        """Stop voice listening."""
        self.is_listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        logger.info("Voice listening stopped")

    def _listen_loop(self) -> None:
        """Continuous listening loop."""
        try:
            with sr.Microphone(device_index=self.config.mic_index) as source:
                # Adjust for ambient noise
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.recognizer.dynamic_energy_threshold = True

                logger.info(f"Listening for wake word: '{self.config.wake_word}'")

                while self.is_listening:
                    try:
                        # Listen for audio
                        audio = self.recognizer.listen(
                            source,
                            timeout=self.config.timeout,
                            phrase_time_limit=self.config.phrase_limit
                        )

                        # Recognize speech
                        try:
                            text = self.recognizer.recognize_google(audio)
                            logger.debug(f"Recognized: {text}")

                            # Check for wake word
                            if self._check_wake_word(text):
                                self.speech_queue.put(text)
                                self._trigger_callbacks(text)

                        except sr.UnknownValueError:
                            logger.debug("Could not understand audio")
                        except sr.RequestError as e:
                            logger.error(f"Speech recognition error: {e}")

                    except sr.RequestError as e:
                        logger.error(f"Microphone error: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Listen loop error: {e}")

        except Exception as e:
            logger.error(f"Voice listening error: {e}")
            self.is_listening = False

    def _check_wake_word(self, text: str) -> bool:
        """Check if wake word is in text.
        
        Args:
            text: Recognized text
            
        Returns:
            True if wake word detected
        """
        if not self.config.enable_wake_word:
            return True

        text_lower = text.lower()
        wake_word_lower = self.config.wake_word.lower()
        return wake_word_lower in text_lower

    def _trigger_callbacks(self, text: str) -> None:
        """Trigger recognition callbacks.
        
        Args:
            text: Recognized text
        """
        for callback in self.recognition_callbacks:
            try:
                callback(text)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def register_recognition_callback(self, callback: Callable[[str], None]) -> None:
        """Register callback for speech recognition.
        
        Args:
            callback: Function to call with recognized text
        """
        self.recognition_callbacks.append(callback)

    async def speak(self, text: str, wait: bool = False) -> None:
        """Speak text using text-to-speech.
        
        Args:
            text: Text to speak
            wait: Wait for speech to complete
        """
        if not text or not self.tts:
            return

        self.is_speaking = True
        try:
            # Use edge_tts for reliable speech
            communicate = self.tts.Communicate(text, self.config.voice_name)
            await communicate.save("temp_speech.mp3")

            # Play audio
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load("temp_speech.mp3")
            pygame.mixer.music.play()

            if wait:
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self.is_speaking = False

    def stop_speaking(self) -> None:
        """Stop speaking immediately."""
        try:
            import pygame
            pygame.mixer.music.stop()
            self.is_speaking = False
            logger.info("Speech stopped")
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")

    def get_microphone_status(self) -> Dict[str, Any]:
        """Get microphone status.
        
        Returns:
            Status dictionary
        """
        return {
            "listening": self.is_listening,
            "speaking": self.is_speaking,
            "device_index": self.config.mic_index,
            "wake_word_enabled": self.config.enable_wake_word,
            "wake_word": self.config.wake_word
        }

    def set_microphone_device(self, device_index: int) -> bool:
        """Set microphone device.
        
        Args:
            device_index: Microphone device index
            
        Returns:
            True if successful
        """
        try:
            self.config.mic_index = device_index
            logger.info(f"Microphone device set to {device_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to set microphone: {e}")
            return False


from typing import Dict, Any
