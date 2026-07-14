"""Voice Manager - Continuous listening, recognition, and TTS with GUI responsiveness."""

import asyncio
import logging
import threading
from typing import Optional, Callable, Any
from queue import Queue

logger = logging.getLogger(__name__)


class VoiceManager:
    """Manage voice input/output with background processing."""

    def __init__(self, wake_word: str = "jarvis"):
        """Initialize Voice Manager.
        
        Args:
            wake_word: Wake word to trigger listening
        """
        self.wake_word = wake_word.lower()
        self.is_listening = False
        self.is_speaking = False
        self.recognition = None
        self.microphone = None
        self.listener_thread = None
        self.speaker_queue: Queue = Queue()
        self.speech_queue: Queue = Queue()
        self._init_voice_engines()

    def _init_voice_engines(self) -> None:
        """Initialize speech recognition and TTS engines."""
        try:
            import speech_recognition as sr
            self.recognition = sr.Recognizer()
            self.microphone = sr.Microphone()
            logger.info("✓ Speech recognition initialized")
        except Exception as e:
            logger.error(f"Speech recognition init failed: {e}")

        try:
            import edge_tts
            logger.info("✓ Edge TTS initialized")
        except Exception as e:
            logger.error(f"Edge TTS init failed: {e}")

    def start_listening(self, on_recognized: Callable[[str], Any]) -> None:
        """Start background listening thread.
        
        Args:
            on_recognized: Callback function for recognized speech
        """
        if self.is_listening:
            return

        self.is_listening = True
        self.listener_thread = threading.Thread(
            target=self._listen_loop,
            args=(on_recognized,),
            daemon=True
        )
        self.listener_thread.start()
        logger.info("Voice listening started")

    def stop_listening(self) -> None:
        """Stop listening thread."""
        self.is_listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        logger.info("Voice listening stopped")

    def _listen_loop(self, on_recognized: Callable[[str], Any]) -> None:
        """Main listening loop."""
        while self.is_listening:
            try:
                if not self.recognition or not self.microphone:
                    return

                with self.microphone as source:
                    self.recognition.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognition.listen(source, timeout=5, phrase_time_limit=10)

                # Process in thread to avoid blocking
                threading.Thread(
                    target=self._process_audio,
                    args=(audio, on_recognized),
                    daemon=True
                ).start()

            except Exception as e:
                logger.debug(f"Listening error: {e}")

    def _process_audio(self, audio: Any, callback: Callable[[str], Any]) -> None:
        """Process recognized audio."""
        try:
            if not self.recognition:
                return

            text = self.recognition.recognize_google(audio)
            logger.info(f"Recognized: {text}")

            if self.wake_word in text.lower():
                # Extract command after wake word
                command = text.lower().replace(self.wake_word, "").strip()
                if command:
                    callback(command)
            else:
                callback(text)

        except Exception as e:
            logger.debug(f"Audio processing error: {e}")

    async def speak(self, text: str, voice: str = "en-US-GuyNeural") -> None:
        """Speak text using TTS.
        
        Args:
            text: Text to speak
            voice: Voice name
        """
        if not text or self.is_speaking:
            return

        try:
            import edge_tts
            
            self.is_speaking = True
            
            # Generate speech in background
            communicate = edge_tts.Communicate(text, voice)
            
            # Use pygame for playback
            import pygame
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                await communicate.save(tmp.name)
                
                pygame.mixer.music.load(tmp.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                logger.info(f"Spoken: {text[:50]}...")
        
        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            self.is_speaking = False

    def stop_speaking(self) -> None:
        """Stop current speech."""
        try:
            import pygame
            pygame.mixer.music.stop()
            self.is_speaking = False
            logger.info("Speech stopped")
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")

    def get_status(self) -> dict:
        """Get voice status."""
        return {
            "listening": self.is_listening,
            "speaking": self.is_speaking,
            "recognition_available": bool(self.recognition),
            "microphone_available": bool(self.microphone)
        }
