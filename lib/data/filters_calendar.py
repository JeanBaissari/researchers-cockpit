"""
Calendar-based data filtering utilities.

Provides functions to filter OHLCV data according to trading calendar sessions.
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def filter_to_calendar_sessions(
    df: pd.DataFrame,
    calendar_obj: Any,
    show_progress: bool = False,
    sid: int = 0,
    calendar_name: str = ""  # Not used, for signature compatibility
) -> pd.DataFrame:
    """
    Filter daily data to include only valid calendar sessions.
    
    Args:
        df: DataFrame with daily OHLCV data (UTC timezone-aware DatetimeIndex)
        calendar_obj: Trading calendar object
        show_progress: Whether to print progress messages
        sid: Symbol ID for logging
        calendar_name: Not used, for signature compatibility
        
    Returns:
        DataFrame filtered to valid calendar sessions only
    """
    if df.empty:
        return df
    
    try:
        min_date = df.index.min().normalize()
        max_date = df.index.max().normalize()
        
        # Get all valid trading sessions within the date range
        valid_calendar_sessions = calendar_obj.sessions_in_range(min_date, max_date)
        
        # Ensure both are timezone-naive for accurate comparison, then normalize to midnight
        if valid_calendar_sessions.tz is not None:
            valid_calendar_sessions = valid_calendar_sessions.tz_convert(None).normalize()
        else:
            valid_calendar_sessions = valid_calendar_sessions.normalize()
        
        current_daily_df_dates = df.index.tz_convert(None).normalize() if df.index.tz is not None else df.index.normalize()
        
        # Filter df to keep only those days that are in valid_calendar_sessions
        df = df[current_daily_df_dates.isin(valid_calendar_sessions)]
        
        if df.empty:
            print(f"  Warning: No daily data after calendar filtering for SID {sid}")
    except Exception as cal_err:
        print(f"Warning: Calendar session filtering failed for SID {sid}: {cal_err}")
        logger.warning(f"Calendar session filtering failed for SID {sid}: {cal_err}")
    
    return df


def filter_daily_to_calendar_sessions(
    df: pd.DataFrame,
    calendar_obj: Any,
    show_progress: bool = False,
    symbol: str = ""
) -> pd.DataFrame:
    """
    Filter daily bars to only include valid calendar sessions.
    
    Used for daily data frequency to ensure bars align with trading calendar.
    
    Args:
        df: DataFrame with daily OHLCV data (UTC timezone-aware DatetimeIndex)
        calendar_obj: Trading calendar object
        show_progress: Whether to print progress messages
        symbol: Symbol name for logging
        
    Returns:
        DataFrame filtered to valid calendar sessions
    """
    if df.empty or len(df) == 0:
        return df
    
    try:
        # Convert index bounds to naive timestamps for calendar API
        idx_min = df.index.min()
        idx_max = df.index.max()
        if idx_min.tz is not None:
            idx_min = idx_min.tz_convert(None)
        if idx_max.tz is not None:
            idx_max = idx_max.tz_convert(None)

        calendar_sessions = calendar_obj.sessions_in_range(idx_min, idx_max)

        # Normalize both to naive for comparison
        if hasattr(calendar_sessions, 'tz') and calendar_sessions.tz is not None:
            calendar_sessions_naive = calendar_sessions.tz_convert(None)
        else:
            calendar_sessions_naive = calendar_sessions

        if df.index.tz is not None:
            bars_index_naive = df.index.tz_convert(None)
        else:
            bars_index_naive = df.index

        # Filter bars to only calendar sessions
        valid_mask = bars_index_naive.normalize().isin(calendar_sessions_naive)
        excluded = (~valid_mask).sum()
        df = df[valid_mask]

        if show_progress and excluded > 0:
            print(f"  {symbol}: Filtered {excluded} non-calendar sessions")
    except Exception as cal_err:
        print(f"Warning: Calendar session filtering failed for {symbol}: {cal_err}")
        logger.warning(f"Calendar session filtering failed for {symbol}: {cal_err}")
    
    return df
