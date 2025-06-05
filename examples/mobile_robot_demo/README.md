# Mobile Robot Demo

This example demonstrates how to use OneCode Plant CLI to set up and manage a complete mobile robot development workflow.

## Overview

This demo shows how to:
- Create a mobile robot workspace
- Set up robot description packages
- Configure navigation with Nav2
- Build and test the complete system
- Run simulation with Gazebo

## Prerequisites

- ROS2 (Humble or later)
- OneCode Plant CLI installed
- Colcon build system
- Nav2 navigation stack
- Gazebo simulation (optional)

## Quick Start

### 1. Create Workspace

```bash
# Create a new mobile robot workspace
onecode create mobile_robot_workspace
cd mobile_robot_workspace
