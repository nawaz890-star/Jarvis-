"""Computer automation tasks."""

import logging
import subprocess
import webbrowser
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import pyautogui
    import pyperclip
    import psutil
    import cv2
except ImportError:
    pyautogui = None
    pyperclip = None
    psutil = None
    cv2 = None

logger = logging.getLogger(__name__)


class AutomationManager:
    """Handles system automation tasks."""

    def __init__(self):
        """Initialize automation manager."""
        self.pyautogui_available = pyautogui is not None
        self.clipboard_available = pyperclip is not None
        self.psutil_available = psutil is not None
        self.vision_available = cv2 is not None

    def open_application(self, app_name: str) -> bool:
        """Open an application.
        
        Args:
            app_name: Application name or path
            
        Returns:
            True if successful
        """
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(f'start {app_name}', shell=True)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.Popen(['open', '-a', app_name])
            logger.info(f"Opened application: {app_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open application: {e}")
            return False

    def open_website(self, url: str) -> bool:
        """Open a website in browser.
        
        Args:
            url: URL to open
            
        Returns:
            True if successful
        """
        try:
            if not url.startswith('http'):
                url = f'https://{url}'
            webbrowser.open(url)
            logger.info(f"Opened website: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open website: {e}")
            return False

    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard.
        
        Args:
            text: Text to copy
            
        Returns:
            True if successful
        """
        if not self.clipboard_available:
            logger.warning("Clipboard not available")
            return False

        try:
            pyperclip.copy(text)
            logger.debug(f"Copied to clipboard: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False

    def get_clipboard(self) -> Optional[str]:
        """Get clipboard contents.
        
        Returns:
            Clipboard text or None
        """
        if not self.clipboard_available:
            return None

        try:
            text = pyperclip.paste()
            logger.debug(f"Retrieved clipboard: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Failed to get clipboard: {e}")
            return None

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        Returns:
            Dictionary with system info
        """
        if not self.psutil_available:
            return {"error": "psutil not available"}

        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 2)
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}

    def take_screenshot(self, filepath: Optional[str] = None) -> Optional[str]:
        """Take a screenshot.
        
        Args:
            filepath: Where to save screenshot
            
        Returns:
            Path to saved screenshot or None
        """
        if not self.vision_available:
            logger.warning("Vision not available")
            return None

        try:
            if not filepath:
                filepath = "screenshot.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            logger.info(f"Screenshot saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def list_files(self, directory: str = ".", max_items: int = 20) -> List[Dict[str, Any]]:
        """List files in directory.
        
        Args:
            directory: Directory path
            max_items: Maximum items to return
            
        Returns:
            List of file info
        """
        try:
            path = Path(directory).expanduser()
            files = []
            
            for item in sorted(path.iterdir())[:max_items]:
                files.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size_kb": round(item.stat().st_size / 1024, 2) if item.is_file() else 0,
                    "path": str(item)
                })
            
            logger.info(f"Listed {len(files)} items in {directory}")
            return files
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def mouse_click(self, x: int, y: int, button: str = "left") -> bool:
        """Simulate mouse click.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button (left/right/middle)
            
        Returns:
            True if successful
        """
        if not self.pyautogui_available:
            logger.warning("PyAutoGUI not available")
            return False

        try:
            pyautogui.click(x, y, button=button)
            logger.debug(f"Mouse click at ({x}, {y}) - {button}")
            return True
        except Exception as e:
            logger.error(f"Failed to click mouse: {e}")
            return False

    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """Simulate typing.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
            
        Returns:
            True if successful
        """
        if not self.pyautogui_available:
            logger.warning("PyAutoGUI not available")
            return False

        try:
            pyautogui.typewrite(text, interval=interval)
            logger.debug(f"Typed: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to type: {e}")
            return False
