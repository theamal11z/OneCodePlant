# OneCode Plant CLI Implementation Guide and Project File Structure Plan

This document provides a comprehensive guide to implementing and developing the OneCode Plant CLI, focusing on integrating tools, creating a fully personalized file structure for an open source project, and outlining a development roadmap.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Objectives](#objectives)
3. [Architecture Overview](#architecture-overview)

   * 3.1. Two-Tier Command Structure
   * 3.2. Plugin System and Wrappers
4. [Project File Structure Design](#project-file-structure-design)

   * 4.1. Directory Layout
   * 4.2. Rationale Behind Structure
5. [CLI Development Best Practices](#cli-development-best-practices)

   * 5.1. Subcommand Organization
   * 5.2. Consistency and Naming Conventions
   * 5.3. Documentation and Help Text
   * 5.4. Error Handling and Exit Codes
6. [Tool Integration Strategy](#tool-integration-strategy)

   * 6.1. Wrapping Existing ROS2CLI Commands
   * 6.2. Integrating Colcon Build System
   * 6.3. Simulation and Nav2 Integration
   * 6.4. MoveIt2, LeRobot, and SymForce Wrappers
   * 6.5. Cloud Deployment (FogROS2) and Multi-Robot (ChoirBot) Support
7. [Implementation Plan](#implementation-plan)

   * 7.1. Technology Stack and Language Choice
   * 7.2. Project Setup and Bootstrapping
   * 7.3. Milestone Breakdown
   * 7.4. Testing Strategy
   * 7.5. CI/CD and Packaging
8. [Development Roadmap](#development-roadmap)

   * 8.1. Phase 1: Foundation and Ros2 Pass-Through
   * 8.2. Phase 2: Tool Wrappers and Enhanced Commands
   * 8.3. Phase 3: Workflow Engine and Orchestration
   * 8.4. Phase 4: Natural Language Interface and AI Extensions
9. [Conclusion](#conclusion)

---

## 1. Introduction

OneCode Plant aims to extend the existing ROS2CLI ecosystem by providing intelligent tooling and unified workflows. This document outlines how to implement a fully featured OneCode CLI, design a maintainable file structure for the project, and integrate various tools to support complex robotic development tasks. The guide is written as a reference plan for developers embarking on building the OneCode Plant open source project.

## 2. Objectives

* Create a clear, maintainable, and scalable project structure that reflects open source best practices.
* Implement a CLI that preserves all original `ros2` commands while adding OneCode-specific extensions.
* Integrate key robotics tools (e.g., Colcon, Gazebo, Nav2, MoveIt2, LeRobot, SymForce, FogROS2, ChoirBot) via wrapper modules.
* Provide a phased development plan with milestones, testing, and CI/CD strategies.
* Ensure consistency, documentation, and ease of use for end users.

## 3. Architecture Overview

### 3.1. Two-Tier Command Structure

OneCode Plant leverages a two-tier command model:

* **Tier 1: Passthrough Mode** – All existing `ros2` commands are executed unchanged. This guarantees backward compatibility and allows users to continue using familiar workflows (`ros2 pkg create`, `ros2 node list`, etc.) without modifications.
* **Tier 2: OneCode Extensions** – Custom commands prefixed with `onecode` (e.g., `onecode build`, `onecode sim start`) that orchestrate sequences of underlying ROS2CLI calls, providing intelligent defaults, enhanced error handling, and workflow automation.

*All Tier 2 subcommands should be organized under a modular plugin system, allowing incremental addition of new capabilities without impacting core pass-through functionality.*

### 3.2. Plugin System and Wrappers

The OneCode Plant CLI should be built around a plugin architecture where each integration (e.g., Colcon, Simulation) is encapsulated in its own module. The primary responsibilities of a wrapper class are:

1. Invoke underlying ROS2CLI functionality (via direct Python bindings or shell calls).
2. Apply intelligent defaults (e.g., default `cmake-args` for builds).
3. Provide error monitoring, logging, and user-friendly output.
4. Offer extensible APIs for contributions (open source collaborators can add new wrappers).

Example (Python pseudocode):

```python
class OneCodeCLI:
    def __init__(self):
        self.ros2_cli = ROS2CLIInterface()  # Binds into ROS2CLI core
        self.plugins = self._load_plugins()

    def execute(self, args):
        if args[0] == 'ros2':
            return self.ros2_cli.run(args)
        else:
            return self._dispatch_onecode(args)
```

Plugins register commands and their handlers via a central registry, allowing dynamic discovery.

## 4. Project File Structure Design

Designing a well-organized file structure is critical for maintainability, discoverability, and community contributions. Below is a recommended directory layout.

```
onecode-plant/                           # Root of the repository
│
├── README.md                            # Project overview, installation, quickstart
├── LICENSE                              # Open source license (e.g., Apache 2.0)
├── setup.py / pyproject.toml            # Packaging metadata (if Python-based)
├── onecode/                             # Main source code directory
│   ├── __init__.py                      # Package initializer
│   ├── cli.py                           # Entry point for `onecode` command
│   ├── core/                            # Core abstractions and utilities
│   │   ├── __init__.py
│   │   ├── ros2_interface.py            # Abstraction layer over ROS2CLI
│   │   ├── plugin_manager.py            # Plugin discovery and registry
│   │   └── utils.py                     # Logging, config parsing, common utils
│   ├── plugins/                         # All OneCode plugins live here
│   │   ├── __init__.py
│   │   ├── colcon_plugin.py             # Build system wrapper
│   │   ├── sim_plugin.py                # Simulation integrations (Gazebo, Isaac, Webots)
│   │   ├── nav2_plugin.py               # Navigation2 integration
│   │   ├── moveit_plugin.py             # MoveIt2 integration
│   │   ├── lerobot_plugin.py            # LeRobot integration
│   │   ├── symforce_plugin.py           # SymForce integration
│   │   ├── fogros2_plugin.py            # FogROS2 (cloud-edge) integration
│   │   └── choirbot_plugin.py           # ChoirBot multi-robot support
│   └── workflows/                       # Pre-defined intelligent workflows
│       ├── __init__.py
│       ├── mobile_robot_setup.py        # Example: full mobile robot dev workflow
│       ├── learning_based_manipulation.py
│       └── multi_robot_coordination.py
├── docs/                                # Documentation (Sphinx, MkDocs, etc.)
│   ├── index.md
│   ├── architecture.md
│   ├── usage.md
│   ├── contribution_guidelines.md
│   └── plugin_development.md
├── tests/                               # Automated tests
│   ├── __init__.py
│   ├── test_cli_core.py
│   ├── test_colcon_plugin.py
│   ├── test_sim_plugin.py
│   └── ...
├── examples/                            # Example projects showcasing OneCode features
│   ├── mobile_robot_demo/
│   ├── nav2_demo/
│   └── multi_robot_demo/
├── scripts/                             # Utility scripts (e.g., code formatters, release scripts)
│   ├── format_code.sh
│   └── release.sh
├── .github/                             # GitHub workflows, issue templates, pull request templates
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── cd.yml
│   └── ISSUE_TEMPLATE.md
└── configs/                             # Default configuration files
    ├── default_config.yaml              # OneCode global defaults
    └── plugin_config.yaml               # Plugin-specific settings
```

### 4.2. Rationale Behind Structure

* **Modularity**: Plugins are isolated, enabling independent development and testing (`onecode/plugins/`).
* **Separation of Concerns**: Core utilities (`onecode/core/`) handle common logic (logging, config parsing, ROS2CLI binding).
* **Discoverability**: `docs/` and `examples/` guide new users through installation, usage, and customization.
* **Testing**: `tests/` ensures each plugin and core component is validated via unit and integration tests.
* **Community-Friendly**: `.github/` folder for CI/CD, contributing guidelines, and issue templates promotes open source collaboration.
* **Configurability**: `configs/` holds default settings, allowing override through environment variables or user-provided config files.

## 5. CLI Development Best Practices

This section covers general best practices when building a CLI, regardless of underlying domain (robots, analytics, etc.).

### 5.1. Subcommand Organization

* Group related functionality under a single top-level command (e.g., `onecode build`, `onecode sim`).
* Ensure global flags (e.g., `--verbose`, `--config`) apply across all subcommands for consistency ([clig.dev](https://clig.dev/?utm_source=chatgpt.com), [dev.to](https://dev.to/wesen/14-great-tips-to-make-amazing-cli-applications-3gp3?utm_source=chatgpt.com)).
* Document each subcommand clearly in help text and man pages (or markdown docs in `docs/`).

### 5.2. Consistency and Naming Conventions

* Use descriptive names for commands and flags; avoid single-letter flags that conflict (e.g., do not use `-f` for both `--force` and `--file`) ([reddit.com](https://www.reddit.com/r/programming/comments/k8jal6/a_guide_to_help_you_write_better_cli/?utm_source=chatgpt.com)).
* Follow a consistent pattern for naming flags across plugins: e.g., `--robot-type`, `--world-file`, `--map-file`.
* Use lowercase, hyphen-separated names for commands (`onecode sim start` vs. `onecode simStart`).

### 5.3. Documentation and Help Text

* Include usage examples in help text, dynamically generated if possible. Consider subcommands auto-listing their own examples.
* Provide a man page or markdown documentation for offline usage. Generate man pages from docstrings or markdown via tools like `pandoc` or `cli-doc` generators ([news.ycombinator.com](https://news.ycombinator.com/item?id=25304257&utm_source=chatgpt.com)).
* Maintain a `docs/` directory with up-to-date guides, plugin development instructions, and API reference.

### 5.4. Error Handling and Exit Codes

* Exit with meaningful codes (`0` for success, non-zero for failures). Map specific error types to distinct codes for scripting (`1` for general error, `2` for config error, etc.).
* Provide user-friendly error messages with actionable hints (e.g., "Missing dependency: install `colcon-common-extensions`").
* Log detailed stack traces optionally to a log file when `--debug` is enabled, while keeping console output concise by default.

## 6. Tool Integration Strategy

OneCode Plant’s core value lies in integrating and wrapping existing robotics tools within intelligent workflows. Below is a strategy for each major integration.

### 6.1. Wrapping Existing ROS2CLI Commands

* **Objective**: Provide seamless pass-through for all `ros2` commands while enabling interception for extended functionality.
* **Implementation**:

  1. Bind into the ROS2CLI Python API (if available), or invoke shell commands and capture stdout/stderr.
  2. In `core/ros2_interface.py`, implement methods such as `run_ros2_command(cmd_list: List[str]) -> ProcessResult` that handle subprocess execution, logging, and error parsing.
  3. In `cli.py`, route any invocation starting with `ros2` directly to `run_ros2_command` without alteration.

### 6.2. Integrating Colcon Build System

* **Plugin**: `colcon_plugin.py`

* **Responsibilities**:

  * Introduce `onecode build` with flags: `--debug`, `--watch`, `--only-changed`, `--parallel-jobs`.
  * Use intelligent defaults: `colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release` when `--debug` is not set; `Debug` otherwise.
  * Wrap `colcon` invocation, parse output, and provide a summarized build status (`Succeeded`, `Failed Packages`, etc.).

* **Example Implementation Snippet**:

  ```python
  class ColconPlugin:
      def run_build(self, args):
          cmd = ['colcon', 'build', '--symlink-install']
          if args.debug:
              cmd += ['--cmake-args', '-DCMAKE_BUILD_TYPE=Debug']
          else:
              cmd += ['--cmake-args', '-DCMAKE_BUILD_TYPE=Release']
          if args.packages:
              cmd += ['--packages-select'] + args.packages
          if args.watch:
              cmd += ['--watch']  # Requires colcon-watch extension
          result = self.ros2_interface.run_cmd(cmd)
          return self._summarize_output(result)
  ```

* **References**: Implementation follows patterns described in OneCode architecture citeturn0file0.

### 6.3. Simulation and Nav2 Integration

* **Simulation Plugin** (`sim_plugin.py`):

  * Supports multiple simulators (Gazebo, Isaac, Webots).
  * Unified command: `onecode sim start --simulator gazebo --world warehouse.sdf --robot turtlebot3`.
  * Internally: Invoke `ros2 launch gazebo_ros gazebo.launch.py` with additional calls to spawn robot models, configure topics, and optionally launch `rviz2` with a default configuration.

* **Nav2 Plugin** (`nav2_plugin.py`):

  * Provides `onecode nav setup --robot-type turtlebot3 --map-file warehouse.yaml`.
  * Internally: Generates a parameter file via helper functions (`_get_optimal_params(robot_type)`), then runs `ros2 launch nav2_bringup bringup_launch.py map:={map_file} params_file:={param_file}`.
  * Also supports `onecode nav tune --environment indoor --robot-type differential` to adjust parameters dynamically using `ros2 param set`.

### 6.4. MoveIt2, LeRobot, and SymForce Wrappers

* **MoveIt2 Plugin** (`moveit_plugin.py`):

  * Commands: `onecode motion setup --robot ur5 --gripper robotiq_2f85`, `onecode motion plan --goal "pick red block from table"`.
  * Internally: Use `ros2 launch moveit_bringup demo.launch.py` or generate URDF/SRDF configs programmatically, then wrap `ros2 action send_goal /execute_trajectory` when planning.

* **LeRobot Plugin** (`lerobot_plugin.py`):

  * Set up learning environments: `onecode learn setup --task manipulation --robot ur5`.
  * Uses `ros2 topic echo` and `ros2 bag record` to record training data.
  * Commands: `onecode learn collect --episodes 100` invokes `ros2 bag record -o training_data.db3 /joint_states /cmd_vel` etc.

* **SymForce Plugin** (`symforce_plugin.py`):

  * Commands: `onecode optimize slam --target embedded --package my_slam_pkg`.
  * Internally: Call SymForce Python API to generate optimized C++ code, integrate into the package’s `CMakeLists.txt`, then invoke `colcon build --packages-select my_slam_pkg`.

### 6.5. Cloud Deployment (FogROS2) and Multi-Robot (ChoirBot) Support

* **FogROS2 Plugin** (`fogros2_plugin.py`):

  * Commands: `onecode deploy hybrid --edge-nodes control,safety --cloud-nodes perception,mapping`.
  * Integrates FogROS2 library and orchestrates launching distributed nodes: edge nodes on local machine (or Kubernetes cluster), cloud nodes via remote launch interfaces (e.g., SSH or cloud orchestration tool).

* **ChoirBot Plugin** (`choirbot_plugin.py`):

  * Commands: `onecode swarm init --robots 5 --formation grid`, `onecode swarm monitor`.
  * Internally: Use ROS2’s namespacing, remappings, and `ros2 launch` for each robot instance. Leverage ChoirBot APIs to coordinate trajectories and communication metrics.

## 7. Implementation Plan

### 7.1. Technology Stack and Language Choice

* **Language**: Python 3.10+ (widely adopted by ROS2 and available on most platforms). Use `argparse` or `click` (see [Simon Willison’s guidelines on Python CLI tools]([simonwillison.net]%28https://simonwillison.net/2023/Sep/30/cli-tools-python/?utm_source=chatgpt.com%29)). `click` is recommended for its decorator-based command definitions and automatic help text generation.
* **Build System**: Rely on `colcon` for building ROS2-related components when needed. For the OneCode CLI itself, use `setuptools` or `poetry` for packaging and dependency management.
* **Testing**: Use `pytest` for unit and integration tests. Mock ROS2CLI calls for offline testing.
* **CI/CD**: GitHub Actions (`.github/workflows/ci.yml`) to automate linting (e.g., `flake8`), type checking (`mypy`), and testing. A separate workflow (`cd.yml`) for automatic releases (tag push triggers build and upload to PyPI).

### 7.2. Project Setup and Bootstrapping

1. **Bootstrap Repository**:

   * Initialize Git repository, add `.gitignore`, set up license (Apache 2.0 or MIT).
   * Create virtual environment and install development dependencies: `click`, `pytest`, `flake8`, `mypy`, `ros2cli` bindings.
   * Set up `setup.py` or `pyproject.toml` with entry point:

     ```ini
     [tool.poetry.scripts]
     onecode = "onecode.cli:main"
     ```
2. **Directory Skeleton**: Create all directories as outlined in Section 4.
3. **Core CLI Entry Point**:

   * Implement `onecode/cli.py` using `click`: define a `@click.group()` with a passthrough for unknown commands that begin with `ros2`.
   * Example:

     ```python
     import click
     from onecode.core.ros2_interface import Ros2Interface

     @click.group(invoke_without_command=True)
     @click.pass_context
     def main(ctx, *args):
         if ctx.invoked_subcommand is None:
             # If first argument is 'ros2', delegate
             # else show help
             click.echo(ctx.get_help())
     ```
4. **Plugin Manager**: Implement `onecode/core/plugin_manager.py` to discover plugins in `onecode/plugins/` and register their commands.

### 7.3. Milestone Breakdown

* **Milestone 1: Core Pass-Through and CLI Framework** (2 weeks)

  * Set up `click` group and passthrough logic for `ros2` commands.
  * Implement `Ros2Interface` to execute shell commands and capture output.
  * Write unit tests for pass-through functionality.

* **Milestone 2: Colcon and Simulation Plugins** (3 weeks)

  * Develop `colcon_plugin.py` with commands: `onecode build [--debug] [--watch] [--only-changed] [--parallel-jobs]`.
  * Develop `sim_plugin.py` supporting `gazebo`, `isaac`, `webots` with common flags.
  * Test integration against a sample ROS2 workspace.

* **Milestone 3: Navigation and MoveIt Plugins** (3 weeks)

  * Implement `nav2_plugin.py` with `onecode nav setup` and `onecode nav tune`.
  * Implement `moveit_plugin.py` with `onecode motion setup` and `onecode motion plan`.
  * Create example scenarios in `examples/nav2_demo/` and `examples/multi_robot_demo/`, verify functionality.

* **Milestone 4: Advanced Wrappers (LeRobot, SymForce, FogROS2, ChoirBot)** (4 weeks)

  * Implement each plugin based on available APIs, stub out missing interfaces with TODOs.
  * Validate wrappers with unit tests (mocking ROS2CLI) and integration tests if possible.

* **Milestone 5: Workflow Engine and Orchestration** (3 weeks)

  * Create predefined workflows in `onecode/workflows/`, allowing chaining of commands (e.g., full mobile robot setup).
  * Implement a lightweight workflow engine to parse YAML-defined workflows (in `configs/`) and execute sequences.
  * Document how to add new workflows.

* **Milestone 6: Documentation, Examples, and Release Prep** (2 weeks)

  * Finalize `docs/` (architecture, usage, plugin development guides).
  * Write comprehensive examples and tutorials.
  * Configure GitHub Actions for CI/CD and release automation.
  * Publish version 0.1.0 to PyPI and announce on community channels.

### 7.4. Testing Strategy

* **Unit Tests**: Mock `Ros2Interface` to simulate subprocess calls, verify command generation and error handling.
* **Integration Tests**: Use a minimal ROS2 workspace (e.g., `tests/fixtures/sample_ws/`) to run `onecode build`, `onecode sim start` in a Docker container with ROS2 installed. Validate expected file output (e.g., build artifacts, PID of simulation process).
* **End-to-End Tests**: Automated scripts in `examples/` that spin up simulated environments and verify key nodes are running via `ros2 node list`.
* **Code Coverage**: Enforce 80% coverage threshold using `pytest-cov`.

### 7.5. CI/CD and Packaging

* **CI Workflow (`.github/workflows/ci.yml`)**:

  * Lint Python code (`flake8`, `black` formatting check).
  * Run `mypy` for static type checking.
  * Execute `pytest` suite (unit and integration tests).
  * Build sdist and wheel, verify installation in a clean virtual environment.

* **CD Workflow (`.github/workflows/cd.yml`)**:

  * Trigger on new tag push (e.g., `v0.*`).
  * Publish to PyPI (using GitHub Secrets for API token).
  * Create GitHub Release with changelog extracted from commit messages.

* **Packaging**:

  * Use `pyproject.toml` for metadata, dependencies pinned to minimum supported versions.
  * Set entry point in `setup.py`:

    ```python
    entry_points={
        'console_scripts': ['onecode=onecode.cli:main']
    }
    ```

## 8. Development Roadmap

Below is a high-level roadmap divided into four phases.

### 8.1. Phase 1: Foundation and Ros2 Pass-Through (Weeks 1–2)

* **Tasks**:

  1. Initialize repository, virtual environment, and packaging setup.
  2. Implement `click`-based CLI framework, binding `onecode` group to passthrough logic.
  3. Develop `Ros2Interface` for invoking `ros2` commands (subprocess wrapper).
  4. Write unit tests for pass-through functionality, ensuring no modifications to `ros2` behavior.

* **Outcomes**:

  * Users can run `onecode ros2 <args...>` and receive identical output to `ros2 <args...>`.
  * Clear foundation for adding new commands.

### 8.2. Phase 2: Tool Wrappers and Enhanced Commands (Weeks 3–8)

* **Colcon Plugin**:

  * Design CLI flags, argument parsing, and intelligent defaults (build type selection, package filtering).
  * Summarize build results, highlight errors.

* **Simulation Plugin**:

  * Support `gazebo`, `isaac`, `webots`. Create abstraction to unify configuration (world file, robot model spawn).
  * Provide optional `--launch-rviz` flag to automatically open RViz with recommended settings.

* **Nav2 Plugin**:

  * Create helper to generate or locate best parameter files for selected robot type.
  * Implement commands for parameter tuning based on environment (indoor, outdoor, differential, omnidirectional configurations).

* **MoveIt Plugin**:

  * Automate URDF/SRDF generation for standard manipulators (UR5, Baxter).
  * Wrap `ros2 action send_goal` to allow high-level motion planning via natural language (stub for Phase 4).

* **Testing and Documentation**:

  * Write unit tests with mocks, integration tests in a minimal ROS2 environment.
  * Document each plugin in `docs/plugin_development.md`.

### 8.3. Phase 3: Workflow Engine and Orchestration (Weeks 9–12)

* **Workflow Engine**:

  * Parse YAML workflow definitions in `configs/` (e.g., `mobile_robot_dev` with sequential steps).
  * Provide CLI command: `onecode workflow run <workflow_name> [--vars key=val,...]`.
  * Implement concurrency control (e.g., optional `--parallel` for independent steps).

* **Predefined Workflows**:

  * Mobile Robot Setup: Create package, build workspace, launch Nav2, start Gazebo simulation, open RViz.
  * Learning-Based Manipulation: Launch MoveIt2, configure LeRobot environment, record data.
  * Multi-Robot Coordination: Initialize swarm nodes, launch ChoirBot coordinator, monitor topics.

* **Testing**:

  * Create end-to-end tests to validate workflows complete successfully in a headless (Docker) environment.

* **Documentation**:

  * Update `docs/workflows.md` with usage examples, tips for defining custom workflows.

### 8.4. Phase 4: Natural Language Interface and AI Extensions (Weeks 13–16)

* **Objective**: Provide an optional layer where users can issue commands in natural language (e.g., `onecode do complete mobile robot setup for warehouse scenario`), interpreted via a simple NLP pipeline.

* **Implementation Steps**:

  1. Evaluate lightweight NLP libraries (e.g., spaCy, NLTK) for intent parsing.
  2. Define grammar rules mapping intents to existing CLI commands (e.g., "build my workspace" → `onecode build`).
  3. Create `onecode ai` subcommand to accept free-form text, parse intents, and dispatch to appropriate plugin.
  4. Provide fallback: if unable to parse, show help or ask clarifying questions.

* **AI Extensions (Optional)**:

  * Integrate with cloud-based LLM APIs (e.g., OpenAI) to generate configuration snippets (e.g., parameter tuning suggestions).
  * Allow dynamic generation of sample launch files based on user-provided requirements.

* **Testing**:

  * Unit tests for NLP parsing functions.
  * Manual QA to ensure reasonable intent mapping.

## 9. Conclusion

This guide and plan provide a detailed roadmap to implement the OneCode Plant CLI, from setting up a solid project structure to integrating a wide variety of robotics tools, and culminating in advanced workflow orchestration and AI-driven features. By following the milestones and best practices outlined above, developers can ensure a maintainable, community-friendly, and powerful CLI that extends the ROS2 ecosystem without replacing existing functionality.

---

*References:*

* OneCode Plant architecture (user-provided PDF) citeturn0file0
* CLI structure and best practices: Pon.Tech.Talk on structuring a CLI (Go-focused, but applicable) ([medium.com](https://medium.com/pon-tech-talk/structuring-a-cli-22e2492717de?utm_source=chatgpt.com))
* CLI Guidelines (clig.dev) on subcommands and consistency ([clig.dev](https://clig.dev/?utm_source=chatgpt.com))
* User experience in CLI design: "Things I've learned about building CLI tools in Python" ([simonwillison.net](https://simonwillison.net/2023/Sep/30/cli-tools-python/?utm_source=chatgpt.com))
* Generating man pages from markdown: CLI documentation practices ([news.ycombinator.com](https://news.ycombinator.com/item?id=25304257&utm_source=chatgpt.com))
* Project-level code generation best practices (Builder.io) for consistent file structure ([builder.io](https://www.builder.io/c/docs/cli-code-generation-best-practices?utm_source=chatgpt.com))

