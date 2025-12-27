"""
Pytest configuration and fixtures for The Researcher's Cockpit tests.
"""

import pytest
import sys
from pathlib import Path
import shutil
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture
def temp_strategy_dir(project_root_path):
    """Create a temporary strategy directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix='test_strategy_')
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_strategy_name():
    """Return a test strategy name."""
    return 'test_strategy'


@pytest.fixture
def test_asset_class():
    """Return a test asset class."""
    return 'equities'


@pytest.fixture
def cleanup_test_strategy(project_root_path, test_strategy_name, test_asset_class):
    """Cleanup test strategy after test."""
    yield
    # Cleanup
    strategy_path = project_root_path / 'strategies' / test_asset_class / test_strategy_name
    results_path = project_root_path / 'results' / test_strategy_name
    
    if strategy_path.exists():
        shutil.rmtree(strategy_path, ignore_errors=True)
    
    if results_path.exists():
        shutil.rmtree(results_path, ignore_errors=True)



