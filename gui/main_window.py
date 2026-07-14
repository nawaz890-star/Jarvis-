"""Main GUI window with modern dark theme."""

import logging
import threading
from typing import Callable, Optional
from datetime import datetime

try:
    import customtkinter as ctk
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    logging.error("customtkinter or pillow not installed")
    ctk = None
    Image = None

from config import (
    GUI_WIDTH, GUI_HEIGHT, GUI_FONT_SIZE, ASSISTANT_NAME, USER_NAME
)

logger = logging.getLogger(__name__)


class JARVISGui:
    """Main GUI window for JARVIS."""

    def __init__(self, on_submit: Callable[[str], str], on_voice_click: Optional[Callable] = None):
        """Initialize GUI.
        
        Args:
            on_submit: Callback when user submits message
            on_voice_click: Callback when voice button clicked
        """
        if not ctk:
            logger.error("customtkinter not available")
            return

        self.on_submit = on_submit
        self.on_voice_click = on_voice_click
        self.is_processing = False
        self.ai_provider = "Unknown"

        # Create root window
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title(f"{ASSISTANT_NAME} Pro v3.0")
        self.root.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        self.root.minsize(800, 500)

        self._setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # Header
        header = ctk.CTkFrame(self.root, fg_color="#1a1a2e")
        header.pack(side="top", fill="x", padx=0, pady=0)

        title_frame = ctk.CTkFrame(header, fg_color="#1a1a2e")
        title_frame.pack(fill="x", padx=15, pady=10)
        
        title = ctk.CTkLabel(
            title_frame,
            text=f"🤖 {ASSISTANT_NAME} Pro",
            font=("Segoe UI", 18, "bold"),
            text_color="#00d4ff"
        )
        title.pack(side="left")

        # Status bar
        self.status_label = ctk.CTkLabel(
            title_frame,
            text="● Connected | Gemini Ready",
            font=("Segoe UI", 10),
            text_color="#00ff00"
        )
        self.status_label.pack(side="right")

        # Main content
        main_frame = ctk.CTkFrame(self.root, fg_color="#0f0f1e")
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Chat display
        chat_frame = ctk.CTkFrame(main_frame)
        chat_frame.pack(fill="both", expand=True, padx=15, pady=10)

        chat_label = ctk.CTkLabel(
            chat_frame,
            text="Conversation",
            font=("Segoe UI", 12, "bold")
        )
        chat_label.pack(anchor="w", pady=(0, 5))

        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            fg_color="#16213e",
            text_color="#e0e0e0",
            font=("Segoe UI", GUI_FONT_SIZE),
            state="disabled",
            corner_radius=8
        )
        self.chat_display.pack(fill="both", expand=True)

        # Input area
        input_frame = ctk.CTkFrame(main_frame, fg_color="#0f0f1e")
        input_frame.pack(fill="x", padx=15, pady=10)

        # Input field
        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message or click the microphone to speak...",
            fg_color="#16213e",
            text_color="#e0e0e0",
            font=("Segoe UI", GUI_FONT_SIZE),
            corner_radius=8,
            height=40
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self._on_submit())

        # Voice button
        self.voice_button = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=40,
            height=40,
            font=("Segoe UI", 18),
            fg_color="#00d4ff",
            hover_color="#00a8cc",
            command=self._on_voice_click
        )
        self.voice_button.pack(side="left", padx=(0, 5))

        # Send button
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            width=80,
            font=("Segoe UI", GUI_FONT_SIZE, "bold"),
            fg_color="#00d4ff",
            hover_color="#00a8cc",
            command=self._on_submit
        )
        self.send_button.pack(side="left")

        # Welcome message
        self._display_message(
            ASSISTANT_NAME,
            f"Hello {USER_NAME}! I'm {ASSISTANT_NAME} Pro v3.0. How can I help you today?"
        )

    def _on_submit(self) -> None:
        """Handle message submission."""
        user_input = self.input_field.get().strip()
        if not user_input or self.is_processing:
            return

        self.input_field.delete(0, "end")
        self._display_message(USER_NAME, user_input)

        # Process in background thread
        def process():
            self.is_processing = True
            self.send_button.configure(state="disabled")
            try:
                response = self.on_submit(user_input)
                self._display_message(ASSISTANT_NAME, response)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                self._display_message(ASSISTANT_NAME, f"Error: {str(e)}")
            finally:
                self.is_processing = False
                self.send_button.configure(state="normal")

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _on_voice_click(self) -> None:
        """Handle voice button click."""
        if self.on_voice_click:
            thread = threading.Thread(target=self.on_voice_click, daemon=True)
            thread.start()

    def _display_message(self, sender: str, message: str) -> None:
        """Display message in chat.
        
        Args:
            sender: Message sender
            message: Message text
        """
        self.chat_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {sender}: {message}\n\n"
        self.chat_display.insert("end", formatted)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def set_status(self, status: str, color: str = "#00ff00") -> None:
        """Update status bar.
        
        Args:
            status: Status text
            color: Text color
        """
        self.status_label.configure(text=status, text_color=color)
        self.root.update()

    def set_ai_provider(self, provider: str) -> None:
        """Update AI provider display.
        
        Args:
            provider: Provider name (Gemini/OpenAI)
        """
        self.ai_provider = provider
        self.set_status(f"● Connected | {provider} Ready")

    def run(self) -> None:
        """Run the GUI."""
        logger.info("Starting GUI")
        self.root.mainloop()

    def _on_closing(self) -> None:
        """Handle window closing."""
        logger.info("GUI closing")
        self.root.destroy()
