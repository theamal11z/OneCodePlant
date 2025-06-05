"""Main CLI entry point for OneCode Plant."""

import sys
import os
import click
from typing import List, Optional

from onecode.core.ros2_interface import ROS2Interface
from onecode.core.plugin_manager import PluginManager
from onecode.core.config import ConfigManager
from onecode.core.utils import setup_logging, get_logger


class OneCodeCLI:
    """Main OneCode CLI class that handles command routing and execution."""
    
    def __init__(self):
        """Initialize the OneCode CLI with all necessary components."""
        self.config_manager = ConfigManager()
        self.logger = get_logger(__name__)
        self.ros2_interface = ROS2Interface()
        self.plugin_manager = PluginManager()
        
        # Load plugins
        self.plugin_manager.load_plugins()
        
    def execute_ros2_passthrough(self, args: List[str]) -> int:
        """Execute ROS2 commands via passthrough mode."""
        self.logger.debug(f"Executing ROS2 passthrough: {' '.join(args)}")
        result = self.ros2_interface.run_command(args)
        return result.returncode if hasattr(result, 'returncode') else 0
    
    def execute_onecode_command(self, ctx, **kwargs) -> int:
        """Execute OneCode-specific commands via plugin system."""
        # This will be called by Click commands
        return 0


# Initialize CLI instance
cli_instance = OneCodeCLI()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.pass_context
def cli(ctx, verbose, debug, config):
    """OneCode Plant - Intelligent ROS2 development tooling."""
    # Setup logging based on flags
    log_level = 'DEBUG' if debug else ('INFO' if verbose else 'WARNING')
    setup_logging(log_level)
    
    # Load custom config if provided
    if config:
        cli_instance.config_manager.load_config(config)
    
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['cli_instance'] = cli_instance


@cli.group()
@click.pass_context
def build(ctx):
    """Build commands for ROS2 packages."""
    pass


@build.command()
@click.option('--debug', is_flag=True, help='Build in debug mode')
@click.option('--packages', multiple=True, help='Specific packages to build')
@click.option('--parallel-jobs', '-j', type=int, help='Number of parallel jobs')
@click.option('--symlink-install', is_flag=True, default=True, help='Use symlink install')
@click.option('--continue-on-error', is_flag=True, help='Continue building other packages on error')
@click.pass_context
def workspace(ctx, debug, packages, parallel_jobs, symlink_install, continue_on_error):
    """Build the entire workspace or specific packages."""
    cli_instance = ctx.obj['cli_instance']
    
    # Get the colcon plugin
    colcon_plugin = cli_instance.plugin_manager.get_plugin('colcon')
    if not colcon_plugin:
        click.echo("Error: Colcon plugin not available", err=True)
        return 1
    
    # Execute build
    return colcon_plugin.build_workspace(
        debug=debug,
        packages=list(packages) if packages else None,
        parallel_jobs=parallel_jobs,
        symlink_install=symlink_install,
        continue_on_error=continue_on_error
    )


@cli.group()
@click.pass_context
def sim(ctx):
    """Simulation commands."""
    pass


@sim.command()
@click.option('--world', help='World file to load')
@click.option('--robot', help='Robot model to spawn')
@click.option('--headless', is_flag=True, help='Run simulation in headless mode')
@click.pass_context
def start(ctx, world, robot, headless):
    """Start a simulation environment."""
    cli_instance = ctx.obj['cli_instance']
    
    sim_plugin = cli_instance.plugin_manager.get_plugin('simulation')
    if not sim_plugin:
        click.echo("Error: Simulation plugin not available", err=True)
        return 1
    
    return sim_plugin.start_simulation(
        world=world,
        robot=robot,
        headless=headless
    )


@cli.command(name='version')
@click.pass_context
def show_version(ctx):
    """Show OneCode Plant version information."""
    from onecode import __version__
    click.echo(f"OneCode Plant CLI v{__version__}")
    
    # Also show ROS2 version if available
    cli_instance = ctx.obj['cli_instance']
    ros2_version = cli_instance.ros2_interface.get_version()
    if ros2_version:
        click.echo(f"ROS2 Version: {ros2_version}")


@cli.command()
@click.pass_context
def plugins(ctx):
    """List available plugins and their status."""
    cli_instance = ctx.obj['cli_instance']
    
    click.echo("Available Plugins:")
    click.echo("-" * 40)
    
    for plugin_name, plugin in cli_instance.plugin_manager.plugins.items():
        status = "✓ Loaded" if plugin.is_available() else "✗ Unavailable"
        click.echo(f"{plugin_name:20} {status}")
        if hasattr(plugin, 'get_info'):
            info = plugin.get_info()
            if info:
                click.echo(f"{'':20} {info}")


def main():
    """Main entry point for the CLI."""
    # Check if this is a ROS2 passthrough command
    if len(sys.argv) > 1 and sys.argv[1] == 'ros2':
        # Remove the 'onecode' from argv and execute ROS2 command
        ros2_args = sys.argv[2:]  # Skip 'onecode' and 'ros2'
        ros2_args.insert(0, 'ros2')  # Add back 'ros2' as the command
        
        cli_instance = OneCodeCLI()
        exit_code = cli_instance.execute_ros2_passthrough(ros2_args)
        sys.exit(exit_code)
    
    # Otherwise, execute OneCode commands
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        setup_logging('DEBUG')  # Enable debug for error reporting
        logger = get_logger(__name__)
        logger.exception("Unexpected error occurred")
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
