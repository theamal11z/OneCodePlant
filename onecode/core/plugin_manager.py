"""Plugin management system for OneCode Plant CLI."""

import os
import importlib
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from onecode.core.utils import get_logger
from onecode.plugins.base import PluginBase


class PluginManager:
    """Manages plugin discovery, loading, and execution."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.logger = get_logger(__name__)
        self.plugins: Dict[str, PluginBase] = {}
        self._plugin_paths: List[Path] = []
        
        # Default plugin search paths
        self._setup_plugin_paths()
    
    def _setup_plugin_paths(self):
        """Setup default plugin search paths."""
        # Built-in plugins
        builtin_path = Path(__file__).parent.parent / 'plugins'
        self._plugin_paths.append(builtin_path)
        
        # User plugins (optional)
        user_home = Path.home()
        user_plugin_path = user_home / '.onecode' / 'plugins'
        if user_plugin_path.exists():
            self._plugin_paths.append(user_plugin_path)
        
        # Environment-specified plugin paths
        env_paths = os.environ.get('ONECODE_PLUGIN_PATH', '')
        if env_paths:
            for path_str in env_paths.split(':'):
                path = Path(path_str)
                if path.exists():
                    self._plugin_paths.append(path)
    
    def add_plugin_path(self, path: Path):
        """Add a custom plugin search path."""
        if path.exists() and path not in self._plugin_paths:
            self._plugin_paths.append(path)
            self.logger.debug(f"Added plugin path: {path}")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the search paths.
        
        Returns:
            List of plugin module names that were discovered
        """
        discovered = []
        
        for plugin_path in self._plugin_paths:
            if not plugin_path.exists():
                continue
                
            self.logger.debug(f"Searching for plugins in: {plugin_path}")
            
            # Look for Python files that end with '_plugin.py'
            for plugin_file in plugin_path.glob('*_plugin.py'):
                if plugin_file.name.startswith('__'):
                    continue
                    
                module_name = plugin_file.stem
                discovered.append(module_name)
                self.logger.debug(f"Discovered plugin: {module_name}")
        
        return discovered
    
    def load_plugin(self, module_name: str) -> Optional[PluginBase]:
        """
        Load a specific plugin by module name.
        
        Args:
            module_name: Name of the plugin module to load
            
        Returns:
            Loaded plugin instance or None if loading failed
        """
        try:
            # Import the plugin module
            module = importlib.import_module(f'onecode.plugins.{module_name}')
            
            # Find plugin classes in the module
            plugin_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, PluginBase) and 
                    obj != PluginBase and 
                    obj.__module__ == module.__name__):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                self.logger.warning(f"No plugin classes found in {module_name}")
                return None
            
            if len(plugin_classes) > 1:
                self.logger.warning(f"Multiple plugin classes found in {module_name}, using first one")
            
            # Instantiate the plugin
            plugin_class = plugin_classes[0]
            plugin_instance = plugin_class()
            
            # Validate the plugin
            if not hasattr(plugin_instance, 'name'):
                self.logger.error(f"Plugin {module_name} missing required 'name' attribute")
                return None
            
            self.logger.info(f"Loaded plugin: {plugin_instance.name}")
            return plugin_instance
            
        except ImportError as e:
            self.logger.error(f"Failed to import plugin {module_name}: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"Error loading plugin {module_name}: {e}")
            return None
    
    def load_plugins(self) -> int:
        """
        Load all discovered plugins.
        
        Returns:
            Number of successfully loaded plugins
        """
        self.logger.info("Loading plugins...")
        
        discovered = self.discover_plugins()
        loaded_count = 0
        
        for module_name in discovered:
            plugin = self.load_plugin(module_name)
            if plugin:
                self.plugins[plugin.name] = plugin
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count} plugins out of {len(discovered)} discovered")
        return loaded_count
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """
        Get a loaded plugin by name.
        
        Args:
            name: Name of the plugin to retrieve
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to their information
        """
        plugin_info = {}
        
        for name, plugin in self.plugins.items():
            info = {
                'name': plugin.name,
                'description': getattr(plugin, 'description', 'No description'),
                'version': getattr(plugin, 'version', 'Unknown'),
                'available': plugin.is_available(),
                'commands': getattr(plugin, 'commands', [])
            }
            
            # Get additional info if available
            if hasattr(plugin, 'get_info'):
                additional_info = plugin.get_info()
                if additional_info:
                    info.update(additional_info)
            
            plugin_info[name] = info
        
        return plugin_info
    
    def reload_plugin(self, name: str) -> bool:
        """
        Reload a specific plugin.
        
        Args:
            name: Name of the plugin to reload
            
        Returns:
            True if reload was successful, False otherwise
        """
        if name not in self.plugins:
            self.logger.error(f"Plugin {name} not currently loaded")
            return False
        
        # Find the module name for this plugin
        plugin = self.plugins[name]
        module_name = plugin.__class__.__module__.split('.')[-1]
        
        try:
            # Remove from loaded plugins
            del self.plugins[name]
            
            # Reload the module
            importlib.reload(importlib.import_module(f'onecode.plugins.{module_name}'))
            
            # Load the plugin again
            reloaded_plugin = self.load_plugin(module_name)
            if reloaded_plugin:
                self.plugins[reloaded_plugin.name] = reloaded_plugin
                self.logger.info(f"Successfully reloaded plugin: {name}")
                return True
            else:
                self.logger.error(f"Failed to reload plugin: {name}")
                return False
                
        except Exception as e:
            self.logger.exception(f"Error reloading plugin {name}: {e}")
            return False
    
    def execute_plugin_command(self, plugin_name: str, command: str, **kwargs) -> int:
        """
        Execute a command on a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            command: Command to execute
            **kwargs: Arguments to pass to the command
            
        Returns:
            Exit code from the command execution
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            self.logger.error(f"Plugin {plugin_name} not found")
            return 1
        
        if not plugin.is_available():
            self.logger.error(f"Plugin {plugin_name} is not available")
            return 1
        
        try:
            if hasattr(plugin, command):
                method = getattr(plugin, command)
                if callable(method):
                    result = method(**kwargs)
                    return result if isinstance(result, int) else 0
                else:
                    self.logger.error(f"Command {command} is not callable on plugin {plugin_name}")
                    return 1
            else:
                self.logger.error(f"Command {command} not found on plugin {plugin_name}")
                return 1
                
        except Exception as e:
            self.logger.exception(f"Error executing {command} on plugin {plugin_name}: {e}")
            return 1
