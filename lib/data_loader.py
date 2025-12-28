"""
Data loading and bundle management for The Researcher's Cockpit.

Provides functions to ingest data from various sources into Zipline bundles
and manage cached API responses.
"""

# Standard library imports
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union, Any

# Third-party imports
import numpy as np
import pandas as pd
import yfinance as yf
from zipline.utils.calendar_utils import get_calendar

# Local imports
from .config import get_data_source, load_settings
from .utils import get_project_root, ensure_dir, fill_data_gaps, normalize_to_utc


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
    data_frequency: str = 'daily'
) -> None:
    """
    Persist bundle metadata to registry file.

    Args:
        bundle_name: Name of the bundle
        symbols: List of symbols in the bundle
        calendar_name: Trading calendar name
        start_date: Start date for data
        end_date: End date for data
        data_frequency: Data frequency ('daily' or 'minute')
    """
    registry = _load_bundle_registry()
    registry[bundle_name] = {
        'symbols': symbols,
        'calendar_name': calendar_name,
        'start_date': start_date,
        'end_date': end_date,
        'data_frequency': data_frequency,
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


def _register_yahoo_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str = 'XNYS',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily'
):
    """
    Register a Yahoo Finance bundle.

    Args:
        bundle_name: Name for the bundle
        symbols: List of symbols to ingest
        calendar_name: Trading calendar name
        start_date: Start date for data (YYYY-MM-DD)
        end_date: End date for data (YYYY-MM-DD)
        data_frequency: Data frequency ('daily' or 'minute')
    """
    from zipline.data.bundles import register, bundles
    
    # Check if already registered
    if bundle_name in bundles:
        return
    
    # Store symbols for this bundle (needed for the ingest function)
    # Use closure to capture symbols
    def make_yahoo_ingest(symbols_list):
        # CRITICAL: Use exchange_calendars code, not common name
        # Zipline-reloaded uses exchange_calendars library codes:
        # - 'XNYS' (NYSE)
        # - 'XNAS' (NASDAQ)
        # - '24/7' (Crypto - always open)
        # calendar_name should already be in exchange_calendars format

        # Get the actual calendar object
        calendar_obj = get_calendar(calendar_name)
        # Use the first session of the calendar as start_session
        first_session = calendar_obj.first_session

        @register(bundle_name, calendar_name=calendar_name)
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
                'asset_name': symbols_list,  # Use symbol as name for now
                'start_date': [start_date_utc] * n_symbols,   # List for datetime64[ns]
                'end_date': [end_date_utc] * n_symbols,       # List for datetime64[ns]
                'exchange': ['NYSE' if calendar_name == 'XNYS' else ('NASDAQ' if calendar_name == 'XNAS' else 'NYSE')] * n_symbols,
                'country_code': ['US'] * n_symbols,  # Add country code column
            }
            equities_df = pd.DataFrame(equities_data, index=pd.Index(range(n_symbols), name='sid'))
            asset_db_writer.write(equities=equities_df)
            
            # Fetch data from Yahoo Finance
            if show_progress:
                print(f"Fetching {data_frequency} data for {len(symbols_list)} symbols from Yahoo Finance...")
            
            # Download data and prepare for writing
            def data_gen():
                # Map data_frequency to yfinance interval
                yf_interval = {'daily': '1d', 'minute': '1m'}.get(data_frequency, '1d')

                # Track successful fetches for validation
                successful_fetches = 0

                for sid, symbol in enumerate(symbols_list):
                    try:
                        ticker = yf.Ticker(symbol)
                        # Use UTC dates for yfinance (convert to naive for API)
                        yf_start = start_date_utc.tz_localize(None).to_pydatetime() if start_date_utc else None
                        yf_end = end_date_utc.tz_localize(None).to_pydatetime() if end_date_utc else None
                        hist = ticker.history(start=yf_start, end=yf_end, interval=yf_interval)

                        if hist.empty:
                            print(f"Warning: No data for {symbol} at {data_frequency} frequency.")
                            continue

                        # Per Zipline patterns: bar data must be at midnight UTC
                        # Yahoo Finance returns dates at midnight EST/EDT which becomes 05:00/04:00 UTC
                        # We need to normalize to midnight UTC by extracting just the date
                        if hist.index.tz is not None:
                            # Convert to UTC first, then normalize to midnight
                            hist.index = hist.index.tz_convert('UTC').normalize()
                        else:
                            # Assume dates are meant to be UTC midnight
                            hist.index = pd.to_datetime(hist.index).normalize().tz_localize('UTC')

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
                        if start_date:
                            user_start = pd.Timestamp(start_date, tz='UTC')
                            bars_df = bars_df[bars_df.index >= user_start]
                        if end_date:
                            user_end = pd.Timestamp(end_date, tz='UTC')
                            bars_df = bars_df[bars_df.index <= user_end]

                        # === CALENDAR BOUNDS FILTERING ===
                        # Align data to calendar first session
                        first_calendar_session = calendar_obj.first_session
                        if first_calendar_session.tz is None:
                            first_calendar_session = first_calendar_session.tz_localize('UTC')
                        bars_df = bars_df[bars_df.index >= first_calendar_session]

                        # === CALENDAR SESSION FILTERING (for FOREX Sunday issue) ===
                        # Filter to only include dates that are valid calendar sessions
                        if len(bars_df) > 0:
                            try:
                                # Convert index bounds to naive timestamps for calendar API
                                idx_min = bars_df.index.min()
                                idx_max = bars_df.index.max()
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

                                if bars_df.index.tz is not None:
                                    bars_index_naive = bars_df.index.tz_convert(None)
                                else:
                                    bars_index_naive = bars_df.index

                                # Filter bars to only calendar sessions
                                valid_mask = bars_index_naive.normalize().isin(calendar_sessions_naive)
                                bars_df = bars_df[valid_mask]

                                if show_progress and (~valid_mask).any():
                                    excluded = (~valid_mask).sum()
                                    print(f"  {symbol}: Filtered {excluded} non-calendar sessions")
                            except Exception as cal_err:
                                print(f"Warning: Calendar session filtering failed for {symbol}: {cal_err}")

                        # Check if we have any data left after filtering
                        if bars_df.empty:
                            print(f"Warning: No data for {symbol} after date/calendar filtering.")
                            continue

                        # === GAP-FILLING FOR FOREX AND CRYPTO ===
                        if 'FOREX' in calendar_name.upper() or 'CRYPTO' in calendar_name.upper():
                            try:
                                # Crypto: stricter gap tolerance (3 days), Forex: 5 days
                                max_gap = 5 if 'FOREX' in calendar_name.upper() else 3
                                bars_df = fill_data_gaps(
                                    bars_df,
                                    calendar_obj,
                                    method='ffill',
                                    max_gap_days=max_gap
                                )
                                if show_progress:
                                    print(f"  Gap-filled {calendar_name} data for {symbol}")
                            except Exception as gap_err:
                                print(f"Warning: Gap-filling failed for {symbol}: {gap_err}")

                        successful_fetches += 1
                        yield sid, bars_df

                    except Exception as e:
                        print(f"Error fetching {data_frequency} data for {symbol}: {e}")
                        continue

                # Validate that at least some data was fetched
                if successful_fetches == 0:
                    raise RuntimeError(
                        f"No data was successfully fetched for any symbol. "
                        f"Symbols attempted: {symbols_list}. "
                        f"Check that symbols are valid and date range has data."
                    )
            
            if data_frequency == 'minute':
                minute_bar_writer.write(data_gen(), show_progress=show_progress)
            else:
                daily_bar_writer.write(data_gen(), show_progress=show_progress)
            
            # Write empty adjustments (no splits/dividends for now)
            # Pass None instead of empty DataFrames to avoid column validation issues
            adjustment_writer.write(splits=None, dividends=None, mergers=None)
        
        return yahoo_ingest
    
    make_yahoo_ingest(symbols)
    _registered_bundles.add(bundle_name)

    # Persist bundle metadata to registry file
    _register_bundle_metadata(
        bundle_name=bundle_name,
        symbols=symbols,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        data_frequency=data_frequency
    )


def ingest_bundle(
    source: str,
    assets: List[str],
    bundle_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    timeframe: str = 'daily', # New parameter
    **kwargs
) -> str:
    """
    Ingest data from a source into a Zipline bundle.

    This function creates or updates Zipline data bundles that serve as the
    primary data source for both `handle_data` and the Zipline Pipeline API.
    Ensure that ingested bundles contain all necessary data (e.g., pricing,
    dividends, splits) for factors defined in zipline.pipeline.

    The ingested data is directly compatible with the Zipline Pipeline API.
    When a pipeline is attached and run in a strategy, it will automatically
    access the data from the appropriate bundle based on the `data_frequency`
    and `bundle` parameters used during ingestion and backtesting.
    """
    if symbols is None or len(symbols) == 0:
        raise ValueError("symbols parameter is required and cannot be empty")
    
    # Get source config
    try:
        source_config = get_data_source(source)
    except KeyError:
        raise ValueError(
            f"Unsupported data source: {source}. "
            f"Supported sources: yahoo, binance, oanda"
        )
    
    if not source_config.get('enabled', False):
        raise ValueError(f"Data source '{source}' is not enabled in config/data_sources.yaml")
    
    # Auto-generate bundle name if not provided
    if bundle_name is None:
        asset_class = assets[0] if assets else 'equities'
        bundle_name = f"{source}_{asset_class}_daily"
    
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
    
    # Set default start date if not provided
    if start_date is None:
        start_date = '2020-01-01'
    
    # Register and ingest Yahoo Finance bundle
    if source == 'yahoo':
        try:
            # Register bundle (will skip if already registered)
            _register_yahoo_bundle(
                bundle_name=bundle_name,
                symbols=symbols,
                calendar_name=calendar_name,
                start_date=start_date,
                end_date=end_date,
                data_frequency=timeframe  # Use the timeframe parameter
            )

            # Ingest the bundle
            from zipline.data.bundles import ingest
            ingest(bundle_name, show_progress=True)
            
            return bundle_name
            
        except Exception as e:
            raise RuntimeError(f"Failed to ingest Yahoo Finance bundle: {e}") from e
    
    elif source == 'binance':
        raise NotImplementedError("Binance bundle ingestion not yet implemented")
    
    elif source == 'oanda':
        raise NotImplementedError("OANDA bundle ingestion not yet implemented")
    
    else:
        raise ValueError(f"Unsupported source: {source}")


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
            data_frequency = bundle_meta.get('data_frequency', 'daily')
            
            # Register custom calendars if needed
            if calendar_name in ['CRYPTO', 'FOREX']:
                from .extension import register_custom_calendars
                register_custom_calendars(calendars=[calendar_name])
            
            # Re-register the bundle with full metadata
            _register_yahoo_bundle(
                bundle_name=bundle_name,
                symbols=symbols,
                calendar_name=calendar_name,
                start_date=start_date,
                data_frequency=data_frequency
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
            except (sqlite3.Error, Exception):
                continue
    
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
                _register_yahoo_bundle(
                    'yahoo_equities_daily',
                    meta.get('symbols', ['SPY']),
                    meta.get('calendar_name', 'XNYS'),
                    meta.get('start_date'),
                    meta.get('data_frequency', 'daily')
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

