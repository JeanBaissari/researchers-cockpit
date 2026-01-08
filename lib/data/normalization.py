"""
Timezone handling and data normalization utilities.

Provides functions for normalizing timestamps to UTC and filling
data gaps according to trading calendars.
"""

import logging
from datetime import datetime
from typing import Union, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from exchange_calendars import ExchangeCalendar

logger = logging.getLogger(__name__)


def normalize_to_utc(dt: Union[pd.Timestamp, datetime, str]) -> pd.Timestamp:
    """
    Normalize a datetime to UTC timezone-naive timestamp.

    Zipline-Reloaded uses UTC internally. All timestamps should be:
    1. Converted to UTC if timezone-aware
    2. Made timezone-naive (Zipline interprets naive as UTC)

    Args:
        dt: Datetime (can be naive, aware, or string)

    Returns:
        Timezone-naive Timestamp in UTC
    """
    ts = pd.Timestamp(dt)

    if ts.tz is not None:
        ts = ts.tz_convert('UTC').tz_localize(None)

    return ts


def normalize_to_calendar_timezone(
    dt: Union[pd.Timestamp, datetime],
    calendar_tz: str = 'America/New_York',
    time_of_day: str = '00:00:00'
) -> pd.Timestamp:
    """DEPRECATED: Use normalize_to_utc() instead."""
    import warnings
    warnings.warn("normalize_to_calendar_timezone is deprecated, use normalize_to_utc", DeprecationWarning)
    return normalize_to_utc(dt)


def fill_data_gaps(
    df: pd.DataFrame,
    calendar: 'ExchangeCalendar',
    method: str = 'ffill',
    max_gap_days: int = 5
) -> pd.DataFrame:
    """
    Fill gaps in OHLCV data to match trading calendar sessions.

    This function is primarily used for FOREX data where Yahoo Finance
    may have inconsistent data coverage that doesn't align with the
    FOREX trading calendar (Mon-Fri 24h).

    Args:
        df: DataFrame with DatetimeIndex and OHLCV columns
        calendar: Trading calendar object (e.g., from get_calendar('FOREX'))
        method: Gap-filling method ('ffill' or 'bfill')
        max_gap_days: Maximum consecutive days to fill (gaps larger than this are logged)

    Returns:
        DataFrame with gaps filled according to calendar sessions

    Notes:
        - Forward-fill preserves last known price (standard forex practice)
        - Volume is set to 0 for synthetic bars (signals no real trades)
        - Gaps exceeding max_gap_days are logged as warnings but still filled
    """
    if df.empty:
        return df

    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.DatetimeIndex(df.index)

    # Get calendar sessions within our data range
    start_date = df.index.min()
    end_date = df.index.max()

    try:
        # Convert to naive timestamps for calendar API (avoids timezone.key error)
        start_naive = start_date.tz_convert(None) if start_date.tz is not None else start_date
        end_naive = end_date.tz_convert(None) if end_date.tz is not None else end_date

        # Get all sessions from the trading calendar
        sessions = calendar.sessions_in_range(start_naive, end_naive)

        if len(sessions) == 0:
            logger.warning(f"No calendar sessions found between {start_date} and {end_date}")
            return df

        # Normalize both to timezone-naive for comparison
        sessions_naive = sessions.tz_localize(None) if sessions.tz is not None else sessions
        df_index_naive = df.index.tz_localize(None) if df.index.tz is not None else df.index

        # Find missing dates
        missing_dates = sessions_naive.difference(df_index_naive.normalize())

        if len(missing_dates) > 0:
            logger.info(f"Found {len(missing_dates)} missing dates, filling gaps...")

            # Check for large gaps
            if len(missing_dates) > 1:
                sorted_missing = missing_dates.sort_values()
                gap_sizes = (sorted_missing[1:] - sorted_missing[:-1]).days
                if hasattr(gap_sizes, 'max') and len(gap_sizes) > 0:
                    max_gap = int(gap_sizes.max()) if hasattr(gap_sizes, 'max') else max_gap_days
                    if max_gap > max_gap_days:
                        logger.warning(
                            f"Large gap detected: {max_gap} consecutive days. "
                            f"This may indicate data source issues."
                        )

        # Reindex to include all calendar sessions
        df_reindexed = df.reindex(sessions_naive)

        # Forward-fill prices
        if method == 'ffill':
            df_reindexed[['open', 'high', 'low', 'close']] = df_reindexed[['open', 'high', 'low', 'close']].ffill()
        elif method == 'bfill':
            df_reindexed[['open', 'high', 'low', 'close']] = df_reindexed[['open', 'high', 'low', 'close']].bfill()

        # Set volume to 0 for filled rows (synthetic bars have no volume)
        if 'volume' in df_reindexed.columns:
            df_reindexed['volume'] = df_reindexed['volume'].fillna(0).astype(int)

        # Restore timezone if original had one
        if df.index.tz is not None:
            # df_reindexed is naive at this point, need to properly restore timezone
            try:
                # First localize to UTC (data is in UTC internally)
                df_reindexed.index = df_reindexed.index.tz_localize('UTC')
                # Then convert to original timezone if different
                original_tz = str(df.index.tz)
                if original_tz != 'UTC':
                    df_reindexed.index = df_reindexed.index.tz_convert(df.index.tz)
            except Exception:
                # Fallback: just localize to original timezone
                try:
                    df_reindexed.index = df_reindexed.index.tz_localize(df.index.tz)
                except Exception:
                    # If all else fails, leave as naive
                    logger.warning("Could not restore timezone, leaving index as naive")

        return df_reindexed

    except Exception as e:
        logger.error(f"Failed to fill data gaps: {e}")
        return df

