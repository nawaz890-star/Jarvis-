#!/usr/bin/env python3
"""JARVIS Pro v3.0 - Production-ready AI Assistant with GUI, Voice, Memory & Automation.

Usage:
    python main.py              # Run with GUI (default)
    python main.py --cli        # Run in CLI mode
    python main.py --voice      # Run in voice-only mode
    python main.py --debug      # Enable debug logging
"""

import sys
import argparse
import logging
import threading
from typing import Optional

from config import ASSISTANT_NAME, USER_NAME, DEBUG_MODE
from core.ai_engine import AIEngine
from core.memory import MemoryManager
from core.search_engine import SearchEngine
from core.voice_manager import VoiceManager
from core.automation import AutomationManager

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try importing GUI
try:
    from gui.main_window import JARVISGui
    GUI_AVAILABLE = True
except ImportError:
    logger.warning("GUI not available")
    GUI_AVAILABLE = False
    JARVISGui = None


class JARVISApplication:
    """Main JARVIS application controller."""

    def __init__(self, mode: str = "gui"):
        """Initialize JARVIS application.
        
        Args:
            mode: Execution mode (gui, cli, voice)
        """
        self.mode = mode
        self.ai_engine = AIEngine()
        self.memory = MemoryManager()
        self.search_engine = SearchEngine()
        self.voice_manager = VoiceManager()
        self.automation = AutomationManager()
        self.gui = None
        self.running = True

        logger.info(f"JARVIS initialized in {mode} mode")

    def _process_message(self, user_input: str) -> str:
        """Process user input through all systems.
        
        Args:
            user_input: User's message
            
        Returns:
            Response from assistant
        """
        if not user_input or not user_input.strip():
            return "Please provide a message."

        logger.info(f"Processing: {user_input[:100]}")

        try:
            # Check for search intent
            search_context = ""
            if self.search_engine.should_search(user_input):
                logger.info("Search intent detected, performing web search...")
                results = self.search_engine.search(user_input)
                search_context = self.search_engine.format_results_for_ai(results)
                logger.info(f"Found {len(results)} search results")

            # Get AI response
            response = self.ai_engine.ask(
                user_input,
                include_history=True,
                search_context=search_context
            )

            # Save to memory
            self.memory.save_conversation(user_input, response)

            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"Error: {str(e)}"

    def _voice_input_handler(self) -> None:
        """Handle voice input in background."""
        try:
            if not self.voice_manager.microphone_available:
                logger.warning("Microphone not available")
                if self.gui:
                    self.gui.set_status("● Error: Microphone not available", "#ff0000")
                return

            logger.info("Listening for voice input...")
            if self.gui:
                self.gui.set_status("● Listening...", "#ffff00")

            # Listen for wake word if enabled
            if not self.voice_manager.listen_for_wake_word(timeout=5):
                logger.debug("Wake word not detected")
                if self.gui:
                    self.gui.set_status("● Connected", "#00ff00")
                return

            # Listen for command
            user_input = self.voice_manager.listen()
            if not user_input:
                if self.gui:
                    self.gui.set_status("● Connected", "#00ff00")
                return

            # Display in GUI
            if self.gui:
                self.gui._display_message(USER_NAME, user_input)

            # Process and respond
            response = self._process_message(user_input)
            
            if self.gui:
                self.gui._display_message(ASSISTANT_NAME, response)
            
            # Speak response
            logger.info("Speaking response...")
            self.voice_manager.speak(response)

            if self.gui:
                self.gui.set_status(f"● Connected | {self.ai_engine.model_in_use}", "#00ff00")

        except Exception as e:
            logger.error(f"Voice input error: {e}", exc_info=True)
            if self.gui:
                self.gui.set_status(f"● Error: {str(e)[:30]}", "#ff0000")

    def run_gui(self) -> None:
        """Run GUI mode."""
        if not GUI_AVAILABLE or not JARVISGui:
            logger.error("GUI not available")
            print("GUI dependencies not installed. Use --cli mode or install: pip install customtkinter pillow")
            self.run_cli()
            return

        try:
            self.gui = JARVISGui(
                on_submit=self._process_message,
                on_voice_click=self._voice_input_handler
            )
            self.gui.set_ai_provider("Initializing...")
            logger.info("Starting GUI mode")
            self.gui.run()
        except Exception as e:
            logger.error(f"GUI error: {e}", exc_info=True)
            print(f"GUI error: {e}. Falling back to CLI.")
            self.run_cli()

    def run_cli(self) -> None:
        """Run CLI mode."""
        print(f"\n{'='*60}")
        print(f"{ASSISTANT_NAME} Pro v3.0 - CLI Mode")
        print(f"{'='*60}")
        print(f"Welcome, {USER_NAME}!\n")
        print("Commands:")
        print("  Type your question or command")
        print("  'voice' - Enter voice mode")
        print("  'memory' - View conversation history")
        print("  'clear' - Clear conversation history")
        print("  'exit' - Quit JARVIS")
        print(f"{'='*60}\n")

        while self.running:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in {"exit", "quit", "bye"}:
                    print(f"{ASSISTANT_NAME}: Goodbye, {USER_NAME}!")
                    break

                if user_input.lower() == "voice":
                    self._voice_input_handler()
                    continue

                if user_input.lower() == "memory":
                    history = self.memory.get_conversation_history(5)
                    for msg in history:
                        print(f"  User: {msg['user_message']}")
                        print(f"  {ASSISTANT_NAME}: {msg['assistant_response']}\n")
                    continue

                if user_input.lower() == "clear":
                    if self.memory.clear_all_history():
                        print(f"{ASSISTANT_NAME}: Conversation history cleared.\n")
                    continue

                if not user_input:
                    continue

                response = self._process_message(user_input)
                print(f"{ASSISTANT_NAME}: {response}\n")

            except KeyboardInterrupt:
                print(f"\n{ASSISTANT_NAME}: Goodbye!")
                break
            except Exception as e:
                logger.error(f"CLI error: {e}", exc_info=True)
                print(f"Error: {e}\n")

    def run_voice(self) -> None:
        """Run voice-only mode."""
        print(f"{ASSISTANT_NAME} Voice Mode - Say something to start")
        print("Press Ctrl+C to exit\n")

        while self.running:
            try:
                user_input = self.voice_manager.listen()
                if not user_input:
                    continue

                response = self._process_message(user_input)
                self.voice_manager.speak(response)

            except KeyboardInterrupt:
                print(f"\n{ASSISTANT_NAME}: Goodbye!")
                self.voice_manager.speak(f"Goodbye {USER_NAME}!")
                break
            except Exception as e:
                logger.error(f"Voice mode error: {e}", exc_info=True)
                print(f"Error: {e}")

    def run(self) -> None:
        """Run the application."""
        try:
            if self.mode == "gui":
                self.run_gui()
            elif self.mode == "cli":
                self.run_cli()
            elif self.mode == "voice":
                self.run_voice()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            print(f"Fatal error: {e}")
            sys.exit(1)
        finally:
            self.running = False
            logger.info("JARVIS shutdown complete")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JARVIS Pro v3.0 - Advanced AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # GUI mode (default)
  python main.py --cli        # CLI mode
  python main.py --voice      # Voice-only mode
  python main.py --debug      # Debug logging enabled
        """
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode instead of GUI"
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Run in voice-only mode"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")

    # Determine mode
    if args.voice:
        mode = "voice"
    elif args.cli:
        mode = "cli"
    else:
        mode = "gui"

    app = JARVISApplication(mode=mode)
    app.run()


if __name__ == "__main__":
    main()
