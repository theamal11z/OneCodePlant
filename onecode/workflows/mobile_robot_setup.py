"""Mobile robot development workflow."""

from pathlib import Path
from typing import Optional, Dict, Any

from onecode.core.utils import get_logger
from onecode.core.ros2_interface import ROS2Interface


class MobileRobotSetupWorkflow:
    """Workflow for setting up a mobile robot development environment."""
    
    def __init__(self):
        """Initialize the workflow."""
        self.logger = get_logger(__name__)
        self.ros2_interface = ROS2Interface()
    
    def create_workspace(self, workspace_name: str, workspace_path: Optional[Path] = None) -> bool:
        """
        Create a new ROS2 workspace for mobile robot development.
        
        Args:
            workspace_name: Name of the workspace
            workspace_path: Path where to create the workspace
            
        Returns:
            True if successful, False otherwise
        """
        if workspace_path is None:
            workspace_path = Path.cwd() / workspace_name
        
        self.logger.info(f"Creating mobile robot workspace: {workspace_path}")
        
        try:
            # Create workspace structure
            src_dir = workspace_path / 'src'
            src_dir.mkdir(parents=True, exist_ok=True)
            
            # Create basic packages
            packages = [
                f"{workspace_name}_description",
                f"{workspace_name}_bringup", 
                f"{workspace_name}_navigation",
                f"{workspace_name}_control"
            ]
            
            for package in packages:
                self._create_package(src_dir, package)
            
            self.logger.info(f"Successfully created workspace: {workspace_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create workspace: {e}")
            return False
    
    def _create_package(self, src_dir: Path, package_name: str) -> bool:
        """Create a ROS2 package with appropriate dependencies."""
        package_dir = src_dir / package_name
        
        if package_dir.exists():
            self.logger.warning(f"Package {package_name} already exists")
            return True
        
        # Determine package dependencies based on name
        dependencies = ['rclcpp', 'rclpy']
        
        if 'description' in package_name:
            dependencies.extend(['robot_state_publisher', 'joint_state_publisher', 'urdf', 'xacro'])
        elif 'bringup' in package_name:
            dependencies.extend(['launch', 'launch_ros'])
        elif 'navigation' in package_name:
            dependencies.extend(['nav2_common', 'nav2_bringup'])
        elif 'control' in package_name:
            dependencies.extend(['controller_manager', 'joint_state_broadcaster'])
        
        # Create package using ros2 pkg create
        cmd = ['ros2', 'pkg', 'create', package_name] + ['--dependencies'] + dependencies
        
        result = self.ros2_interface.run_command(cmd, cwd=src_dir)
        
        if result.success:
            self.logger.info(f"Created package: {package_name}")
            return True
        else:
            self.logger.error(f"Failed to create package: {package_name}")
            return False
    
    def setup_navigation(self, workspace_path: Path, robot_name: str) -> bool:
        """
        Setup navigation configuration for the mobile robot.
        
        Args:
            workspace_path: Path to the workspace
            robot_name: Name of the robot
            
        Returns:
            True if successful, False otherwise
        """
        nav_package = workspace_path / 'src' / f"{robot_name}_navigation"
        
        if not nav_package.exists():
            self.logger.error(f"Navigation package not found: {nav_package}")
            return False
        
        self.logger.info(f"Setting up navigation for {robot_name}")
        
        try:
            # Create navigation config directories
            config_dir = nav_package / 'config'
            config_dir.mkdir(exist_ok=True)
            
            launch_dir = nav_package / 'launch'
            launch_dir.mkdir(exist_ok=True)
            
            # Create basic navigation parameter file
            nav_params = self._generate_nav_params(robot_name)
            nav_params_file = config_dir / 'nav2_params.yaml'
            
            with open(nav_params_file, 'w') as f:
                f.write(nav_params)
            
            # Create basic navigation launch file
            nav_launch = self._generate_nav_launch(robot_name)
            nav_launch_file = launch_dir / 'navigation.launch.py'
            
            with open(nav_launch_file, 'w') as f:
                f.write(nav_launch)
            
            self.logger.info("Navigation setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup navigation: {e}")
            return False
    
    def _generate_nav_params(self, robot_name: str) -> str:
        """Generate basic navigation parameters."""
        return f"""# Navigation parameters for {robot_name}

bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom
    bt_loop_duration: 10
    default_server_timeout: 20
    enable_groot_monitoring: True
    groot_zmq_publisher_port: 1666
    groot_zmq_server_port: 1667
    default_nav_to_pose_bt_xml: ""
    default_nav_through_poses_bt_xml: ""
    plugin_lib_names:
    - nav2_compute_path_to_pose_action_bt_node
    - nav2_compute_path_through_poses_action_bt_node
    - nav2_follow_path_action_bt_node
    - nav2_back_up_action_bt_node
    - nav2_spin_action_bt_node
    - nav2_wait_action_bt_node
    - nav2_clear_costmap_service_bt_node
    - nav2_is_stuck_condition_bt_node
    - nav2_goal_reached_condition_bt_node
    - nav2_goal_updated_condition_bt_node
    - nav2_initial_pose_received_condition_bt_node
    - nav2_reinitialize_global_localization_service_bt_node
    - nav2_rate_controller_bt_node
    - nav2_distance_controller_bt_node
    - nav2_speed_controller_bt_node
    - nav2_truncate_path_action_bt_node
    - nav2_goal_updater_node_bt_node
    - nav2_recovery_node_bt_node
    - nav2_pipeline_sequence_bt_node
    - nav2_round_robin_node_bt_node
    - nav2_transform_available_condition_bt_node
    - nav2_time_expired_condition_bt_node
    - nav2_distance_traveled_condition_bt_node
    - nav2_single_trigger_bt_node
    - nav2_is_battery_low_condition_bt_node
    - nav2_navigate_through_poses_action_bt_node
    - nav2_navigate_to_pose_action_bt_node
    - nav2_remove_passed_goals_action_bt_node
    - nav2_planner_selector_bt_node
    - nav2_controller_selector_bt_node
    - nav2_goal_checker_selector_bt_node

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.5
    min_theta_velocity_threshold: 0.001
    failure_tolerance: 0.3
    progress_checker_plugin: "progress_checker"
    goal_checker_plugins: ["general_goal_checker"]
    controller_plugins: ["FollowPath"]

    progress_checker:
      plugin: "nav2_controller::SimpleProgressChecker"
      required_movement_radius: 0.5
      movement_time_allowance: 10.0
      
    general_goal_checker:
      stateful: True
      plugin: "nav2_controller::SimpleGoalChecker"
      xy_goal_tolerance: 0.25
      yaw_goal_tolerance: 0.25
      
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      debug_trajectory_details: True
      min_vel_x: 0.0
      min_vel_y: 0.0
      max_vel_x: 0.26
      max_vel_y: 0.0
      max_vel_theta: 1.0
      min_speed_xy: 0.0
      max_speed_xy: 0.26
      min_speed_theta: 0.0
      acc_lim_x: 2.5
      acc_lim_y: 0.0
      acc_lim_theta: 3.2
      decel_lim_x: -2.5
      decel_lim_y: 0.0
      decel_lim_theta: -3.2
      vx_samples: 20
      vy_samples: 5
      vtheta_samples: 20
      sim_time: 1.7
      linear_granularity: 0.05
      angular_granularity: 0.025
      transform_tolerance: 0.2
      xy_goal_tolerance: 0.25
      trans_stopped_velocity: 0.25
      short_circuit_trajectory_evaluation: True
      stateful: True
      critics: ["RotateToGoal", "Oscillation", "BaseObstacle", "GoalAlign", "PathAlign", "PathDist", "GoalDist"]
      BaseObstacle.scale: 0.02
      PathAlign.scale: 32.0
      PathAlign.forward_point_distance: 0.1
      GoalAlign.scale: 24.0
      GoalAlign.forward_point_distance: 0.1
      PathDist.scale: 32.0
      GoalDist.scale: 24.0
      RotateToGoal.scale: 32.0
      RotateToGoal.slowing_factor: 5.0
      RotateToGoal.lookahead_time: -1.0

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      use_sim_time: True
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      robot_radius: 0.22
      plugins: ["voxel_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: True
        publish_voxel_map: True
        origin_z: 0.0
        z_resolution: 0.05
        z_voxels: 16
        max_obstacle_height: 2.0
        mark_threshold: 0
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      static_layer:
        map_subscribe_transient_local: True
      always_send_full_costmap: True
        
global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      use_sim_time: True
      robot_radius: 0.22
      resolution: 0.05
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: True
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          obstacle_max_range: 2.5
          obstacle_min_range: 0.0
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_subscribe_transient_local: True
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
      always_send_full_costmap: True

map_server:
  ros__parameters:
    use_sim_time: True
    yaml_filename: ""

map_saver:
  ros__parameters:
    use_sim_time: True
    save_map_timeout: 5.0
    free_thresh_default: 0.25
    occupied_thresh_default: 0.65
    map_subscribe_transient_local: True

planner_server:
  ros__parameters:
    expected_planner_frequency: 20.0
    use_sim_time: True
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_navfn_planner/NavfnPlanner"
      tolerance: 0.5
      use_astar: false
      allow_unknown: true

smoother_server:
  ros__parameters:
    use_sim_time: True
    smoother_plugins: ["simple_smoother"]
    simple_smoother:
      plugin: "nav2_smoother::SimpleSmoother"
      tolerance: 1.0e-10
      max_its: 1000
      do_refinement: True

behavior_server:
  ros__parameters:
    costmap_topic: local_costmap/costmap_raw
    footprint_topic: local_costmap/published_footprint
    cycle_frequency: 10.0
    behavior_plugins: ["spin", "backup", "drive_on_heading", "wait"]
    spin:
      plugin: "nav2_behaviors/Spin"
    backup:
      plugin: "nav2_behaviors/BackUp"
    drive_on_heading:
      plugin: "nav2_behaviors/DriveOnHeading"
    wait:
      plugin: "nav2_behaviors/Wait"
    global_frame: odom
    robot_base_frame: base_link
    transform_tolerance: 0.1
    use_sim_time: true
    simulate_ahead_time: 2.0
    max_rotational_vel: 1.0
    min_rotational_vel: 0.4
    rotational_acc_lim: 3.2

robot_state_publisher:
  ros__parameters:
    use_sim_time: True

waypoint_follower:
  ros__parameters:
    loop_rate: 20
    stop_on_failure: false
    waypoint_task_executor_plugin: "wait_at_waypoint"   
    wait_at_waypoint:
      plugin: "nav2_waypoint_follower::WaitAtWaypoint"
      enabled: True
      waypoint_pause_duration: 200
"""
    
    def _generate_nav_launch(self, robot_name: str) -> str:
        """Generate basic navigation launch file."""
        return f'''"""Launch navigation for {robot_name}."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description for navigation."""
    
    # Get the launch directory
    nav_package_dir = get_package_share_directory('{robot_name}_navigation')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # Create the launch configuration variables
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    use_composition = LaunchConfiguration('use_composition')
    use_respawn = LaunchConfiguration('use_respawn')
    
    # Declare the launch arguments
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Top-level namespace')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true')

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart', 
        default_value='true',
        description='Automatically startup the nav2 stack')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(nav_package_dir, 'config', 'nav2_params.yaml'),
        description='Full path to the ROS2 parameters file to use')

    declare_use_composition_cmd = DeclareLaunchArgument(
        'use_composition', 
        default_value='False',
        description='Whether to use composed bringup')

    declare_use_respawn_cmd = DeclareLaunchArgument(
        'use_respawn', 
        default_value='False',
        description='Whether to respawn if a node crashes')

    # Specify the actions
    bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={{'namespace': namespace,
                          'use_sim_time': use_sim_time,
                          'autostart': autostart,
                          'params_file': params_file,
                          'use_composition': use_composition,
                          'use_respawn': use_respawn}}.items())

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_use_composition_cmd)
    ld.add_action(declare_use_respawn_cmd)

    # Add the actions to launch all of the navigation nodes
    ld.add_action(bringup_cmd)

    return ld
'''
