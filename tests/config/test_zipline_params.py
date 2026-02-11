"""
Tests for lib/config/zipline_params.py

Tests the bridge between our YAML-based config system and Zipline's
run_algorithm() parameter API.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from lib.config.zipline_params import (
    ZiplineRunParams,
    extract_zipline_params,
    validate_zipline_params,
)


class TestZiplineRunParams:
    """Tests for ZiplineRunParams dataclass."""

    def test_creation(self):
        """Test creating ZiplineRunParams with required fields."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=calendar,
        )

        assert params.start == start
        assert params.end == end
        assert params.capital_base == 100000.0
        assert params.bundle == "test_bundle"
        assert params.data_frequency == "daily"
        assert params.trading_calendar == calendar
        assert params.benchmark_returns is None
        assert params.metrics_set is None

    def test_to_dict(self):
        """Test converting ZiplineRunParams to dictionary."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()
        benchmark = pd.Series([0.01, 0.02], index=pd.DatetimeIndex(["2020-01-01", "2020-01-02"]))

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=calendar,
            benchmark_returns=benchmark,
            metrics_set="default",
        )

        result = params.to_dict()

        assert result["start"] == start
        assert result["end"] == end
        assert result["capital_base"] == 100000.0
        assert result["bundle"] == "test_bundle"
        assert result["data_frequency"] == "daily"
        pd.testing.assert_series_equal(result["benchmark_returns"], benchmark)
        assert result["metrics_set"] == "default"
        # trading_calendar should not be in dict (passed separately)
        assert "trading_calendar" not in result

    def test_to_dict_excludes_none(self):
        """Test that to_dict() excludes None values."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=calendar,
        )

        result = params.to_dict()

        assert "benchmark_returns" not in result
        assert "metrics_set" not in result


class TestExtractZiplineParams:
    """Tests for extract_zipline_params()."""

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_extract_from_function_args(self, mock_load_params):
        """Test extracting parameters from function arguments."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()

        params = extract_zipline_params(
            strategy_name="test_strategy",
            start_date="2020-01-01",
            end_date="2020-12-31",
            capital_base=200000.0,
            bundle="custom_bundle",
            data_frequency="minute",
            trading_calendar=calendar,
        )

        assert params.start == start
        assert params.end == end
        assert params.capital_base == 200000.0
        assert params.bundle == "custom_bundle"
        assert params.data_frequency == "minute"
        assert params.trading_calendar == calendar

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_extract_from_params_yaml(self, mock_load_params):
        """Test extracting parameters from strategy parameters.yaml."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "capital": 150000.0,
                "bundle": "yaml_bundle",
                "data_frequency": "daily",
            }
        }

        calendar = Mock()

        params = extract_zipline_params(
            strategy_name="test_strategy",
            trading_calendar=calendar,
        )

        assert params.start == pd.Timestamp("2020-01-01")
        assert params.end == pd.Timestamp("2020-12-31")
        assert params.capital_base == 150000.0
        assert params.bundle == "yaml_bundle"
        assert params.data_frequency == "daily"

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_function_args_override_yaml(self, mock_load_params):
        """Test that function arguments override YAML parameters."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "capital": 150000.0,
                "bundle": "yaml_bundle",
            }
        }

        calendar = Mock()

        params = extract_zipline_params(
            strategy_name="test_strategy",
            start_date="2021-01-01",  # Override YAML
            capital_base=200000.0,  # Override YAML
            trading_calendar=calendar,
        )

        assert params.start == pd.Timestamp("2021-01-01")  # Function arg wins
        assert params.capital_base == 200000.0  # Function arg wins
        assert params.end == pd.Timestamp("2020-12-31")  # From YAML
        assert params.bundle == "yaml_bundle"  # From YAML

    @patch("lib.config.zipline_params.load_strategy_params")
    @patch("lib.config.zipline_params.get_default_bundle")
    def test_default_bundle_from_asset_class(self, mock_get_bundle, mock_load_params):
        """Test using default bundle from asset class."""
        mock_load_params.return_value = {"backtest": {"start_date": "2020-01-01"}}
        mock_get_bundle.return_value = "default_crypto_bundle"

        calendar = Mock()

        params = extract_zipline_params(
            strategy_name="test_strategy",
            asset_class="crypto",
            trading_calendar=calendar,
        )

        assert params.bundle == "default_crypto_bundle"
        mock_get_bundle.assert_called_once_with("crypto")

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_missing_start_date_raises_error(self, mock_load_params):
        """Test that missing start_date raises ValueError."""
        mock_load_params.return_value = {"backtest": {}}

        calendar = Mock()

        with pytest.raises(ValueError, match="start_date required"):
            extract_zipline_params(
                strategy_name="test_strategy",
                trading_calendar=calendar,
            )

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_missing_bundle_raises_error(self, mock_load_params):
        """Test that missing bundle raises ValueError."""
        mock_load_params.return_value = {"backtest": {"start_date": "2020-01-01"}}

        calendar = Mock()

        with pytest.raises(ValueError, match="bundle required"):
            extract_zipline_params(
                strategy_name="test_strategy",
                trading_calendar=calendar,
            )

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_missing_trading_calendar_raises_error(self, mock_load_params):
        """Test that missing trading_calendar raises ValueError."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "bundle": "test_bundle",
            }
        }

        with pytest.raises(ValueError, match="trading_calendar required"):
            extract_zipline_params(
                strategy_name="test_strategy",
            )

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_invalid_data_frequency_raises_error(self, mock_load_params):
        """Test that invalid data_frequency raises ValueError."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "bundle": "test_bundle",
                "data_frequency": "invalid",
            }
        }

        calendar = Mock()

        with pytest.raises(ValueError, match="data_frequency must be 'daily' or 'minute'"):
            extract_zipline_params(
                strategy_name="test_strategy",
                trading_calendar=calendar,
            )

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_timezone_normalization(self, mock_load_params):
        """Test that timezone-aware timestamps are normalized."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "bundle": "test_bundle",
            }
        }

        calendar = Mock()

        # Pass timezone-aware date
        params = extract_zipline_params(
            strategy_name="test_strategy",
            start_date="2020-01-01",
            trading_calendar=calendar,
        )

        # Should be timezone-naive
        assert params.start.tz is None
        assert params.end.tz is None

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_default_end_date(self, mock_load_params):
        """Test that default end_date is today if not provided."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "bundle": "test_bundle",
            }
        }

        calendar = Mock()

        params = extract_zipline_params(
            strategy_name="test_strategy",
            trading_calendar=calendar,
        )

        # Should default to today (approximately)
        assert params.end >= pd.Timestamp.today().normalize()

    @patch("lib.config.zipline_params.load_strategy_params")
    def test_default_capital(self, mock_load_params):
        """Test that default capital_base is 100000 if not provided."""
        mock_load_params.return_value = {
            "backtest": {
                "start_date": "2020-01-01",
                "bundle": "test_bundle",
            }
        }

        calendar = Mock()

        params = extract_zipline_params(
            strategy_name="test_strategy",
            trading_calendar=calendar,
        )

        assert params.capital_base == 100000.0


class TestValidateZiplineParams:
    """Tests for validate_zipline_params()."""

    def test_valid_params(self):
        """Test validation passes for valid parameters."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=calendar,
        )

        is_valid, errors = validate_zipline_params(params)

        assert is_valid
        assert len(errors) == 0

    def test_start_after_end_raises_error(self):
        """Test validation fails when start >= end."""
        start = pd.Timestamp("2020-12-31")
        end = pd.Timestamp("2020-01-01")
        calendar = Mock()

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=calendar,
        )

        is_valid, errors = validate_zipline_params(params)

        assert not is_valid
        assert any("start" in e and "end" in e for e in errors)

    def test_negative_capital_raises_error(self):
        """Test validation fails for negative capital_base."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=-1000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=calendar,
        )

        is_valid, errors = validate_zipline_params(params)

        assert not is_valid
        assert any("capital_base" in e for e in errors)

    def test_invalid_data_frequency_raises_error(self):
        """Test validation fails for invalid data_frequency."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        calendar = Mock()

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="invalid",
            trading_calendar=calendar,
        )

        is_valid, errors = validate_zipline_params(params)

        assert not is_valid
        assert any("data_frequency" in e for e in errors)

    def test_missing_trading_calendar_raises_error(self):
        """Test validation fails when trading_calendar is None."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")

        params = ZiplineRunParams(
            start=start,
            end=end,
            capital_base=100000.0,
            bundle="test_bundle",
            data_frequency="daily",
            trading_calendar=None,
        )

        is_valid, errors = validate_zipline_params(params)

        assert not is_valid
        assert any("trading_calendar" in e for e in errors)
