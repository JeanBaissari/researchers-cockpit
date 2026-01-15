"""
Main bundle API for The Researcher's Cockpit.

Provides the primary public interface for bundle ingestion and loading.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional

from ..config import get_data_source
from .timeframes import (
    TIMEFRAME_TO_YF_INTERVAL,
    get_timeframe_info,
)
from .registry import (
    load_bundle_registry,
    add_registered_bundle,
)
from .utils import extract_symbols_from_bundle
from .yahoo_bundle import register_yahoo_bundle
from .csv_bundle import register_csv_bundle

logger = logging.getLogger(__name__)


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
        source: Data source name ('yahoo', 'binance', 'oanda', 'csv')
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
            - '4h': 4-hour (730 days max, aggregated from 1h)
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

    # CSV source is handled specially - it doesn't require config/data_sources.yaml entry
    # because it reads from local files, not an external API
    if source != 'csv':
        # Get source config for API-based sources
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
        from ..extension import register_custom_calendars
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
    
    # Log if aggregation will be used
    if tf_info['requires_aggregation']:
        logger.info(
            f"Timeframe {timeframe} requires aggregation from {tf_info['yf_interval']} "
            f"to {tf_info['aggregation_target']}"
        )

    # Register and ingest Yahoo Finance bundle
    if source == 'yahoo':
        try:
            # Register bundle (will skip if already registered unless force=True)
            register_yahoo_bundle(
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
            register_csv_bundle(
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
    from zipline.data.bundles import load, bundles, register

    # Check if bundle is registered
    if bundle_name not in bundles:
        # First, check the persistent bundle registry for metadata
        registry = load_bundle_registry()
        
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
                from ..extension import register_custom_calendars
                register_custom_calendars(calendars=[calendar_name])

            # Re-register the bundle with full metadata (preserves timeframe)
            register_yahoo_bundle(
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
                    from ..extension import register_custom_calendars
                    register_custom_calendars(calendars=['CRYPTO'])
                elif 'forex' in bundle_name:
                    calendar_name = 'FOREX'
                    from ..extension import register_custom_calendars
                    register_custom_calendars(calendars=['FOREX'])
                else:
                    calendar_name = 'XNYS'

                # Try to extract symbols from the asset database
                symbols = extract_symbols_from_bundle(bundle_name)
                
                if symbols:
                    # Re-register with extracted symbols
                    register_yahoo_bundle(
                        bundle_name=bundle_name,
                        symbols=symbols,
                        calendar_name=calendar_name
                    )
                else:
                    # Register a no-op ingest function - data already exists on disk
                    @register(bundle_name, calendar_name=calendar_name)
                    def noop_ingest(environ, asset_db_writer, minute_bar_writer,
                                    daily_bar_writer, adjustment_writer, calendar,
                                    start_session, end_session, cache, show_progress, timestamp):
                        """No-op ingest for already ingested bundle."""
                        pass

                    add_registered_bundle(bundle_name)
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
    registry = load_bundle_registry()
    if bundle_name in registry:
        symbols = registry[bundle_name].get('symbols', [])
        if symbols:
            return symbols

    # Fall back to extracting from SQLite database
    symbols = extract_symbols_from_bundle(bundle_name)
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















