"""
Test timeframe configuration and validation.

Tests for timeframe-to-interval mapping, data limits, and timeframe validation.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import (
    VALID_TIMEFRAMES,
    VALID_SOURCES,
    TIMEFRAME_TO_YF_INTERVAL,
    TIMEFRAME_DATA_LIMITS,
    get_timeframe_info,
    validate_timeframe_date_range,
    get_minutes_per_day,
)


class TestTimeframeConfiguration:
    """Tests for timeframe configuration and validation."""

    @pytest.mark.unit
    def test_timeframe_to_yf_interval_mapping(self):
        """Verify timeframe to yfinance interval mapping is complete."""
        # Check expected timeframes exist
        expected = ['1m', '5m', '15m', '30m', '1h', 'daily', '1d']
        for tf in expected:
            if tf in VALID_TIMEFRAMES:
                assert tf in TIMEFRAME_TO_YF_INTERVAL, f"Missing timeframe: {tf}"

    @pytest.mark.unit
    def test_timeframe_data_limits(self):
        """Verify data limits are set correctly for each timeframe."""
        # Check intraday limits
        if '1m' in TIMEFRAME_DATA_LIMITS:
            assert TIMEFRAME_DATA_LIMITS.get('1m') is not None
            assert TIMEFRAME_DATA_LIMITS.get('1m') <= 7  # 7 days max for 1m

        if '5m' in TIMEFRAME_DATA_LIMITS:
            assert TIMEFRAME_DATA_LIMITS.get('5m') is not None
            assert TIMEFRAME_DATA_LIMITS.get('5m') <= 60  # 60 days max for 5m

        if '1h' in TIMEFRAME_DATA_LIMITS:
            assert TIMEFRAME_DATA_LIMITS.get('1h') is not None
            assert TIMEFRAME_DATA_LIMITS.get('1h') <= 730  # 730 days max for 1h

    @pytest.mark.unit
    def test_crypto_minutes_per_day(self):
        """Test CRYPTO calendar has 1440 minutes per day."""
        mpd = get_minutes_per_day('CRYPTO')
        assert mpd == 1440

