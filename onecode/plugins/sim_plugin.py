"""Simulation plugin for OneCode Plant CLI."""

import shutil
import os
import signal
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from onecode.plugins.base import PluginBase
from onecode.core.ros2_interface import ROS2Interface
from onecode.core.utils import get_logger


class SimulationPlugin(PluginBase):
    """Plugin for managing simulation environments."""
    
    def __init__(self):
        """Initialize the Simulation plugin."""
        super().__init__()
        self.ros2_interface = ROS2Interface()
        self._gazebo_available = None
        self._running_processes = []
    
    @property
    def name(self) -> str:
        """Plugin name."""
        return "simulation"
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return "Simulation environment management (Gazebo, Isaac Sim, etc.)"
    
    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"
    
    @property
    def commands(self) -> List[str]:
        """List of commands provided by this plugin."""
        return [
            "start_simulation",
            "stop_simulation",
            "list_worlds",
            "spawn_robot"
        ]
    
    def is_available(self) -> bool:
        """Check if simulation tools are available."""
        if self._gazebo_available is None:
            # Check for Gazebo (both classic and new)
            self._gazebo_available = (
                shutil.which('gazebo') is not None or 
                shutil.which('gz') is not None or
                shutil.which('ign') is not None
            )
            
            if not self._gazebo_available:
                self.logger.warning("No simulation tools found (Gazebo, Ignition, etc.)")
        
        return self._gazebo_available
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """Get additional information about the simulation plugin."""
        info = super().get_info()
        
        if info is not None and self.is_available():
            # Check which simulators are available
            simulators = []
            
            if shutil.which('gazebo'):
                result = self.ros2_interface.run_command(['gazebo', '--version'], capture_output=True)
                if result.success:
                    simulators.append(f"Gazebo Classic: {result.stdout.strip()}")
            
            if shutil.which('gz'):
                result = self.ros2_interface.run_command(['gz', '--version'], capture_output=True)
                if result.success:
                    simulators.append(f"Gazebo: {result.stdout.strip()}")
            
            if shutil.which('ign'):
                result = self.ros2_interface.run_command(['ign', '--versions'], capture_output=True)
                if result.success:
                    simulators.append(f"Ignition: {result.stdout.strip()}")
            
            info['available_simulators'] = simulators
        
        return info
    
    def start_simulation(self, world: Optional[str] = None, robot: Optional[str] = None,
                        headless: bool = False, extra_args: Optional[List[str]] = None) -> int:
        """
        Start a simulation environment.
        
        Args:
            world: World file to load
            robot: Robot model to spawn
            headless: Run simulation in headless mode
            extra_args: Additional arguments to pass to the simulator
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self.is_available():
            self.logger.error("No simulation tools available")
            return 1
        
        # Determine which simulator to use
        simulator_cmd = self._get_preferred_simulator()
        if not simulator_cmd:
            self.logger.error("No suitable simulator found")
            return 1
        
        self.logger.info(f"Starting simulation with {simulator_cmd[0]}")
        
        # Build command
        cmd = simulator_cmd.copy()
        
        # Add headless mode
        if headless:
            if 'gazebo' in cmd[0]:
                cmd.append('--headless')
            elif 'gz' in cmd[0] or 'ign' in cmd[0]:
                cmd.extend(['--headless-rendering', '-s'])
        
        # Add world file
        if world:
            world_path = self._find_world_file(world)
            if world_path:
                cmd.append(str(world_path))
                self.logger.info(f"Loading world: {world_path}")
            else:
                self.logger.warning(f"World file not found: {world}")
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        self.logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            # Start the simulation process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if headless else None,
                stderr=subprocess.PIPE if headless else None
            )
            
            self._running_processes.append(process)
            
            # If spawning a robot, do it after simulation starts
            if robot and not headless:
                self._spawn_robot_delayed(robot)
            
            if headless:
                # Wait for process to complete in headless mode
                return_code = process.wait()
                self._running_processes.remove(process)
                return return_code
            else:
                # Return immediately for GUI mode
                self.logger.info("Simulation started in GUI mode")
                return 0
                
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            return 1
    
    def stop_simulation(self) -> int:
        """
        Stop all running simulation processes.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self._running_processes:
            self.logger.info("No running simulation processes")
            return 0
        
        self.logger.info(f"Stopping {len(self._running_processes)} simulation process(es)")
        
        for process in self._running_processes[:]:  # Copy list to avoid modification issues
            try:
                process.terminate()
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't terminate gracefully, forcing...")
                process.kill()
            except Exception as e:
                self.logger.error(f"Error stopping process: {e}")
            finally:
                if process in self._running_processes:
                    self._running_processes.remove(process)
        
        self.logger.info("All simulation processes stopped")
        return 0
    
    def list_worlds(self, search_paths: Optional[List[str]] = None) -> int:
        """
        List available world files.
        
        Args:
            search_paths: Additional paths to search for world files
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        world_files = self._find_world_files(search_paths)
        
        if world_files:
            print("Available world files:")
            print("-" * 40)
            for world_file in sorted(world_files):
                print(f"  {world_file.name:30} {world_file.parent}")
        else:
            print("No world files found")
        
        return 0
    
    def spawn_robot(self, robot: str, x: float = 0.0, y: float = 0.0, z: float = 0.0,
                   yaw: float = 0.0) -> int:
        """
        Spawn a robot in the simulation.
        
        Args:
            robot: Robot model name or path to robot description
            x: X position
            y: Y position  
            z: Z position
            yaw: Yaw rotation
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if not self.ros2_interface.is_available():
            self.logger.error("ROS2 not available for robot spawning")
            return 1
        
        # Try to spawn robot using ros2 service call
        spawn_args = '{{name: "{}", xml: "", initial_pose: {{position: {{x: {}, y: {}, z: {}}}, orientation: {{z: {}}}}}}}'.format(
            robot, x, y, z, yaw
        )
        cmd = [
            'ros2', 'service', 'call', '/spawn_entity',
            'gazebo_msgs/SpawnEntity',
            spawn_args
        ]
        
        self.logger.info(f"Spawning robot {robot} at position ({x}, {y}, {z})")
        result = self.ros2_interface.run_command(cmd)
        
        if result.success:
            self.logger.info(f"Successfully spawned robot: {robot}")
        else:
            self.logger.error(f"Failed to spawn robot: {robot}")
        
        return result.returncode
    
    def _get_preferred_simulator(self) -> Optional[List[str]]:
        """Get the preferred simulator command."""
        # Prefer newer Gazebo over classic
        if shutil.which('gz'):
            return ['gz', 'sim']
        elif shutil.which('ign'):
            return ['ign', 'gazebo']
        elif shutil.which('gazebo'):
            return ['gazebo']
        
        return None
    
    def _find_world_file(self, world_name: str) -> Optional[Path]:
        """Find a world file by name."""
        if Path(world_name).exists():
            return Path(world_name)
        
        # Search in common world directories
        search_paths = [
            Path.cwd(),
            Path('/usr/share/gazebo/worlds'),
            Path('/opt/ros/*/share/*/worlds').expanduser(),
        ]
        
        # Add environment paths
        gazebo_model_path = os.environ.get('GAZEBO_MODEL_PATH', '')
        if gazebo_model_path:
            for path in gazebo_model_path.split(':'):
                search_paths.append(Path(path))
        
        for search_path in search_paths:
            if search_path.exists():
                for world_file in search_path.rglob(f"{world_name}*"):
                    if world_file.suffix in ['.world', '.sdf']:
                        return world_file
        
        return None
    
    def _find_world_files(self, additional_paths: Optional[List[str]] = None) -> List[Path]:
        """Find all available world files."""
        world_files = []
        
        search_paths = [
            Path('/usr/share/gazebo/worlds'),
            Path.cwd(),
        ]
        
        if additional_paths:
            search_paths.extend([Path(p) for p in additional_paths])
        
        # Add environment paths
        gazebo_model_path = os.environ.get('GAZEBO_MODEL_PATH', '')
        if gazebo_model_path:
            for path in gazebo_model_path.split(':'):
                search_paths.append(Path(path))
        
        for search_path in search_paths:
            if search_path.exists():
                for world_file in search_path.rglob('*'):
                    if world_file.suffix in ['.world', '.sdf'] and world_file.is_file():
                        world_files.append(world_file)
        
        return world_files
    
    def _spawn_robot_delayed(self, robot: str):
        """Spawn robot after a delay to ensure simulation is ready."""
        import threading
        import time
        
        def delayed_spawn():
            time.sleep(3)  # Wait for simulation to initialize
            self.spawn_robot(robot)
        
        thread = threading.Thread(target=delayed_spawn, daemon=True)
        thread.start()
    
    def cleanup(self) -> bool:
        """Cleanup running processes."""
        self.stop_simulation()
        return super().cleanup()
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for the simulation plugin."""
        return {
            "type": "object",
            "properties": {
                "default_world": {
                    "type": ["string", "null"],
                    "default": None
                },
                "default_robot": {
                    "type": ["string", "null"],
                    "default": None
                },
                "headless_mode": {
                    "type": "boolean",
                    "default": False
                },
                "auto_close_on_exit": {
                    "type": "boolean",
                    "default": True
                },
                "gazebo_model_path": {
                    "type": ["string", "null"],
                    "default": None
                },
                "gazebo_resource_path": {
                    "type": ["string", "null"],
                    "default": None
                }
            }
        }
