"""
pytest configuration for parts unit tests

This module sets up the test environment for running unit tests with pytest.
"""

import sys
import os

# Add the project root to sys.path so 'parts' can be imported
# conftest.py is at tests/unit/conftest.py, so we need to go up 3 levels
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def pytest_configure(config):
    """
    pytest hook called before test collection begins.
    This is where we can set up global test configuration.
    """
    # Ensure the project root is in sys.path for test execution
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
