"""Configuration management for JARVIS Pro."""

import os
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, using environment variables only")

# ============================================================================
# API Keys and Credentials
# ============================================================================
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() or None
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "").strip() or None
SEARCH_API_KEY: Optional[str] = os.getenv("SEARCH_API_KEY", "").strip() or None

# ============================================================================
# Voice Configuration
# ============================================================================
VOICE_NAME: str = os.getenv("VOICE_NAME", "en-US-GuyNeural").strip()
WAKE_WORD: str = os.getenv("WAKE_WORD", "jarvis").strip().lower()
ENABLE_WAKE_WORD: bool = os.getenv("ENABLE_WAKE_WORD", "true").lower() in ("1", "true", "yes")

try:
    MIC_DEVICE_INDEX: int = int(os.getenv("MIC_DEVICE_INDEX", "0"))
except (ValueError, TypeError):
    MIC_DEVICE_INDEX = 0
    logger.warning("Invalid MIC_DEVICE_INDEX, using default: 0")

# Voice processing settings
VOICE_TIMEOUT: int = 10
VOICE_PHRASE_LIMIT: int = 10
VOICE_CONFIDENCE_THRESHOLD: float = 0.5
NOISE_DURATION: float = 1.0

# ============================================================================
# Memory and Database
# ============================================================================
DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", "./data/jarvis.db"))
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

try:
    MEMORY_MAX_ITEMS: int = int(os.getenv("MEMORY_MAX_ITEMS", "500"))
except (ValueError, TypeError):
    MEMORY_MAX_ITEMS = 500
    logger.warning("Invalid MEMORY_MAX_ITEMS, using default: 500")

try:
    MEMORY_TTL_DAYS: int = int(os.getenv("MEMORY_TTL_DAYS", "90"))
except (ValueError, TypeError):
    MEMORY_TTL_DAYS = 90
    logger.warning("Invalid MEMORY_TTL_DAYS, using default: 90")

# ============================================================================
# Assistant Personality
# ============================================================================
ASSISTANT_NAME: str = os.getenv("ASSISTANT_NAME", "Jarvis").strip()
USER_NAME: str = os.getenv("USER_NAME", "User").strip()
ASSISTANT_VERSION: str = "3.0.0"

SYSTEM_PROMPT: str = f"""You are {ASSISTANT_NAME}, an advanced AI assistant with the following capabilities:
- Engage in natural conversations
- Answer questions on virtually any topic
- Help with coding and programming
- Provide web search results when needed
- Assist with automation and system tasks
- Remember previous conversations
- Be helpful, harmless, and honest

Keep responses clear, concise, and engaging. Use markdown formatting when appropriate."""

# ============================================================================
# Features Configuration
# ============================================================================
AUTO_WEB_SEARCH_ENABLE: bool = os.getenv("AUTO_WEB_SEARCH_ENABLE", "true").lower() in ("1", "true", "yes")
MAX_SEARCH_RESULTS: int = 5
SEARCH_TIMEOUT: int = 10

# ============================================================================
# Security
# ============================================================================
allowlist_str = os.getenv("COMMAND_ALLOWLIST", "").strip()
COMMAND_ALLOWLIST: list = [
    cmd.strip() for cmd in allowlist_str.split(",") if cmd.strip()
] if allowlist_str else []

denylist_str = os.getenv(
    "COMMAND_DENYLIST",
    "rm,format,shutdown,reboot,del,wipe,sudo,dd,mkfs"
).strip()
COMMAND_DENYLIST: list = [cmd.strip() for cmd in denylist_str.split(",") if cmd.strip()]

# ============================================================================
# GUI Configuration
# ============================================================================
GUI_THEME: str = "dark"
GUI_WIDTH: int = 1200
GUI_HEIGHT: int = 700
GUI_FONT_SIZE: int = 11

# ============================================================================
# Debug and Logging
# ============================================================================
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() in ("1", "true", "yes")

if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("Debug mode enabled")

# ============================================================================
# Validation
# ============================================================================
if not GEMINI_API_KEY and not OPENAI_API_KEY:
    logger.warning(
        "No AI API keys configured. Set GEMINI_API_KEY or OPENAI_API_KEY in .env"
    )

if not SEARCH_API_KEY:
    logger.warning(
        "Search API key not configured. Web search will be disabled. "
        "Set SEARCH_API_KEY in .env to enable."
    )

logger.info(f"JARVIS {ASSISTANT_VERSION} initialized with config: "
            f"Name={ASSISTANT_NAME}, User={USER_NAME}, DB={DATABASE_PATH}")
