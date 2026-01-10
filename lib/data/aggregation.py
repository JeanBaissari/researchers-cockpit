"""
OHLCV data aggregation utilities.

Provides functions for resampling and aggregating time-series data
to different timeframes.
"""

import pandas as pd
from typing import Dict, List


# Timeframe to pandas offset alias mapping
TIMEFRAME_MAP = {
    '1m': '1min', '1min': '1min',
    '2m': '2min', '2min': '2min',
    '5m': '5min', '5min': '5min', '5T': '5min',
    '10m': '10min', '10min': '10min', '10T': '10min',
    '15m': '15min', '15min': '15min', '15T': '15min',
    '30m': '30min', '30min': '30min', '30T': '30min',
    '1h': '1h', '60m': '1h', '1H': '1h',
    '2h': '2h', '2H': '2h',
    '4h': '4h', '4H': '4h',
    'D': '1D', '1d': '1D', 'daily': '1D',
    'W': '1W', '1w': '1W', 'weekly': '1W',
}

# Timeframe hierarchy in minutes
TIMEFRAME_MINUTES = {
    '1m': 1, '2m': 2, '5m': 5, '10m': 10, '15m': 15, '30m': 30,
    '1h': 60, '2h': 120, '4h': 240,
    'daily': 1440, '1d': 1440,
    'weekly': 10080, '1w': 10080,
}


def aggregate_ohlcv(
    df: pd.DataFrame,
    target_timeframe: str,
    method: str = 'standard'
) -> pd.DataFrame:
    """
    Aggregate OHLCV data to a higher timeframe.

    Takes lower-timeframe data (e.g., 1-minute) and aggregates it to
    a higher timeframe (e.g., 5-minute, 15-minute, 1-hour).

    Args:
        df: DataFrame with DatetimeIndex and OHLCV columns (open, high, low, close, volume)
        target_timeframe: Target timeframe string. Options:
            - '5m', '5min', '5T': 5 minutes
            - '15m', '15min', '15T': 15 minutes
            - '30m', '30min', '30T': 30 minutes
            - '1h', '60m', '1H': 1 hour
            - '4h', '4H': 4 hours
            - 'D', '1d', 'daily': Daily
        method: Aggregation method. Currently only 'standard' supported.

    Returns:
        DataFrame with aggregated OHLCV data at target timeframe

    Example:
        >>> # Aggregate 1-minute to 5-minute
        >>> df_5m = aggregate_ohlcv(df_1m, '5m')

        >>> # Aggregate 1-minute to hourly
        >>> df_1h = aggregate_ohlcv(df_1m, '1h')
    """
    if df.empty:
        return df

    # Normalize timeframe string to pandas offset alias
    target_freq = TIMEFRAME_MAP.get(target_timeframe, target_timeframe)

    # Define aggregation rules
    agg_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }

    # Ensure we have the required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Resample and aggregate
    df_agg = df[required_cols].resample(target_freq).agg(agg_rules)

    # Drop rows with NaN values (incomplete periods)
    df_agg = df_agg.dropna()

    return df_agg


def resample_to_timeframe(
    df: pd.DataFrame,
    source_timeframe: str,
    target_timeframe: str
) -> pd.DataFrame:
    """
    Resample OHLCV data from one timeframe to another.

    This is a convenience wrapper around aggregate_ohlcv that validates
    the transformation is valid (can only aggregate up, not down).

    Args:
        df: DataFrame with DatetimeIndex and OHLCV columns
        source_timeframe: Source timeframe (e.g., '1m', '5m')
        target_timeframe: Target timeframe (e.g., '1h', 'daily')

    Returns:
        DataFrame with resampled OHLCV data

    Raises:
        ValueError: If trying to downsample (e.g., 1h to 1m)

    Example:
        >>> df_hourly = resample_to_timeframe(df_minute, '1m', '1h')
    """
    source_mins = TIMEFRAME_MINUTES.get(source_timeframe.lower(), 0)
    target_mins = TIMEFRAME_MINUTES.get(target_timeframe.lower(), 0)

    if source_mins == 0 or target_mins == 0:
        raise ValueError(
            f"Unknown timeframe. Source: {source_timeframe}, Target: {target_timeframe}. "
            f"Valid options: {list(TIMEFRAME_MINUTES.keys())}"
        )

    if target_mins < source_mins:
        raise ValueError(
            f"Cannot downsample from {source_timeframe} to {target_timeframe}. "
            f"Aggregation only works for upsampling (e.g., 1m -> 5m)."
        )

    if target_mins == source_mins:
        return df.copy()  # No change needed

    return aggregate_ohlcv(df, target_timeframe)


def create_multi_timeframe_data(
    df: pd.DataFrame,
    source_timeframe: str,
    target_timeframes: List[str]
) -> Dict[str, pd.DataFrame]:
    """
    Create multiple timeframe views of the same data.

    Useful for multi-timeframe analysis strategies that need to
    reference different timeframes simultaneously.

    Args:
        df: DataFrame with DatetimeIndex and OHLCV columns (source data)
        source_timeframe: Timeframe of source data (e.g., '1m')
        target_timeframes: List of target timeframes (e.g., ['5m', '15m', '1h'])

    Returns:
        Dictionary mapping timeframe to aggregated DataFrame

    Example:
        >>> mtf_data = create_multi_timeframe_data(df_1m, '1m', ['5m', '15m', '1h'])
        >>> df_5m = mtf_data['5m']
        >>> df_1h = mtf_data['1h']
    """
    result = {source_timeframe: df.copy()}

    for tf in target_timeframes:
        if tf != source_timeframe:
            result[tf] = resample_to_timeframe(df, source_timeframe, tf)

    return result


def get_timeframe_multiplier(base_tf: str, target_tf: str) -> int:
    """
    Calculate how many base timeframe bars fit into one target timeframe bar.

    Args:
        base_tf: Base timeframe (e.g., '1m')
        target_tf: Target timeframe (e.g., '5m')

    Returns:
        Integer multiplier (e.g., 5 for 1m->5m, 60 for 1m->1h)

    Example:
        >>> get_timeframe_multiplier('1m', '5m')
        5
        >>> get_timeframe_multiplier('1m', '1h')
        60
    """
    base_mins = TIMEFRAME_MINUTES.get(base_tf.lower(), 1)
    target_mins = TIMEFRAME_MINUTES.get(target_tf.lower(), 1)

    if base_mins == 0:
        return 1

    return target_mins // base_mins





