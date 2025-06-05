"""Base plugin class for OneCode Plant CLI."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from onecode.core.utils import get_logger


class PluginBase(ABC):
    """Base class for all OneCode plugins."""
    
    def __init__(self):
        """Initialize the plugin."""
        self.logger = get_logger(self.__class__.__module__)
        self._initialize()
    
    def _initialize(self):
        """Plugin-specific initialization. Override in subclasses."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return "No description provided"
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @property 
    def commands(self) -> List[str]:
        """List of commands provided by this plugin."""
        return []
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the plugin is available for use.
        
        This should check for required dependencies, tools, etc.
        
        Returns:
            True if the plugin can be used, False otherwise
        """
        pass
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """
        Get additional information about the plugin.
        
        Returns:
            Dictionary with plugin information or None
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'available': self.is_available(),
            'commands': self.commands
        }
    
    def validate_args(self, **kwargs) -> bool:
        """
        Validate arguments passed to plugin commands.
        
        Args:
            **kwargs: Arguments to validate
            
        Returns:
            True if arguments are valid, False otherwise
        """
        return True
    
    def get_help(self, command: Optional[str] = None) -> str:
        """
        Get help text for the plugin or a specific command.
        
        Args:
            command: Specific command to get help for
            
        Returns:
            Help text string
        """
        if command is None:
            return f"{self.name}: {self.description}"
        else:
            return f"No help available for command: {command}"
    
    def setup(self) -> bool:
        """
        Setup the plugin (install dependencies, configure, etc.).
        
        Returns:
            True if setup was successful, False otherwise
        """
        self.logger.info(f"Setting up plugin: {self.name}")
        return True
    
    def cleanup(self) -> bool:
        """
        Cleanup the plugin (remove temporary files, etc.).
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        self.logger.debug(f"Cleaning up plugin: {self.name}")
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this plugin.
        
        Returns:
            JSON schema dictionary for plugin configuration
        """
        return {}
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Configure the plugin with the given configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration was successful, False otherwise
        """
        self.logger.debug(f"Configuring plugin {self.name} with config: {config}")
        return True