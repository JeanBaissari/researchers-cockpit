"""
FOREX-specific data filtering utilities.

Provides functions to filter and process FOREX OHLCV data according to
FOREX market-specific requirements (pre-session bars, Sunday consolidation).
"""

import logging
from typing import Any

import pandas as pd

from .forex import consolidate_sunday_to_friday

logger = logging.getLogger(__name__)


def filter_forex_presession_bars(
    df: pd.DataFrame,
    calendar_obj: Any,
    show_progress: bool = False,
    symbol: str = "",
    calendar_name: str = ""  # Not used, for signature compatibility
) -> pd.DataFrame:
    """
    Filter out FOREX pre-session bars (00:00-04:59 UTC).
    
    FOREX sessions span midnight UTC (05:00 UTC to 04:58 UTC next day).
    Bars at 00:00-04:59 UTC on a given date actually belong to the PREVIOUS
    day's session. The minute bar writer creates indices starting at session
    open (05:00 UTC), so pre-session bars cause KeyError.
    
    Args:
        df: DataFrame with UTC timezone-aware DatetimeIndex
        calendar_obj: Trading calendar object
        show_progress: Whether to print progress messages
        symbol: Symbol name for logging
        calendar_name: Not used, for signature compatibility
        
    Returns:
        DataFrame with pre-session bars filtered out
    """
    if df.empty:
        return df
    
    try:
        # Get unique dates in the data
        unique_dates = df.index.normalize().unique()
        valid_mask = pd.Series(True, index=df.index)

        for date_ts in unique_dates:
            try:
                # Get session open for this date
                date_naive = date_ts.tz_convert(None) if date_ts.tz else date_ts
                if date_naive not in calendar_obj.sessions:
                    # Not a trading day, mark all bars for this date as invalid
                    date_bars = df.index.normalize() == date_ts
                    valid_mask[date_bars] = False
                    continue

                session_open = calendar_obj.session_open(date_naive)
                # Ensure session_open is UTC for comparison
                if session_open.tz is None:
                    session_open = session_open.tz_localize('UTC')
                elif str(session_open.tz) != 'UTC':
                    session_open = session_open.tz_convert('UTC')

                # Find bars on this date that are before session open
                date_bars = df.index.normalize() == date_ts
                pre_session = df.index < session_open
                invalid = date_bars & pre_session
                valid_mask[invalid] = False
            except Exception:
                # If we can't get session info, keep the bars
                continue

        excluded = (~valid_mask).sum()
        if excluded > 0:
            if show_progress:
                print(f"  {symbol}: Filtered {excluded} pre-session bars (FOREX 00:00-04:59 UTC)")
            df = df[valid_mask]
    except Exception as forex_err:
        print(f"Warning: FOREX intraday session filtering failed for {symbol}: {forex_err}")
        logger.warning(f"FOREX intraday session filtering failed for {symbol}: {forex_err}")
    
    return df


def consolidate_forex_sunday_to_friday(
    df: pd.DataFrame,
    calendar_obj: Any,
    show_progress: bool = False,
    sid: int = 0,
    calendar_name: str = ""  # Not used, for signature compatibility
) -> pd.DataFrame:
    """
    Consolidate FOREX Sunday bars into the preceding Friday's close.
    
    Wrapper around forex.consolidate_sunday_to_friday with logging support.
    
    Args:
        df: DataFrame with daily OHLCV data (UTC timezone-aware DatetimeIndex)
        calendar_obj: Trading calendar object
        show_progress: Whether to print progress messages
        sid: Symbol ID for logging
        calendar_name: Not used, for signature compatibility
        
    Returns:
        DataFrame with Sunday data consolidated into Friday
    """
    if df.empty:
        return df
    
    # Count Sunday bars before consolidation for logging
    sunday_count = (df.index.dayofweek == 6).sum()
    
    if sunday_count > 0 and show_progress:
        print(f"  SID {sid}: Consolidating {sunday_count} Sunday bars into Friday...")
    
    # Call the utility function to consolidate Sunday into Friday
    result_df = consolidate_sunday_to_friday(df, calendar_obj)
    
    if show_progress and sunday_count > 0:
        new_sunday_count = (result_df.index.dayofweek == 6).sum()
        consolidated = sunday_count - new_sunday_count
        print(f"  SID {sid}: Consolidated {consolidated} Sunday bars into Friday")
    
    return result_df
