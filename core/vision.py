"""Vision Engine - Image analysis, OCR, and screenshot analysis."""

import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionEngine:
    """Process and analyze images."""

    def __init__(self):
        """Initialize Vision Engine."""
        self.ocr_available = self._check_ocr()
        self.cv_available = self._check_opencv()

    def _check_ocr(self) -> bool:
        """Check if pytesseract is available."""
        try:
            import pytesseract
            return True
        except ImportError:
            return False

    def _check_opencv(self) -> bool:
        """Check if OpenCV is available."""
        try:
            import cv2
            return True
        except ImportError:
            return False

    def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR.
        
        Args:
            image_path: Path to image
            
        Returns:
            Extracted text
        """
        if not self.ocr_available:
            return ""

        try:
            from PIL import Image
            import pytesseract

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            logger.info(f"Extracted text from: {image_path}")
            return text
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

    def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """Analyze screenshot.
        
        Args:
            screenshot_path: Path to screenshot
            
        Returns:
            Analysis results
        """
        try:
            # Extract text from screenshot
            text = self.extract_text(screenshot_path)
            
            return {
                "success": True,
                "text": text,
                "path": screenshot_path,
                "character_count": len(text),
                "line_count": len(text.split("\n"))
            }
        except Exception as e:
            logger.error(f"Screenshot analysis error: {e}")
            return {"success": False, "error": str(e)}
