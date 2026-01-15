"""
FOREX-specific data processing utilities.

Provides functions for handling FOREX market data quirks,
including Sunday bar consolidation.
"""

import logging
from typing import Any, Optional, List

import pandas as pd

logger = logging.getLogger(__name__)


def _validate_ohlcv_columns(df: pd.DataFrame) -> None:
    """
    Validate that DataFrame has required OHLCV columns.

    Args:
        df: DataFrame to validate

    Raises:
        ValueError: If required columns are missing
    """
    required = ['open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {missing}")


def _ensure_naive_utc_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame has a timezone-naive UTC index.

    Converts timezone-aware indices to UTC and then removes timezone info.

    Args:
        df: DataFrame with DatetimeIndex

    Returns:
        DataFrame with timezone-naive index (UTC)
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.DatetimeIndex(df.index)

    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)

    return df


def consolidate_sunday_to_friday(df: pd.DataFrame, calendar_obj: Optional[Any] = None) -> pd.DataFrame:
    """
    Consolidate FOREX Sunday bars into the preceding Friday's close.

    FOREX markets close Friday evening and reopen Sunday evening. Sunday bars
    represent weekend gap activity that should be merged into Friday's bar to
    preserve weekend gap semantics while ensuring Monday starts clean.

    This approach:
    - Updates Friday's close to Sunday's close (captures weekend movement)
    - Updates Friday's high to max(friday_high, sunday_high)
    - Updates Friday's low to min(friday_low, sunday_low)
    - Aggregates Sunday volume into Friday
    - Drops all Sunday rows

    Args:
        df: DataFrame with daily OHLCV data and DatetimeIndex.
            Can be timezone-aware or naive (will be normalized to naive UTC).
        calendar_obj: Optional ExchangeCalendar (for compatibility, not used)

    Returns:
        DataFrame with Sunday data consolidated into Friday.
        Always returns timezone-naive UTC index for Zipline compatibility.

    Example:
        >>> df_forex = consolidate_sunday_to_friday(df_raw)
        >>> # Sunday bars are now merged into Friday, ready for Zipline
    """
    if df.empty:
        return df

    # Validate required columns
    _validate_ohlcv_columns(df)

    # Normalize to naive UTC for consistent processing
    df = _ensure_naive_utc_index(df.copy())
    df.index = df.index.normalize()

    # Identify Sunday bars (dayofweek == 6)
    sunday_mask = df.index.dayofweek == 6
    sunday_count = sunday_mask.sum()

    if sunday_count == 0:
        logger.debug("No Sunday bars to consolidate")
        return df

    logger.info(f"Consolidating {sunday_count} Sunday bars into Friday...")

    # Get all Sunday dates
    sunday_dates = df.index[sunday_mask].tolist()

    consolidated_count = 0
    dropped_sundays: List[pd.Timestamp] = []

    for sunday_date in sunday_dates:
        # Calculate the preceding Friday (Sunday - 2 days)
        friday_date = sunday_date - pd.Timedelta(days=2)

        # Normalize to midnight for index lookup
        friday_normalized = friday_date.normalize()

        # Check if Friday exists in the data
        if friday_normalized not in df.index:
            logger.warning(
                f"No Friday bar found for Sunday {sunday_date.date()}. "
                f"Sunday bar will be dropped without consolidation."
            )
            dropped_sundays.append(sunday_date)
            continue

        # Get Sunday and Friday data
        sunday_row = df.loc[sunday_date]
        friday_row = df.loc[friday_normalized]

        # Update Friday's OHLCV with Sunday's data
        # Close: Use Sunday's close (captures weekend movement)
        df.loc[friday_normalized, 'close'] = sunday_row['close']

        # High: Max of Friday and Sunday highs
        df.loc[friday_normalized, 'high'] = max(friday_row['high'], sunday_row['high'])

        # Low: Min of Friday and Sunday lows
        df.loc[friday_normalized, 'low'] = min(friday_row['low'], sunday_row['low'])

        # Volume: Aggregate Sunday volume into Friday
        df.loc[friday_normalized, 'volume'] = friday_row['volume'] + sunday_row['volume']

        # Mark Sunday for removal
        dropped_sundays.append(sunday_date)
        consolidated_count += 1

    # Drop all Sunday rows
    if dropped_sundays:
        df = df.drop(dropped_sundays)

    logger.info(
        f"Sunday consolidation complete. Consolidated {consolidated_count} bars, "
        f"dropped {len(dropped_sundays)} Sunday rows"
    )

    return df















