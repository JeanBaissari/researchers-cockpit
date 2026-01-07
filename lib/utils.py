"""
Utility functions for The Researcher's Cockpit.

Provides file operations, directory management, YAML handling, and strategy creation utilities.
"""

import shutil
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Any
import pandas as pd # Added pandas import


def get_project_root() -> Path:
    """
    Get the project root directory.

    Uses marker-based discovery for robust root resolution.
    Delegates to lib.paths for the actual implementation.

    Returns:
        Path: Absolute path to project root
    """
    # Import here to avoid circular imports during module loading
    from .paths import get_project_root as _get_project_root
    return _get_project_root()


def ensure_dir(path: Path) -> Path:
    """
    Create directory if it doesn't exist.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path: The directory path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp_dir(base_path: Path, prefix: str) -> Path:
    """
    Create a timestamped directory.
    
    Args:
        base_path: Base directory path
        prefix: Prefix for directory name (e.g., 'backtest', 'optimization')
        
    Returns:
        Path: Path to the created directory
        
    Example:
        >>> timestamp_dir(Path('results/spy_sma'), 'backtest')
        Path('results/spy_sma/backtest_20241220_143022')
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dir_name = f"{prefix}_{timestamp}"
    dir_path = base_path / dir_name
    ensure_dir(dir_path)
    return dir_path


def update_symlink(target: Path, link_path: Path) -> None:
    """
    Create or update a symlink pointing to target.
    
    Args:
        target: Path to the target directory/file
        link_path: Path where the symlink should be created
        
    Raises:
        OSError: If symlink creation fails
    """
    # Remove existing symlink or file if it exists
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    
    # Create new symlink
    link_path.symlink_to(target)
    
    # Verify symlink was created correctly
    if not link_path.exists():
        raise OSError(f"Failed to create symlink {link_path} -> {target}")


def load_yaml(path: Path) -> dict:
    """
    Safely load a YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        dict: Parsed YAML content
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {path}: {e}")


def save_yaml(data: dict, path: Path) -> None:
    """
    Save data to a YAML file with formatting.
    
    Args:
        data: Dictionary to save
        path: Path to save YAML file
        
    Raises:
        OSError: If file write fails
    """
    ensure_dir(path.parent)
    
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)


def get_strategy_path(strategy_name: str, asset_class: Optional[str] = None) -> Path:
    """
    Locate a strategy directory.
    
    Args:
        strategy_name: Name of strategy (e.g., 'spy_sma_cross')
        asset_class: Optional asset class ('crypto', 'forex', 'equities')
                    If None, searches all asset classes
        
    Returns:
        Path: Path to strategy directory
        
    Raises:
        FileNotFoundError: If strategy not found
    """
    root = get_project_root()
    strategies_dir = root / 'strategies'
    
    if asset_class:
        # Direct path
        strategy_path = strategies_dir / asset_class / strategy_name
        if strategy_path.exists():
            return strategy_path
    else:
        # Search all asset classes
        for asset_class in ['crypto', 'forex', 'equities']:
            strategy_path = strategies_dir / asset_class / strategy_name
            if strategy_path.exists():
                return strategy_path
    
    # Not found
    raise FileNotFoundError(
        f"Strategy '{strategy_name}' not found. "
        f"Searched in: {strategies_dir}/*/{strategy_name}"
    )


def create_strategy(
    strategy_name: str,
    asset_class: str,
    from_template: bool = True
) -> Path:
    """
    Create a new strategy directory.
    
    Args:
        strategy_name: Name for the new strategy
        asset_class: Asset class ('crypto', 'forex', 'equities')
        from_template: If True, copy from _template
        
    Returns:
        Path: Path to created strategy directory
        
    Raises:
        ValueError: If strategy already exists
        FileNotFoundError: If template doesn't exist
    """
    root = get_project_root()
    strategy_path = root / 'strategies' / asset_class / strategy_name
    
    if strategy_path.exists():
        raise ValueError(f"Strategy '{strategy_name}' already exists at {strategy_path}")
    
    if from_template:
        template_path = root / 'strategies' / '_template'
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found at {template_path}")
        
        # Copy template
        shutil.copytree(template_path, strategy_path)
    else:
        # Create empty directory
        ensure_dir(strategy_path)
    
    return strategy_path


def create_strategy_from_template(
    name: str,
    asset_class: str,
    asset_symbol: str
) -> Path:
    """
    Create a new strategy from template with asset symbol configured.
    
    This is a convenience function that:
    1. Copies the template
    2. Updates parameters.yaml with asset_symbol
    3. Creates results directory
    4. Creates results symlink
    
    Args:
        name: Strategy name (e.g., 'spy_sma_cross')
        asset_class: Asset class ('crypto', 'forex', 'equities')
        asset_symbol: Asset symbol (e.g., 'SPY', 'BTC-USD')
        
    Returns:
        Path: Path to created strategy directory
    """
    root = get_project_root()
    
    # Create strategy from template
    strategy_path = create_strategy(name, asset_class, from_template=True)
    
    # Update parameters.yaml with asset_symbol
    params_path = strategy_path / 'parameters.yaml'
    if params_path.exists():
        params = load_yaml(params_path)
        if 'strategy' not in params:
            params['strategy'] = {}
        params['strategy']['asset_symbol'] = asset_symbol
        save_yaml(params, params_path)
    
    # Create results directory
    results_dir = root / 'results' / name
    ensure_dir(results_dir)
    
    # Create symlink from strategy to results
    strategy_results_link = strategy_path / 'results'
    update_symlink(results_dir, strategy_results_link)
    
    return strategy_path


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
    calendar: 'TradingCalendar',
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
    import logging
    logger = logging.getLogger(__name__)

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


def check_and_fix_symlinks(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> list[Path]:
    """
    Check and fix broken symlinks within a strategy's results directory.

    Args:
        strategy_name: Name of the strategy
        asset_class: Optional asset class hint for strategy location

    Returns:
        list[Path]: A list of paths to fixed symlinks
    """
    root = get_project_root()
    strategy_path = get_strategy_path(strategy_name, asset_class)
    results_base = root / 'results' / strategy_name

    fixed_links = []

    # Check strategy's own symlink to results
    strategy_results_link = strategy_path / 'results'
    if strategy_results_link.is_symlink() and not strategy_results_link.exists():
        update_symlink(results_base, strategy_results_link)
        fixed_links.append(strategy_results_link)

    # Check the 'latest' symlink in the results base directory
    latest_link = results_base / 'latest'
    if latest_link.is_symlink() and not latest_link.exists():
        # Try to find the latest actual results directory
        subdirs = sorted([d for d in results_base.iterdir() if d.is_dir() and d.name.startswith('backtest_')], reverse=True)
        if subdirs:
            update_symlink(subdirs[0], latest_link)
            fixed_links.append(latest_link)

    return fixed_links


# =============================================================================
# DATA AGGREGATION UTILITIES
# =============================================================================

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
    import numpy as np

    if df.empty:
        return df

    # Normalize timeframe string to pandas offset alias
    timeframe_map = {
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

    target_freq = timeframe_map.get(target_timeframe, target_timeframe)

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
    # Define timeframe hierarchy (in minutes)
    timeframe_minutes = {
        '1m': 1, '2m': 2, '5m': 5, '10m': 10, '15m': 15, '30m': 30,
        '1h': 60, '2h': 120, '4h': 240,
        'daily': 1440, '1d': 1440,
        'weekly': 10080, '1w': 10080,
    }

    source_mins = timeframe_minutes.get(source_timeframe.lower(), 0)
    target_mins = timeframe_minutes.get(target_timeframe.lower(), 0)

    if source_mins == 0 or target_mins == 0:
        raise ValueError(
            f"Unknown timeframe. Source: {source_timeframe}, Target: {target_timeframe}. "
            f"Valid options: {list(timeframe_minutes.keys())}"
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
    target_timeframes: list
) -> dict:
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
    timeframe_minutes = {
        '1m': 1, '2m': 2, '5m': 5, '10m': 10, '15m': 15, '30m': 30,
        '1h': 60, '2h': 120, '4h': 240,
        'daily': 1440, '1d': 1440,
        'weekly': 10080, '1w': 10080,
    }

    base_mins = timeframe_minutes.get(base_tf.lower(), 1)
    target_mins = timeframe_minutes.get(target_tf.lower(), 1)

    if base_mins == 0:
        return 1

    return target_mins // base_mins


# =============================================================================
# FOREX-SPECIFIC UTILITIES
# =============================================================================

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
    validate_ohlcv_columns(df)
    
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
    dropped_sundays = []
    
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

