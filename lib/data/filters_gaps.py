"""
Gap-filling utilities for data processing.

Provides functions to apply gap-filling for FOREX and CRYPTO daily data.
"""

import logging
from typing import Any

import pandas as pd

from .normalization import fill_data_gaps

logger = logging.getLogger(__name__)


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
