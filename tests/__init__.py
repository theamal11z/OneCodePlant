"""Test suite for OneCode Plant CLI."""

# Test configuration
import os
import sys
from pathlib import Path

# Add source directory to path for testing
test_dir = Path(__file__).parent
src_dir = test_dir.parent
sys.path.insert(0, str(src_dir))

# Set test environment variables
os.environ['ONECODE_ENV'] = 'test'
os.environ['ONECODE_LOG_LEVEL'] = 'DEBUG'
