"""Configuration management for OneCode Plant CLI."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict

from onecode.core.utils import get_logger, get_onecode_config_dir, load_yaml_file, save_yaml_file


@dataclass
class BuildConfig:
    """Configuration for build operations."""
    cmake_build_type: str = "Release"
    symlink_install: bool = True
    parallel_jobs: Optional[int] = None
    continue_on_error: bool = False
    cmake_args: Optional[str] = None
    ament_cmake_args: Optional[str] = None


@dataclass 
class SimulationConfig:
    """Configuration for simulation operations."""
    default_world: Optional[str] = None
    default_robot: Optional[str] = None
    headless_mode: bool = False
    auto_close_on_exit: bool = True
    gazebo_model_path: Optional[str] = None
    gazebo_resource_path: Optional[str] = None


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    file: Optional[str] = None
    max_file_size: str = "10MB"
    backup_count: int = 5


@dataclass
class OneCodeConfig:
    """Main configuration class for OneCode Plant CLI."""
    build: BuildConfig = None
    simulation: SimulationConfig = None
    logging: LoggingConfig = None
    plugins: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.build is None:
            self.build = BuildConfig()
        if self.simulation is None:
            self.simulation = SimulationConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.plugins is None:
            self.plugins = {}


class ConfigManager:
    """Manages configuration loading, saving, and access."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.logger = get_logger(__name__)
        self.config = OneCodeConfig()
        self._config_file: Optional[Path] = None
        
        # Load default configuration
        self._load_default_config()
        
        # Load user configuration if it exists
        self._load_user_config()
    
    def _load_default_config(self):
        """Load the default configuration."""
        try:
            # Look for default config in the package
            default_config_path = Path(__file__).parent.parent.parent / 'configs' / 'default_config.yaml'
            if default_config_path.exists():
                config_data = load_yaml_file(default_config_path)
                self._update_config_from_dict(config_data)
                self.logger.debug(f"Loaded default config from {default_config_path}")
        except Exception as e:
            self.logger.warning(f"Failed to load default config: {e}")
    
    def _load_user_config(self):
        """Load user-specific configuration."""
        try:
            config_dir = get_onecode_config_dir()
            user_config_path = config_dir / 'config.yaml'
            
            if user_config_path.exists():
                config_data = load_yaml_file(user_config_path)
                self._update_config_from_dict(config_data)
                self._config_file = user_config_path
                self.logger.debug(f"Loaded user config from {user_config_path}")
        except Exception as e:
            self.logger.warning(f"Failed to load user config: {e}")
    
    def load_config(self, config_path: Union[str, Path]):
        """
        Load configuration from a specific file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            config_data = load_yaml_file(config_path)
            self._update_config_from_dict(config_data)
            self._config_file = Path(config_path)
            self.logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            raise
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from a dictionary."""
        if not config_data:
            return
        
        # Update build config
        if 'build' in config_data:
            build_data = config_data['build']
            for key, value in build_data.items():
                if hasattr(self.config.build, key):
                    setattr(self.config.build, key, value)
        
        # Update simulation config
        if 'simulation' in config_data:
            sim_data = config_data['simulation']
            for key, value in sim_data.items():
                if hasattr(self.config.simulation, key):
                    setattr(self.config.simulation, key, value)
        
        # Update logging config
        if 'logging' in config_data:
            log_data = config_data['logging']
            for key, value in log_data.items():
                if hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)
        
        # Update plugin config
        if 'plugins' in config_data:
            self.config.plugins.update(config_data['plugins'])
    
    def save_config(self, config_path: Optional[Union[str, Path]] = None):
        """
        Save the current configuration to a file.
        
        Args:
            config_path: Path to save the config. If None, uses the last loaded path.
        """
        if config_path is None:
            if self._config_file is None:
                # Use default user config path
                config_dir = get_onecode_config_dir()
                config_path = config_dir / 'config.yaml'
            else:
                config_path = self._config_file
        
        config_path = Path(config_path)
        
        try:
            # Convert config to dictionary
            config_dict = {
                'build': asdict(self.config.build),
                'simulation': asdict(self.config.simulation),
                'logging': asdict(self.config.logging),
                'plugins': self.config.plugins
            }
            
            save_yaml_file(config_dict, config_path)
            self._config_file = config_path
            self.logger.info(f"Saved config to {config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config to {config_path}: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'build.parallel_jobs')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            parts = key.split('.')
            value = self.config
            
            for part in parts:
                value = getattr(value, part)
            
            return value
        except (AttributeError, KeyError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'build.parallel_jobs')
            value: Value to set
        """
        parts = key.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid config key: {key}")
        
        # Navigate to the parent object
        obj = self.config
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        # Set the final attribute
        setattr(obj, parts[-1], value)
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration dictionary
        """
        return self.config.plugins.get(plugin_name, {})
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """
        Set configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: Plugin configuration dictionary
        """
        self.config.plugins[plugin_name] = config
    
    def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """
        Update configuration for a specific plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: Plugin configuration dictionary to merge
        """
        if plugin_name not in self.config.plugins:
            self.config.plugins[plugin_name] = {}
        
        self.config.plugins[plugin_name].update(config)
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """
        Get configuration overrides from environment variables.
        
        Returns:
            Dictionary of environment-based config overrides
        """
        overrides = {}
        
        # Build configuration overrides
        env_build_type = os.getenv('ONECODE_BUILD_TYPE')
        if env_build_type:
            overrides['build.cmake_build_type'] = env_build_type
        
        env_parallel_jobs = os.getenv('ONECODE_PARALLEL_JOBS')
        if env_parallel_jobs:
            try:
                overrides['build.parallel_jobs'] = int(env_parallel_jobs)
            except ValueError:
                self.logger.warning(f"Invalid ONECODE_PARALLEL_JOBS value: {env_parallel_jobs}")
        
        # Logging configuration overrides
        env_log_level = os.getenv('ONECODE_LOG_LEVEL')
        if env_log_level:
            overrides['logging.level'] = env_log_level
        
        env_log_file = os.getenv('ONECODE_LOG_FILE')
        if env_log_file:
            overrides['logging.file'] = env_log_file
        
        return overrides
    
    def apply_environment_overrides(self):
        """Apply configuration overrides from environment variables."""
        overrides = self.get_environment_overrides()
        
        for key, value in overrides.items():
            try:
                self.set(key, value)
                self.logger.debug(f"Applied environment override: {key} = {value}")
            except Exception as e:
                self.logger.warning(f"Failed to apply environment override {key}: {e}")
