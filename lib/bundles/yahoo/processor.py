"""
Yahoo Finance data processor for The Researcher's Cockpit.

Handles OHLCV normalization, timezone handling, gap filling, and volume adjustments.
Extracted from yahoo_bundle.py as part of v1.0.11 refactoring.
"""

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

from ...data.filters import (
    filter_forex_presession_bars,
    consolidate_forex_sunday_to_friday,
    filter_to_calendar_sessions,
    filter_daily_to_calendar_sessions,
    apply_gap_filling,
)
from ..utils import aggregate_to_4h

logger = logging.getLogger(__name__)


def process_yahoo_data(
    hist: pd.DataFrame,
    data_frequency: str,
    calendar_obj: Any,
    calendar_name: str,
    start_date: Optional[str],
    end_date: Optional[str],
    requires_aggregation: bool,
    aggregation_target: Optional[str],
    symbol: str,
    show_progress: bool = False
) -> pd.DataFrame:
    """
    Process Yahoo Finance data for Zipline ingestion.

    Handles:
    - Timestamp normalization (daily vs intraday)
    - 4H aggregation if needed
    - Date filtering
    - Calendar bounds filtering
    - FOREX pre-session filtering
    - Gap filling

    Args:
        hist: Raw DataFrame from yfinance
        data_frequency: 'daily' or 'minute'
        calendar_obj: Trading calendar object
        calendar_name: Calendar name ('XNYS', 'CRYPTO', 'FOREX')
        start_date: User-specified start date (YYYY-MM-DD)
        end_date: User-specified end date (YYYY-MM-DD)
        requires_aggregation: Whether to aggregate (e.g., 1h -> 4h)
        aggregation_target: Target timeframe if aggregating
        symbol: Symbol being processed
        show_progress: Whether to print progress

    Returns:
        Processed DataFrame ready for Zipline writer

    Raises:
        ValueError: If no data remains after processing
    """
    # === TIMESTAMP NORMALIZATION ===
    # Daily: Normalize to midnight UTC
    # Intraday: Keep time-of-day, ensure UTC
    if data_frequency == 'daily':
        if hist.index.tz is not None:
            hist.index = hist.index.tz_convert('UTC').normalize()
        else:
            hist.index = pd.to_datetime(hist.index).normalize().tz_localize('UTC')
    else:
        # Intraday: Keep time-of-day
        if hist.index.tz is not None:
            hist.index = hist.index.tz_convert('UTC')
        else:
            hist.index = pd.to_datetime(hist.index).tz_localize('UTC')

    # === VOLUME HANDLING ===
    # Use float64 for volume to handle large crypto volumes
    volume_data = hist['Volume'].astype('float64')

    # Validate volume exceeds uint32 limits
    max_vol = volume_data.max()
    uint32_max = np.iinfo(np.uint32).max
    if max_vol > uint32_max and show_progress:
        print(f"  {symbol}: Volume exceeds uint32 ({max_vol:.2e}), using float64 storage")

    # Remove NaN/Inf
    if volume_data.isna().any():
        volume_data = volume_data.fillna(0)
    if np.isinf(volume_data).any():
        volume_data = volume_data.replace([np.inf, -np.inf], 0)

    # Create bars DataFrame
    bars_df = pd.DataFrame({
        'open': hist['Open'],
        'high': hist['High'],
        'low': hist['Low'],
        'close': hist['Close'],
        'volume': volume_data,
    }, index=hist.index)

    # === 4H AGGREGATION ===
    if requires_aggregation and aggregation_target == '4h':
        original_count = len(bars_df)
        bars_df = aggregate_to_4h(bars_df)
        if show_progress:
            print(f"  {symbol}: Aggregated {original_count} 1h bars to {len(bars_df)} 4h bars")

    # === USER DATE FILTERING ===
    if start_date:
        user_start = pd.Timestamp(start_date, tz='UTC')
        bars_df = bars_df[bars_df.index >= user_start]
    if end_date:
        user_end = pd.Timestamp(end_date, tz='UTC')
        bars_df = bars_df[bars_df.index <= user_end]

    # === CALENDAR BOUNDS FILTERING ===
    first_calendar_session = calendar_obj.first_session
    if first_calendar_session.tz is None:
        first_calendar_session = first_calendar_session.tz_localize('UTC')
    bars_df = bars_df[bars_df.index >= first_calendar_session]

    # === CALENDAR SESSION FILTERING (daily data) ===
    if data_frequency == 'daily' and len(bars_df) > 0:
        bars_df = filter_daily_to_calendar_sessions(bars_df, calendar_obj, show_progress, symbol)

    # === FOREX PRE-SESSION FILTERING (intraday data) ===
    if data_frequency == 'minute' and 'FOREX' in calendar_name.upper():
        bars_df = filter_forex_presession_bars(bars_df, calendar_obj, show_progress, symbol)

    # Check if we have data after filtering
    if bars_df.empty:
        raise ValueError(f"No data for {symbol} after filtering")

    # === GAP FILLING (daily data only) ===
    if data_frequency == 'daily':
        if 'FOREX' in calendar_name.upper() or 'CRYPTO' in calendar_name.upper():
            bars_df = apply_gap_filling(bars_df, calendar_obj, calendar_name, show_progress, symbol)

    return bars_df


def aggregate_to_daily(minute_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate minute bars to daily bars.

    Args:
        minute_df: DataFrame with minute OHLCV data

    Returns:
        DataFrame with daily OHLCV data
    """
    from ...utils import aggregate_ohlcv
    return aggregate_ohlcv(minute_df, 'daily')
