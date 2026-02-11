"""
Test bundle management functions.

Tests for ingest_bundle function covering validation, source handling,
calendar registration, and error cases.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles.management import ingest_bundle


class TestIngestBundleValidation:
    """Tests for ingest_bundle validation and error handling."""

    @pytest.mark.unit
    def test_ingest_bundle_empty_symbols(self):
        """Test ingest_bundle raises ValueError for empty symbols."""
        with pytest.raises(ValueError, match="symbols parameter is required and cannot be empty"):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=[])

    @pytest.mark.unit
    def test_ingest_bundle_none_symbols(self):
        """Test ingest_bundle raises ValueError for None symbols."""
        with pytest.raises(ValueError, match="symbols parameter is required and cannot be empty"):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=None)

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_invalid_timeframe(self, mock_get_timeframe_info):
        """Test ingest_bundle raises ValueError for invalid timeframe."""
        mock_get_timeframe_info.side_effect = ValueError("Unsupported timeframe: invalid")

        with pytest.raises(ValueError, match="Unsupported timeframe: invalid"):
            ingest_bundle(
                source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="invalid"
            )

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_weekly_timeframe_rejected(self, mock_get_timeframe_info):
        """Test ingest_bundle rejects weekly timeframe."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(
            ValueError, match="Timeframe 'weekly' is not compatible with Zipline bundles"
        ):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="weekly")

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_monthly_timeframe_rejected(self, mock_get_timeframe_info):
        """Test ingest_bundle rejects monthly timeframe."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(
            ValueError, match="Timeframe 'monthly' is not compatible with Zipline bundles"
        ):
            ingest_bundle(
                source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="monthly"
            )

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_unsupported_source(self, mock_get_data_source, mock_get_timeframe_info):
        """Test ingest_bundle raises ValueError for unsupported source."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_get_data_source.side_effect = KeyError("unsupported_source")

        with pytest.raises(ValueError, match="Unsupported data source: unsupported_source"):
            ingest_bundle(source="unsupported_source", assets=["equities"], symbols=["AAPL"])

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_disabled_source(self, mock_get_data_source, mock_get_timeframe_info):
        """Test ingest_bundle raises ValueError for disabled source."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_get_data_source.return_value = {"enabled": False}

        with pytest.raises(ValueError, match="Data source 'yahoo' is not enabled"):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"])


class TestIngestBundleYahoo:
    """Tests for ingest_bundle with Yahoo Finance source."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_success(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test successful Yahoo bundle ingestion."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo",
            assets=["equities"],
            symbols=["AAPL"],
            bundle_name="test_bundle",
            timeframe="daily",
        )

        assert result == "test_bundle"
        mock_register_yahoo.assert_called_once()
        mock_ingest.assert_called_once_with("test_bundle", show_progress=True)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_auto_generated_name(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion with auto-generated bundle name."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="daily"
        )

        assert result == "yahoo_equities_daily"
        mock_register_yahoo.assert_called_once()
        mock_ingest.assert_called_once_with("yahoo_equities_daily", show_progress=True)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_crypto_calendar(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion with crypto assets registers CRYPTO calendar."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo", assets=["crypto"], symbols=["BTC-USD"], timeframe="daily"
        )

        assert result == "yahoo_crypto_daily"
        mock_register_calendars.assert_called_once_with(calendars=["CRYPTO"])
        mock_register_yahoo.assert_called_once()
        # Verify calendar_name was passed as 'CRYPTO'
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["calendar_name"] == "CRYPTO"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_forex_calendar(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion with forex assets registers FOREX calendar."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo", assets=["forex"], symbols=["EURUSD=X"], timeframe="daily"
        )

        assert result == "yahoo_forex_daily"
        mock_register_calendars.assert_called_once_with(calendars=["FOREX"])
        mock_register_yahoo.assert_called_once()
        # Verify calendar_name was passed as 'FOREX'
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["calendar_name"] == "FOREX"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_custom_calendar(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion with custom calendar name."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo",
            assets=["equities"],
            symbols=["AAPL"],
            calendar_name="XNAS",
            timeframe="daily",
        )

        assert result == "yahoo_equities_daily"
        mock_register_yahoo.assert_called_once()
        # Verify custom calendar_name was passed
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["calendar_name"] == "XNAS"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_limited_timeframe_start_date(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion with limited timeframe auto-adjusts start_date."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": 60,
            "data_frequency": "minute",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="5m"
        )

        assert result == "yahoo_equities_5m"
        mock_register_yahoo.assert_called_once()
        # Verify start_date was auto-adjusted
        call_kwargs = mock_register_yahoo.call_args[1]
        assert "start_date" in call_kwargs
        # Start date should be approximately 60 days ago
        start_date = call_kwargs["start_date"]
        expected_date = (datetime.now().date() - timedelta(days=60)).isoformat()
        assert start_date == expected_date

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_forex_intraday_end_date(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion for FOREX intraday auto-excludes current day."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": 60,
            "data_frequency": "minute",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo", assets=["forex"], symbols=["EURUSD=X"], timeframe="1h"
        )

        assert result == "yahoo_forex_1h"
        mock_register_yahoo.assert_called_once()
        # Verify end_date was set to yesterday
        call_kwargs = mock_register_yahoo.call_args[1]
        assert "end_date" in call_kwargs
        end_date = call_kwargs["end_date"]
        expected_date = (datetime.now().date() - timedelta(days=1)).isoformat()
        assert end_date == expected_date

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_force_flag(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion with force flag."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"], force=True)

        assert result == "yahoo_equities_daily"
        mock_register_yahoo.assert_called_once()
        # Verify force flag was passed
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["force"] is True

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_failure(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion handles registration failure."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_register_yahoo.side_effect = Exception("Registration failed")

        with pytest.raises(RuntimeError, match="Failed to ingest Yahoo Finance bundle"):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"])

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_yahoo_ingest_failure(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test Yahoo bundle ingestion handles ingest failure."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_ingest.side_effect = Exception("Ingest failed")

        with pytest.raises(RuntimeError, match="Failed to ingest Yahoo Finance bundle"):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"])


class TestIngestBundleCSV:
    """Tests for ingest_bundle with CSV source."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_not_registered(
        self, mock_get_timeframe_info, mock_bundles, mock_ingest
    ):
        """Test CSV bundle ingestion raises error when bundle not registered."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: False

        with pytest.raises(ValueError, match="CSV bundle 'csv_equities_daily' not registered"):
            ingest_bundle(source="csv", assets=["equities"], symbols=["AAPL"])

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_forex_registers_calendar(
        self,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_bundles,
        mock_ingest,
    ):
        """Test CSV bundle ingestion registers FOREX calendar when auto-detected."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_forex_daily"

        result = ingest_bundle(
            source="csv",
            assets=["forex"],
            symbols=["EURUSD"],
            bundle_name="csv_forex_daily",
            timeframe="daily",
        )

        assert result == "csv_forex_daily"
        mock_register_calendars.assert_called_once_with(calendars=["FOREX"])
        mock_ingest.assert_called_once_with("csv_forex_daily", show_progress=True)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_success(self, mock_get_timeframe_info, mock_bundles, mock_ingest):
        """Test CSV bundle ingestion succeeds when bundle is registered."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_equities_daily"

        result = ingest_bundle(
            source="csv", assets=["equities"], symbols=["AAPL"], bundle_name="csv_equities_daily"
        )

        assert result == "csv_equities_daily"
        mock_ingest.assert_called_once_with("csv_equities_daily", show_progress=True)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_ingest_failure(
        self, mock_get_timeframe_info, mock_bundles, mock_ingest
    ):
        """Test CSV bundle ingestion handles ingest failure."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_equities_daily"
        mock_ingest.side_effect = Exception("Ingest failed")

        with pytest.raises(RuntimeError, match="Failed to ingest CSV bundle"):
            ingest_bundle(
                source="csv",
                assets=["equities"],
                symbols=["AAPL"],
                bundle_name="csv_equities_daily",
            )


class TestIngestBundleUnsupportedSources:
    """Tests for ingest_bundle with unsupported sources."""

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_binance_not_implemented(
        self, mock_get_data_source, mock_get_timeframe_info
    ):
        """Test Binance bundle ingestion raises NotImplementedError."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(
            NotImplementedError, match="Binance bundle ingestion not yet implemented"
        ):
            ingest_bundle(source="binance", assets=["crypto"], symbols=["BTC-USD"])

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_oanda_not_implemented(
        self, mock_get_data_source, mock_get_timeframe_info
    ):
        """Test OANDA bundle ingestion raises NotImplementedError."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(NotImplementedError, match="OANDA bundle ingestion not yet implemented"):
            ingest_bundle(source="oanda", assets=["forex"], symbols=["EURUSD=X"])

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_unknown_source_falls_through_to_final_guard(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
    ):
        """
        Test ingest_bundle rejects unknown sources even if config lookup succeeds.

        This covers the final `else:` guard in ingest_bundle() for non-yahoo/non-csv sources.
        """
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(ValueError, match="Unsupported data source: alphavantage"):
            ingest_bundle(
                source="alphavantage",
                assets=["equities"],
                symbols=["AAPL"],
            )


class TestIngestBundleEdgeCases:
    """Tests for ingest_bundle edge cases and parameter handling."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_custom_dates(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle with custom start and end dates."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo",
            assets=["equities"],
            symbols=["AAPL"],
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        assert result == "yahoo_equities_daily"
        mock_register_yahoo.assert_called_once()
        # Verify custom dates were passed
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["start_date"] == "2020-01-01"
        assert call_kwargs["end_date"] == "2023-12-31"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_timeframe_normalization(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle normalizes timeframe (1d -> daily)."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="1d"
        )

        # Bundle name should use 'daily' not '1d'
        assert result == "yahoo_equities_daily"
        mock_register_yahoo.assert_called_once()
        # Verify timeframe was passed correctly
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["timeframe"] == "1d"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_requires_aggregation(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle handles timeframes requiring aggregation."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": 720,
            "data_frequency": "minute",
            "requires_aggregation": True,
            "yf_interval": "1h",
            "aggregation_target": "4h",
        }

        result = ingest_bundle(
            source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="4h"
        )

        assert result == "yahoo_equities_4h"
        mock_register_yahoo.assert_called_once()
        # Verify timeframe info was passed
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["timeframe"] == "4h"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_forex_intraday_no_end_date_override(
        self, mock_get_timeframe_info, mock_bundles, mock_ingest
    ):
        """Test CSV source does NOT auto-exclude current day for FOREX intraday."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "minute",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_forex_1h"

        result = ingest_bundle(
            source="csv",
            assets=["forex"],
            symbols=["EURUSD"],
            bundle_name="csv_forex_1h",
            timeframe="1h",
            end_date="2025-12-31",  # Custom end date should be preserved (not auto-adjusted for CSV)
        )

        assert result == "csv_forex_1h"
        mock_ingest.assert_called_once_with("csv_forex_1h", show_progress=True)
        # Note: CSV sources don't get end_date auto-adjustment (only API sources do)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_default_start_date(
        self, mock_get_timeframe_info, mock_bundles, mock_ingest
    ):
        """Test CSV bundle ingestion uses default start_date when not provided."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_equities_daily"

        result = ingest_bundle(
            source="csv",
            assets=["equities"],
            symbols=["AAPL"],
            bundle_name="csv_equities_daily",
        )

        assert result == "csv_equities_daily"
        mock_ingest.assert_called_once_with("csv_equities_daily", show_progress=True)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_csv_minute_frequency(
        self, mock_get_timeframe_info, mock_bundles, mock_ingest
    ):
        """Test CSV bundle ingestion with minute frequency."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "minute",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_equities_1h"

        result = ingest_bundle(
            source="csv",
            assets=["equities"],
            symbols=["AAPL"],
            bundle_name="csv_equities_1h",
            timeframe="1h",
        )

        assert result == "csv_equities_1h"
        mock_ingest.assert_called_once_with("csv_equities_1h", show_progress=True)


class TestIngestBundleAssetHandling:
    """Tests for ingest_bundle asset class handling."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_empty_assets_defaults_to_equities(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle defaults to 'equities' when assets list is empty."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(source="yahoo", assets=[], symbols=["AAPL"], timeframe="daily")

        assert result == "yahoo_equities_daily"
        mock_register_yahoo.assert_called_once()
        # Verify calendar_name defaults to XNYS for equities
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["calendar_name"] == "XNYS"

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_multiple_assets_uses_first(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle uses first asset class when multiple provided."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        result = ingest_bundle(
            source="yahoo",
            assets=["crypto", "equities"],
            symbols=["BTC-USD"],
            timeframe="daily",
        )

        # Should use first asset class "crypto"
        assert result == "yahoo_crypto_daily"
        mock_register_calendars.assert_called_once_with(calendars=["CRYPTO"])
        mock_register_yahoo.assert_called_once()
        call_kwargs = mock_register_yahoo.call_args[1]
        assert call_kwargs["calendar_name"] == "CRYPTO"


class TestIngestBundleTimeframeRejection:
    """Tests for timeframe rejection logic."""

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_1wk_timeframe_rejected(self, mock_get_timeframe_info):
        """Test ingest_bundle rejects 1wk timeframe."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(
            ValueError, match="Timeframe '1wk' is not compatible with Zipline bundles"
        ):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="1wk")

    @pytest.mark.unit
    @patch("lib.bundles.management.get_timeframe_info")
    def test_ingest_bundle_1mo_timeframe_rejected(self, mock_get_timeframe_info):
        """Test ingest_bundle rejects 1mo timeframe."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        with pytest.raises(
            ValueError, match="Timeframe '1mo' is not compatible with Zipline bundles"
        ):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"], timeframe="1mo")


class TestIngestBundleLogging:
    """Tests for logging behavior in ingest_bundle."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    @patch("lib.bundles.management.logger")
    def test_ingest_bundle_logs_ingestion_details(
        self,
        mock_logger,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle logs ingestion details."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        ingest_bundle(
            source="yahoo",
            assets=["equities"],
            symbols=["AAPL"],
            bundle_name="test_bundle",
            timeframe="daily",
        )

        # Verify logging calls
        assert mock_logger.info.called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Ingesting yahoo/equities bundle" in str(call) for call in log_calls)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    @patch("lib.bundles.management.logger")
    def test_ingest_bundle_logs_aggregation_warning(
        self,
        mock_logger,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle logs aggregation warning when required."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": 720,
            "data_frequency": "minute",
            "requires_aggregation": True,
            "yf_interval": "1h",
            "aggregation_target": "4h",
        }

        ingest_bundle(
            source="yahoo",
            assets=["equities"],
            symbols=["AAPL"],
            bundle_name="test_bundle",
            timeframe="4h",
        )

        # Verify aggregation warning is logged
        assert mock_logger.info.called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("requires aggregation" in str(call).lower() for call in log_calls)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    @patch("lib.bundles.management.logger")
    def test_ingest_bundle_logs_forex_intraday_exclusion(
        self,
        mock_logger,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle logs FOREX intraday current day exclusion."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": 60,
            "data_frequency": "minute",
            "requires_aggregation": False,
        }

        ingest_bundle(
            source="yahoo",
            assets=["forex"],
            symbols=["EURUSD=X"],
            bundle_name="test_bundle",
            timeframe="1h",
        )

        # Verify FOREX intraday exclusion is logged
        assert mock_logger.info.called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("FOREX intraday" in str(call) for call in log_calls)
        assert any("Auto-excluding current day" in str(call) for call in log_calls)


class TestIngestBundleErrorHandling:
    """Tests for error handling and exception chaining."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    @patch("lib.bundles.management.logger")
    def test_ingest_bundle_logs_exception_on_failure(
        self,
        mock_logger,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle logs exception details on failure."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_register_yahoo.side_effect = Exception("Registration failed")

        with pytest.raises(RuntimeError):
            ingest_bundle(source="yahoo", assets=["equities"], symbols=["AAPL"])

        # Verify exception was logged
        mock_logger.exception.assert_called_once()
        assert "Failed to ingest Yahoo Finance bundle" in str(mock_logger.exception.call_args)

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("zipline.data.bundles.bundles")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.logger")
    def test_ingest_bundle_csv_logs_exception_on_failure(
        self, mock_logger, mock_get_timeframe_info, mock_bundles, mock_ingest
    ):
        """Test CSV bundle ingestion logs exception details on failure."""
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }
        mock_bundles.__contains__ = lambda self, key: key == "csv_equities_daily"
        mock_ingest.side_effect = Exception("Ingest failed")

        with pytest.raises(RuntimeError):
            ingest_bundle(
                source="csv",
                assets=["equities"],
                symbols=["AAPL"],
                bundle_name="csv_equities_daily",
            )

        # Verify exception was logged
        mock_logger.exception.assert_called_once()
        assert "Failed to ingest CSV bundle" in str(mock_logger.exception.call_args)


class TestIngestBundleKwargsPassthrough:
    """Tests for kwargs passthrough to underlying functions."""

    @pytest.mark.unit
    @patch("zipline.data.bundles.ingest")
    @patch("lib.bundles.management.register_yahoo_bundle")
    @patch("lib.bundles.management.register_custom_calendars")
    @patch("lib.bundles.management.get_timeframe_info")
    @patch("lib.bundles.management.get_data_source")
    def test_ingest_bundle_passes_kwargs_to_register_yahoo(
        self,
        mock_get_data_source,
        mock_get_timeframe_info,
        mock_register_calendars,
        mock_register_yahoo,
        mock_ingest,
    ):
        """Test ingest_bundle passes additional kwargs to register_yahoo_bundle."""
        mock_get_data_source.return_value = {"enabled": True}
        mock_get_timeframe_info.return_value = {
            "data_limit_days": None,
            "data_frequency": "daily",
            "requires_aggregation": False,
        }

        ingest_bundle(
            source="yahoo",
            assets=["equities"],
            symbols=["AAPL"],
            bundle_name="test_bundle",
            custom_param="test_value",
        )

        # Verify kwargs were passed (though register_yahoo_bundle may not use them)
        mock_register_yahoo.assert_called_once()
        # The function signature doesn't explicitly accept **kwargs, but Python allows it
        # This test verifies the function doesn't crash with extra kwargs
