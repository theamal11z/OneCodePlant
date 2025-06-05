"""Test configuration and fixtures for OneCode Plant CLI tests."""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from onecode.core.config import ConfigManager
from onecode.core.ros2_interface import ROS2Interface, ProcessResult
from onecode.core.plugin_manager import PluginManager


@pytest.fixture
def temp_workspace():
    """Create a temporary ROS2 workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        
        # Create workspace structure
        (workspace_path / 'src').mkdir()
        (workspace_path / 'build').mkdir(exist_ok=True)
        (workspace_path / 'install').mkdir(exist_ok=True)
        (workspace_path / 'log').mkdir(exist_ok=True)
        
        yield workspace_path


@pytest.fixture
def temp_package(temp_workspace):
    """Create a temporary ROS2 package for testing."""
    package_name = "test_package"
    package_path = temp_workspace / 'src' / package_name
    package_path.mkdir()
    
    # Create package.xml
    package_xml_content = f"""<?xml version="1.0"?>
<package format="3">
  <name>{package_name}</name>
  <version>0.0.0</version>
  <description>Test package for OneCode Plant CLI</description>
  <maintainer email="test@example.com">Test Maintainer</maintainer>
  <license>Apache-2.0</license>
  
  <buildtool_depend>ament_cmake</buildtool_depend>
  
  <depend>rclcpp</depend>
  <depend>std_msgs</depend>
  
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>
  
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>"""
    
    (package_path / 'package.xml').write_text(package_xml_content)
    
    # Create CMakeLists.txt
    cmake_content = f"""cmake_minimum_required(VERSION 3.8)
project({package_name})

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
"""
    
    (package_path / 'CMakeLists.txt').write_text(cmake_content)
    
    yield package_path


@pytest.fixture
def mock_ros2_interface():
    """Create a mocked ROS2Interface for testing."""
    with patch('onecode.core.ros2_interface.ROS2Interface') as mock_class:
        mock_instance = MagicMock()
        mock_instance.is_available.return_value = True
        mock_instance.get_version.return_value = "humble"
        mock_instance.run_command.return_value = ProcessResult(
            returncode=0,
            stdout="Success",
            stderr="",
            command=["ros2", "test"]
        )
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config_manager():
    """Create a mocked ConfigManager for testing."""
    with patch('onecode.core.config.ConfigManager') as mock_class:
        mock_instance = MagicMock()
        mock_instance.config = MagicMock()
        mock_instance.config.build = MagicMock()
        mock_instance.config.simulation = MagicMock()
        mock_instance.config.logging = MagicMock()
        mock_instance.config.plugins = {}
        
        # Set default values
        mock_instance.get.return_value = None
        mock_instance.get_plugin_config.return_value = {}
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_plugin_manager():
    """Create a mocked PluginManager for testing."""
    with patch('onecode.core.plugin_manager.PluginManager') as mock_class:
        mock_instance = MagicMock()
        mock_instance.plugins = {}
        mock_instance.load_plugins.return_value = 0
        mock_instance.get_plugin.return_value = None
        mock_instance.list_plugins.return_value = {}
        
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def isolated_config():
    """Create an isolated configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / '.config' / 'onecode'
        config_dir.mkdir(parents=True)
        
        # Patch the config directory functions
        with patch('onecode.core.utils.get_onecode_config_dir', return_value=config_dir):
            config_manager = ConfigManager()
            yield config_manager


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls for testing."""
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Success"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_colcon_available():
    """Mock colcon availability."""
    with patch('shutil.which') as mock_which:
        mock_which.return_value = '/usr/bin/colcon'
        yield mock_which


@pytest.fixture
def mock_gazebo_available():
    """Mock Gazebo availability."""
    with patch('shutil.which') as mock_which:
        def which_side_effect(cmd):
            if cmd in ['gazebo', 'gz', 'ign']:
                return f'/usr/bin/{cmd}'
            return None
        
        mock_which.side_effect = which_side_effect
        yield mock_which


@pytest.fixture
def sample_world_file():
    """Create a sample world file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.world', delete=False) as temp_file:
        world_content = """<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="test_world">
    <include>
      <uri>model://ground_plane</uri>
    </include>
    <include>
      <uri>model://sun</uri>
    </include>
  </world>
</sdf>"""
        temp_file.write(world_content.encode())
        temp_file.flush()
        
        yield Path(temp_file.name)
        
        # Cleanup
        os.unlink(temp_file.name)


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration after each test."""
    import logging
    
    # Store original state
    original_handlers = logging.getLogger('onecode').handlers[:]
    original_level = logging.getLogger('onecode').level
    
    yield
    
    # Restore original state
    logger = logging.getLogger('onecode')
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    for handler in original_handlers:
        logger.addHandler(handler)
    logger.setLevel(original_level)


@pytest.fixture
def environment_variables():
    """Manage environment variables for testing."""
    original_env = os.environ.copy()
    
    def set_env(**kwargs):
        for key, value in kwargs.items():
            os.environ[key] = str(value)
    
    def clear_env(*keys):
        for key in keys:
            os.environ.pop(key, None)
    
    def restore_env():
        os.environ.clear()
        os.environ.update(original_env)
    
    # Create a context manager-like object
    env_manager = type('EnvManager', (), {
        'set': set_env,
        'clear': clear_env,
        'restore': restore_env
    })()
    
    yield env_manager
    
    # Cleanup
    restore_env()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_ros2: mark test as requiring ROS2 installation"
    )
    config.addinivalue_line(
        "markers", "requires_colcon: mark test as requiring Colcon installation"
    )
    config.addinivalue_line(
        "markers", "requires_gazebo: mark test as requiring Gazebo installation"
    )


def pytest_runtest_setup(item):
    """Setup for individual test runs."""
    # Skip tests that require external dependencies if not available
    if item.get_closest_marker("requires_ros2"):
        if not shutil.which('ros2'):
            pytest.skip("ROS2 not available")
    
    if item.get_closest_marker("requires_colcon"):
        if not shutil.which('colcon'):
            pytest.skip("Colcon not available")
    
    if item.get_closest_marker("requires_gazebo"):
        if not any(shutil.which(cmd) for cmd in ['gazebo', 'gz', 'ign']):
            pytest.skip("Gazebo not available")


# Custom assertions
def assert_command_contains(command_list, expected_args):
    """Assert that a command list contains expected arguments."""
    command_str = ' '.join(command_list)
    for arg in expected_args:
        assert arg in command_str, f"Expected '{arg}' in command: {command_str}"


def assert_file_exists(file_path):
    """Assert that a file exists."""
    path = Path(file_path)
    assert path.exists(), f"File does not exist: {path}"


def assert_directory_structure(base_path, expected_structure):
    """Assert that a directory has the expected structure."""
    base = Path(base_path)
    
    for item in expected_structure:
        item_path = base / item
        assert item_path.exists(), f"Expected path does not exist: {item_path}"


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_package_xml(name, dependencies=None):
        """Create a package.xml content string."""
        dependencies = dependencies or ['rclcpp', 'std_msgs']
        
        deps_xml = '\n'.join(f'  <depend>{dep}</depend>' for dep in dependencies)
        
        return f"""<?xml version="1.0"?>
<package format="3">
  <name>{name}</name>
  <version>0.0.0</version>
  <description>Test package</description>
  <maintainer email="test@example.com">Test</maintainer>
  <license>Apache-2.0</license>
  
  <buildtool_depend>ament_cmake</buildtool_depend>
  
{deps_xml}
  
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>
  
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>"""
    
    @staticmethod
    def create_launch_file(name, nodes=None):
        """Create a launch file content string."""
        nodes = nodes or []
        
        nodes_code = '\n'.join(f"""    Node(
        package='{node["package"]}',
        executable='{node["executable"]}',
        name='{node["name"]}'
    ),""" for node in nodes)
        
        return f"""from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
{nodes_code}
    ])
"""


# Export fixtures and utilities
__all__ = [
    'temp_workspace',
    'temp_package', 
    'mock_ros2_interface',
    'mock_config_manager',
    'mock_plugin_manager',
    'isolated_config',
    'mock_subprocess',
    'mock_colcon_available',
    'mock_gazebo_available',
    'sample_world_file',
    'environment_variables',
    'assert_command_contains',
    'assert_file_exists',
    'assert_directory_structure',
    'TestDataFactory'
]
