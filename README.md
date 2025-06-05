# OneCode Plant CLI

**Intelligent ROS2 development tooling and unified workflows**

[![CI](https://github.com/your-org/onecode-plant/workflows/CI/badge.svg)](https://github.com/your-org/onecode-plant/actions)
[![codecov](https://codecov.io/gh/your-org/onecode-plant/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/onecode-plant)
[![PyPI version](https://badge.fury.io/py/onecode-plant-cli.svg)](https://badge.fury.io/py/onecode-plant-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

OneCode Plant CLI extends ROS2CLI with intelligent tooling and unified workflows for robotics development. It provides a two-tier command structure that maintains complete backward compatibility with ROS2 while adding powerful automation and workflow capabilities.

## ✨ Features

- **🔄 ROS2 Passthrough**: All existing `ros2` commands work unchanged
- **🏗️ Intelligent Workflows**: Automated sequences for common robotics tasks  
- **🔌 Plugin Architecture**: Extensible system for tool integration
- **⚡ Enhanced Build System**: Colcon integration with intelligent defaults
- **🎮 Simulation Management**: Unified interface for Gazebo, Isaac Sim, and more
- **🧭 Navigation Support**: Advanced Nav2 integration and configuration
- **🤖 Multi-Robot Coordination**: Built-in support for distributed robotics

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone <repository-url>
cd onecode-plant-cli
pip install -e .
