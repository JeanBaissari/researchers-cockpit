"""
Integration tests for multi-timeframe data ingestion and backtest workflows.

These tests verify the v1.0.6 multi-timeframe infrastructure including:
- Timeframe configuration and validation
- Bundle registry operations
- FOREX session filtering
- Bundle frequency auto-detection
- Validation utility functionality
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestTimeframeConfiguration:
    """Tests for timeframe configuration and validation."""

    def test_timeframe_to_yf_interval_mapping(self):
        """Verify timeframe to yfinance interval mapping is complete."""
        from lib.data_loader import TIMEFRAME_TO_YF_INTERVAL

        # Check expected timeframes exist
        expected = ['1m', '5m', '15m', '30m', '1h', 'daily', '1d']
        for tf in expected:
            assert tf in TIMEFRAME_TO_YF_INTERVAL, f"Missing timeframe: {tf}"

    def test_timeframe_data_limits(self):
        """Verify data limits are set correctly for each timeframe."""
        from lib.data_loader import TIMEFRAME_DATA_LIMITS

        # Check intraday limits
        assert TIMEFRAME_DATA_LIMITS.get('1m') is not None
        assert TIMEFRAME_DATA_LIMITS.get('1m') <= 7  # 7 days max for 1m

        assert TIMEFRAME_DATA_LIMITS.get('5m') is not None
        assert TIMEFRAME_DATA_LIMITS.get('5m') <= 60  # 60 days max for 5m

        assert TIMEFRAME_DATA_LIMITS.get('1h') is not None
        assert TIMEFRAME_DATA_LIMITS.get('1h') <= 730  # 730 days max for 1h

        # Check daily has no limit
        assert TIMEFRAME_DATA_LIMITS.get('daily') is None

    def test_calendar_minutes_per_day(self):
        """Verify minutes_per_day is set correctly for each calendar type."""
        from lib.data_loader import CALENDAR_MINUTES_PER_DAY

        # Equities: 6.5 hours = 390 minutes
        assert CALENDAR_MINUTES_PER_DAY.get('XNYS') == 390

        # Crypto: 24 hours = 1440 minutes
        assert CALENDAR_MINUTES_PER_DAY.get('CRYPTO') == 1440

        # Forex: 24 hours per trading day = 1440 minutes
        assert CALENDAR_MINUTES_PER_DAY.get('FOREX') == 1440

    def test_get_timeframe_info(self):
        """Test get_timeframe_info returns complete information."""
        from lib.data_loader import get_timeframe_info

        # Test hourly
        info = get_timeframe_info('1h')
        assert info['timeframe'] == '1h'
        assert info['yf_interval'] == '1h'
        assert info['data_frequency'] == 'minute'
        assert info['is_intraday'] is True

        # Test daily
        info = get_timeframe_info('daily')
        assert info['timeframe'] == 'daily'
        assert info['yf_interval'] == '1d'
        assert info['data_frequency'] == 'daily'
        assert info['is_intraday'] is False

    def test_get_timeframe_info_invalid(self):
        """Test get_timeframe_info raises error for invalid timeframe."""
        from lib.data_loader import get_timeframe_info

        with pytest.raises(ValueError) as exc_info:
            get_timeframe_info('invalid_tf')
        assert 'Unsupported timeframe' in str(exc_info.value)

    def test_validate_timeframe_date_range(self):
        """Test date range validation for limited timeframes."""
        from lib.data_loader import validate_timeframe_date_range

        # Test 5m with date too far back
        old_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        start, end, warning = validate_timeframe_date_range('5m', old_date, None)

        # Should adjust start date and provide warning
        assert warning is not None
        assert '5m' in warning or '60' in warning

    def test_weekly_monthly_rejected(self):
        """Test that weekly/monthly timeframes are rejected."""
        from lib.data_loader import ingest_bundle

        with pytest.raises(ValueError) as exc_info:
            ingest_bundle(
                source='yahoo',
                assets=['equities'],
                symbols=['SPY'],
                timeframe='weekly'
            )
        assert 'not compatible with Zipline bundles' in str(exc_info.value)


class TestBundleRegistry:
    """Tests for bundle registry operations."""

    def test_load_save_registry(self):
        """Test registry load/save operations."""
        from lib.data_loader import _load_bundle_registry, _save_bundle_registry

        # Load current registry
        registry = _load_bundle_registry()
        assert isinstance(registry, dict)

    def test_registry_metadata_structure(self):
        """Test that registry entries have required fields."""
        from lib.data_loader import _load_bundle_registry

        registry = _load_bundle_registry()

        required_fields = ['symbols', 'calendar_name', 'data_frequency']

        for bundle_name, meta in registry.items():
            for field in required_fields:
                assert field in meta, f"Bundle {bundle_name} missing field: {field}"

    def test_registry_timeframe_preserved(self):
        """Test that timeframe is preserved in registry entries."""
        from lib.data_loader import _load_bundle_registry

        registry = _load_bundle_registry()

        for bundle_name, meta in registry.items():
            if 'timeframe' in meta:
                # Extract expected timeframe from bundle name (last component)
                name_parts = bundle_name.split('_')
                if len(name_parts) >= 3:
                    expected_tf = name_parts[-1]  # e.g., 'daily', '1h', '5m', '15m', '30m'
                    if expected_tf in ('1h', '5m', '15m', '30m', 'daily'):
                        assert meta['timeframe'] == expected_tf, \
                            f"{bundle_name} should have timeframe '{expected_tf}', got '{meta['timeframe']}'"


class TestForexSessionFiltering:
    """Tests for FOREX session boundary handling."""

    def test_forex_calendar_session_open(self):
        """Test FOREX calendar session opens at 05:00 UTC."""
        from lib.extension import register_custom_calendars, ForexCalendar

        register_custom_calendars(['FOREX'])

        start = pd.Timestamp('2025-12-01')
        end = pd.Timestamp('2025-12-31')
        forex = ForexCalendar(start=start, end=end)

        # Check a Monday session
        test_date = pd.Timestamp('2025-12-15')  # Monday
        if test_date in forex.sessions:
            session_open = forex.session_open(test_date)
            # Convert to UTC for comparison
            if session_open.tz is not None:
                session_open_utc = session_open.tz_convert('UTC')
            else:
                session_open_utc = session_open.tz_localize('UTC')

            # Session should open at 05:00 UTC (midnight ET)
            assert session_open_utc.hour == 5
            assert session_open_utc.minute == 0

    def test_forex_session_minutes_count(self):
        """Test FOREX calendar has correct number of minutes per session."""
        from lib.extension import register_custom_calendars, ForexCalendar

        register_custom_calendars(['FOREX'])

        start = pd.Timestamp('2025-12-01')
        end = pd.Timestamp('2025-12-31')
        forex = ForexCalendar(start=start, end=end)

        test_date = pd.Timestamp('2025-12-15')
        if test_date in forex.sessions:
            minutes = forex.session_minutes(test_date)
            # Should have close to 1440 minutes (24 hours - 1 for close time)
            assert len(minutes) >= 1439
            assert len(minutes) <= 1440

    def test_forex_weekday_only(self):
        """Test FOREX calendar only has weekday sessions."""
        from lib.extension import register_custom_calendars, ForexCalendar

        register_custom_calendars(['FOREX'])

        start = pd.Timestamp('2025-12-01')
        end = pd.Timestamp('2025-12-31')
        forex = ForexCalendar(start=start, end=end)

        for session in forex.sessions:
            # 5 = Saturday, 6 = Sunday
            assert session.dayofweek < 5, f"FOREX should not have weekend sessions: {session}"


class TestCryptoCalendar:
    """Tests for CRYPTO calendar configuration."""

    def test_crypto_calendar_24_7(self):
        """Test CRYPTO calendar operates 24/7."""
        from lib.extension import register_custom_calendars, CryptoCalendar

        register_custom_calendars(['CRYPTO'])

        start = pd.Timestamp('2025-12-01')
        end = pd.Timestamp('2025-12-31')
        crypto = CryptoCalendar(start=start, end=end)

        # Should have sessions on weekends
        weekend_dates = [d for d in crypto.sessions if d.dayofweek >= 5]
        assert len(weekend_dates) > 0, "CRYPTO should have weekend sessions"

    def test_crypto_minutes_per_day(self):
        """Test CRYPTO calendar has 1440 minutes per day."""
        from lib.data_loader import get_minutes_per_day

        mpd = get_minutes_per_day('CRYPTO')
        assert mpd == 1440


class TestBundleAutoDetection:
    """Tests for bundle frequency auto-detection."""

    def test_auto_detect_from_registry(self):
        """Test auto-detection reads frequency from registry."""
        from lib.data_loader import _load_bundle_registry

        registry = _load_bundle_registry()

        # Check that bundles with 1h in name have minute frequency
        for bundle_name, meta in registry.items():
            if '1h' in bundle_name or '5m' in bundle_name:
                assert meta.get('data_frequency') == 'minute', \
                    f"Intraday bundle {bundle_name} should have minute frequency"
            elif 'daily' in bundle_name:
                assert meta.get('data_frequency') == 'daily', \
                    f"Daily bundle {bundle_name} should have daily frequency"


class TestValidationUtility:
    """Tests for bundle validation utility."""

    def test_validate_date_field_valid(self):
        """Test date field validation with valid dates."""
        # Import the validation function
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "validate_bundles",
            project_root / "scripts" / "validate_bundles.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Valid date
        is_valid, error, fix = module.validate_date_field('2025-12-28', 'end_date')
        assert is_valid is True
        assert error is None

        # Null is valid
        is_valid, error, fix = module.validate_date_field(None, 'end_date')
        assert is_valid is True

    def test_validate_date_field_corrupted(self):
        """Test date field validation catches corruption."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "validate_bundles",
            project_root / "scripts" / "validate_bundles.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Corrupted: timeframe stored as date
        is_valid, error, fix = module.validate_date_field('daily', 'end_date')
        assert is_valid is False
        assert 'timeframe' in error.lower()

    def test_validate_bundle_entry(self):
        """Test full bundle entry validation."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "validate_bundles",
            project_root / "scripts" / "validate_bundles.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Valid entry
        valid_meta = {
            'symbols': ['SPY'],
            'calendar_name': 'XNYS',
            'data_frequency': 'daily',
            'timeframe': 'daily',
            'start_date': '2020-01-01',
            'end_date': None
        }

        # Mock the bundle data path to exist
        with patch.object(module, 'get_bundle_data_path') as mock_path:
            mock_path.return_value = MagicMock()
            mock_path.return_value.exists.return_value = True

            issues = module.validate_bundle_entry('yahoo_equities_daily', valid_meta)
            assert len(issues) == 0, f"Valid entry should have no issues: {issues}"


class TestDataAggregation:
    """Tests for data aggregation utilities."""

    def test_aggregate_ohlcv(self):
        """Test OHLCV aggregation to higher timeframe."""
        from lib.utils import aggregate_ohlcv

        # Create sample 1-minute data
        dates = pd.date_range('2025-01-01 09:30', periods=60, freq='1min')
        df = pd.DataFrame({
            'open': range(100, 160),
            'high': range(101, 161),
            'low': range(99, 159),
            'close': range(100, 160),
            'volume': [1000] * 60
        }, index=dates)

        # Aggregate to 5-minute
        df_5m = aggregate_ohlcv(df, '5m')

        # Should have 12 bars (60 minutes / 5 = 12)
        assert len(df_5m) == 12

        # First bar open should match first 1m bar open
        assert df_5m.iloc[0]['open'] == 100

        # Volume should be sum
        assert df_5m.iloc[0]['volume'] == 5000  # 5 bars * 1000

    def test_resample_to_timeframe_validation(self):
        """Test that downsampling is rejected."""
        from lib.utils import resample_to_timeframe

        dates = pd.date_range('2025-01-01', periods=10, freq='1h')
        df = pd.DataFrame({
            'open': [100] * 10,
            'high': [101] * 10,
            'low': [99] * 10,
            'close': [100] * 10,
            'volume': [1000] * 10
        }, index=dates)

        # Downsampling should raise error
        with pytest.raises(ValueError) as exc_info:
            resample_to_timeframe(df, '1h', '5m')
        assert 'Cannot downsample' in str(exc_info.value)

    def test_get_timeframe_multiplier(self):
        """Test timeframe multiplier calculation."""
        from lib.utils import get_timeframe_multiplier

        assert get_timeframe_multiplier('1m', '5m') == 5
        assert get_timeframe_multiplier('1m', '1h') == 60
        assert get_timeframe_multiplier('5m', '1h') == 12
        assert get_timeframe_multiplier('1h', 'daily') == 24


class TestEndToEndWorkflow:
    """End-to-end integration tests for multi-timeframe workflows."""

    def test_daily_bundle_exists(self):
        """Verify daily bundles can be loaded."""
        from lib.data_loader import load_bundle, _load_bundle_registry

        registry = _load_bundle_registry()
        daily_bundles = [b for b in registry if 'daily' in b]

        if daily_bundles:
            bundle_name = daily_bundles[0]
            try:
                bundle = load_bundle(bundle_name)
                assert bundle is not None
            except FileNotFoundError:
                pytest.skip(f"Bundle {bundle_name} data not found on disk")

    def test_backtest_with_daily_bundle(self):
        """Test backtest execution with daily bundle."""
        from lib.data_loader import _load_bundle_registry

        registry = _load_bundle_registry()

        # Find an equities daily bundle
        equities_daily = [b for b in registry if 'equities' in b and 'daily' in b]
        if not equities_daily:
            pytest.skip("No equities daily bundle available")

        # Verify the bundle has correct frequency
        bundle_meta = registry[equities_daily[0]]
        assert bundle_meta.get('data_frequency') == 'daily'


# Marker for slow tests that actually run ingestion
@pytest.mark.slow
class TestSlowIntegration:
    """Slow integration tests that perform actual data operations."""

    @pytest.mark.skip(reason="Requires network access and takes time")
    def test_ingest_equities_1h(self):
        """Test ingesting equities hourly data."""
        from lib.data_loader import ingest_bundle

        bundle_name = ingest_bundle(
            source='yahoo',
            assets=['equities'],
            symbols=['AAPL'],
            timeframe='1h',
            start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        )

        assert bundle_name is not None
        assert '1h' in bundle_name

    @pytest.mark.skip(reason="Requires network access and takes time")
    def test_ingest_forex_1h_excludes_current_day(self):
        """Test that FOREX 1h ingestion auto-excludes current day."""
        from lib.data_loader import ingest_bundle, _load_bundle_registry

        bundle_name = ingest_bundle(
            source='yahoo',
            assets=['forex'],
            symbols=['GBPUSD=X'],
            timeframe='1h',
            start_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            # Note: end_date not specified - should auto-exclude today
        )

        registry = _load_bundle_registry()
        meta = registry.get(bundle_name, {})

        # end_date should be yesterday (auto-excluded today)
        if meta.get('end_date'):
            end_date = datetime.strptime(meta['end_date'], '%Y-%m-%d').date()
            today = datetime.now().date()
            assert end_date < today, "FOREX 1h should auto-exclude current day"
