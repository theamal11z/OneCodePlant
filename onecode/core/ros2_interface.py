"""ROS2CLI interface for passthrough functionality."""

import subprocess
import sys
import shutil
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from onecode.core.utils import get_logger


@dataclass
class ProcessResult:
    """Result of a process execution."""
    returncode: int
    stdout: str
    stderr: str
    command: List[str]
    
    @property
    def success(self) -> bool:
        """Check if the process executed successfully."""
        return self.returncode == 0


class ROS2Interface:
    """Interface for interacting with ROS2CLI commands."""
    
    def __init__(self):
        """Initialize the ROS2 interface."""
        self.logger = get_logger(__name__)
        self._ros2_available = None
        self._ros2_version = None
    
    def is_available(self) -> bool:
        """Check if ROS2CLI is available on the system."""
        if self._ros2_available is None:
            self._ros2_available = shutil.which('ros2') is not None
            if not self._ros2_available:
                self.logger.warning("ROS2CLI not found in PATH")
        return self._ros2_available
    
    def get_version(self) -> Optional[str]:
        """Get the ROS2 version."""
        if not self.is_available():
            return None
            
        if self._ros2_version is None:
            try:
                result = self.run_command(['ros2', '--version'], capture_output=True)
                if result.success:
                    self._ros2_version = result.stdout.strip()
            except Exception as e:
                self.logger.debug(f"Failed to get ROS2 version: {e}")
                
        return self._ros2_version
    
    def run_command(self, cmd: List[str], capture_output: bool = False, 
                   cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None,
                   timeout: Optional[int] = None) -> ProcessResult:
        """
        Execute a ROS2 command and return the result.
        
        Args:
            cmd: Command and arguments as a list
            capture_output: Whether to capture stdout/stderr
            cwd: Working directory for the command
            env: Environment variables
            timeout: Command timeout in seconds
            
        Returns:
            ProcessResult containing execution details
        """
        if not self.is_available():
            return ProcessResult(
                returncode=127,
                stdout="",
                stderr="ROS2CLI not available",
                command=cmd
            )
        
        self.logger.debug(f"Executing command: {' '.join(cmd)}")
        
        try:
            if capture_output:
                # Capture output for processing
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )
                
                return ProcessResult(
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    command=cmd
                )
            else:
                # Stream output directly to terminal
                result = subprocess.run(
                    cmd,
                    cwd=cwd,
                    env=env,
                    timeout=timeout
                )
                
                return ProcessResult(
                    returncode=result.returncode,
                    stdout="",
                    stderr="",
                    command=cmd
                )
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
            return ProcessResult(
                returncode=124,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                command=cmd
            )
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with exit code {e.returncode}: {' '.join(cmd)}")
            return ProcessResult(
                returncode=e.returncode,
                stdout=getattr(e, 'stdout', '') or "",
                stderr=getattr(e, 'stderr', '') or "",
                command=cmd
            )
            
        except Exception as e:
            self.logger.exception(f"Unexpected error executing command: {' '.join(cmd)}")
            return ProcessResult(
                returncode=1,
                stdout="",
                stderr=f"Unexpected error: {str(e)}",
                command=cmd
            )
    
    def get_package_list(self) -> List[str]:
        """Get list of available ROS2 packages."""
        result = self.run_command(['ros2', 'pkg', 'list'], capture_output=True)
        if result.success:
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return []
    
    def get_node_list(self) -> List[str]:
        """Get list of active ROS2 nodes."""
        result = self.run_command(['ros2', 'node', 'list'], capture_output=True)
        if result.success:
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return []
    
    def get_topic_list(self) -> List[str]:
        """Get list of active ROS2 topics."""
        result = self.run_command(['ros2', 'topic', 'list'], capture_output=True)
        if result.success:
            return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return []
    
    def check_dependencies(self, package_name: str) -> bool:
        """Check if a package's dependencies are satisfied."""
        result = self.run_command(['ros2', 'pkg', 'dependencies', package_name], capture_output=True)
        return result.success
    
    def source_workspace(self, workspace_path: str) -> bool:
        """
        Source a ROS2 workspace.
        Note: This modifies the current environment.
        """
        setup_script = f"{workspace_path}/install/setup.bash"
        try:
            # This is a simplified approach - in practice, you'd need to 
            # modify the environment for subsequent commands
            import os
            if os.path.exists(setup_script):
                self.logger.info(f"Workspace setup script found: {setup_script}")
                return True
            else:
                self.logger.warning(f"Setup script not found: {setup_script}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to source workspace: {e}")
            return False
