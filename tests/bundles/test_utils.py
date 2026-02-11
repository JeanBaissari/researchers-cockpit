"""
Test bundle utility functions.

Tests for bundle validation, symbol extraction, and date validation utilities.
"""

# ruff: noqa: E402

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles.utils import (
    validate_bundle_exists,
    ensure_bundle_registered,
    is_valid_date_string,
    extract_symbols_from_bundle,
    aggregate_to_4h,
)
import pandas as pd


class TestValidateBundleExists:
    """Tests for validate_bundle_exists function."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_validate_bundle_exists_registered(self, mock_init):
        """Test validate_bundle_exists returns True for registered bundle."""
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = validate_bundle_exists("test_bundle")
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_validate_bundle_exists_not_registered(self, mock_init):
        """Test validate_bundle_exists returns False for unregistered bundle."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = validate_bundle_exists("nonexistent_bundle")
            assert result is False
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.utils.Path")
    def test_validate_bundle_exists_with_filesystem_check(self, mock_path_class, mock_init):
        """Test validate_bundle_exists with filesystem check enabled."""
        mock_bundles = {"test_bundle": MagicMock()}

        # Mock filesystem path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        # Chain the path operations: home() / '.zipline' / 'data' / bundle_name
        mock_home = MagicMock()
        mock_zipline = MagicMock()
        mock_data = MagicMock()
        mock_bundle_path = mock_path
        mock_home.__truediv__.return_value = mock_zipline
        mock_zipline.__truediv__.return_value = mock_data
        mock_data.__truediv__.return_value = mock_bundle_path
        mock_path_class.home.return_value = mock_home

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = validate_bundle_exists("test_bundle", check_filesystem=True)
            assert result is True
            mock_init.assert_called_once()
            mock_path.exists.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    @patch("lib.bundles.utils.Path")
    def test_validate_bundle_exists_filesystem_missing(self, mock_path_class, mock_init):
        """Test validate_bundle_exists returns False when filesystem check fails."""
        mock_bundles = {"test_bundle": MagicMock()}

        # Mock filesystem path doesn't exist
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        # Chain the path operations: home() / '.zipline' / 'data' / bundle_name
        mock_home = MagicMock()
        mock_zipline = MagicMock()
        mock_data = MagicMock()
        mock_bundle_path = mock_path
        mock_home.__truediv__.return_value = mock_zipline
        mock_zipline.__truediv__.return_value = mock_data
        mock_data.__truediv__.return_value = mock_bundle_path
        mock_path_class.home.return_value = mock_home

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = validate_bundle_exists("test_bundle", check_filesystem=True)
            assert result is False
            mock_init.assert_called_once()
            mock_path.exists.assert_called_once()


class TestEnsureBundleRegistered:
    """Tests for ensure_bundle_registered function."""

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_exists(self, mock_init):
        """Test ensure_bundle_registered returns True for registered bundle."""
        mock_bundles = {"test_bundle": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = ensure_bundle_registered("test_bundle")
            assert result is True
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_not_exists_raises(self, mock_init):
        """Test ensure_bundle_registered raises FileNotFoundError for unregistered bundle."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError, match="Bundle 'nonexistent_bundle' not found"):
                ensure_bundle_registered("nonexistent_bundle")
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_not_exists_returns_false(self, mock_init):
        """Test ensure_bundle_registered returns False when raise_on_missing=False."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            result = ensure_bundle_registered("nonexistent_bundle", raise_on_missing=False)
            assert result is False
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_custom_exception(self, mock_init):
        """Test ensure_bundle_registered raises custom exception type."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(ValueError, match="Bundle 'missing_bundle' not found"):
                ensure_bundle_registered(
                    "missing_bundle", raise_on_missing=True, exception_type=ValueError
                )
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_error_message_includes_available_bundles(self, mock_init):
        """Test ensure_bundle_registered error message includes available bundles."""
        mock_bundles = {"bundle1": MagicMock(), "bundle2": MagicMock()}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                ensure_bundle_registered("missing_bundle")

            error_msg = str(exc_info.value)
            assert "bundle1" in error_msg or "bundle2" in error_msg
            assert "Available bundles" in error_msg
            assert "ingest_data.py" in error_msg
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_error_message_no_bundles(self, mock_init):
        """Test ensure_bundle_registered error message when no bundles exist."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                ensure_bundle_registered("missing_bundle")

            error_msg = str(exc_info.value)
            assert "(none)" in error_msg or "Available bundles" in error_msg
            assert "ingest_data.py" in error_msg
            mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_log_on_missing(self, mock_init):
        """Test ensure_bundle_registered logs full message when log_on_missing=True."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with patch("lib.bundles.utils.logger") as mock_logger:
                result = ensure_bundle_registered(
                    "missing_bundle",
                    raise_on_missing=False,
                    log_on_missing=True,
                )
                assert result is False
                assert mock_logger.log.called
                # Ensure message is actionable (ingestion hint included)
                logged_msg = mock_logger.log.call_args[0][1]
                assert "ingest_data.py" in logged_msg
                mock_init.assert_called_once()

    @pytest.mark.unit
    @patch("lib.bundles.initialization.ensure_bundles_initialized")
    def test_ensure_bundle_registered_hints_are_included_in_message(self, mock_init):
        """Test ensure_bundle_registered embeds source/symbol/date hints in the ingest command."""
        mock_bundles = {}

        with patch("zipline.data.bundles.bundles", mock_bundles):
            with pytest.raises(FileNotFoundError) as exc_info:
                ensure_bundle_registered(
                    "missing_bundle",
                    source_hint="csv",
                    symbols_hint="EURUSD",
                    start_date_hint="2020-01-01",
                    end_date_hint="2020-12-31",
                )

        msg = str(exc_info.value)
        assert "--source csv" in msg
        assert "--symbols EURUSD" in msg
        assert "--start-date 2020-01-01" in msg
        assert "--end-date 2020-12-31" in msg


class TestIsValidDateString:
    """Tests for is_valid_date_string function."""

    @pytest.mark.unit
    def test_valid_date_string(self):
        """Test is_valid_date_string with valid date strings."""
        assert is_valid_date_string("2020-01-01") is True
        assert is_valid_date_string("2023-12-31") is True
        assert is_valid_date_string("1999-01-15") is True

    @pytest.mark.unit
    def test_invalid_date_string(self):
        """Test is_valid_date_string with invalid date strings."""
        assert is_valid_date_string("2020-13-01") is False  # Invalid month
        assert is_valid_date_string("2020-01-32") is False  # Invalid day
        assert is_valid_date_string("2020/01/01") is False  # Wrong format
        assert is_valid_date_string("01-01-2020") is False  # Wrong format
        assert is_valid_date_string("") is False  # Empty string
        assert is_valid_date_string(None) is False  # None
        assert is_valid_date_string(123) is False  # Not a string


class TestExtractSymbolsFromBundle:
    """Tests for extract_symbols_from_bundle function."""

    @pytest.mark.unit
    @patch("lib.bundles.utils.Path")
    def test_extract_symbols_bundle_not_found(self, mock_path_class):
        """Test extract_symbols_from_bundle returns empty list when bundle doesn't exist."""
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path_class.home.return_value.__truediv__.return_value.__truediv__.return_value = (
            mock_path
        )

        result = extract_symbols_from_bundle("nonexistent_bundle")
        assert result == []

    @pytest.mark.unit
    @patch("lib.bundles.utils.Path")
    def test_extract_symbols_no_asset_db(self, mock_path_class):
        """Test extract_symbols_from_bundle returns empty list when asset DB not found."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = []  # No ingestion directories
        mock_path_class.home.return_value.__truediv__.return_value.__truediv__.return_value = (
            mock_path
        )

        result = extract_symbols_from_bundle("test_bundle")
        assert result == []


class TestAggregateTo4h:
    """Tests for aggregate_to_4h function."""

    @pytest.mark.unit
    def test_aggregate_to_4h_valid_data(self):
        """Test aggregate_to_4h with valid 1h OHLCV data."""
        # Create 1h data (8 hours = 2 4h bars)
        dates = pd.date_range("2020-01-01 00:00", periods=8, freq="1h", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0],
                "high": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5],
                "low": [99.5, 100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5],
                "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700],
            },
            index=dates,
        )

        result = aggregate_to_4h(df)

        # Should have 2 bars (8 hours / 4 hours)
        assert len(result) == 2
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns

        # First bar: open=100.0, high=max(100.5, 101.5, 102.5, 103.5), close=103.5
        assert result.iloc[0]["open"] == 100.0
        assert result.iloc[0]["close"] == 103.5
        assert result.iloc[0]["volume"] == 4600  # Sum of first 4 hours

    @pytest.mark.unit
    def test_aggregate_to_4h_empty_dataframe(self):
        """Test aggregate_to_4h with empty DataFrame."""
        df = pd.DataFrame()
        result = aggregate_to_4h(df)
        assert result.empty

    @pytest.mark.unit
    def test_aggregate_to_4h_missing_columns(self):
        """Test aggregate_to_4h raises ValueError for missing columns."""
        dates = pd.date_range("2020-01-01 00:00", periods=4, freq="1h", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0],
                "high": [100.5, 101.5, 102.5, 103.5],
                # Missing low, close, volume
            },
            index=dates,
        )

        with pytest.raises(ValueError, match="missing required columns"):
            aggregate_to_4h(df)
