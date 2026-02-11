"""
Test backtest preprocessing functions.

Tests for validate_session_alignment, validate_strategy_symbols, and validate_bundle_date_range.
"""

# ruff: noqa: E402

# Standard library imports
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest.preprocessing import (
    validate_session_alignment,
    validate_strategy_symbols,
    validate_bundle_date_range,
)


class TestValidateSessionAlignment:
    """Tests for validate_session_alignment function."""

    @pytest.mark.unit
    @patch("lib.backtest.preprocessing.ensure_bundle_registered")
    def test_validate_session_alignment_registered(self, mock_ensure_registered):
        """Test validate_session_alignment passes for registered bundle."""
        mock_ensure_registered.return_value = True

        validate_session_alignment(
            bundle="test_bundle",
            start_date=pd.Timestamp("2020-01-01"),
            end_date=pd.Timestamp("2020-12-31"),
        )

        mock_ensure_registered.assert_called_once_with(
            "test_bundle",
            raise_on_missing=False,
            exception_type=ValueError,
            log_on_missing=True,
            log_level=logging.WARNING,
        )

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.utils.ensure_bundle_registered")
    def test_validate_session_alignment_strict_mode(self, mock_ensure_registered, mock_init):
        """Test validate_session_alignment raises in strict mode for missing bundle."""
        mock_ensure_registered.side_effect = ValueError("Bundle 'missing' not found")
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(ValueError, match="Bundle 'missing' not found"):
                validate_session_alignment(
                    bundle="missing",
                    start_date=pd.Timestamp("2020-01-01"),
                    end_date=pd.Timestamp("2020-12-31"),
                    validate_calendar_flag=True,
                )

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.utils.ensure_bundle_registered")
    def test_validate_session_alignment_warn_mode(self, mock_ensure_registered, mock_init):
        """Test validate_session_alignment warns but doesn't raise in warn mode."""
        mock_ensure_registered.return_value = False
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            # Should not raise, just log warning
            validate_session_alignment(
                bundle="missing",
                start_date=pd.Timestamp("2020-01-01"),
                end_date=pd.Timestamp("2020-12-31"),
                validate_calendar_flag=False,
            )


class TestValidateStrategySymbols:
    """Tests for validate_strategy_symbols function."""

    @pytest.mark.unit
    @patch("lib.backtest.preprocessing.load_strategy_params")
    @patch("lib.backtest.preprocessing.get_bundle_symbols")
    def test_validate_strategy_symbols_success(self, mock_get_symbols, mock_load_params):
        """Test validate_strategy_symbols passes when symbol exists in bundle."""
        mock_load_params.return_value = {"strategy": {"asset_symbol": "AAPL"}}
        mock_get_symbols.return_value = ["AAPL", "MSFT"]
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with patch("lib.bundles.initialization.ensure_bundles_initialized"):
                validate_strategy_symbols("test_strategy", "test_bundle")

        mock_load_params.assert_called_once_with("test_strategy", None)
        mock_get_symbols.assert_called_once_with("test_bundle")

    @pytest.mark.unit
    @patch("lib.backtest.preprocessing.load_strategy_params")
    @patch("lib.backtest.preprocessing.get_bundle_symbols")
    def test_validate_strategy_symbols_missing_symbol(self, mock_get_symbols, mock_load_params):
        """Test validate_strategy_symbols raises when symbol not in bundle."""
        mock_load_params.return_value = {"strategy": {"asset_symbol": "AAPL"}}
        mock_get_symbols.return_value = ["MSFT", "GOOGL"]
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with patch("lib.bundles.initialization.ensure_bundles_initialized"):
                with pytest.raises(ValueError) as exc_info:
                    validate_strategy_symbols("test_strategy", "test_bundle")
        msg = str(exc_info.value)
        assert "Strategy 'test_strategy' requires symbol 'AAPL'" in msg
        # Ensure we no longer hardcode a specific source like "yahoo" in guidance
        assert "--source <SOURCE>" in msg
        assert "--symbols AAPL" in msg
        assert "--bundle-name test_bundle" in msg

    @pytest.mark.unit
    @patch("lib.backtest.preprocessing.load_strategy_params")
    @patch("lib.backtest.preprocessing.get_bundle_symbols")
    def test_validate_strategy_symbols_bundle_not_found(self, mock_get_symbols, mock_load_params):
        """Test validate_strategy_symbols propagates FileNotFoundError from get_bundle_symbols."""
        mock_load_params.return_value = {"strategy": {"asset_symbol": "AAPL"}}
        # get_bundle_symbols uses ensure_bundle_registered internally
        mock_get_symbols.side_effect = FileNotFoundError("Bundle 'missing' not found")
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with patch("lib.bundles.initialization.ensure_bundles_initialized"):
                with pytest.raises(FileNotFoundError, match="Bundle 'missing' not found"):
                    validate_strategy_symbols("test_strategy", "missing")

    @pytest.mark.unit
    @patch("lib.config.strategy.load_strategy_params")
    def test_validate_strategy_symbols_no_params(self, mock_load_params):
        """Test validate_strategy_symbols skips validation when no params file."""
        mock_load_params.side_effect = FileNotFoundError("No parameters.yaml")

        # Should not raise, just skip validation
        validate_strategy_symbols("test_strategy", "test_bundle")


class TestValidateBundleDateRange:
    """Tests for validate_bundle_date_range function."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_validate_bundle_date_range_success(self, mock_load, mock_init):
        """Test validate_bundle_date_range passes for valid date range."""
        # Mock bundle with sessions
        mock_bundle = MagicMock()
        mock_bundle.equity_daily_bar_reader.sessions = pd.date_range(
            "2020-01-01", "2020-12-31", freq="D"
        )
        mock_load.return_value = mock_bundle
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            start_ts, end_ts = validate_bundle_date_range(
                bundle="test_bundle",
                start_date="2020-06-01",
                end_date="2020-06-30",
                data_frequency="daily",
                trading_calendar=MagicMock(),
            )

        mock_load.assert_called_once_with("test_bundle")
        assert isinstance(start_ts, pd.Timestamp)
        assert isinstance(end_ts, pd.Timestamp)

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_validate_bundle_date_range_start_before_bundle(self, mock_load, mock_init):
        """Test validate_bundle_date_range raises when start date before bundle range."""
        mock_bundle = MagicMock()
        mock_bundle.equity_daily_bar_reader.sessions = pd.date_range(
            "2020-06-01", "2020-12-31", freq="D"
        )
        mock_load.return_value = mock_bundle
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(ValueError) as exc_info:
                validate_bundle_date_range(
                    bundle="test_bundle",
                    start_date="2020-01-01",
                    end_date="2020-12-31",
                    data_frequency="daily",
                    trading_calendar=MagicMock(),
                )
        msg = str(exc_info.value)
        assert "Requested start date" in msg
        assert "--start-date 2020-01-01" in msg
        assert "--bundle-name test_bundle" in msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("zipline.data.bundles.load")
    def test_validate_bundle_date_range_end_after_bundle(self, mock_load, mock_init):
        """Test validate_bundle_date_range raises when end date after bundle range."""
        mock_bundle = MagicMock()
        mock_bundle.equity_daily_bar_reader.sessions = pd.date_range(
            "2020-01-01", "2020-06-30", freq="D"
        )
        mock_load.return_value = mock_bundle
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(ValueError) as exc_info:
                validate_bundle_date_range(
                    bundle="test_bundle",
                    start_date="2020-01-01",
                    end_date="2020-12-31",
                    data_frequency="daily",
                    trading_calendar=MagicMock(),
                )
        msg = str(exc_info.value)
        assert "Requested end date" in msg
        assert "--end-date 2020-12-31" in msg
        assert "--bundle-name test_bundle" in msg

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_validate_bundle_date_range_bundle_not_found(self, mock_init):
        """Test validate_bundle_date_range propagates FileNotFoundError from load_bundle."""
        # load_bundle uses ensure_bundle_registered internally
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError, match="Bundle 'missing' not found"):
                validate_bundle_date_range(
                    bundle="missing",
                    start_date="2020-01-01",
                    end_date="2020-12-31",
                    data_frequency="daily",
                    trading_calendar=MagicMock(),
                )
