"""
Utility functions for The Researcher's Cockpit.

Provides file operations, directory management, YAML handling, and strategy creation utilities.
"""

import shutil
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
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
        # Get all sessions from the trading calendar
        sessions = calendar.sessions_in_range(start_date, end_date)

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
            df_reindexed.index = df_reindexed.index.tz_localize(df.index.tz)

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

