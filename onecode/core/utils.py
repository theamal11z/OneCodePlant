"""Common utilities and helper functions."""

import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger('onecode')
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    # Ensure it's under the onecode namespace
    if not name.startswith('onecode'):
        name = f'onecode.{name}'
    
    return logging.getLogger(name)


def load_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        Dictionary containing the YAML data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {path}: {e}")


def save_yaml_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save data to a YAML file.
    
    Args:
        data: Dictionary to save
        file_path: Path where to save the file
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, default_flow_style=False, indent=2)


def find_ros2_workspace() -> Optional[Path]:
    """
    Find the current ROS2 workspace by looking for common indicators.
    
    Returns:
        Path to the workspace root or None if not found
    """
    current_dir = Path.cwd()
    
    # Look for workspace indicators
    workspace_indicators = [
        'src',
        'build',
        'install',
        'log'
    ]
    
    # Check current directory and parent directories
    for directory in [current_dir] + list(current_dir.parents):
        # Check if this looks like a workspace root
        indicator_count = sum(1 for indicator in workspace_indicators 
                            if (directory / indicator).exists())
        
        if indicator_count >= 2:  # At least 2 indicators present
            return directory
    
    return None


def find_package_xml(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the nearest package.xml file.
    
    Args:
        start_path: Starting directory to search from
        
    Returns:
        Path to package.xml or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current_dir = Path(start_path)
    
    # Search up the directory tree
    for directory in [current_dir] + list(current_dir.parents):
        package_xml = directory / 'package.xml'
        if package_xml.exists():
            return package_xml
    
    return None


def get_package_name(package_xml_path: Path) -> Optional[str]:
    """
    Extract package name from package.xml.
    
    Args:
        package_xml_path: Path to package.xml file
        
    Returns:
        Package name or None if not found
    """
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(package_xml_path)
        root = tree.getroot()
        
        name_element = root.find('name')
        if name_element is not None:
            return name_element.text.strip()
    except Exception:
        pass
    
    return None


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_onecode_cache_dir() -> Path:
    """
    Get the OneCode cache directory, creating it if necessary.
    
    Returns:
        Path to the cache directory
    """
    cache_dir = Path.home() / '.cache' / 'onecode'
    return ensure_directory(cache_dir)


def get_onecode_config_dir() -> Path:
    """
    Get the OneCode configuration directory, creating it if necessary.
    
    Returns:
        Path to the config directory
    """
    config_dir = Path.home() / '.config' / 'onecode'
    return ensure_directory(config_dir)


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def is_ros2_package(path: Path) -> bool:
    """
    Check if a directory is a ROS2 package.
    
    Args:
        path: Directory path to check
        
    Returns:
        True if the directory contains a package.xml file
    """
    return (path / 'package.xml').exists()


def get_terminal_width() -> int:
    """
    Get the current terminal width.
    
    Returns:
        Terminal width in characters
    """
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80  # Default fallback


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
