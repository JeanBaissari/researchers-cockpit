"""
Data loading and bundle management for The Researcher's Cockpit.

Provides functions to ingest data from various sources into Zipline bundles
and manage cached API responses. Supports multiple timeframes including:
- daily (1d): Full historical data
- 1h: Up to 730 days (yfinance limit)
- 30m, 15m, 5m: Up to 60 days (yfinance limit)
- 1m: Up to 7 days (yfinance limit)
"""

# Standard library imports
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union, Any, Dict

# Third-party imports
import numpy as np
import pandas as pd
import yfinance as yf
from zipline.utils.calendar_utils import get_calendar

# Local imports
from .config import get_data_source, load_settings
from .utils import get_project_root, ensure_dir, fill_data_gaps, normalize_to_utc, aggregate_ohlcv, consolidate_sunday_to_friday
from .data_validation import DataValidator, ValidationConfig

logger = logging.getLogger(__name__)

# =============================================================================
# TIMEFRAME CONFIGURATION
# =============================================================================

# Supported timeframes with their yfinance interval codes
TIMEFRAME_TO_YF_INTERVAL: Dict[str, str] = {
    '1m': '1m',
    '2m': '2m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '4h': '4h',      # Note: yfinance doesn't support 4h natively, requires aggregation
    'daily': '1d',
    '1d': '1d',
    'weekly': '1wk',
    '1wk': '1wk',
    'monthly': '1mo',
    '1mo': '1mo',
}

# Data retention limits for yfinance (in days)
# These are CONSERVATIVE limits - slightly less than Yahoo Finance maximums
# to avoid edge-case rejections from the API
TIMEFRAME_DATA_LIMITS: Dict[str, Optional[int]] = {
    '1m': 6,         # 7 days max, use 6 for safety
    '2m': 55,        # 60 days max, use 55 for safety
    '5m': 55,        # 60 days max, use 55 for safety
    '15m': 55,       # 60 days max, use 55 for safety
    '30m': 55,       # 60 days max, use 55 for safety
    '1h': 720,       # 730 days max, use 720 for safety
    '4h': 55,        # 60 days max (via 1h aggregation)
    'daily': None,   # Unlimited
    '1d': None,      # Unlimited
    'weekly': None,  # Unlimited
    '1wk': None,     # Unlimited
    'monthly': None, # Unlimited
    '1mo': None,     # Unlimited
}

# Zipline data frequency classification
# NOTE: weekly/monthly are NOT compatible with Zipline bundles.
# Zipline's daily bar writer expects data for EVERY trading session.
# Weekly/monthly data should be aggregated from daily data using lib/utils.py
TIMEFRAME_TO_DATA_FREQUENCY: Dict[str, str] = {
    '1m': 'minute',
    '5m': 'minute',
    '15m': 'minute',
    '30m': 'minute',
    '1h': 'minute',   # Zipline treats all sub-daily as 'minute'
    '4h': 'minute',   # Requires aggregation from 1h (yfinance doesn't support 4h)
    'daily': 'daily',
    '1d': 'daily',
    # weekly/monthly removed - use aggregation from daily data instead
}

# Valid timeframes for CLI
VALID_TIMEFRAMES = list(TIMEFRAME_TO_YF_INTERVAL.keys())

# Minutes per day for different calendar types
# This is critical for minute bar writers to correctly index data
CALENDAR_MINUTES_PER_DAY: Dict[str, int] = {
    'XNYS': 390,      # NYSE: 9:30 AM - 4:00 PM = 6.5 hours = 390 minutes
    'XNAS': 390,      # NASDAQ: Same as NYSE
    'CRYPTO': 1440,   # Crypto: 24/7 = 24 * 60 = 1440 minutes
    'FOREX': 1440,    # Forex: 24/5 (but each day is 24 hours)
}

def get_minutes_per_day(calendar_name: str) -> int:
    """
    Get the number of trading minutes per day for a calendar.

    This is required for proper minute bar writer configuration.
    24/7 markets (CRYPTO) and 24/5 markets (FOREX) have 1440 minutes per day.
    Standard equity markets have ~390 minutes (6.5 hours).

    Args:
        calendar_name: Trading calendar name (e.g., 'XNYS', 'CRYPTO', 'FOREX')

    Returns:
        Number of trading minutes per day
    """
    return CALENDAR_MINUTES_PER_DAY.get(calendar_name.upper(), 390)


def get_timeframe_info(timeframe: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a timeframe.

    Args:
        timeframe: Timeframe string (e.g., '1h', 'daily', '5m')

    Returns:
        Dictionary with yf_interval, data_limit_days, data_frequency, is_intraday

    Raises:
        ValueError: If timeframe is not supported
    """
    timeframe = timeframe.lower()
    if timeframe not in TIMEFRAME_TO_YF_INTERVAL:
        raise ValueError(
            f"Unsupported timeframe: {timeframe}. "
            f"Valid options: {VALID_TIMEFRAMES}"
        )

    return {
        'timeframe': timeframe,
        'yf_interval': TIMEFRAME_TO_YF_INTERVAL[timeframe],
        'data_limit_days': TIMEFRAME_DATA_LIMITS.get(timeframe),
        'data_frequency': TIMEFRAME_TO_DATA_FREQUENCY.get(timeframe, 'daily'),
        'is_intraday': timeframe not in ('daily', '1d', 'weekly', '1wk', 'monthly', '1mo'),
    }


def validate_timeframe_date_range(
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple:
    """
    Validate and adjust date range based on timeframe data limits.

    Args:
        timeframe: Timeframe string
        start_date: Requested start date (YYYY-MM-DD)
        end_date: Requested end date (YYYY-MM-DD)

    Returns:
        Tuple of (adjusted_start_date, adjusted_end_date, warning_message)
    """
    info = get_timeframe_info(timeframe)
    limit_days = info['data_limit_days']
    warning = None

    if limit_days is None:
        # No limit, return as-is
        return start_date, end_date, None

    # Calculate the earliest available date
    today = datetime.now().date()
    earliest_available = today - timedelta(days=limit_days)

    # Parse start_date if provided
    if start_date:
        requested_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        if requested_start < earliest_available:
            warning = (
                f"Warning: {timeframe} data only available for last {limit_days} days. "
                f"Adjusting start_date from {start_date} to {earliest_available.isoformat()}"
            )
            start_date = earliest_available.isoformat()
    else:
        # Default to earliest available for limited timeframes
        start_date = earliest_available.isoformat()

    return start_date, end_date, warning


def _is_valid_date_string(date_str: str) -> bool:
    """
    Check if a string is a valid YYYY-MM-DD date.

    Args:
        date_str: String to validate

    Returns:
        True if valid date format, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def _get_bundle_registry_path() -> Path:
    """Get the path to the bundle registry file."""
    return Path.home() / '.zipline' / 'bundle_registry.json'


def _load_bundle_registry() -> dict:
    """Load the bundle registry from disk."""
    registry_path = _get_bundle_registry_path()
    if registry_path.exists():
        try:
            with open(registry_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_bundle_registry(registry: dict) -> None:
    """Save the bundle registry to disk."""
    registry_path = _get_bundle_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)


def _register_bundle_metadata(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily',
    timeframe: str = 'daily'
) -> None:
    """
    Persist bundle metadata to registry file.

    Args:
        bundle_name: Name of the bundle
        symbols: List of symbols in the bundle
        calendar_name: Trading calendar name
        start_date: Start date for data
        end_date: End date for data (actual date string, not the timeframe)
        data_frequency: Zipline data frequency ('daily' or 'minute')
        timeframe: Actual data timeframe ('1m', '5m', '1h', 'daily', etc.)
    """
    registry = _load_bundle_registry()
    registry[bundle_name] = {
        'symbols': symbols,
        'calendar_name': calendar_name,
        'start_date': start_date,
        'end_date': end_date,
        'data_frequency': data_frequency,
        'timeframe': timeframe,
        'registered_at': datetime.now().isoformat()
    }
    _save_bundle_registry(registry)


def get_bundle_path(bundle_name: str) -> Path:
    """
    Get the path where a bundle should be stored.
    
    Args:
        bundle_name: Name of the bundle
        
    Returns:
        Path: Path to bundle directory
    """
    root = get_project_root()
    return root / 'data' / 'bundles' / bundle_name


def list_bundles() -> List[str]:
    """
    List all available Zipline bundles.
    
    Returns:
        list: List of bundle names
    """
    try:
        from zipline.data.bundles import bundles
        return list(bundles.keys())
    except ImportError:
        return []


# Store registered bundles to avoid re-registration
_registered_bundles = set()


def unregister_bundle(bundle_name: str) -> bool:
    """
    Unregister a bundle from Zipline's registry.

    This removes the bundle registration from Zipline's in-memory registry,
    allowing it to be re-registered with new parameters. Does not delete
    the bundle data from disk.

    Args:
        bundle_name: Name of the bundle to unregister

    Returns:
        True if bundle was unregistered, False if it wasn't registered
    """
    from zipline.data.bundles import bundles, unregister as zipline_unregister

    if bundle_name in bundles:
        zipline_unregister(bundle_name)
        _registered_bundles.discard(bundle_name)
        return True
    return False


# =============================================================================
# CSV COLUMN NORMALIZATION
# =============================================================================

def _normalize_csv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CSV column names to lowercase standard format.
    
    Handles various column naming conventions:
    - Title case: Open, High, Low, Close, Volume
    - Uppercase: OPEN, HIGH, LOW, CLOSE, VOLUME
    - Mixed case: open, HIGH, Close, etc.
    - With prefixes: Adj Close, Adj_Close, adjusted_close
    
    Args:
        df: DataFrame with potentially non-standard column names
        
    Returns:
        DataFrame with normalized lowercase column names
        
    Raises:
        ValueError: If required OHLCV columns cannot be identified
    """
    # Create a mapping from original to normalized names
    column_mapping = {}
    
    # Define patterns for each required column
    column_patterns = {
        'open': [r'^open$', r'^o$'],
        'high': [r'^high$', r'^h$'],
        'low': [r'^low$', r'^l$'],
        'close': [r'^close$', r'^c$', r'^adj[_\s]?close$', r'^adjusted[_\s]?close$'],
        'volume': [r'^volume$', r'^vol$', r'^v$'],
    }
    
    # Track which columns we've found
    found_columns = {}
    
    for target_name, patterns in column_patterns.items():
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for pattern in patterns:
                if re.match(pattern, col_lower):
                    if target_name not in found_columns:
                        found_columns[target_name] = col
                        column_mapping[col] = target_name
                    break
            if target_name in found_columns:
                break
    
    # Check for missing required columns
    required = {'open', 'high', 'low', 'close', 'volume'}
    missing = required - set(found_columns.keys())
    
    if missing:
        raise ValueError(
            f"CSV missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Expected: open, high, low, close, volume (case-insensitive)"
        )
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Keep only the required columns (drop any extras like 'Dividends', 'Stock Splits')
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    return df


def _parse_csv_filename(filename: str, symbol: str, timeframe: str) -> tuple:
    """
    Parse CSV filename to extract date range using flexible regex patterns.
    
    Supports multiple filename formats:
    - EURUSD_1h_20200102-050000_20250717-030000_ready.csv
    - EURUSD_1h_20200102_20250717_ready.csv
    - EURUSD_1h_2020-01-02_2025-07-17.csv
    - EURUSD_1h.csv (no dates in filename)
    
    Args:
        filename: CSV filename (without path)
        symbol: Expected symbol name
        timeframe: Expected timeframe
        
    Returns:
        Tuple of (start_date: pd.Timestamp or None, end_date: pd.Timestamp or None)
    """
    # Remove extension
    stem = Path(filename).stem
    
    # Pattern 1: SYMBOL_TIMEFRAME_YYYYMMDD-HHMMSS_YYYYMMDD-HHMMSS_suffix
    # Example: EURUSD_1h_20200102-050000_20250717-030000_ready
    pattern1 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{8})(?:-\d{6})?_'  # Start date with optional time
        r'(\d{8})(?:-\d{6})?'   # End date with optional time
        r'(?:_\w+)?$'           # Optional suffix like _ready
    )
    
    # Pattern 2: SYMBOL_TIMEFRAME_YYYY-MM-DD_YYYY-MM-DD
    # Example: EURUSD_1h_2020-01-02_2025-07-17
    pattern2 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{4}-\d{2}-\d{2})_'  # Start date
        r'(\d{4}-\d{2}-\d{2})'   # End date
        r'(?:_\w+)?$'            # Optional suffix
    )
    
    # Pattern 3: SYMBOL_TIMEFRAME_YYYYMMDD_YYYYMMDD
    # Example: EURUSD_1h_20200102_20250717
    pattern3 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{8})_'              # Start date
        r'(\d{8})'               # End date
        r'(?:_\w+)?$'            # Optional suffix
    )
    
    # Try each pattern
    for pattern in [pattern1, pattern2, pattern3]:
        match = pattern.match(stem)
        if match:
            start_str, end_str = match.groups()
            
            # Parse dates based on format
            try:
                if '-' in start_str:
                    # YYYY-MM-DD format
                    start_date = pd.Timestamp(start_str, tz='UTC')
                    end_date = pd.Timestamp(end_str, tz='UTC')
                else:
                    # YYYYMMDD format
                    start_date = pd.Timestamp(
                        f"{start_str[:4]}-{start_str[4:6]}-{start_str[6:8]}", 
                        tz='UTC'
                    )
                    end_date = pd.Timestamp(
                        f"{end_str[:4]}-{end_str[4:6]}-{end_str[6:8]}", 
                        tz='UTC'
                    )
                
                # Normalize start to beginning of day, end to end of day
                start_date = start_date.normalize()
                end_date = end_date.normalize() + pd.Timedelta(days=1, seconds=-1)
                
                return start_date, end_date
            except Exception as e:
                logger.warning(f"Failed to parse dates from filename {filename}: {e}")
                continue
    
    # No pattern matched - return None for both dates
    logger.info(f"Could not parse dates from filename {filename}. Using full file range.")
    return None, None


# =============================================================================
# SHARED FOREX/CRYPTO PROCESSING HELPERS
# =============================================================================

def _filter_forex_presession_bars(df: pd.DataFrame, calendar_obj, show_progress: bool = False, symbol: str = "") -> pd.DataFrame:
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


def _consolidate_forex_sunday_to_friday(df: pd.DataFrame, calendar_obj, show_progress: bool = False, sid: int = 0) -> pd.DataFrame:
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


def _filter_to_calendar_sessions(df: pd.DataFrame, calendar_obj, show_progress: bool = False, sid: int = 0) -> pd.DataFrame:
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


def _apply_gap_filling(df: pd.DataFrame, calendar_obj, calendar_name: str, show_progress: bool = False, symbol: str = "") -> pd.DataFrame:
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


def _filter_daily_to_calendar_sessions(df: pd.DataFrame, calendar_obj, show_progress: bool = False, symbol: str = "") -> pd.DataFrame:
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


def _register_csv_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    timeframe: str,
    asset_class: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force: bool = False
):
    """
    Register a local CSV data bundle for ingestion.
    This function expects CSV files to be located in:
    data/processed/{timeframe}/{symbol}_{timeframe}_{start_date}-{end_date}_ready.csv
    
    Expected CSV columns: Date, Open, High, Low, Close, Volume
    """
    from zipline.data.bundles import register, bundles
    
    if bundle_name in bundles:
        if force:
            unregister_bundle(bundle_name)
        else:
            logger.info(f"Bundle {bundle_name} already registered. Use --force to re-ingest.")
            return

    # Capture closure variables for the ingest function
    closure_start_date = start_date
    closure_end_date = end_date
    closure_timeframe = timeframe
    closure_calendar_name = calendar_name

    def make_csv_ingest(symbols_list):
        mpd = get_minutes_per_day(closure_calendar_name)
        
        @register(bundle_name, calendar_name=closure_calendar_name, minutes_per_day=mpd)
        def csv_ingest(environ, asset_db_writer, minute_bar_writer,
                         daily_bar_writer, adjustment_writer, calendar,
                         start_session, end_session, cache, show_progress, timestamp):
            """CSV bundle ingest function."""
            
            # Get calendar object inside ingest function (consistent with Yahoo pattern)
            calendar_obj = get_calendar(closure_calendar_name)
            
            # Use user-specified start/end dates from closure, converted to UTC
            start_date_utc = pd.Timestamp(closure_start_date, tz='UTC').normalize() if closure_start_date else None
            end_date_utc = pd.Timestamp(closure_end_date, tz='UTC').normalize() if closure_end_date else None

            if show_progress:
                print(f"Ingesting {closure_timeframe} data for {len(symbols_list)} symbols from local CSVs...")

            # Initialize data validator for CSV data quality checks
            config = ValidationConfig(timeframe=closure_timeframe)
            data_validator = DataValidator(config=config)

            # Get Zipline data frequency from timeframe info
            tf_info = get_timeframe_info(closure_timeframe)
            data_frequency = tf_info['data_frequency']

            def data_gen():
                local_data_path = get_project_root() / 'data' / 'processed' / closure_timeframe
                if not local_data_path.is_dir():
                    raise FileNotFoundError(f"Local CSV data directory not found: {local_data_path}")

                successful_fetches = 0
                for sid, symbol in enumerate(symbols_list):
                    try:
                        # Use glob to find files matching the pattern
                        # e.g., EURUSD_1h_20200102-050000_20250717-030000_ready.csv
                        file_pattern = f"{symbol}_{closure_timeframe}_*.csv"
                        matching_files = list(local_data_path.glob(file_pattern))

                        if not matching_files:
                            print(f"Warning: No CSV file found for {symbol} with pattern '{file_pattern}' in {local_data_path}")
                            continue
                        
                        # Assuming only one matching file for now, or pick the first one
                        csv_file = matching_files[0] 
                        
                        # Parse dates from filename using flexible regex
                        file_start_date, file_end_date = _parse_csv_filename(
                            csv_file.name, symbol, closure_timeframe
                        )

                        df = pd.read_csv(
                            csv_file,
                            parse_dates=[0],
                            index_col=0,
                        )
                        
                        if df.empty:
                            print(f"Warning: Empty data for {symbol} from {csv_file}.")
                            continue

                        # === COLUMN NORMALIZATION ===
                        # Normalize column names to lowercase standard format
                        try:
                            df = _normalize_csv_columns(df)
                        except ValueError as col_err:
                            print(f"Error: {col_err}")
                            logger.error(f"Column normalization failed for {symbol}: {col_err}")
                            continue

                        # === DATA VALIDATION HOOK ===
                        # Validate CSV data quality before ingestion
                        if show_progress:
                            print(f"  Validating data for {symbol}...")
                        
                        validation_result = data_validator.validate(df, asset_name=symbol)
                        
                        if not validation_result.passed:
                            # Log validation errors
                            error_checks = validation_result.error_checks[:5]
                            error_summary = "; ".join([
                                f"{check.details.get('field', check.name)}: {check.message}" 
                                for check in error_checks
                            ])
                            if len(validation_result.error_checks) > 5:
                                error_summary += f" ... and {len(validation_result.error_checks) - 5} more errors"
                            
                            print(f"  Error: Data validation failed for {symbol}: {error_summary}")
                            logger.error(f"CSV data validation failed for {symbol}: {error_summary}")
                            print(f"  Error: Validation failed for {symbol}. Skipping symbol.")
                            continue
                        else:
                            if show_progress:
                                print(f"  ✓ Data validation passed for {symbol}")
                        
                        # Log any warnings even if validation passed
                        if validation_result.warning_checks:
                            warning_summary = "; ".join([
                                check.message for check in validation_result.warning_checks[:3]
                            ])
                            if len(validation_result.warning_checks) > 3:
                                warning_summary += f" ... and {len(validation_result.warning_checks) - 3} more warnings"
                            logger.info(f"Data validation warnings for {symbol}: {warning_summary}")

                        # Ensure timezone-aware UTC index
                        df.index = pd.to_datetime(df.index, utc=True)
                        
                        # Determine the effective start and end dates for filtering:
                        # If user provided start_date/end_date, use those. Otherwise, use dates from filename.
                        effective_start_date = pd.Timestamp(closure_start_date, tz='UTC') if closure_start_date else file_start_date
                        effective_end_date = pd.Timestamp(closure_end_date, tz='UTC') if closure_end_date else file_end_date

                        # Apply effective date filtering
                        if effective_start_date is not None:
                            df = df[df.index >= effective_start_date]
                        if effective_end_date is not None:
                            df = df[df.index <= effective_end_date]

                        # === CALENDAR BOUNDS FILTERING ===
                        # Align data to calendar first session
                        first_calendar_session = calendar_obj.first_session
                        if first_calendar_session.tz is None:
                            first_calendar_session = first_calendar_session.tz_localize('UTC')
                        df = df[df.index >= first_calendar_session]

                        # === FOREX PRE-SESSION FILTERING (for intraday data) ===
                        if data_frequency == 'minute' and 'FOREX' in closure_calendar_name.upper():
                            df = _filter_forex_presession_bars(df, calendar_obj, show_progress, symbol)

                        # === CALENDAR SESSION FILTERING (for daily data) ===
                        if data_frequency == 'daily' and len(df) > 0:
                            df = _filter_daily_to_calendar_sessions(df, calendar_obj, show_progress, symbol)

                        # === GAP-FILLING FOR FOREX AND CRYPTO (daily data only) ===
                        if data_frequency == 'daily':
                            if 'FOREX' in closure_calendar_name.upper() or 'CRYPTO' in closure_calendar_name.upper():
                                df = _apply_gap_filling(df, calendar_obj, closure_calendar_name, show_progress, symbol)

                        # Prepare DataFrame with required columns
                        bars_df = pd.DataFrame({
                            'open': df['open'],
                            'high': df['high'],
                            'low': df['low'],
                            'close': df['close'],
                            'volume': df['volume'],
                        }, index=df.index)

                        if bars_df.empty:
                            print(f"Warning: No data for {symbol} after date filtering.")
                            continue

                        successful_fetches += 1
                        yield sid, bars_df

                    except Exception as e:
                        print(f"Error processing CSV data for {symbol}: {e}")
                        logger.exception(f"Error processing CSV data for {symbol}")
                        continue
                
                if successful_fetches == 0:
                    raise RuntimeError(
                        f"No CSV data was successfully loaded for any symbol. "
                        f"Symbols attempted: {symbols_list}. "
                        f"Check that CSV files exist in data/processed/{closure_timeframe}/ and are correctly formatted."
                    )

            if data_frequency == 'minute':
                # For intraday bundles, we need to write BOTH minute and daily bars.
                # Step 1: Collect all minute data (generator can only be consumed once)
                if show_progress:
                    print("  Collecting minute data for aggregation...")
                all_minute_data = list(data_gen())

                if not all_minute_data:
                    raise RuntimeError("No minute data was collected. Check symbol validity and date range.")

                # Step 2: Build asset metadata from collected data
                # This ensures start/end dates are accurate (not NaT)
                asset_data_list = []
                for sid, minute_df in all_minute_data:
                    symbol = symbols_list[sid]
                    first_trade = minute_df.index.min().normalize()
                    last_trade = minute_df.index.max().normalize()
                    asset_data_list.append({
                        'sid': sid,
                        'symbol': symbol,
                        'asset_name': symbol,
                        'start_date': first_trade,
                        'end_date': last_trade,
                        'exchange': 'CSV',
                        'country_code': 'XX',
                    })
                assets_df = pd.DataFrame(asset_data_list).set_index('sid')
                asset_db_writer.write(equities=assets_df)

                # Step 3: Write minute bars
                if show_progress:
                    print(f"  Writing {len(all_minute_data)} symbol(s) to minute bar writer...")
                minute_bar_writer.write(iter(all_minute_data), show_progress=show_progress)

                # Step 4: Aggregate minute data to daily and write to daily bar writer
                if show_progress:
                    print("  Aggregating minute data to daily bars...")

                def daily_data_gen():
                    """Generator that yields aggregated daily data from minute data."""
                    for sid, minute_df in all_minute_data:
                        try:
                            daily_df = aggregate_ohlcv(minute_df, 'daily')
                            if daily_df.empty:
                                print(f"  Warning: No daily data after aggregating minute data for SID {sid}")
                                continue
                            # Ensure UTC timezone and normalize to midnight
                            if daily_df.index.tz is not None:
                                daily_df.index = daily_df.index.tz_convert('UTC').normalize()
                            else:
                                daily_df.index = daily_df.index.tz_localize('UTC').normalize()

                            # === FOREX SUNDAY CONSOLIDATION ===
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = _consolidate_forex_sunday_to_friday(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            # === CALENDAR SESSION FILTERING ===
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = _filter_to_calendar_sessions(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            yield sid, daily_df
                        except Exception as agg_err:
                            print(f"  Warning: Failed to aggregate daily data for SID {sid}: {agg_err}")
                            logger.exception(f"Failed to aggregate daily data for SID {sid}")
                            continue

                daily_bar_writer.write(daily_data_gen(), show_progress=show_progress)

                if show_progress:
                    print("  ✓ Both minute and daily bars written successfully")
            else:
                # Daily data frequency
                # Step 1: Collect all daily data
                if show_progress:
                    print("  Collecting daily data...")
                all_daily_data = list(data_gen())

                if not all_daily_data:
                    raise RuntimeError("No daily data was collected. Check symbol validity and date range.")

                # Step 2: Build asset metadata from collected data
                asset_data_list = []
                for sid, daily_df in all_daily_data:
                    symbol = symbols_list[sid]
                    first_trade = daily_df.index.min().normalize()
                    last_trade = daily_df.index.max().normalize()
                    asset_data_list.append({
                        'sid': sid,
                        'symbol': symbol,
                        'asset_name': symbol,
                        'start_date': first_trade,
                        'end_date': last_trade,
                        'exchange': 'CSV',
                        'country_code': 'XX',
                    })
                assets_df = pd.DataFrame(asset_data_list).set_index('sid')
                asset_db_writer.write(equities=assets_df)

                # Step 3: Write daily bars
                daily_bar_writer.write(iter(all_daily_data), show_progress=show_progress)

            adjustment_writer.write(splits=None, dividends=None, mergers=None)
        
        return csv_ingest
    
    make_csv_ingest(symbols)
    _registered_bundles.add(bundle_name)

    _register_bundle_metadata(
        bundle_name=bundle_name,
        symbols=symbols,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        data_frequency=get_timeframe_info(timeframe)['data_frequency'],
        timeframe=timeframe
    )


def _register_yahoo_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str = 'XNYS',

    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily',
    timeframe: str = 'daily',
    force: bool = False
):
    """
    Register a Yahoo Finance bundle with multi-timeframe support.

    Args:
        bundle_name: Name for the bundle
        symbols: List of symbols to ingest
        calendar_name: Trading calendar name
        start_date: Start date for data (YYYY-MM-DD)
        end_date: End date for data (YYYY-MM-DD)
        data_frequency: Zipline data frequency ('daily' or 'minute')
        timeframe: Actual timeframe for yfinance ('1m', '5m', '15m', '1h', 'daily', etc.)
        force: If True, unregister and re-register even if already registered
    """
    from zipline.data.bundles import register, bundles

    # Check if already registered
    if bundle_name in bundles:
        if force:
            unregister_bundle(bundle_name)
        else:
            return

    # Validate and adjust date range based on timeframe limits for Yahoo Finance
    adjusted_start_date, adjusted_end_date, warning = validate_timeframe_date_range(
        timeframe, start_date, end_date
    )
    if warning:
        logger.warning(warning)
        print(warning)

    # Get yfinance interval from timeframe
    yf_interval = TIMEFRAME_TO_YF_INTERVAL.get(timeframe.lower(), '1d')

    # Capture closure variables explicitly
    closure_start_date = adjusted_start_date
    closure_end_date = adjusted_end_date
    closure_data_frequency = data_frequency
    closure_timeframe = timeframe
    closure_yf_interval = yf_interval
    closure_calendar_name = calendar_name

    # Store symbols for this bundle (needed for the ingest function)
    # Use closure to capture symbols
    def make_yahoo_ingest(symbols_list):
        # CRITICAL: Use exchange_calendars code, not common name
        # Zipline-reloaded uses exchange_calendars library codes:
        # - 'XNYS' (NYSE)
        # - 'XNAS' (NASDAQ)
        # - '24/7' (Crypto - always open)
        # calendar_name should already be in exchange_calendars format

        # Get minutes_per_day for the calendar type
        # CRITICAL: This must be set correctly for minute bar writers
        # 24/7 markets (CRYPTO) need 1440, standard markets use 390
        mpd = get_minutes_per_day(closure_calendar_name)

        @register(bundle_name, calendar_name=closure_calendar_name, minutes_per_day=mpd)
        def yahoo_ingest(environ, asset_db_writer, minute_bar_writer,
                         daily_bar_writer, adjustment_writer, calendar,
                         start_session, end_session, cache, show_progress, timestamp):
            """Yahoo Finance bundle ingest function.

            Args:
                environ: Environment variables
                asset_db_writer: Asset database writer
                minute_bar_writer: Minute bar writer
                daily_bar_writer: Daily bar writer
                adjustment_writer: Adjustment writer
                calendar: Trading calendar
                start_session: Start session timestamp
                end_session: End session timestamp
                cache: Cache object
                show_progress: Whether to show progress
                timestamp: Bundle timestamp string
            """
            # Get calendar object inside ingest function for consistency
            calendar_obj = get_calendar(closure_calendar_name)
            
            # Convert start/end sessions to timezone-aware UTC at midnight
            # Per Zipline patterns: dates must be pd.Timestamp with tz='utc'
            def to_utc_midnight(ts):
                """Convert timestamp to midnight UTC, timezone-aware."""
                if ts is None:
                    return None
                # Convert to UTC if timezone-aware
                if hasattr(ts, 'tz') and ts.tz is not None:
                    ts = ts.tz_convert('UTC')
                # Normalize to midnight and ensure UTC timezone
                return pd.Timestamp(ts.date(), tz='UTC')

            start_date_utc = to_utc_midnight(start_session)
            end_date_utc = to_utc_midnight(end_session)

            # Create asset metadata DataFrame with SID as index
            # CRITICAL: Pass dates as lists to ensure datetime64[ns] dtype (not datetime64[s])
            # Pandas 2.x creates datetime64[s] for broadcasted single values, but Zipline
            # expects nanoseconds when reading back via pd.Timestamp(..., unit='ns')
            n_symbols = len(symbols_list)
            equities_data = {
                'symbol': symbols_list,
                'asset_name': symbols_list,  # Use symbol as name for now'
                'start_date': [start_date_utc] * n_symbols,   # List for datetime64[ns]
                'end_date': [end_date_utc] * n_symbols,       # List for datetime64[ns]
                'exchange': ['NYSE' if closure_calendar_name == 'XNYS' else ('NASDAQ' if closure_calendar_name == 'XNAS' else 'NYSE')] * n_symbols,
                'country_code': ['US'] * n_symbols,  # Add country code column
            }
            equities_df = pd.DataFrame(equities_data, index=pd.Index(range(n_symbols), name='sid'))
            asset_db_writer.write(equities=equities_df)

            # Fetch data from Yahoo Finance
            if show_progress:
                print(f"Fetching {closure_timeframe} data for {len(symbols_list)} symbols from Yahoo Finance...")
                if closure_data_frequency == 'minute':
                    print(f"  Using minute bar writer (yfinance interval: {closure_yf_interval})")

            # Download data and prepare for writing
            def data_gen():
                # Use the yf_interval from closure (set based on timeframe)
                current_yf_interval = closure_yf_interval

                # Track successful fetches for validation
                successful_fetches = 0

                for sid, symbol in enumerate(symbols_list):
                    try:
                        ticker = yf.Ticker(symbol)
                        # CRITICAL: Use user-specified dates from closure, not Zipline's session dates
                        # For intraday data (1h, 5m, etc.), yfinance has strict date limits
                        # The closure_start_date/closure_end_date are the user's intended range
                        if closure_start_date:
                            yf_start = pd.Timestamp(closure_start_date).to_pydatetime()
                        else:
                            yf_start = start_date_utc.tz_localize(None).to_pydatetime() if start_date_utc else None

                        if closure_end_date:
                            yf_end = pd.Timestamp(closure_end_date).to_pydatetime()
                        else:
                            yf_end = None  # Let yfinance use today

                        hist = ticker.history(start=yf_start, end=yf_end, interval=current_yf_interval)

                        if hist.empty:
                            print(f"Warning: No data for {symbol} at {closure_timeframe} timeframe.")
                            continue

                        # Timestamp handling depends on data frequency:
                        # - Daily data: Normalize to midnight UTC (Zipline expectation)
                        # - Intraday data (minute, hourly): Keep time-of-day, just ensure UTC
                        if closure_data_frequency == 'daily':
                            # Per Zipline patterns: daily bar data must be at midnight UTC
                            if hist.index.tz is not None:
                                hist.index = hist.index.tz_convert('UTC').normalize()
                            else:
                                hist.index = pd.to_datetime(hist.index).normalize().tz_localize('UTC')
                        else:
                            # Intraday data: Keep time-of-day information, ensure UTC
                            if hist.index.tz is not None:
                                hist.index = hist.index.tz_convert('UTC')
                            else:
                                hist.index = pd.to_datetime(hist.index).tz_localize('UTC')

                        # Prepare DataFrame with required columns
                        # Use float64 for volume to handle large crypto volumes
                        # uint32 max is ~4.29B, insufficient for BTC daily volumes
                        volume_data = hist['Volume'].astype('float64')

                        # Validate and log if volume exceeds uint32 limits
                        max_vol = volume_data.max()
                        uint32_max = np.iinfo(np.uint32).max
                        if max_vol > uint32_max:
                            if show_progress:
                                print(f"  {symbol}: Volume exceeds uint32 ({max_vol:.2e}), using float64 storage")

                        # Verify no NaN/Inf after conversion
                        if volume_data.isna().any():
                            volume_data = volume_data.fillna(0)
                        if np.isinf(volume_data).any():
                            volume_data = volume_data.replace([np.inf, -np.inf], 0)

                        bars_df = pd.DataFrame({
                            'open': hist['Open'],
                            'high': hist['High'],
                            'low': hist['Low'],
                            'close': hist['Close'],
                            'volume': volume_data,
                        }, index=hist.index)

                        # === USER-SPECIFIED DATE FILTERING ===
                        # Filter to user-specified date range (from closure)
                        if closure_start_date:
                            user_start = pd.Timestamp(closure_start_date, tz='UTC')
                            bars_df = bars_df[bars_df.index >= user_start]
                        if closure_end_date:
                            user_end = pd.Timestamp(closure_end_date, tz='UTC')
                            bars_df = bars_df[bars_df.index <= user_end]

                        # === CALENDAR BOUNDS FILTERING ===
                        # Align data to calendar first session
                        first_calendar_session = calendar_obj.first_session
                        if first_calendar_session.tz is None:
                            first_calendar_session = first_calendar_session.tz_localize('UTC')
                        bars_df = bars_df[bars_df.index >= first_calendar_session]

                        # === CALENDAR SESSION FILTERING (for daily data) ===
                        if closure_data_frequency == 'daily' and len(bars_df) > 0:
                            bars_df = _filter_daily_to_calendar_sessions(bars_df, calendar_obj, show_progress, symbol)

                        # === FOREX PRE-SESSION FILTERING (for intraday data) ===
                        if closure_data_frequency == 'minute' and 'FOREX' in closure_calendar_name.upper():
                            bars_df = _filter_forex_presession_bars(bars_df, calendar_obj, show_progress, symbol)

                        # Check if we have any data left after filtering
                        if bars_df.empty:
                            print(f"Warning: No data for {symbol} after date/calendar filtering.")
                            continue

                        # === GAP-FILLING FOR FOREX AND CRYPTO (daily data only) ===
                        if closure_data_frequency == 'daily':
                            if 'FOREX' in closure_calendar_name.upper() or 'CRYPTO' in closure_calendar_name.upper():
                                bars_df = _apply_gap_filling(bars_df, calendar_obj, closure_calendar_name, show_progress, symbol)

                        successful_fetches += 1
                        yield sid, bars_df

                    except Exception as e:
                        print(f"Error fetching {closure_timeframe} data for {symbol}: {e}")
                        logger.exception(f"Error fetching {closure_timeframe} data for {symbol}")
                        continue

                # Validate that at least some data was fetched
                if successful_fetches == 0:
                    raise RuntimeError(
                        f"No data was successfully fetched for any symbol. "
                        f"Symbols attempted: {symbols_list}. "
                        f"Check that symbols are valid and date range has data."
                    )
            
            if closure_data_frequency == 'minute':
                # For intraday bundles, we need to write BOTH minute and daily bars.
                # Zipline's internal operations (benchmark, history window, Pipeline API)
                # require valid daily bar data even when running minute-frequency backtests.
                # Without daily bars, the daily_bar_reader has NaT for first_trading_day,
                # causing: AttributeError: 'NaTType' object has no attribute 'normalize'

                # Step 1: Collect all minute data (generator can only be consumed once)
                if show_progress:
                    print("  Collecting minute data for aggregation...")
                all_minute_data = list(data_gen())

                if not all_minute_data:
                    raise RuntimeError("No minute data was collected. Check symbol validity and date range.")

                # Step 2: Write minute bars
                if show_progress:
                    print(f"  Writing {len(all_minute_data)} symbol(s) to minute bar writer...")
                minute_bar_writer.write(iter(all_minute_data), show_progress=show_progress)

                # Step 3: Aggregate minute data to daily and write to daily bar writer
                # This ensures the daily bar reader has valid data for Zipline's internal operations
                if show_progress:
                    print("  Aggregating minute data to daily bars...")

                def daily_data_gen():
                    """Generator that yields aggregated daily data from minute data."""
                    for sid, minute_df in all_minute_data:
                        try:
                            # Aggregate minute bars to daily
                            daily_df = aggregate_ohlcv(minute_df, 'daily')

                            if daily_df.empty:
                                print(f"  Warning: No daily data after aggregating minute data for SID {sid}")
                                continue

                            # Ensure UTC timezone and normalize to midnight
                            # This needs to happen BEFORE shifting, as shifting operates on dates
                            if daily_df.index.tz is None:
                                daily_df.index = daily_df.index.tz_localize('UTC')
                            elif str(daily_df.index.tz) != 'UTC':
                                daily_df.index = daily_df.index.tz_convert('UTC')
                            daily_df.index = daily_df.index.normalize() # Normalize to midnight UTC

                            # === FOREX SUNDAY CONSOLIDATION ===
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = _consolidate_forex_sunday_to_friday(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            # === CALENDAR SESSION FILTERING ===
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = _filter_to_calendar_sessions(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            yield sid, daily_df
                        except Exception as agg_err:
                            print(f"  Warning: Failed to aggregate daily data for SID {sid}: {agg_err}")
                            logger.exception(f"Failed to aggregate daily data for SID {sid}")
                            continue

                daily_bar_writer.write(daily_data_gen(), show_progress=show_progress)

                if show_progress:
                    print("  ✓ Both minute and daily bars written successfully")
            else:
                daily_bar_writer.write(data_gen(), show_progress=show_progress)

            # Write empty adjustments (no splits/dividends for now)
            # Pass None instead of empty DataFrames to avoid column validation issues
            adjustment_writer.write(splits=None, dividends=None, mergers=None)
        
        return yahoo_ingest
    
    make_yahoo_ingest(symbols)
    _registered_bundles.add(bundle_name)

    # Persist bundle metadata to registry file (include timeframe for reconstruction)
    _register_bundle_metadata(
        bundle_name=bundle_name,
        symbols=symbols,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        data_frequency=data_frequency,
        timeframe=timeframe
    )


def ingest_bundle(
    source: str,
    assets: List[str],
    bundle_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    timeframe: str = 'daily',
    force: bool = False,
    **kwargs
) -> str:
    """
    Ingest data from a source into a Zipline bundle.

    This function creates or updates Zipline data bundles that serve as the
    primary data source for both `handle_data` and the Zipline Pipeline API.
    Supports multiple timeframes with automatic data limit validation.

    Args:
        source: Data source name ('yahoo', 'binance', 'oanda')
        assets: List of asset classes (['crypto'], ['forex'], ['equities'])
        bundle_name: Custom bundle name. Auto-generated as {source}_{asset}_{timeframe} if not provided
        symbols: List of symbols to ingest (required)
        start_date: Start date (YYYY-MM-DD). Adjusted automatically for limited timeframes
        end_date: End date (YYYY-MM-DD). Defaults to today
        calendar_name: Trading calendar ('XNYS', 'CRYPTO', 'FOREX'). Auto-detected from asset class
        timeframe: Data timeframe. Options:
            - '1m': 1-minute (7 days max)
            - '5m': 5-minute (60 days max)
            - '15m': 15-minute (60 days max)
            - '30m': 30-minute (60 days max)
            - '1h': 1-hour (730 days max)
            - 'daily' or '1d': Daily (unlimited)
            - 'weekly' or '1wk': Weekly (unlimited)
        force: If True, unregister and re-register the bundle even if already registered.
            Required for re-ingestion with updated parameters.

    Returns:
        Bundle name string

    Raises:
        ValueError: If symbols empty, source not supported, or timeframe invalid
        RuntimeError: If ingestion fails

    Example:
        >>> ingest_bundle('yahoo', ['equities'], symbols=['SPY'], timeframe='1h')
        'yahoo_equities_1h'
    """
    if symbols is None or len(symbols) == 0:
        raise ValueError("symbols parameter is required and cannot be empty")

    # Validate timeframe
    timeframe = timeframe.lower()
    try:
        tf_info = get_timeframe_info(timeframe)
    except ValueError as e:
        raise ValueError(str(e))

    # Reject weekly/monthly - they're not compatible with Zipline bundles
    # Zipline's daily bar writer expects data for EVERY trading session
    if timeframe in ('weekly', '1wk', 'monthly', '1mo'):
        raise ValueError(
            f"Timeframe '{timeframe}' is not compatible with Zipline bundles. "
            f"Zipline's daily bar writer expects data for every trading session. "
            f"For weekly/monthly data, ingest daily data and use lib/utils.py "
            f"aggregation functions (aggregate_ohlcv, resample_to_timeframe)."
        )

    # Get source config
    try:
        source_config = get_data_source(source)
    except KeyError:
        raise ValueError(
            f"Unsupported data source: {source}. "
            f"Supported sources: yahoo, binance, oanda, csv"
        )

    if not source_config.get('enabled', False):
        raise ValueError(f"Data source '{source}' is not enabled in config/data_sources.yaml")


    # Determine asset class (needed for logging and calendar auto-detection)
    asset_class = assets[0] if assets else 'equities'

    # Auto-generate bundle name with timeframe suffix
    if bundle_name is None:
        # Normalize timeframe for bundle name (daily -> daily, 1d -> daily, etc.)
        tf_normalized = {
            '1d': 'daily', '1wk': 'weekly', '1mo': 'monthly'
        }.get(timeframe, timeframe)
        bundle_name = f"{source}_{asset_class}_{tf_normalized}"

    # Auto-detect calendar using canonical names
    if calendar_name is None:
        if 'crypto' in assets:
            calendar_name = 'CRYPTO'
        elif 'forex' in assets:
            calendar_name = 'FOREX'
        else:
            calendar_name = 'XNYS'

    # Register custom calendars if needed
    if calendar_name in ['CRYPTO', 'FOREX']:
        from .extension import register_custom_calendars
        register_custom_calendars(calendars=[calendar_name])

    # Set default start date based on timeframe if not already set
    if start_date is None:
        if tf_info['data_limit_days']:
            # For limited timeframes, use max available range
            earliest = datetime.now().date() - timedelta(days=tf_info['data_limit_days'])
            start_date = earliest.isoformat()
        else:
            start_date = '2020-01-01'

    # Get the Zipline data frequency (daily or minute)
    data_frequency = tf_info['data_frequency']

    # Validate timeframe compatibility with calendar
    if data_frequency == 'minute' and calendar_name in ('XNYS', 'XNAS') and timeframe not in TIMEFRAME_TO_YF_INTERVAL:
        # This is a defensive check; TIMEFRAME_TO_YF_INTERVAL should always contain intraday timeframes
        # that map to 'minute' frequency. If somehow a minute timeframe slips through
        # that is not explicitly defined in TIMEFRAME_TO_YF_INTERVAL, it's an issue.
        raise ValueError(
            f"Incompatible timeframe '{timeframe}' with calendar '{calendar_name}'. "
            f"Minute frequency data requires a supported intraday timeframe. "
            f"Please check TIMEFRAME_TO_YF_INTERVAL configuration."
        )

    # === AUTO-EXCLUDE CURRENT DAY FOR FOREX INTRADAY ===
    # FOREX sessions span midnight UTC (05:00 UTC to 04:58 UTC next day).
    # Current-day data from yfinance includes incomplete session data that
    # can cause indexing errors. Auto-exclude current day for safety.
    if calendar_name == 'FOREX' and data_frequency == 'minute' and end_date is None:
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        logger.info(
            f"FOREX intraday: Auto-excluding current day. "
            f"Setting end_date to {yesterday} to avoid incomplete session data."
        )
        print(f"Note: FOREX intraday data excludes current day (end_date set to {yesterday})")
        end_date = yesterday

    # Log ingestion details
    logger.info(
        f"Ingesting {source}/{asset_class} bundle: {bundle_name} "
        f"(timeframe={timeframe}, frequency={data_frequency})"
    )

    # Register and ingest Yahoo Finance bundle
    if source == 'yahoo':
        try:
            # Register bundle (will skip if already registered unless force=True)
            _register_yahoo_bundle(
                bundle_name=bundle_name,
                symbols=symbols,
                calendar_name=calendar_name,
                start_date=start_date,
                end_date=end_date,
                data_frequency=data_frequency,
                timeframe=timeframe,  # Pass actual timeframe for yfinance interval
                force=force
            )

            # Ingest the bundle
            from zipline.data.bundles import ingest
            ingest(bundle_name, show_progress=True)

            return bundle_name

        except Exception as e:
            logger.exception(f"Failed to ingest Yahoo Finance bundle: {bundle_name}")
            raise RuntimeError(f"Failed to ingest Yahoo Finance bundle: {e}") from e

    elif source == 'binance':
        raise NotImplementedError("Binance bundle ingestion not yet implemented")

    elif source == 'oanda':
        raise NotImplementedError("OANDA bundle ingestion not yet implemented")

    elif source == 'csv':
        try:
            _register_csv_bundle(
                bundle_name=bundle_name,
                symbols=symbols,
                calendar_name=calendar_name,
                timeframe=timeframe,
                asset_class=asset_class,
                start_date=start_date,
                end_date=end_date,
                force=force
            )
            from zipline.data.bundles import ingest
            ingest(bundle_name, show_progress=True)
            return bundle_name
        except Exception as e:
            logger.exception(f"Failed to ingest local CSV bundle: {bundle_name}")
            raise RuntimeError(f"Failed to ingest local CSV bundle: {e}") from e

    else:
        raise ValueError(
            f"Unsupported data source: {source}. "
            f"Supported sources: yahoo, binance, oanda, csv"
        )


def load_bundle(bundle_name: str) -> Any:
    """
    Verify that a bundle exists and is loadable.

    For dynamically registered bundles (like yahoo_equities_daily), this will
    attempt to re-register them if they're not in the registry but data exists.
    This uses a persistent bundle registry file to restore bundle metadata
    across Python sessions.
    
    This bundle serves as the primary data source for both `handle_data` and the
    Zipline Pipeline API.

    Args:
        bundle_name: Name of bundle to check

    Returns:
        BundleData: Bundle data object from Zipline

    Raises:
        FileNotFoundError: If bundle doesn't exist
        RuntimeError: If bundle loading fails
    """
    from zipline.data.bundles import load, bundles
    import os

    # Check if bundle is registered
    if bundle_name not in bundles:
        # First, check the persistent bundle registry for metadata
        registry = _load_bundle_registry()
        
        if bundle_name in registry:
            # Re-register using persisted metadata
            bundle_meta = registry[bundle_name]
            calendar_name = bundle_meta.get('calendar_name', 'XNYS')
            symbols = bundle_meta.get('symbols', [])
            start_date = bundle_meta.get('start_date')
            end_date = bundle_meta.get('end_date')
            data_frequency = bundle_meta.get('data_frequency', 'daily')
            timeframe = bundle_meta.get('timeframe', 'daily')

            # Register custom calendars if needed
            if calendar_name in ['CRYPTO', 'FOREX']:
                from .extension import register_custom_calendars
                register_custom_calendars(calendars=[calendar_name])

            # Re-register the bundle with full metadata (preserves timeframe)
            _register_yahoo_bundle(
                bundle_name=bundle_name,
                symbols=symbols,
                calendar_name=calendar_name,
                start_date=start_date,
                end_date=end_date,
                data_frequency=data_frequency,
                timeframe=timeframe
            )
        elif bundle_name.startswith('yahoo_'):
            # Fallback: Check if bundle data exists on disk
            bundle_data_path = Path.home() / '.zipline' / 'data' / bundle_name
            if bundle_data_path.exists():
                # Infer calendar from bundle name
                if 'crypto' in bundle_name:
                    calendar_name = 'CRYPTO'
                    # Register CRYPTO calendar first
                    from .extension import register_custom_calendars
                    register_custom_calendars(calendars=['CRYPTO'])
                elif 'forex' in bundle_name:
                    calendar_name = 'FOREX'
                    from .extension import register_custom_calendars
                    register_custom_calendars(calendars=['FOREX'])
                else:
                    calendar_name = 'XNYS'

                # Try to extract symbols from the asset database
                symbols = _extract_symbols_from_bundle(bundle_name)
                
                if symbols:
                    # Re-register with extracted symbols
                    _register_yahoo_bundle(
                        bundle_name=bundle_name,
                        symbols=symbols,
                        calendar_name=calendar_name
                    )
                else:
                    # Register a no-op ingest function - data already exists on disk
                    from zipline.data.bundles import register

                    @register(bundle_name, calendar_name=calendar_name)
                    def noop_ingest(environ, asset_db_writer, minute_bar_writer,
                                    daily_bar_writer, adjustment_writer, calendar,
                                    start_session, end_session, cache, show_progress, timestamp):
                        """No-op ingest for already ingested bundle."""
                        pass

                    _registered_bundles.add(bundle_name)
            else:
                raise FileNotFoundError(
                    f"Bundle '{bundle_name}' not found. "
                    f"Please ensure the bundle is ingested. You can try running: "
                    f"python scripts/ingest_data.py --source <YOUR_SOURCE> --symbols <YOUR_SYMBOLS> --bundle-name {bundle_name}"
                )
        else:
            raise FileNotFoundError(
                f"Bundle '{bundle_name}' not found. "
                f"Please ensure the bundle is ingested. You can try running: "
                f"python scripts/ingest_data.py --source <YOUR_SOURCE> --symbols <YOUR_SYMBOLS> --bundle-name {bundle_name}"
            )

    try:
        bundle_data = load(bundle_name)
        return bundle_data
    except Exception as e:
        logger.exception(f"Failed to load bundle '{bundle_name}'")
        raise RuntimeError(f"Failed to load bundle '{bundle_name}': {e}") from e


def _extract_symbols_from_bundle(bundle_name: str) -> List[str]:
    """
    Extract symbol list from an existing bundle's SQLite asset database.

    Args:
        bundle_name: Name of the bundle

    Returns:
        List of symbols, or empty list if extraction fails
    """
    import sqlite3

    bundle_data_path = Path.home() / '.zipline' / 'data' / bundle_name
    if not bundle_data_path.exists():
        return []

    # Find the most recent ingestion directory
    ingestion_dirs = sorted(bundle_data_path.glob('*'), reverse=True)
    for ingestion_dir in ingestion_dirs:
        asset_db_path = ingestion_dir / 'assets-8.sqlite'
        if not asset_db_path.exists():
            # Try older versions
            for version in range(7, 0, -1):
                asset_db_path = ingestion_dir / f'assets-{version}.sqlite'
                if asset_db_path.exists():
                    break

        if asset_db_path.exists():
            try:
                conn = sqlite3.connect(str(asset_db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT symbol FROM equity_symbol_mappings")
                symbols = [row[0] for row in cursor.fetchall()]
                conn.close()
                if symbols:
                    return list(set(symbols))  # Remove duplicates
            except (sqlite3.Error, Exception) as e:
                logger.warning(f"Failed to extract symbols from {asset_db_path}: {e}")
                continue

    return []


def get_bundle_symbols(bundle_name: str) -> List[str]:
    """
    Get the list of symbols available in a bundle.

    This function first checks the bundle registry for persisted metadata,
    then falls back to extracting symbols from the bundle's SQLite database.

    Args:
        bundle_name: Name of the bundle (e.g., 'yahoo_equities_daily')

    Returns:
        List of symbol strings available in the bundle

    Raises:
        FileNotFoundError: If bundle doesn't exist

    Example:
        >>> symbols = get_bundle_symbols('yahoo_equities_daily')
        >>> print(symbols)
        ['SPY', 'AAPL', 'GOOGL']
    """
    # First check the persistent bundle registry
    registry = _load_bundle_registry()
    if bundle_name in registry:
        symbols = registry[bundle_name].get('symbols', [])
        if symbols:
            return symbols

    # Fall back to extracting from SQLite database
    symbols = _extract_symbols_from_bundle(bundle_name)
    if symbols:
        return symbols

    # Check if bundle data directory exists at all
    bundle_data_path = Path.home() / '.zipline' / 'data' / bundle_name
    if not bundle_data_path.exists():
        raise FileNotFoundError(
            f"Bundle '{bundle_name}' not found. "
            f"Run: python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS> --bundle-name {bundle_name}"
        )

    # Bundle exists but couldn't extract symbols - return empty list with warning
    logger.warning(
        f"Could not extract symbols from bundle '{bundle_name}'. "
        f"Bundle may be empty or corrupted."
    )
    return []


def cache_api_data(
    source: str,
    symbols: List[str],
    start_date: str,
    end_date: Optional[str] = None
) -> Path:
    """
    Cache API response data to disk.
    
    Args:
        source: Data source name
        symbols: List of symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD) or None for today
        
    Returns:
        Path: Path to cached file
    """
    root = get_project_root()
    cache_dir = root / 'data' / 'cache'
    ensure_dir(cache_dir)
    
    # Generate cache filename
    date_str = datetime.now().strftime('%Y%m%d')
    symbols_str = '_'.join(symbols[:3])  # First 3 symbols
    if len(symbols) > 3:
        symbols_str += f"_and_{len(symbols)-3}_more"
    
    cache_file = cache_dir / f"{source}_{symbols_str}_{date_str}.parquet"
    
    # Fetch and cache data
    if source == 'yahoo':
        try:
            data_list = []
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                hist['symbol'] = symbol
                data_list.append(hist)
            
            if data_list:
                combined = pd.concat(data_list)
                combined.to_parquet(cache_file)
                return cache_file
        except Exception as e:
            logger.exception(f"Failed to cache Yahoo Finance data")
            raise RuntimeError(f"Failed to cache Yahoo Finance data: {e}") from e
    
    raise ValueError(f"Caching not implemented for source: {source}")


def clear_cache(older_than_days: int = 7) -> int:
    """
    Clean expired cache files.
    
    Args:
        older_than_days: Delete files older than this many days
        
    Returns:
        int: Number of files deleted
    """
    root = get_project_root()
    cache_dir = root / 'data' / 'cache'
    
    if not cache_dir.exists():
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=older_than_days)
    deleted_count = 0
    
    for cache_file in cache_dir.glob('*.parquet'):
        if cache_file.stat().st_mtime < cutoff_date.timestamp():
            cache_file.unlink()
            deleted_count += 1
    
    return deleted_count


# Auto-register yahoo_equities_daily bundle if data exists (for MVP)
def _auto_register_yahoo_bundle_if_exists():
    """Auto-register yahoo_equities_daily bundle if data was ingested."""
    import logging

    zipline_data_dir = Path.home() / '.zipline' / 'data' / 'yahoo_equities_daily'
    if not zipline_data_dir.exists():
        return

    try:
        from zipline.data.bundles import bundles
        if 'yahoo_equities_daily' not in bundles:
            # First try to load from registry
            registry = _load_bundle_registry()
            if 'yahoo_equities_daily' in registry:
                meta = registry['yahoo_equities_daily']
                # Validate end_date (may be corrupted from earlier bug)
                end_date = meta.get('end_date')
                if end_date and not _is_valid_date_string(end_date):
                    end_date = None
                _register_yahoo_bundle(
                    bundle_name='yahoo_equities_daily',
                    symbols=meta.get('symbols', ['SPY']),
                    calendar_name=meta.get('calendar_name', 'XNYS'),
                    start_date=meta.get('start_date'),
                    end_date=end_date,
                    data_frequency=meta.get('data_frequency', 'daily'),
                    timeframe=meta.get('timeframe', 'daily')
                )
            else:
                # Fallback to extracting symbols from database
                symbols = _extract_symbols_from_bundle('yahoo_equities_daily')
                if symbols:
                    _register_yahoo_bundle('yahoo_equities_daily', symbols, 'XNYS')
                else:
                    _register_yahoo_bundle('yahoo_equities_daily', ['SPY'], 'XNYS')
    except ImportError:
        pass  # Zipline not installed
    except Exception as e:
        logging.getLogger(__name__).warning(f"Auto-registration failed: {e}")


# Try to auto-register on import (for MVP convenience)
try:
    _auto_register_yahoo_bundle_if_exists()
except Exception:
    pass
