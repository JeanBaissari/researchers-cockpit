"""
Data loading and bundle management for The Researcher's Cockpit.

Provides functions to ingest data from various sources into Zipline bundles
and manage cached API responses.
"""

# Standard library imports
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union, Any

# Third-party imports
import pandas as pd
import yfinance as yf
from zipline.utils.calendar_utils import get_calendar

# Local imports
from .config import get_data_source, load_settings
from .utils import get_project_root, ensure_dir, normalize_to_calendar_timezone

# Auto-register yahoo_equities_daily bundle if data exists (for MVP)
def _auto_register_yahoo_bundle_if_exists():
    """Auto-register yahoo_equities_daily bundle if data was ingested."""
    from pathlib import Path
    import logging

    zipline_data_dir = Path.home() / '.zipline' / 'data' / 'yahoo_equities_daily'
    if not zipline_data_dir.exists():
        return

    try:
        from zipline.data.bundles import bundles
        if 'yahoo_equities_daily' not in bundles:
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
    data_frequency: str = 'daily' # New parameter
):
    """
    Register a Yahoo Finance bundle.
    
    Args:
        bundle_name: Name for the bundle
        symbols: List of symbols to ingest
        calendar_name: Trading calendar name
        start_date: Start date for data (YYYY-MM-DD)
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
        # Use the first trading session of the calendar as start_session
        first_trading_session = calendar_obj.first_trading_session

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
            # Normalize start_session and end_session to UTC for yfinance, if they are timezone-naive
            if start_session is not None and start_session.tz is None:
                start_session = start_session.tz_localize('UTC')
            if end_session is not None and end_session.tz is None:
                end_session = end_session.tz_localize('UTC')

            # Get calendar timezone - Zipline passes calendar object with timezone info
            # For US equities (XNYS), this is 'America/New_York' (EST/EDT)
            calendar_tz = str(calendar.tz) if hasattr(calendar, 'tz') else 'America/New_York'
            
            # Normalize dates to midnight in calendar timezone, then make timezone-naive
            # This is what Zipline expects - dates represent market days in calendar timezone
            # Create asset metadata DataFrame with SID as index
            equities_data = {
                'symbol': symbols_list,
                'asset_name': symbols_list,  # Use symbol as name for now
                'start_date': start_session.tz_localize(None),  # Zipline expects timezone-naive UTC for asset metadata
                'end_date': end_session.tz_localize(None),       # Zipline expects timezone-naive UTC for asset metadata
                'exchange': 'NYSE' if calendar_name == 'XNYS' else ('NASDAQ' if calendar_name == 'XNAS' else 'NYSE'),
            }
            equities_df = pd.DataFrame(equities_data, index=pd.Index(range(len(symbols_list)), name='sid'))
            asset_db_writer.write(equities=equities_df)
            
            # Fetch data from Yahoo Finance
            if show_progress:
                print(f"Fetching {data_frequency} data for {len(symbols_list)} symbols from Yahoo Finance...")
            
            # Download data and prepare for writing
            def data_gen(): # Renamed to data_gen to be used for both daily and minute
                # Map data_frequency to yfinance interval
                yf_interval = {'daily': '1d', 'minute': '1m'}.get(data_frequency, '1d')

                for sid, symbol in enumerate(symbols_list):
                    try:
                        ticker = yf.Ticker(symbol)
                        # Use yf_interval for fetching data. Pass UTC-localized start/end sessions.
                        # Convert to timezone-naive datetime objects for yfinance
                        yf_start = start_session.to_pydatetime().replace(tzinfo=None) if start_session else None
                        yf_end = end_session.to_pydatetime().replace(tzinfo=None) if end_session else None
                        hist = ticker.history(start=yf_start, end=yf_end, interval=yf_interval)
                        
                        if hist.empty:
                            print(f"Warning: No data for {symbol} at {data_frequency} frequency.")
                            continue
                        
                        # Simplify to UTC conversion
                        if hist.index.tz is not None:
                            hist.index = hist.index.tz_convert('UTC').tz_localize(None)
                        else:
                            hist.index = pd.to_datetime(hist.index)

                        # Prepare DataFrame with required columns
                        bars_df = pd.DataFrame({
                            'open': hist['Open'],
                            'high': hist['High'],
                            'low': hist['Low'],
                            'close': hist['Close'],
                            'volume': hist['Volume'].astype(int),
                        }, index=hist.index)
                        
                        yield sid, bars_df
                        
                    except Exception as e:
                        print(f"Error fetching {data_frequency} data for {symbol}: {e}")
                        continue
            
            if data_frequency == 'minute':
                minute_bar_writer.write(data_gen(), show_progress=show_progress)
            else:
                daily_bar_writer.write(data_gen(), show_progress=show_progress)
            
            # Write empty adjustments (no splits/dividends for now)
            adjustment_writer.write(splits=pd.DataFrame(), dividends=pd.DataFrame(), mergers=pd.DataFrame())
        
        return yahoo_ingest
    
    make_yahoo_ingest(symbols)
    _registered_bundles.add(bundle_name)


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
                start_date=start_date
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
        # Check if it's a yahoo bundle and try to re-register
        if bundle_name.startswith('yahoo_'):
            # Try to infer symbols from bundle name or check if data exists
            # For MVP, we'll require re-ingestion if not registered
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

