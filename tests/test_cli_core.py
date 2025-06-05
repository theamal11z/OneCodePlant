"""Tests for core CLI functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from onecode.cli import OneCodeCLI
from onecode.core.config import ConfigManager
from onecode.core.ros2_interface import ROS2Interface, ProcessResult
from onecode.core.plugin_manager import PluginManager


class TestOneCodeCLI:
    """Test cases for OneCodeCLI class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.cli = OneCodeCLI()
    
    def test_cli_initialization(self):
        """Test CLI initializes correctly."""
        assert self.cli.config_manager is not None
        assert self.cli.ros2_interface is not None
        assert self.cli.plugin_manager is not None
        assert self.cli.logger is not None
    
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_ros2_passthrough(self, mock_run_command):
        """Test ROS2 command passthrough functionality."""
        # Mock successful command execution
        mock_run_command.return_value = ProcessResult(
            returncode=0,
            stdout="test output",
            stderr="",
            command=['ros2', 'pkg', 'list']
        )
        
        # Test passthrough
        result = self.cli.execute_ros2_passthrough(['ros2', 'pkg', 'list'])
        
        assert result == 0
        mock_run_command.assert_called_once_with(['ros2', 'pkg', 'list'])
    
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_ros2_passthrough_failure(self, mock_run_command):
        """Test ROS2 command passthrough with failure."""
        # Mock failed command execution
        mock_run_command.return_value = ProcessResult(
            returncode=1,
            stdout="",
            stderr="command failed",
            command=['ros2', 'pkg', 'invalid']
        )
        
        # Test passthrough failure
        result = self.cli.execute_ros2_passthrough(['ros2', 'pkg', 'invalid'])
        
        assert result == 1
        mock_run_command.assert_called_once_with(['ros2', 'pkg', 'invalid'])


class TestConfigManager:
    """Test cases for ConfigManager class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config_manager = ConfigManager()
    
    def test_config_initialization(self):
        """Test config manager initializes with defaults."""
        assert self.config_manager.config is not None
        assert self.config_manager.config.build is not None
        assert self.config_manager.config.simulation is not None
        assert self.config_manager.config.logging is not None
    
    def test_get_config_value(self):
        """Test getting configuration values."""
        # Test default values
        assert self.config_manager.get('build.cmake_build_type') == 'Release'
        assert self.config_manager.get('build.symlink_install') is True
        assert self.config_manager.get('nonexistent.key', 'default') == 'default'
    
    def test_set_config_value(self):
        """Test setting configuration values."""
        self.config_manager.set('build.cmake_build_type', 'Debug')
        assert self.config_manager.get('build.cmake_build_type') == 'Debug'
    
    def test_plugin_config(self):
        """Test plugin-specific configuration."""
        test_config = {'test_key': 'test_value'}
        self.config_manager.set_plugin_config('test_plugin', test_config)
        
        retrieved_config = self.config_manager.get_plugin_config('test_plugin')
        assert retrieved_config == test_config
    
    def test_config_file_operations(self):
        """Test saving and loading configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / 'test_config.yaml'
            
            # Set some test values
            self.config_manager.set('build.cmake_build_type', 'Debug')
            self.config_manager.set('logging.level', 'DEBUG')
            
            # Save config
            self.config_manager.save_config(config_path)
            assert config_path.exists()
            
            # Create new config manager and load
            new_config_manager = ConfigManager()
            new_config_manager.load_config(config_path)
            
            # Verify values were loaded
            assert new_config_manager.get('build.cmake_build_type') == 'Debug'
            assert new_config_manager.get('logging.level') == 'DEBUG'


class TestROS2Interface:
    """Test cases for ROS2Interface class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.ros2_interface = ROS2Interface()
    
    def test_interface_initialization(self):
        """Test ROS2 interface initializes correctly."""
        assert self.ros2_interface.logger is not None
        assert self.ros2_interface._ros2_available is None  # Lazy evaluation
    
    @patch('shutil.which')
    def test_availability_check(self, mock_which):
        """Test ROS2 availability checking."""
        # Test when ROS2 is available
        mock_which.return_value = '/usr/bin/ros2'
        assert self.ros2_interface.is_available() is True
        
        # Reset and test when ROS2 is not available
        self.ros2_interface._ros2_available = None
        mock_which.return_value = None
        assert self.ros2_interface.is_available() is False
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_subprocess):
        """Test successful command execution."""
        # Mock successful subprocess
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "test output"
        mock_process.stderr = ""
        mock_subprocess.return_value = mock_process
        
        # Mock ROS2 availability
        with patch.object(self.ros2_interface, 'is_available', return_value=True):
            result = self.ros2_interface.run_command(['ros2', 'pkg', 'list'], capture_output=True)
        
        assert result.success is True
        assert result.returncode == 0
        assert result.stdout == "test output"
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_subprocess):
        """Test failed command execution."""
        # Mock failed subprocess
        mock_subprocess.side_effect = Exception("Command failed")
        
        # Mock ROS2 availability
        with patch.object(self.ros2_interface, 'is_available', return_value=True):
            result = self.ros2_interface.run_command(['ros2', 'invalid', 'command'], capture_output=True)
        
        assert result.success is False
        assert result.returncode == 1
        assert "Unexpected error" in result.stderr
    
    def test_ros2_unavailable(self):
        """Test behavior when ROS2 is not available."""
        with patch.object(self.ros2_interface, 'is_available', return_value=False):
            result = self.ros2_interface.run_command(['ros2', 'pkg', 'list'])
        
        assert result.success is False
        assert result.returncode == 127
        assert "ROS2CLI not available" in result.stderr


class TestPluginManager:
    """Test cases for PluginManager class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.plugin_manager = PluginManager()
    
    def test_plugin_manager_initialization(self):
        """Test plugin manager initializes correctly."""
        assert self.plugin_manager.logger is not None
        assert isinstance(self.plugin_manager.plugins, dict)
        assert len(self.plugin_manager._plugin_paths) > 0
    
    def test_plugin_discovery(self):
        """Test plugin discovery functionality."""
        discovered = self.plugin_manager.discover_plugins()
        assert isinstance(discovered, list)
        
        # Should find at least the colcon and sim plugins
        plugin_names = [name.replace('_plugin', '') for name in discovered]
        assert 'colcon' in plugin_names or 'sim' in plugin_names
    
    def test_plugin_loading(self):
        """Test plugin loading functionality."""
        # Load plugins
        loaded_count = self.plugin_manager.load_plugins()
        assert loaded_count >= 0
        
        # Check if any plugins were loaded
        if loaded_count > 0:
            assert len(self.plugin_manager.plugins) > 0
    
    def test_get_plugin(self):
        """Test getting loaded plugins."""
        # Load plugins first
        self.plugin_manager.load_plugins()
        
        # Test getting existing plugin (if any)
        for plugin_name in self.plugin_manager.plugins:
            plugin = self.plugin_manager.get_plugin(plugin_name)
            assert plugin is not None
            assert hasattr(plugin, 'name')
            assert hasattr(plugin, 'is_available')
        
        # Test getting non-existent plugin
        non_existent = self.plugin_manager.get_plugin('non_existent_plugin')
        assert non_existent is None
    
    def test_list_plugins(self):
        """Test listing plugin information."""
        # Load plugins first
        self.plugin_manager.load_plugins()
        
        plugin_info = self.plugin_manager.list_plugins()
        assert isinstance(plugin_info, dict)
        
        # Check structure of plugin info
        for name, info in plugin_info.items():
            assert 'name' in info
            assert 'description' in info
            assert 'available' in info
            assert isinstance(info['available'], bool)


class TestEnvironmentOverrides:
    """Test cases for environment variable overrides."""
    
    def test_build_type_override(self):
        """Test build type environment override."""
        with patch.dict(os.environ, {'ONECODE_BUILD_TYPE': 'Debug'}):
            config_manager = ConfigManager()
            config_manager.apply_environment_overrides()
            assert config_manager.get('build.cmake_build_type') == 'Debug'
    
    def test_parallel_jobs_override(self):
        """Test parallel jobs environment override."""
        with patch.dict(os.environ, {'ONECODE_PARALLEL_JOBS': '8'}):
            config_manager = ConfigManager()
            config_manager.apply_environment_overrides()
            assert config_manager.get('build.parallel_jobs') == 8
    
    def test_log_level_override(self):
        """Test log level environment override."""
        with patch.dict(os.environ, {'ONECODE_LOG_LEVEL': 'DEBUG'}):
            config_manager = ConfigManager()
            config_manager.apply_environment_overrides()
            assert config_manager.get('logging.level') == 'DEBUG'
    
    def test_invalid_parallel_jobs_override(self):
        """Test invalid parallel jobs environment override."""
        with patch.dict(os.environ, {'ONECODE_PARALLEL_JOBS': 'invalid'}):
            config_manager = ConfigManager()
            # Should not raise exception but log warning
            config_manager.apply_environment_overrides()
            # Parallel jobs should remain default (None)
            assert config_manager.get('build.parallel_jobs') is None


if __name__ == '__main__':
    pytest.main([__file__])
