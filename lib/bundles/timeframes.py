"""
Timeframe configuration for Zipline bundles.

Defines supported timeframes, their yfinance interval codes,
data retention limits, and utility functions.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# =============================================================================
# TIMEFRAME CONFIGURATION
# =============================================================================

# Supported timeframes with their yfinance interval codes
# NOTE: 4h is NOT natively supported by yfinance - it requires fetching 1h data
# and aggregating. Use aggregate_to_4h() helper when timeframe='4h'.
TIMEFRAME_TO_YF_INTERVAL: Dict[str, str] = {
    '1m': '1m',
    '2m': '2m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '4h': '1h',      # Fetch 1h data, then aggregate to 4h
    'daily': '1d',
    '1d': '1d',
    'weekly': '1wk',
    '1wk': '1wk',
    'monthly': '1mo',
    '1mo': '1mo',
}

# Timeframes that require post-fetch aggregation
# Maps timeframe -> (fetch_interval, aggregation_target)
TIMEFRAMES_REQUIRING_AGGREGATION: Dict[str, str] = {
    '4h': '4h',  # Fetch 1h, aggregate to 4h
}

# Data retention limits for yfinance (in days)
# These are CONSERVATIVE limits - slightly less than Yahoo Finance maximums
# to avoid edge-case rejections from the API
TIMEFRAME_DATA_LIMITS: Dict[str, Optional[int]] = {
    '1m': 6,         # 7 days max, use 6 for safety
    '2m': 55,        # 60 days max, use 55 for safety
    '5m': 55,        # 60 days max, use 55 for safety
    '15m': 55,       # 60 days max, use 55 for safety
    '30m': 55,       # 60 days max, use 55 for safety
    '1h': 720,       # 730 days max, use 720 for safety
    '4h': 720,       # Uses 1h data limit (730 days max)
    'daily': None,   # Unlimited
    '1d': None,      # Unlimited
    'weekly': None,  # Unlimited
    '1wk': None,     # Unlimited
    'monthly': None, # Unlimited
    '1mo': None,     # Unlimited
}

# Zipline data frequency classification
# NOTE: weekly/monthly are NOT compatible with Zipline bundles.
# Zipline's daily bar writer expects data for EVERY trading session.
# Weekly/monthly data should be aggregated from daily data using lib/utils.py
TIMEFRAME_TO_DATA_FREQUENCY: Dict[str, str] = {
    '1m': 'minute',
    '5m': 'minute',
    '15m': 'minute',
    '30m': 'minute',
    '1h': 'minute',   # Zipline treats all sub-daily as 'minute'
    '4h': 'minute',   # Requires aggregation from 1h (yfinance doesn't support 4h)
    'daily': 'daily',
    '1d': 'daily',
    # weekly/monthly removed - use aggregation from daily data instead
}

# Valid timeframes for CLI
VALID_TIMEFRAMES = list(TIMEFRAME_TO_YF_INTERVAL.keys())

# Minutes per day for different calendar types
# This is critical for minute bar writers to correctly index data
CALENDAR_MINUTES_PER_DAY: Dict[str, int] = {
    'XNYS': 390,      # NYSE: 9:30 AM - 4:00 PM = 6.5 hours = 390 minutes
    'XNAS': 390,      # NASDAQ: Same as NYSE
    'CRYPTO': 1440,   # Crypto: 24/7 = 24 * 60 = 1440 minutes
    'FOREX': 1440,    # Forex: 24/5 (but each day is 24 hours)
}


def get_minutes_per_day(calendar_name: str) -> int:
    """
    Get the number of trading minutes per day for a calendar.

    This is required for proper minute bar writer configuration.
    24/7 markets (CRYPTO) and 24/5 markets (FOREX) have 1440 minutes per day.
    Standard equity markets have ~390 minutes (6.5 hours).

    Args:
        calendar_name: Trading calendar name (e.g., 'XNYS', 'CRYPTO', 'FOREX')

    Returns:
        Number of trading minutes per day
    """
    return CALENDAR_MINUTES_PER_DAY.get(calendar_name.upper(), 390)


def get_timeframe_info(timeframe: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a timeframe.

    Args:
        timeframe: Timeframe string (e.g., '1h', 'daily', '5m')

    Returns:
        Dictionary with yf_interval, data_limit_days, data_frequency, is_intraday,
        requires_aggregation, aggregation_target

    Raises:
        ValueError: If timeframe is not supported
    """
    timeframe = timeframe.lower()
    if timeframe not in TIMEFRAME_TO_YF_INTERVAL:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}. "
            f"Valid options: {VALID_TIMEFRAMES}"
        )

    return {
        'timeframe': timeframe,
        'yf_interval': TIMEFRAME_TO_YF_INTERVAL[timeframe],
        'data_limit_days': TIMEFRAME_DATA_LIMITS.get(timeframe),
        'data_frequency': TIMEFRAME_TO_DATA_FREQUENCY.get(timeframe, 'daily'),
        'is_intraday': timeframe not in ('daily', '1d', 'weekly', '1wk', 'monthly', '1mo'),
        'requires_aggregation': timeframe in TIMEFRAMES_REQUIRING_AGGREGATION,
        'aggregation_target': TIMEFRAMES_REQUIRING_AGGREGATION.get(timeframe),
    }


def validate_timeframe_date_range(
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple:
    """
    Validate and adjust date range based on timeframe data limits.

    Args:
        timeframe: Timeframe string
        start_date: Requested start date (YYYY-MM-DD)
        end_date: Requested end date (YYYY-MM-DD)

    Returns:
        Tuple of (adjusted_start_date, adjusted_end_date, warning_message)
    """
    info = get_timeframe_info(timeframe)
    limit_days = info['data_limit_days']
    warning = None

    if limit_days is None:
        # No limit, return as-is
        return start_date, end_date, None

    # Calculate the earliest available date
    today = datetime.now().date()
    earliest_available = today - timedelta(days=limit_days)

    # Parse start_date if provided
    if start_date:
        requested_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        if requested_start < earliest_available:
            warning = (
                f"Warning: {timeframe} data only available for last {limit_days} days. "
                f"Adjusting start_date from {start_date} to {earliest_available.isoformat()}"
            )
            start_date = earliest_available.isoformat()
    else:
        # Default to earliest available for limited timeframes
        start_date = earliest_available.isoformat()

    return start_date, end_date, warning

