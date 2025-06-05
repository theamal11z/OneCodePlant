"""Setup script for OneCode Plant CLI."""

from setuptools import setup, find_packages
from pathlib import Path
import re

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read the version from __init__.py
def get_version():
    """Extract version from onecode/__init__.py."""
    init_file = this_directory / "onecode" / "__init__.py"
    content = init_file.read_text(encoding='utf-8')
    version_match = re.search(r'__version__ = ["\']([^"\']*)["\']', content)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# Define package requirements
install_requires = [
    "click>=8.0.0",
    "PyYAML>=6.0",
    "setuptools>=45.0.0",
]

# Define development requirements
dev_requires = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "pytest-xdist>=3.0.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=4.0.0",
    "mypy>=0.990",
    "pre-commit>=2.20.0",
]

# Define documentation requirements
docs_requires = [
    "mkdocs>=1.4.0",
    "mkdocs-material>=8.5.0",
    "mkdocs-mermaid2-plugin>=0.6.0",
]

# Define test requirements (for CI environments)
test_requires = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0", 
    "pytest-mock>=3.10.0",
    "pytest-xdist>=3.0.0",
    "pytest-benchmark>=4.0.0",
]

setup(
    name="onecode-plant-cli",
    version=get_version(),
    author="OneCode Plant Team",
    author_email="team@onecode-plant.org",
    description="Intelligent ROS2 development tooling and unified workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/onecode-plant/onecode-plant-cli",
    project_urls={
        "Bug Reports": "https://github.com/onecode-plant/onecode-plant-cli/issues",
        "Source": "https://github.com/onecode-plant/onecode-plant-cli",
        "Documentation": "https://onecode-plant.github.io/onecode-plant-cli/",
        "Changelog": "https://github.com/onecode-plant/onecode-plant-cli/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Software Distribution",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Framework :: Robot Framework",
        "Topic :: Scientific/Engineering :: Robotics",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
        "docs": docs_requires,
        "test": test_requires,
        "all": dev_requires + docs_requires + test_requires,
    },
    entry_points={
        "console_scripts": [
            "onecode=onecode.cli:main",
        ],
        "onecode.plugins": [
            "colcon=onecode.plugins.colcon_plugin:ColconPlugin",
            "simulation=onecode.plugins.sim_plugin:SimulationPlugin",
        ],
    },
    include_package_data=True,
    package_data={
        "onecode": [
            "configs/*.yaml",
            "configs/*.yml",
        ],
    },
    data_files=[
        ("etc/onecode", ["configs/default_config.yaml", "configs/plugin_config.yaml"]),
    ],
    zip_safe=False,
    keywords=[
        "robotics",
        "ros2",
        "cli",
        "automation",
        "development",
        "workflow",
        "build-tools",
        "simulation",
        "navigation",
        "colcon",
        "gazebo",
        "nav2",
    ],
    platforms=["any"],
    license="Apache 2.0",
    maintainer="OneCode Plant Team",
    maintainer_email="team@onecode-plant.org",
)
