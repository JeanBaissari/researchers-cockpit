"""
Data filtering utilities for FOREX, crypto, and calendar-based processing.

Provides functions to filter and process OHLCV data according to
trading calendar sessions and market-specific requirements.
"""

import logging
from typing import Any

import pandas as pd

from .normalization import fill_data_gaps
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
    
    Wrapper around utils.consolidate_sunday_to_friday with logging support.
    
    Args:
        df: DataFrame with daily OHLCV data (UTC timezone-aware DatetimeIndex)
        calendar_obj: Trading calendar object
        show_progress: Whether to print progress messages
        sid: Symbol ID for logging
        
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


def apply_gap_filling(
    df: pd.DataFrame,
    calendar_obj: Any,
    calendar_name: str,
    show_progress: bool = False,
    symbol: str = ""
) -> pd.DataFrame:
    """
    Apply gap-filling for FOREX and CRYPTO daily data.
    
    Args:
        df: DataFrame with daily OHLCV data
        calendar_obj: Trading calendar object
        calendar_name: Calendar name string (e.g., 'FOREX', 'CRYPTO')
        show_progress: Whether to print progress messages
        symbol: Symbol name for logging
        
    Returns:
        DataFrame with gaps filled
    """
    if df.empty:
        return df
    
    try:
        # Crypto: stricter gap tolerance (3 days), Forex: 5 days
        max_gap = 5 if 'FOREX' in calendar_name.upper() else 3
        df = fill_data_gaps(
            df,
            calendar_obj,
            method='ffill',
            max_gap_days=max_gap
        )
        if show_progress:
            print(f"  Gap-filled {calendar_name} data for {symbol}")
    except Exception as gap_err:
        print(f"Warning: Gap-filling failed for {symbol}: {gap_err}")
        logger.warning(f"Gap-filling failed for {symbol}: {gap_err}")
    
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


# Backward compatibility aliases (private functions with underscore prefix)
_filter_forex_presession_bars = filter_forex_presession_bars
_consolidate_forex_sunday_to_friday = consolidate_forex_sunday_to_friday
_filter_to_calendar_sessions = filter_to_calendar_sessions
_apply_gap_filling = apply_gap_filling
_filter_daily_to_calendar_sessions = filter_daily_to_calendar_sessions

