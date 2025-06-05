"""Tests for Colcon plugin functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from onecode.plugins.colcon_plugin import ColconPlugin
from onecode.core.ros2_interface import ProcessResult


class TestColconPlugin:
    """Test cases for ColconPlugin class."""
    
    def setup_method(self):
        """Setup test environment."""
        self.plugin = ColconPlugin()
    
    def test_plugin_properties(self):
        """Test plugin basic properties."""
        assert self.plugin.name == "colcon"
        assert "Colcon build system" in self.plugin.description
        assert self.plugin.version == "1.0.0"
        assert "build_workspace" in self.plugin.commands
        assert "clean_workspace" in self.plugin.commands
        assert "test_workspace" in self.plugin.commands
        assert "list_packages" in self.plugin.commands
    
    @patch('shutil.which')
    def test_availability_check(self, mock_which):
        """Test plugin availability checking."""
        # Test when colcon is available
        mock_which.return_value = '/usr/bin/colcon'
        assert self.plugin.is_available() is True
        
        # Reset and test when colcon is not available
        self.plugin._colcon_available = None
        mock_which.return_value = None
        assert self.plugin.is_available() is False
    
    @patch('onecode.core.utils.find_ros2_workspace')
    def test_build_workspace_no_workspace(self, mock_find_workspace):
        """Test build workspace when no workspace is found."""
        mock_find_workspace.return_value = None
        
        result = self.plugin.build_workspace()
        assert result == 1  # Should fail
    
    @patch('onecode.core.utils.find_ros2_workspace')
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_build_workspace_success(self, mock_run_command, mock_find_workspace):
        """Test successful workspace build."""
        # Mock workspace found
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            mock_find_workspace.return_value = workspace_path
            
            # Mock successful build
            mock_run_command.return_value = ProcessResult(
                returncode=0,
                stdout="Build completed",
                stderr="",
                command=['colcon', 'build']
            )
            
            # Mock plugin availability
            with patch.object(self.plugin, 'is_available', return_value=True):
                result = self.plugin.build_workspace()
            
            assert result == 0
            mock_run_command.assert_called_once()
            
            # Check that the command includes expected arguments
            call_args = mock_run_command.call_args
            cmd = call_args[0][0]  # First positional argument
            assert 'colcon' in cmd
            assert 'build' in cmd
            assert '--symlink-install' in cmd
    
    @patch('onecode.core.utils.find_ros2_workspace')
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_build_workspace_debug_mode(self, mock_run_command, mock_find_workspace):
        """Test workspace build in debug mode."""
        # Mock workspace found
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            mock_find_workspace.return_value = workspace_path
            
            # Mock successful build
            mock_run_command.return_value = ProcessResult(
                returncode=0,
                stdout="Build completed",
                stderr="",
                command=['colcon', 'build']
            )
            
            # Mock plugin availability
            with patch.object(self.plugin, 'is_available', return_value=True):
                result = self.plugin.build_workspace(debug=True)
            
            assert result == 0
            
            # Check that debug build type is used
            call_args = mock_run_command.call_args
            cmd = call_args[0][0]
            cmd_str = ' '.join(cmd)
            assert '-DCMAKE_BUILD_TYPE=Debug' in cmd_str
    
    @patch('onecode.core.utils.find_ros2_workspace')
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_build_workspace_specific_packages(self, mock_run_command, mock_find_workspace):
        """Test workspace build with specific packages."""
        # Mock workspace found
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            mock_find_workspace.return_value = workspace_path
            
            # Mock successful build
            mock_run_command.return_value = ProcessResult(
                returncode=0,
                stdout="Build completed",
                stderr="",
                command=['colcon', 'build']
            )
            
            # Mock plugin availability
            with patch.object(self.plugin, 'is_available', return_value=True):
                result = self.plugin.build_workspace(packages=['pkg1', 'pkg2'])
            
            assert result == 0
            
            # Check that specific packages are included
            call_args = mock_run_command.call_args
            cmd = call_args[0][0]
            assert '--packages-select' in cmd
            assert 'pkg1' in cmd
            assert 'pkg2' in cmd
    
    @patch('onecode.core.utils.find_ros2_workspace')
    @patch('shutil.rmtree')
    def test_clean_workspace(self, mock_rmtree, mock_find_workspace):
        """Test workspace cleaning."""
        # Mock workspace found
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            mock_find_workspace.return_value = workspace_path
            
            # Create mock directories
            build_dir = workspace_path / 'build'
            build_dir.mkdir()
            
            with patch.object(build_dir, 'exists', return_value=True):
                result = self.plugin.clean_workspace(build_dir=True)
            
            assert result == 0
            mock_rmtree.assert_called_once()
    
    @patch('onecode.core.utils.find_ros2_workspace')
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_test_workspace(self, mock_run_command, mock_find_workspace):
        """Test workspace testing."""
        # Mock workspace found
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            mock_find_workspace.return_value = workspace_path
            
            # Mock successful test
            mock_run_command.return_value = ProcessResult(
                returncode=0,
                stdout="Tests completed",
                stderr="",
                command=['colcon', 'test']
            )
            
            # Mock plugin availability
            with patch.object(self.plugin, 'is_available', return_value=True):
                result = self.plugin.test_workspace()
            
            assert result == 0
            
            # Should call both test and test-result commands
            assert mock_run_command.call_count >= 1
            
            # First call should be the test command
            first_call = mock_run_command.call_args_list[0]
            cmd = first_call[0][0]
            assert 'colcon' in cmd
            assert 'test' in cmd
    
    @patch('onecode.core.utils.find_ros2_workspace')
    @patch('onecode.core.ros2_interface.ROS2Interface.run_command')
    def test_list_packages(self, mock_run_command, mock_find_workspace):
        """Test package listing."""
        # Mock workspace found
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            mock_find_workspace.return_value = workspace_path
            
            # Mock successful package list
            mock_run_command.return_value = ProcessResult(
                returncode=0,
                stdout="package1\npackage2\npackage3",
                stderr="",
                command=['colcon', 'list']
            )
            
            # Mock plugin availability
            with patch.object(self.plugin, 'is_available', return_value=True):
                result = self.plugin.list_packages()
            
            assert result == 0
            mock_run_command.assert_called_once()
            
            # Check command structure
            call_args = mock_run_command.call_args
            cmd = call_args[0][0]
            assert 'colcon' in cmd
            assert 'list' in cmd
            assert '--topological-order' in cmd
    
    def test_plugin_unavailable(self):
        """Test plugin behavior when colcon is unavailable."""
        with patch.object(self.plugin, 'is_available', return_value=False):
            # All operations should fail when colcon is unavailable
            assert self.plugin.build_workspace() == 1
            assert self.plugin.test_workspace() == 1
            assert self.plugin.list_packages() == 1
    
    def test_get_info(self):
        """Test plugin info retrieval."""
        with patch.object(self.plugin, 'is_available', return_value=True):
            # Mock colcon version
            mock_result = ProcessResult(
                returncode=0,
                stdout="colcon-core 0.10.0",
                stderr="",
                command=['colcon', '--version']
            )
            
            with patch.object(self.plugin.ros2_interface, 'run_command', return_value=mock_result):
                info = self.plugin.get_info()
            
            assert info is not None
            assert 'name' in info
            assert 'available' in info
            assert info['name'] == 'colcon'
    
    def test_config_schema(self):
        """Test plugin configuration schema."""
        schema = self.plugin.get_config_schema()
        
        assert isinstance(schema, dict)
        assert 'type' in schema
        assert schema['type'] == 'object'
        assert 'properties' in schema
        
        properties = schema['properties']
        assert 'cmake_build_type' in properties
        assert 'symlink_install' in properties
        assert 'parallel_jobs' in properties
    
    @patch('onecode.core.utils.find_ros2_workspace')
    def test_count_packages(self, mock_find_workspace):
        """Test package counting functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            src_dir = workspace_path / 'src'
            src_dir.mkdir()
            
            # Create mock package.xml files
            pkg1_dir = src_dir / 'pkg1'
            pkg1_dir.mkdir()
            (pkg1_dir / 'package.xml').touch()
            
            pkg2_dir = src_dir / 'pkg2' 
            pkg2_dir.mkdir()
            (pkg2_dir / 'package.xml').touch()
            
            count = self.plugin._count_packages(workspace_path)
            assert count == 2


if __name__ == '__main__':
    pytest.main([__file__])
