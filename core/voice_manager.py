"""Advanced voice processing with wake word detection and TTS."""

import logging
import asyncio
import os
from threading import Thread
from typing import Optional, Callable
from queue import Queue

import speech_recognition as sr

from config import (
    VOICE_NAME, MIC_DEVICE_INDEX, VOICE_TIMEOUT,
    VOICE_PHRASE_LIMIT, ENABLE_WAKE_WORD, WAKE_WORD
)

logger = logging.getLogger(__name__)

# Import optional dependencies
try:
    import edge_tts
except ImportError:
    edge_tts = None
    logger.warning("edge-tts not installed")

try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None
    logger.warning("pygame not installed")


class VoiceManager:
    """Manages voice input and output."""

    def __init__(self):
        """Initialize voice manager."""
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.microphone_available = self._check_microphone()
        self.tts_available = edge_tts is not None and pygame is not None

    def _check_microphone(self) -> bool:
        """Check if microphone is available.
        
        Returns:
            True if microphone detected
        """
        try:
            with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
                logger.info(f"Microphone available at index {MIC_DEVICE_INDEX}")
                return True
        except Exception as e:
            logger.error(f"Microphone not available: {e}")
            return False

    def listen(self, timeout: int = VOICE_TIMEOUT) -> Optional[str]:
        """Listen to microphone input.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Recognized text or None
        """
        if not self.microphone_available:
            logger.error("Microphone not available")
            return None

        try:
            with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening...")
                
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=VOICE_PHRASE_LIMIT
                )

            # Try Google Speech Recognition
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text
            except sr.UnknownValueError:
                logger.debug("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition API error: {e}")
                return None

        except sr.MicrophoneError as e:
            logger.error(f"Microphone error: {e}")
            return None
        except sr.RequestError as e:
            logger.error(f"Microphone request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected voice error: {e}")
            return None

    def listen_for_wake_word(self, timeout: int = 30) -> bool:
        """Listen for wake word.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if wake word detected
        """
        if not ENABLE_WAKE_WORD:
            return True

        text = self.listen(timeout=timeout)
        if text and WAKE_WORD.lower() in text.lower():
            logger.info(f"Wake word '{WAKE_WORD}' detected")
            return True
        return False

    def speak(self, text: str, use_threading: bool = True) -> bool:
        """Generate and play speech.
        
        Args:
            text: Text to speak
            use_threading: Whether to use threading to avoid blocking
            
        Returns:
            True if successful
        """
        if not text or not text.strip():
            return False

        if not self.tts_available:
            logger.warning("Text-to-speech not available")
            logger.info(f"Text: {text}")
            return False

        if use_threading:
            thread = Thread(target=self._speak_internal, args=(text,), daemon=True)
            thread.start()
            return True
        else:
            return self._speak_internal(text)

    def _speak_internal(self, text: str) -> bool:
        """Internal speech generation.
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        try:
            # Generate speech
            audio_file = "temp_voice.mp3"
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def generate():
                comm = edge_tts.Communicate(text, VOICE_NAME)
                await comm.save(audio_file)
            
            loop.run_until_complete(generate())
            loop.close()

            # Play audio
            if os.path.exists(audio_file):
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Cleanup
                try:
                    pygame.mixer.music.stop()
                    os.remove(audio_file)
                except Exception as e:
                    logger.debug(f"Cleanup error: {e}")

            return True
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            return False

    def get_available_microphones(self) -> list:
        """Get list of available microphones.
        
        Returns:
            List of microphone device info
        """
        try:
            mics = sr.Microphone.list_microphone_indexes()
            logger.info(f"Found {len(mics)} microphones")
            return mics
        except Exception as e:
            logger.error(f"Error listing microphones: {e}")
            return []
