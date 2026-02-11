"""
Test Yahoo Finance bundle registration.

Tests for register_yahoo_bundle and auto_register_yahoo_bundle_if_exists functions.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles.yahoo.registration import (
    register_yahoo_bundle,
    auto_register_yahoo_bundle_if_exists,
)


class TestRegisterYahooBundle:
    """Tests for register_yahoo_bundle function."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_daily_success(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test successful daily bundle registration."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["AAPL", "MSFT"],
            calendar_name="XNYS",
            start_date="2020-01-01",
            end_date="2023-12-31",
            data_frequency="daily",
            timeframe="daily",
        )

        # Verify register was called
        assert mock_register.called
        call_args = mock_register.call_args
        assert call_args[0][0] == "test_bundle"
        assert call_args[1]["calendar_name"] == "XNYS"
        assert call_args[1]["minutes_per_day"] == 390

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {"test_bundle": MagicMock()})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    def test_register_yahoo_bundle_already_exists_no_force(
        self,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle returns early if bundle exists and force=False."""
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["AAPL"],
            force=False,
        )

        # Should not call register since bundle already exists
        mock_register.assert_not_called()

    @pytest.mark.unit
    @patch("zipline.data.bundles.unregister")
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {"test_bundle": MagicMock()})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_force_re_registers(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
        mock_unregister,
    ):
        """Test register_yahoo_bundle unregisters and re-registers when force=True."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["AAPL"],
            force=True,
        )

        # Should unregister first, then register
        mock_unregister.assert_called_once_with("test_bundle")
        assert mock_register.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.logger")
    def test_register_yahoo_bundle_date_validation_warning(
        self,
        mock_logger,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle logs warning when date range is adjusted."""
        mock_mpd.return_value = 390
        warning_msg = "Start date adjusted to 2020-01-01 due to timeframe limit"
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", warning_msg)
        mock_get_tf_info.return_value = {
            "yf_interval": "1m",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["AAPL"],
            timeframe="1m",
        )

        # Should log warning
        mock_logger.warning.assert_called_once_with(warning_msg)
        assert mock_register.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_crypto_calendar(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle with CRYPTO calendar (1440 minutes per day)."""
        mock_mpd.return_value = 1440  # 24/7 market
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_crypto",
            symbols=["BTC-USD"],
            calendar_name="CRYPTO",
        )

        call_args = mock_register.call_args
        assert call_args[1]["calendar_name"] == "CRYPTO"
        assert call_args[1]["minutes_per_day"] == 1440

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_forex_calendar(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle with FOREX calendar (1440 minutes per day)."""
        mock_mpd.return_value = 1440  # 24/5 market
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_forex",
            symbols=["EURUSD=X"],
            calendar_name="FOREX",
        )

        call_args = mock_register.call_args
        assert call_args[1]["calendar_name"] == "FOREX"
        assert call_args[1]["minutes_per_day"] == 1440

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_minute_frequency(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle with minute data frequency."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_minute",
            symbols=["AAPL"],
            data_frequency="minute",
            timeframe="1h",
        )

        assert mock_register.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_requires_aggregation(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle with timeframe requiring aggregation (4h)."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": True,
            "aggregation_target": "4h",
        }

        register_yahoo_bundle(
            bundle_name="test_4h",
            symbols=["AAPL"],
            timeframe="4h",
        )

        assert mock_register.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    def test_register_yahoo_bundle_ingest_function_daily(
        self,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that registered ingest function works correctly for daily data."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        # Mock calendar
        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        # Mock data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1000000, 1100000],
            },
            index=pd.date_range("2020-01-01", periods=2, freq="D", tz="UTC"),
        )

        mock_fetch.return_value = sample_data
        mock_process.return_value = sample_data

        # Capture the function passed to the decorator
        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        # Set up the mock to return our capturing decorator BEFORE calling register_yahoo_bundle
        mock_register.return_value = decorator_that_captures

        # Register bundle
        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["AAPL"],
        )

        # Verify register was called
        assert mock_register.called
        # Verify the decorator was called with a function
        assert len(captured_func) > 0, "Function should have been captured by decorator"
        registered_func = captured_func[0]
        assert callable(registered_func), "Captured function should be callable"

        # Mock Zipline writer objects
        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        # Consume the generator to simulate Zipline's writer behavior.
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Call the ingest function
        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Verify asset_db_writer was called
        assert mock_asset_db_writer.write.called
        # Verify daily_bar_writer was called (not minute for daily frequency)
        assert mock_daily_bar_writer.write.called
        # Verify adjustment_writer was called
        assert mock_adjustment_writer.write.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    def test_register_yahoo_bundle_ingest_function_minute(
        self,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that registered ingest function works correctly for minute data."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        # Mock calendar
        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        # Mock minute data
        minute_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1000000, 1100000],
            },
            index=pd.date_range("2020-01-01 09:30", periods=2, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        # Mock daily aggregation
        daily_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [103.0],
                "low": [99.0],
                "close": [102.0],
                "volume": [2100000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="UTC"),
        )
        mock_aggregate.return_value = daily_data

        # Capture the function passed to the decorator
        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        # Set up the mock to return our capturing decorator BEFORE calling register_yahoo_bundle
        mock_register.return_value = decorator_that_captures

        # Register bundle
        register_yahoo_bundle(
            bundle_name="test_minute",
            symbols=["AAPL"],
            data_frequency="minute",
            timeframe="1h",
        )

        # Get the registered ingest function
        assert mock_register.called
        assert len(captured_func) > 0, "Function should have been captured by decorator"
        registered_func = captured_func[0]

        # Mock Zipline writer objects
        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        # Consume the generator to simulate Zipline's writer behavior.
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Call the ingest function
        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Verify both minute and daily writers were called
        assert mock_minute_bar_writer.write.called
        assert mock_daily_bar_writer.write.called
        # Verify aggregation was called
        assert mock_aggregate.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    def test_register_yahoo_bundle_fetch_failure_continues(
        self,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that ingest function continues when one symbol fails to fetch."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        # First symbol fails, second succeeds
        sample_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="UTC"),
        )

        def fetch_side_effect(symbol, *args, **kwargs):
            if symbol == "INVALID":
                raise ValueError(f"No data for {symbol}")
            return sample_data

        mock_fetch.side_effect = fetch_side_effect
        mock_process.return_value = sample_data

        # Capture the function passed to the decorator
        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["INVALID", "AAPL"],
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        # Consume the generator to simulate Zipline's writer behavior (and trigger RuntimeError).
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Should not raise - should continue with valid symbol
        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Should still write data for valid symbol
        assert mock_daily_bar_writer.write.called

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    def test_register_yahoo_bundle_all_symbols_fail_raises(
        self,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that ingest function raises when all symbols fail to fetch."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        # All symbols fail
        mock_fetch.side_effect = ValueError("No data available")

        # Capture the function passed to the decorator
        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["INVALID1", "INVALID2"],
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        # Consume the generator to simulate Zipline's writer behavior (and trigger RuntimeError).
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Should raise RuntimeError when all symbols fail
        with pytest.raises(RuntimeError, match="No data was successfully fetched"):
            registered_func(
                environ={},
                asset_db_writer=mock_asset_db_writer,
                minute_bar_writer=mock_minute_bar_writer,
                daily_bar_writer=mock_daily_bar_writer,
                adjustment_writer=mock_adjustment_writer,
                calendar=mock_calendar,
                start_session=pd.Timestamp("2020-01-01", tz="UTC"),
                end_session=pd.Timestamp("2023-12-31", tz="UTC"),
                cache={},
                show_progress=False,
                timestamp=pd.Timestamp.now(),
            )

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    def test_register_yahoo_bundle_default_calendar(
        self,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test register_yahoo_bundle uses XNYS as default calendar."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        register_yahoo_bundle(
            bundle_name="test_bundle",
            symbols=["AAPL"],
            # calendar_name not specified, should default to 'XNYS'
        )

        call_args = mock_register.call_args
        assert call_args[1]["calendar_name"] == "XNYS"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    @patch("lib.bundles.yahoo.registration.consolidate_forex_sunday_to_friday")
    @patch("lib.bundles.yahoo.registration.filter_to_calendar_sessions")
    @patch("lib.bundles.yahoo.registration.apply_gap_filling")
    def test_register_yahoo_bundle_forex_minute_processing(
        self,
        mock_gap_filling,
        mock_filter_sessions,
        mock_consolidate_sunday,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test FOREX-specific processing in minute-to-daily aggregation path."""
        mock_mpd.return_value = 1440
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        # Mock minute data
        minute_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [102.0, 103.0, 104.0],
                "low": [99.0, 100.0, 101.0],
                "close": [101.0, 102.0, 103.0],
                "volume": [1000000, 1100000, 1200000],
            },
            index=pd.date_range("2020-01-01 00:00", periods=3, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        # Mock daily aggregation
        daily_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [104.0],
                "low": [99.0],
                "close": [103.0],
                "volume": [3300000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="UTC"),
        )
        mock_aggregate.return_value = daily_data
        mock_consolidate_sunday.return_value = daily_data
        mock_filter_sessions.return_value = daily_data
        mock_gap_filling.return_value = daily_data

        # Capture the function passed to the decorator
        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        # Register bundle with FOREX calendar
        register_yahoo_bundle(
            bundle_name="test_forex_minute",
            symbols=["EURUSD=X"],
            calendar_name="FOREX",
            data_frequency="minute",
            timeframe="1h",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        # Mock Zipline writer objects
        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Call the ingest function
        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Verify FOREX-specific processing was called
        assert mock_consolidate_sunday.called, "Sunday consolidation should be called for FOREX"
        assert mock_filter_sessions.called, "Calendar session filtering should be called for FOREX"
        assert mock_gap_filling.called, "Gap filling should be called for FOREX"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    @patch("lib.bundles.yahoo.registration.apply_gap_filling")
    def test_register_yahoo_bundle_crypto_gap_filling(
        self,
        mock_gap_filling,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test CRYPTO gap filling in minute-to-daily aggregation path."""
        mock_mpd.return_value = 1440
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        minute_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1000000, 1100000],
            },
            index=pd.date_range("2020-01-01 00:00", periods=2, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        daily_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [103.0],
                "low": [99.0],
                "close": [102.0],
                "volume": [2100000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="UTC"),
        )
        mock_aggregate.return_value = daily_data
        mock_gap_filling.return_value = daily_data

        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_crypto_minute",
            symbols=["BTC-USD"],
            calendar_name="CRYPTO",
            data_frequency="minute",
            timeframe="1h",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Verify gap filling was called for CRYPTO
        assert mock_gap_filling.called, "Gap filling should be called for CRYPTO"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    def test_register_yahoo_bundle_empty_aggregation_skips(
        self,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that empty daily data after aggregation is skipped."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        minute_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01 09:30", periods=1, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        # Return empty DataFrame after aggregation
        mock_aggregate.return_value = pd.DataFrame()

        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_empty_agg",
            symbols=["AAPL"],
            data_frequency="minute",
            timeframe="1h",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        # Track what gets written
        written_data = []

        def write_side_effect(gen, **kwargs):
            for item in gen:
                written_data.append(item)

        mock_daily_bar_writer.write.side_effect = write_side_effect
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Should not raise, should skip empty data
        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Empty data should be skipped, so nothing written to daily writer
        assert len(written_data) == 0, "Empty aggregated data should be skipped"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    @patch("lib.bundles.yahoo.registration.consolidate_forex_sunday_to_friday")
    def test_register_yahoo_bundle_forex_consolidation_empties_data(
        self,
        mock_consolidate,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that empty data after FOREX consolidation is skipped."""
        mock_mpd.return_value = 1440
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        minute_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01 00:00", periods=1, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        daily_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="UTC"),
        )
        mock_aggregate.return_value = daily_data
        # Consolidation returns empty DataFrame
        mock_consolidate.return_value = pd.DataFrame()

        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_forex_empty",
            symbols=["EURUSD=X"],
            calendar_name="FOREX",
            data_frequency="minute",
            timeframe="1h",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        written_data = []

        def write_side_effect(gen, **kwargs):
            for item in gen:
                written_data.append(item)

        mock_daily_bar_writer.write.side_effect = write_side_effect
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Empty data after consolidation should be skipped
        assert len(written_data) == 0, "Empty data after consolidation should be skipped"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    def test_register_yahoo_bundle_timezone_normalization(
        self,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test timezone normalization in daily aggregation path."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        minute_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01 09:30", periods=1, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        # Return data with different timezone
        daily_data_tz = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="America/New_York"),
        )
        mock_aggregate.return_value = daily_data_tz

        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_tz",
            symbols=["AAPL"],
            data_frequency="minute",
            timeframe="1h",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        written_data = []

        def write_side_effect(gen, **kwargs):
            for item in gen:
                written_data.append(item)

        mock_daily_bar_writer.write.side_effect = write_side_effect
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=pd.Timestamp("2020-01-01", tz="UTC"),
            end_session=pd.Timestamp("2023-12-31", tz="UTC"),
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Verify data was written (timezone normalization should have occurred)
        assert len(written_data) > 0, "Data should be written after timezone normalization"
        # Verify the written data has UTC timezone
        sid, df = written_data[0]
        assert str(df.index.tz) == "UTC", "Data should be normalized to UTC"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    def test_register_yahoo_bundle_asset_metadata_creation(
        self,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test asset metadata creation in ingest function."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1d",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        sample_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01", periods=1, freq="D", tz="UTC"),
        )

        mock_fetch.return_value = sample_data
        mock_process.return_value = sample_data

        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        symbols = ["AAPL", "MSFT", "GOOGL"]
        register_yahoo_bundle(
            bundle_name="test_metadata",
            symbols=symbols,
            calendar_name="XNYS",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        mock_daily_bar_writer.write.side_effect = lambda gen, **kwargs: list(gen)
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        start_session = pd.Timestamp("2020-01-01", tz="UTC")
        end_session = pd.Timestamp("2023-12-31", tz="UTC")

        registered_func(
            environ={},
            asset_db_writer=mock_asset_db_writer,
            minute_bar_writer=mock_minute_bar_writer,
            daily_bar_writer=mock_daily_bar_writer,
            adjustment_writer=mock_adjustment_writer,
            calendar=mock_calendar,
            start_session=start_session,
            end_session=end_session,
            cache={},
            show_progress=False,
            timestamp=pd.Timestamp.now(),
        )

        # Verify asset_db_writer.write was called
        assert mock_asset_db_writer.write.called, "Asset metadata should be written"

        # Verify the equities DataFrame structure
        call_args = mock_asset_db_writer.write.call_args
        assert "equities" in call_args.kwargs, "Should write equities metadata"

        equities_df = call_args.kwargs["equities"]
        assert len(equities_df) == len(symbols), "Should have one row per symbol"
        assert list(equities_df["symbol"]) == symbols, "Symbols should match"
        assert list(equities_df["asset_name"]) == symbols, "Asset names should match symbols"
        assert all(equities_df["exchange"] == "NYSE"), "Exchange should be NYSE for XNYS calendar"
        assert all(equities_df["country_code"] == "US"), "Country code should be US"

    @pytest.mark.unit
    @patch("zipline.data.bundles.register")
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.get_timeframe_info")
    @patch("lib.bundles.yahoo.registration.validate_timeframe_date_range")
    @patch("lib.bundles.yahoo.registration.get_minutes_per_day")
    @patch("lib.bundles.yahoo.registration.get_calendar")
    @patch("lib.bundles.yahoo.registration.fetch_yahoo_data")
    @patch("lib.bundles.yahoo.registration.process_yahoo_data")
    @patch("lib.bundles.yahoo.registration.aggregate_to_daily")
    def test_register_yahoo_bundle_aggregation_exception_handling(
        self,
        mock_aggregate,
        mock_process,
        mock_fetch,
        mock_get_calendar,
        mock_mpd,
        mock_validate_dates,
        mock_get_tf_info,
        mock_register,
    ):
        """Test that aggregation exceptions are caught and logged."""
        mock_mpd.return_value = 390
        mock_validate_dates.return_value = ("2020-01-01", "2023-12-31", None)
        mock_get_tf_info.return_value = {
            "yf_interval": "1h",
            "requires_aggregation": False,
            "aggregation_target": None,
        }

        mock_calendar = MagicMock()
        mock_get_calendar.return_value = mock_calendar

        minute_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1000000],
            },
            index=pd.date_range("2020-01-01 09:30", periods=1, freq="h", tz="UTC"),
        )

        mock_fetch.return_value = minute_data
        mock_process.return_value = minute_data

        # Aggregation raises exception
        mock_aggregate.side_effect = ValueError("Aggregation failed")

        captured_func = []

        def decorator_that_captures(func):
            captured_func.append(func)
            return func

        mock_register.return_value = decorator_that_captures

        register_yahoo_bundle(
            bundle_name="test_agg_error",
            symbols=["AAPL"],
            data_frequency="minute",
            timeframe="1h",
        )

        assert len(captured_func) > 0
        registered_func = captured_func[0]

        mock_asset_db_writer = MagicMock()
        mock_daily_bar_writer = MagicMock()
        written_data = []

        def write_side_effect(gen, **kwargs):
            for item in gen:
                written_data.append(item)

        mock_daily_bar_writer.write.side_effect = write_side_effect
        mock_minute_bar_writer = MagicMock()
        mock_adjustment_writer = MagicMock()

        # Should not raise, should continue with other symbols
        with patch("lib.bundles.yahoo.registration.logger") as mock_logger:
            registered_func(
                environ={},
                asset_db_writer=mock_asset_db_writer,
                minute_bar_writer=mock_minute_bar_writer,
                daily_bar_writer=mock_daily_bar_writer,
                adjustment_writer=mock_adjustment_writer,
                calendar=mock_calendar,
                start_session=pd.Timestamp("2020-01-01", tz="UTC"),
                end_session=pd.Timestamp("2023-12-31", tz="UTC"),
                cache={},
                show_progress=False,
                timestamp=pd.Timestamp.now(),
            )

            # Should log exception
            assert mock_logger.exception.called, "Exception should be logged"
            logged_msg = mock_logger.exception.call_args[0][0]
            assert "Failed to aggregate daily data" in logged_msg

        # Failed aggregation should not produce data
        assert len(written_data) == 0, "Failed aggregation should not produce data"


class TestAutoRegisterYahooBundleIfExists:
    """Tests for auto_register_yahoo_bundle_if_exists function."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.register_yahoo_bundle")
    def test_auto_register_bundle_exists_not_registered(
        self,
        mock_register,
    ):
        """Test auto_register registers bundle when data exists but not registered."""
        # Mock path exists
        with patch("lib.bundles.yahoo.registration.Path") as mock_path_class:
            mock_home = MagicMock()
            mock_data_dir = MagicMock()
            mock_data_dir.exists.return_value = True
            mock_home.joinpath.return_value = mock_data_dir
            mock_path_class.home.return_value = mock_home

            # Mock symbol extraction (imported inside function from ..utils)
            with patch("lib.bundles.utils.extract_symbols_from_bundle") as mock_extract:
                mock_extract.return_value = ["SPY", "QQQ"]

                auto_register_yahoo_bundle_if_exists()

                mock_extract.assert_called_once_with("yahoo_equities_daily")
                mock_register.assert_called_once_with(
                    "yahoo_equities_daily", ["SPY", "QQQ"], "XNYS"
                )

    @pytest.mark.unit
    @patch("zipline.data.bundles.bundles", {"yahoo_equities_daily": MagicMock()})
    @patch("lib.bundles.yahoo.registration.register_yahoo_bundle")
    def test_auto_register_bundle_already_registered(
        self,
        mock_register,
    ):
        """Test auto_register does nothing when bundle already registered."""
        # Mock path exists
        with patch("lib.bundles.yahoo.registration.Path") as mock_path_class:
            mock_home = MagicMock()
            mock_data_dir = MagicMock()
            mock_data_dir.exists.return_value = True
            mock_home.joinpath.return_value = mock_data_dir
            mock_path_class.home.return_value = mock_home

            with patch("lib.bundles.utils.extract_symbols_from_bundle") as mock_extract:
                auto_register_yahoo_bundle_if_exists()

                # Should not extract symbols or register
                mock_extract.assert_not_called()
                mock_register.assert_not_called()

    @pytest.mark.unit
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.register_yahoo_bundle")
    def test_auto_register_bundle_not_exists(
        self,
        mock_register,
    ):
        """Test auto_register does nothing when bundle data doesn't exist."""
        # Mock path doesn't exist
        with patch("lib.bundles.yahoo.registration.Path") as mock_path_class:
            mock_home = MagicMock()
            mock_data_dir = MagicMock()
            mock_data_dir.exists.return_value = False
            mock_home.joinpath.return_value = mock_data_dir
            mock_path_class.home.return_value = mock_home

            # Function returns early if path doesn't exist, so extract_symbols_from_bundle
            # is never imported or called
            auto_register_yahoo_bundle_if_exists()

            # Should not register (function returns early)
            mock_register.assert_not_called()

    @pytest.mark.unit
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.register_yahoo_bundle")
    def test_auto_register_extraction_fails_fallback(
        self,
        mock_register,
    ):
        """Test auto_register falls back to SPY when symbol extraction fails."""
        # Mock path exists
        with patch("lib.bundles.yahoo.registration.Path") as mock_path_class:
            mock_home = MagicMock()
            mock_data_dir = MagicMock()
            mock_data_dir.exists.return_value = True
            mock_home.joinpath.return_value = mock_data_dir
            mock_path_class.home.return_value = mock_home

            # Mock extraction returns empty list
            with patch("lib.bundles.utils.extract_symbols_from_bundle") as mock_extract:
                mock_extract.return_value = []

                auto_register_yahoo_bundle_if_exists()

                mock_extract.assert_called_once_with("yahoo_equities_daily")
                # Should fallback to SPY
                mock_register.assert_called_once_with("yahoo_equities_daily", ["SPY"], "XNYS")

    @pytest.mark.unit
    @patch("lib.bundles.yahoo.registration.register_yahoo_bundle")
    def test_auto_register_handles_import_error(
        self,
        mock_register,
    ):
        """Test auto_register handles ImportError gracefully."""
        # Mock path exists
        with patch("lib.bundles.yahoo.registration.Path") as mock_path_class:
            mock_home = MagicMock()
            mock_data_dir = MagicMock()
            mock_data_dir.exists.return_value = True
            mock_home.__truediv__.return_value = mock_data_dir
            mock_path_class.home.return_value = mock_home

            # Make importing zipline.data.bundles raise ImportError without recursion.
            original_import = __import__

            def mock_import(name, *args, **kwargs):
                if name == "zipline.data.bundles":
                    raise ImportError("Zipline not installed")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                auto_register_yahoo_bundle_if_exists()
                mock_register.assert_not_called()

    @pytest.mark.unit
    @patch("zipline.data.bundles.bundles", {})
    @patch("lib.bundles.yahoo.registration.register_yahoo_bundle")
    def test_auto_register_handles_general_exception(
        self,
        mock_register,
    ):
        """Test auto_register handles general exceptions gracefully."""
        # Mock path exists
        with patch("lib.bundles.yahoo.registration.Path") as mock_path_class:
            mock_home = MagicMock()
            mock_data_dir = MagicMock()
            mock_data_dir.exists.return_value = True
            mock_home.__truediv__.return_value = mock_data_dir
            mock_path_class.home.return_value = mock_home

            # Mock exception during registration
            mock_register.side_effect = Exception("Registration failed")

            # Should not raise, should log warning
            with patch("lib.bundles.yahoo.registration.logger") as mock_logger:
                with patch("lib.bundles.utils.extract_symbols_from_bundle") as mock_extract:
                    mock_extract.return_value = ["SPY"]

                    auto_register_yahoo_bundle_if_exists()

                    assert mock_logger.warning.called, "Warning should have been logged"
                    warning_msg = mock_logger.warning.call_args[0][0]
                    assert "Auto-registration failed" in warning_msg
