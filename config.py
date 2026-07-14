"""Production configuration management for JARVIS Pro v3.1."""

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
# Ollama Configuration (Local LLM)
# ============================================================================
ENABLE_OLLAMA: bool = os.getenv("ENABLE_OLLAMA", "false").lower() in ("1", "true", "yes")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")

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

try:
    MEMORY_TTL_DAYS: int = int(os.getenv("MEMORY_TTL_DAYS", "90"))
except (ValueError, TypeError):
    MEMORY_TTL_DAYS = 90

# ============================================================================
# Assistant Personality
# ============================================================================
ASSISTANT_NAME: str = os.getenv("ASSISTANT_NAME", "Jarvis").strip()
USER_NAME: str = os.getenv("USER_NAME", "User").strip()
ASSISTANT_VERSION: str = "3.1.0"

SYSTEM_PROMPT: str = f"""You are {ASSISTANT_NAME}, an advanced AI assistant. You are helpful, friendly, and professional.

Capabilities:
- Natural conversation and problem-solving
- Web search integration for current information
- Code generation and explanation (Python, JavaScript, TypeScript, Java, C++, C#, PHP, SQL, HTML, CSS, React, Vue, Angular, Node.js, Next.js)
- Website generation and component building
- System automation and file operations
- Screenshot and vision analysis
- Project management and scaffolding
- Conversation memory and context awareness

Behavior:
- Keep responses concise and clear
- Use markdown formatting for better readability
- Proactively offer help based on context
- Be honest about limitations
- Prioritize user safety and privacy"""

# ============================================================================
# Features Configuration
# ============================================================================
AUTO_WEB_SEARCH_ENABLE: bool = os.getenv("AUTO_WEB_SEARCH_ENABLE", "true").lower() in ("1", "true", "yes")
MAX_SEARCH_RESULTS: int = 5
SEARCH_TIMEOUT: int = 10

# ============================================================================
# Coding Assistant
# ============================================================================
ENABLE_CODING_ASSISTANT: bool = os.getenv("ENABLE_CODING_ASSISTANT", "true").lower() in ("1", "true", "yes")

# ============================================================================
# Website Generator
# ============================================================================
ENABLE_WEBSITE_GENERATOR: bool = os.getenv("ENABLE_WEBSITE_GENERATOR", "true").lower() in ("1", "true", "yes")
DEFAULT_FRAMEWORK: str = os.getenv("DEFAULT_FRAMEWORK", "react").strip().lower()

# ============================================================================
# Security
# ============================================================================
allowlist_str = os.getenv("COMMAND_ALLOWLIST", "").strip()
COMMAND_ALLOWLIST: list = [
    cmd.strip() for cmd in allowlist_str.split(",") if cmd.strip()
] if allowlist_str else []

denylist_str = os.getenv(
    "COMMAND_DENYLIST",
    "rm,format,shutdown,reboot,del,wipe,sudo,dd,mkfs,fdisk"
).strip()
COMMAND_DENYLIST: list = [cmd.strip() for cmd in denylist_str.split(",") if cmd.strip()]

# ============================================================================
# GUI Configuration
# ============================================================================
GUI_THEME: str = "dark"
GUI_WIDTH: int = 1200
GUI_HEIGHT: int = 700
GUI_FONT_SIZE: int = 11
GUI_FONT_FAMILY: str = "Segoe UI"

# ============================================================================
# Performance and Threading
# ============================================================================
MAX_THREADS: int = 4
QUEUE_TIMEOUT: float = 30.0
REQUEST_TIMEOUT: int = 30
AI_RESPONSE_TIMEOUT: int = 60

# ============================================================================
# Debug and Logging
# ============================================================================
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() in ("1", "true", "yes")

if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)

# ============================================================================
# Paths
# ============================================================================
PROJECT_ROOT: Path = Path(__file__).parent
DATA_DIR: Path = PROJECT_ROOT / "data"
LOGS_DIR: Path = DATA_DIR / "logs"
CODE_PROJECTS_DIR: Path = DATA_DIR / "projects"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CODE_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Validation
# ============================================================================
if not GEMINI_API_KEY and not OPENAI_API_KEY and not ENABLE_OLLAMA:
    logger.warning(
        "No AI API keys or Ollama configured. Set GEMINI_API_KEY, OPENAI_API_KEY, or enable Ollama"
    )

if not SEARCH_API_KEY:
    logger.info(
        "Search API key not configured. Web search will be disabled. "
        "Set SEARCH_API_KEY in .env to enable."
    )

logger.info(f"JARVIS {ASSISTANT_VERSION} initialized - "
            f"Name={ASSISTANT_NAME}, User={USER_NAME}, DB={DATABASE_PATH}")
