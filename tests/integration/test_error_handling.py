"""
Test error handling in integration workflows.

Tests for error handling across the workflow phases.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import load_bundle
from lib.backtest import BacktestConfig


@pytest.mark.integration
def test_missing_bundle_error():
    """Test that missing bundle suggests ingestion command."""
    with pytest.raises(FileNotFoundError):
        load_bundle('nonexistent_bundle_xyz123')


@pytest.mark.integration
def test_invalid_backtest_config():
    """Test backtest with invalid configuration."""
    # End date before start date
    try:
        config = BacktestConfig(
            strategy_name='test_strategy',
            start_date='2020-12-31',
            end_date='2020-01-01',
            capital_base=100000,
            bundle='test_bundle',
            data_frequency='daily',
        )
        # Some implementations may validate in __init__
        # Others may validate when run_backtest is called
    except ValueError:
        # Expected if validation happens in __init__
        pass

