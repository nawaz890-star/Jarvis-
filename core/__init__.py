"""JARVIS Core Modules - Production AI Operating System."""

__version__ = "4.0.0"
__author__ = "JARVIS Development Team"
__license__ = "MIT"

from core.ai_provider_manager import AIProviderManager
from core.memory_manager import MemoryManager
from core.voice_manager import VoiceManager
from core.search_engine import SearchEngine
from core.coding_assistant import CodingAssistant
from core.website_generator import WebsiteGenerator
from core.app_generator import AppGenerator
from core.file_manager import FileManager
from core.vscode_integration import VSCodeIntegration
from core.git_manager import GitManager
from core.automation import AutomationEngine
from core.vision import VisionEngine
from core.plugin_system import PluginManager

__all__ = [
    "AIProviderManager",
    "MemoryManager",
    "VoiceManager",
    "SearchEngine",
    "CodingAssistant",
    "WebsiteGenerator",
    "AppGenerator",
    "FileManager",
    "VSCodeIntegration",
    "GitManager",
    "AutomationEngine",
    "VisionEngine",
    "PluginManager",
]
