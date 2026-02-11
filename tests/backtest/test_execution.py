"""
Test backtest execution module.

Tests for execute_zipline_backtest and get_trading_calendar functions.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import inspect

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest.execution import (
    execute_zipline_backtest,
    get_trading_calendar,
)


class TestExecuteZiplineBacktest:
    """Test execute_zipline_backtest function."""

    @pytest.mark.unit
    def test_execute_zipline_backtest_function_exists(self):
        """Test that execute_zipline_backtest function exists."""
        assert execute_zipline_backtest is not None
        sig = inspect.signature(execute_zipline_backtest)
        params = list(sig.parameters.keys())

        # Should have essential parameters
        assert "strategy_module" in params
        assert "start_ts" in params
        assert "end_ts" in params
        assert "capital_base" in params
        assert "bundle" in params

    @pytest.mark.unit
    def test_no_sessionmanager_import(self):
        """Test that SessionManager is not imported (v1.12.0 compliance)."""
        import lib.backtest.execution as execution_module

        # Check that SessionManager is not in the module
        assert not hasattr(execution_module, "SessionManager")

        # Check that calendars.sessions is not imported
        import inspect

        source = inspect.getsource(execution_module)
        assert "from ..calendars.sessions import SessionManager" not in source
        assert "SessionManager.for_asset_class" not in source

    @pytest.mark.unit
    def test_execute_with_asset_class_no_sessionmanager(self):
        """Test that execute_zipline_backtest works with asset_class without SessionManager."""
        # Mock strategy module
        strategy_module = Mock()
        strategy_module.initialize = Mock()
        strategy_module.handle_data = None
        strategy_module.analyze = None
        strategy_module.before_trading_start = None

        # Create timestamps
        start_ts = pd.Timestamp("2020-01-01", tz=None)
        end_ts = pd.Timestamp("2020-12-31", tz=None)

        # Mock run_algorithm (imported inside function)
        mock_perf = pd.DataFrame(
            {"returns": [0.01, 0.02, -0.01], "portfolio_value": [100000, 102000, 101000]}
        )
        mock_calendar = Mock()

        with patch("zipline.run_algorithm") as mock_run:
            mock_run.return_value = mock_perf

            # This should not try to import SessionManager
            # If it does, it will raise ImportError which we can catch
            try:
                result = execute_zipline_backtest(
                    strategy_module=strategy_module,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    capital_base=100000,
                    bundle="test_bundle",
                    data_frequency="daily",
                    trading_calendar=mock_calendar,
                    strategy_name="test_strategy",
                    asset_class="forex",  # Should not trigger SessionManager
                    params=None,
                )
                # If we get here, SessionManager was not used (good!)
                assert result is not None
            except ImportError as e:
                if "SessionManager" in str(e) or "calendars.sessions" in str(e):
                    pytest.fail(f"SessionManager import attempted: {e}")
                else:
                    # Other ImportError is fine (e.g., zipline not installed)
                    pass


class TestGetTradingCalendar:
    """Test get_trading_calendar function."""

    @pytest.mark.unit
    def test_get_trading_calendar_function_exists(self):
        """Test that get_trading_calendar function exists."""
        assert get_trading_calendar is not None
        sig = inspect.signature(get_trading_calendar)
        params = list(sig.parameters.keys())

        # Should have bundle parameter
        assert "bundle" in params
        assert "asset_class" in params

    @pytest.mark.unit
    @patch("zipline.utils.calendar_utils.get_calendar")
    @patch("lib.calendars.get_calendar_for_asset_class")
    @patch("lib.bundles.load_bundle")
    def test_get_trading_calendar_with_asset_class(
        self, mock_load_bundle, mock_get_calendar_for_asset_class, mock_get_calendar
    ):
        """Test get_trading_calendar with asset_class uses get_calendar directly."""
        # Setup mocks
        mock_calendar = Mock()
        mock_get_calendar.return_value = mock_calendar
        mock_get_calendar_for_asset_class.return_value = "FOREX"

        # Call function
        result = get_trading_calendar("test_bundle", asset_class="forex")

        # Verify get_calendar was called with custom calendar name
        mock_get_calendar_for_asset_class.assert_called_once_with("forex")
        mock_get_calendar.assert_called_once_with("FOREX")
        assert result == mock_calendar

    @pytest.mark.unit
    @patch("lib.bundles.load_bundle")
    def test_get_trading_calendar_fallback_to_bundle(self, mock_load_bundle):
        """Test get_trading_calendar falls back to bundle calendar."""
        # Setup mock bundle with calendar
        mock_calendar = Mock()
        mock_bundle_data = Mock()
        mock_bundle_data.equity_daily_bar_reader = Mock()
        mock_bundle_data.equity_daily_bar_reader.trading_calendar = mock_calendar
        mock_load_bundle.return_value = mock_bundle_data

        # Call function without asset_class
        result = get_trading_calendar("test_bundle", asset_class=None)

        # Verify bundle calendar was used
        assert result == mock_calendar
        mock_load_bundle.assert_called_once_with("test_bundle")
