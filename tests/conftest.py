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


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow integration tests that require network access"
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow (requires --run-slow to run)")


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --run-slow is passed."""
    if config.getoption("--run-slow"):
        # --run-slow given in cli: do not skip slow tests
        return

    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


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



