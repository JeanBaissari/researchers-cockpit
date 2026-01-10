"""
Utility functions for validation.

Provides helper functions used across validation modules.
"""

import hashlib
from typing import Optional

import pandas as pd


def normalize_dataframe_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame has a proper DatetimeIndex.
    
    Args:
        df: DataFrame to normalize
        
    Returns:
        DataFrame with DatetimeIndex
        
    Raises:
        ValueError: If index cannot be converted to DatetimeIndex
    """
    if isinstance(df.index, pd.DatetimeIndex):
        return df

    try:
        df = df.copy()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        raise ValueError(f"Could not convert index to DatetimeIndex: {e}") from e


def ensure_timezone(
    index: pd.DatetimeIndex,
    tz: str = 'UTC'
) -> pd.DatetimeIndex:
    """
    Ensure DatetimeIndex has a consistent timezone.
    
    Args:
        index: DatetimeIndex to normalize
        tz: Target timezone (default: UTC)
        
    Returns:
        Timezone-aware DatetimeIndex
    """
    if index.tz is None:
        return index.tz_localize(tz)
    return index.tz_convert(tz)


def compute_dataframe_hash(df: pd.DataFrame) -> str:
    """
    Compute a hash of DataFrame contents for integrity checking.
    
    Uses SHA256 for strong collision resistance.
    
    Args:
        df: DataFrame to hash
        
    Returns:
        SHA256 hash string (64 characters)
    """
    hash_values = pd.util.hash_pandas_object(df, index=True)
    combined = hashlib.sha256(hash_values.values.tobytes())
    return combined.hexdigest()


def parse_timeframe(timeframe: Optional[str]) -> Optional[pd.Timedelta]:
    """
    Parse timeframe string to Timedelta.
    
    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')
        
    Returns:
        Corresponding Timedelta or None if unknown
    """
    from .core import TIMEFRAME_INTERVALS
    
    if not timeframe:
        return None
    return TIMEFRAME_INTERVALS.get(timeframe.lower())


def is_intraday_timeframe(timeframe: Optional[str]) -> Optional[bool]:
    """
    Check if timeframe is intraday.
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        True if intraday, False if daily+, None if unknown
    """
    from .core import INTRADAY_TIMEFRAMES
    
    if not timeframe:
        return None
    return timeframe.lower() in INTRADAY_TIMEFRAMES


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero
        
    Returns:
        Result of division or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_z_scores(series: pd.Series) -> pd.Series:
    """
    Calculate z-scores for a series.
    
    Args:
        series: Input series (typically returns)
        
    Returns:
        Series of absolute z-scores
    """
    mean_val = series.mean()
    std_val = series.std()
    
    if std_val == 0 or pd.isna(std_val):
        return pd.Series(0, index=series.index)
    
    return ((series - mean_val) / std_val).abs()





