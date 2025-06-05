"""Colcon build system plugin for OneCode Plant CLI."""

import shutil
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from onecode.plugins.base import PluginBase
from onecode.core.ros2_interface import ROS2Interface
from onecode.core.utils import find_ros2_workspace, format_duration, get_terminal_width
import time


class ColconPlugin(PluginBase):
    """Plugin for integrating with the Colcon build system."""
    
    def __init__(self):
        """Initialize the Colcon plugin."""
        super().__init__()
        self.ros2_interface = ROS2Interface()
        self._colcon_available = None
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return "colcon"
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return "Colcon build system integration for ROS2 packages"
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @property
    def commands(self) -> List[str]:
        """List of commands provided by this plugin."""
        return [
            "build_workspace",
            "clean_workspace", 
            "test_workspace",
            "list_packages"
        ]
    
    def is_available(self) -> bool:
        """Check if Colcon is available."""
        if self._colcon_available is None:
            self._colcon_available = shutil.which('colcon') is not None
            if not self._colcon_available:
                self.logger.warning("Colcon not found in PATH")
        return self._colcon_available
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get additional information about the Colcon plugin."""
        info = super().get_info()
        
        if self.is_available():
            # Get colcon version
            result = self.ros2_interface.run_command(['colcon', '--version'], capture_output=True)
            if result.success:
                info['colcon_version'] = result.stdout.strip()
        
        # Find workspace info
        workspace = find_ros2_workspace()
        if workspace:
            info['workspace_path'] = str(workspace)
            info['workspace_packages'] = self._count_packages(workspace)
        
        return info
    
    def _count_packages(self, workspace_path: Path) -> int:
        """Count the number of packages in a workspace."""
        src_dir = workspace_path / 'src'
        if not src_dir.exists():
            return 0
        
        package_count = 0
        for item in src_dir.rglob('package.xml'):
            package_count += 1
        
        return package_count
    
    def build_workspace(self, debug: bool = False, packages: Optional[List[str]] = None,
                       parallel_jobs: Optional[int] = None, symlink_install: bool = True,
                       continue_on_error: bool = False, cmake_args: Optional[str] = None,
                       ament_cmake_args: Optional[str] = None) -> int:
        """
        Build the ROS2 workspace using Colcon.
        
        Args:
            debug: Build in debug mode
            packages: Specific packages to build
            parallel_jobs: Number of parallel jobs
            symlink_install: Use symlink install
            continue_on_error: Continue building other packages on error
            cmake_args: Additional CMake arguments
            ament_cmake_args: Additional ament CMake arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self.is_available():
            self.logger.error("Colcon is not available")
            return 1
        
        # Find workspace
        workspace = find_ros2_workspace()
        if not workspace:
            self.logger.error("No ROS2 workspace found")
            return 1
        
        self.logger.info(f"Building workspace: {workspace}")
        
        # Build command
        cmd = ['colcon', 'build']
        
        # Add symlink install
        if symlink_install:
            cmd.append('--symlink-install')
        
        # Add build type
        build_type = 'Debug' if debug else 'Release'
        cmd.extend(['--cmake-args', f'-DCMAKE_BUILD_TYPE={build_type}'])
        
        # Add custom cmake args
        if cmake_args:
            cmd.extend(['--cmake-args'] + cmake_args.split())
        
        # Add ament cmake args
        if ament_cmake_args:
            cmd.extend(['--ament-cmake-args'] + ament_cmake_args.split())
        
        # Add parallel jobs
        if parallel_jobs:
            cmd.extend(['--parallel-workers', str(parallel_jobs)])
        
        # Add continue on error
        if continue_on_error:
            cmd.append('--continue-on-error')
        
        # Add specific packages
        if packages:
            cmd.extend(['--packages-select'] + packages)
        
        # Add output formatting
        cmd.extend(['--event-handlers', 'console_direct+'])
        
        self.logger.info(f"Executing: {' '.join(cmd)}")
        
        # Execute build
        start_time = time.time()
        result = self.ros2_interface.run_command(cmd, cwd=workspace)
        build_time = time.time() - start_time
        
        # Report results
        if result.success:
            self.logger.info(f"Build completed successfully in {format_duration(build_time)}")
        else:
            self.logger.error(f"Build failed after {format_duration(build_time)}")
        
        return result.returncode
    
    def clean_workspace(self, build_dir: bool = True, install_dir: bool = False, 
                       log_dir: bool = False) -> int:
        """
        Clean workspace build artifacts.
        
        Args:
            build_dir: Clean build directory
            install_dir: Clean install directory  
            log_dir: Clean log directory
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        workspace = find_ros2_workspace()
        if not workspace:
            self.logger.error("No ROS2 workspace found")
            return 1
        
        self.logger.info(f"Cleaning workspace: {workspace}")
        
        cleaned_dirs = []
        
        if build_dir:
            build_path = workspace / 'build'
            if build_path.exists():
                shutil.rmtree(build_path)
                cleaned_dirs.append('build')
        
        if install_dir:
            install_path = workspace / 'install'
            if install_path.exists():
                shutil.rmtree(install_path)
                cleaned_dirs.append('install')
        
        if log_dir:
            log_path = workspace / 'log'
            if log_path.exists():
                shutil.rmtree(log_path)
                cleaned_dirs.append('log')
        
        if cleaned_dirs:
            self.logger.info(f"Cleaned directories: {', '.join(cleaned_dirs)}")
        else:
            self.logger.info("No directories to clean")
        
        return 0
    
    def test_workspace(self, packages: Optional[List[str]] = None,
                      parallel_jobs: Optional[int] = None) -> int:
        """
        Run tests for packages in the workspace.
        
        Args:
            packages: Specific packages to test
            parallel_jobs: Number of parallel jobs
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self.is_available():
            self.logger.error("Colcon is not available")
            return 1
        
        workspace = find_ros2_workspace()
        if not workspace:
            self.logger.error("No ROS2 workspace found")
            return 1
        
        self.logger.info(f"Running tests in workspace: {workspace}")
        
        # Test command
        cmd = ['colcon', 'test']
        
        # Add parallel jobs
        if parallel_jobs:
            cmd.extend(['--parallel-workers', str(parallel_jobs)])
        
        # Add specific packages
        if packages:
            cmd.extend(['--packages-select'] + packages)
        
        # Execute tests
        start_time = time.time()
        result = self.ros2_interface.run_command(cmd, cwd=workspace)
        test_time = time.time() - start_time
        
        # Run test result summary
        if result.success:
            summary_cmd = ['colcon', 'test-result', '--verbose']
            self.ros2_interface.run_command(summary_cmd, cwd=workspace)
        
        # Report results
        if result.success:
            self.logger.info(f"Tests completed successfully in {format_duration(test_time)}")
        else:
            self.logger.error(f"Tests failed after {format_duration(test_time)}")
        
        return result.returncode
    
    def list_packages(self, workspace_path: Optional[Path] = None) -> int:
        """
        List packages in the workspace.
        
        Args:
            workspace_path: Optional workspace path (uses current if not specified)
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self.is_available():
            self.logger.error("Colcon is not available")
            return 1
        
        if workspace_path is None:
            workspace_path = find_ros2_workspace()
        
        if not workspace_path:
            self.logger.error("No ROS2 workspace found")
            return 1
        
        # List packages command
        cmd = ['colcon', 'list', '--topological-order']
        
        result = self.ros2_interface.run_command(cmd, cwd=workspace_path, capture_output=True)
        
        if result.success:
            print("Packages in workspace:")
            print("-" * 40)
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            self.logger.error("Failed to list packages")
        
        return result.returncode
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for the Colcon plugin."""
        return {
            "type": "object",
            "properties": {
                "cmake_build_type": {
                    "type": "string",
                    "enum": ["Debug", "Release", "RelWithDebInfo", "MinSizeRel"],
                    "default": "Release"
                },
                "symlink_install": {
                    "type": "boolean",
                    "default": True
                },
                "parallel_jobs": {
                    "type": ["integer", "null"],
                    "minimum": 1,
                    "default": None
                },
                "continue_on_error": {
                    "type": "boolean", 
                    "default": False
                },
                "cmake_args": {
                    "type": ["string", "null"],
                    "default": None
                },
                "ament_cmake_args": {
                    "type": ["string", "null"],
                    "default": None
                }
            }
        }
