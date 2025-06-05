# Plugin Development Guide

This guide covers how to develop custom plugins for OneCode Plant CLI to extend its functionality with your own tools and workflows.

## Table of Contents

1. [Plugin Architecture](#plugin-architecture)
2. [Getting Started](#getting-started)
3. [Plugin Base Class](#plugin-base-class)
4. [Development Workflow](#development-workflow)
5. [Advanced Features](#advanced-features)
6. [Testing Plugins](#testing-plugins)
7. [Distribution](#distribution)
8. [Examples](#examples)

## Plugin Architecture

OneCode Plant uses a plugin-based architecture that allows extending the CLI with custom functionality. Plugins are Python modules that inherit from the `PluginBase` class and implement specific interfaces.

### Plugin Types

1. **Tool Wrappers**: Integrate external command-line tools
2. **Workflow Plugins**: Implement complex multi-step operations
3. **Integration Plugins**: Connect with external services or APIs
4. **Custom Commands**: Add domain-specific commands

### Plugin Discovery

Plugins are discovered through:

1. **Built-in plugins**: Located in `onecode/plugins/`
2. **User plugins**: Located in `~/.onecode/plugins/`
3. **Environment paths**: Specified in `ONECODE_PLUGIN_PATH`
4. **Installed packages**: Using entry points

## Getting Started

### Prerequisites

- Python 3.8+
- OneCode Plant CLI installed
- Basic understanding of Python classes and modules

### Creating Your First Plugin

1. **Create the plugin file**:
   ```bash
   mkdir -p ~/.onecode/plugins
   touch ~/.onecode/plugins/my_tool_plugin.py
   