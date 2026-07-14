"""Plugin System - Dynamic plugin loading and management."""

import logging
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class Plugin:
    """Base plugin class."""

    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize plugin.
        
        Args:
            name: Plugin name
            version: Plugin version
        """
        self.name = name
        self.version = version
        self.enabled = True
        self.metadata: Dict[str, Any] = {}

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute plugin."""
        raise NotImplementedError


class PluginManager:
    """Manage dynamic plugins."""

    def __init__(self, plugins_dir: str = "plugins"):
        """Initialize Plugin Manager.
        
        Args:
            plugins_dir: Directory containing plugins
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, Plugin] = {}
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    def load_plugin(self, plugin_path: str) -> Dict[str, Any]:
        """Load plugin from file.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            Load status
        """
        try:
            path = Path(plugin_path)
            if not path.exists():
                return {"success": False, "error": "Plugin file not found"}

            spec = importlib.util.spec_from_file_location(path.stem, path)
            if not spec or not spec.loader:
                return {"success": False, "error": "Invalid plugin"}

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extract plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                    plugin = attr()
                    self.plugins[plugin.name] = plugin
                    logger.info(f"Loaded plugin: {plugin.name}")
                    return {"success": True, "plugin": plugin.name}

            return {"success": False, "error": "No plugin class found"}
        except Exception as e:
            logger.error(f"Plugin load error: {e}")
            return {"success": False, "error": str(e)}

    def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Unload plugin.
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Unload status
        """
        try:
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
                logger.info(f"Unloaded plugin: {plugin_name}")
                return {"success": True}
            return {"success": False, "error": "Plugin not found"}
        except Exception as e:
            logger.error(f"Plugin unload error: {e}")
            return {"success": False, "error": str(e)}

    def enable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Enable plugin.
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Status
        """
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            logger.info(f"Enabled plugin: {plugin_name}")
            return {"success": True}
        return {"success": False, "error": "Plugin not found"}

    def disable_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Disable plugin.
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Status
        """
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            logger.info(f"Disabled plugin: {plugin_name}")
            return {"success": True}
        return {"success": False, "error": "Plugin not found"}

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins.
        
        Returns:
            List of plugins
        """
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "enabled": plugin.enabled
            }
            for plugin in self.plugins.values()
        ]
