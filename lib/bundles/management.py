"""
Bundle management functions for The Researcher's Cockpit (v1.12.0+).

Note: CSV bundle registration removed in v1.12.0.
- For CSV bundles, register directly in ~/.zipline/extension.py using csvdir_equities()
- This function now only supports Yahoo Finance source
- Registry tracking removed (use Zipline's bundles dict directly)

Extracted from api.py as part of v1.0.11 refactoring.
Updated for v1.12.0 NO WRAPPERS directive.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from ..config import get_data_source
from .timeframes import get_timeframe_info
from .yahoo import register_yahoo_bundle
from ..calendars import register_custom_calendars
from ..calendars import get_calendar_for_asset_class

logger = logging.getLogger(__name__)


def ingest_bundle(
    source: str,
    assets: List[str],
    bundle_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    timeframe: str = "daily",
    force: bool = False,
    **kwargs,
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
        timeframe: Data timeframe ('1m', '5m', '15m', '1h', '4h', 'daily', etc.)
        force: If True, unregister and re-register the bundle even if already registered

    Returns:
        Bundle name string

    Raises:
        ValueError: If symbols empty, source not supported, or timeframe invalid
        RuntimeError: If ingestion fails
    """
    if symbols is None or len(symbols) == 0:
        raise ValueError("symbols parameter is required and cannot be empty")

    # Validate timeframe
    timeframe = timeframe.lower()
    try:
        tf_info = get_timeframe_info(timeframe)
    except ValueError as e:
        raise ValueError(str(e))

    # Reject weekly/monthly
    if timeframe in ("weekly", "1wk", "monthly", "1mo"):
        raise ValueError(
            f"Timeframe '{timeframe}' is not compatible with Zipline bundles. "
            f"For weekly/monthly data, ingest daily data and use aggregation functions."
        )

    # Validate source
    if source != "csv":
        try:
            source_config = get_data_source(source)
        except KeyError:
            raise ValueError(
                f"Unsupported data source: {source}. Supported sources: yahoo, binance, oanda, csv"
            )

        if not source_config.get("enabled", False):
            raise ValueError(f"Data source '{source}' is not enabled in config/data_sources.yaml")

    # Determine asset class
    asset_class = assets[0] if assets else "equities"

    # Auto-generate bundle name
    if bundle_name is None:
        tf_normalized = {"1d": "daily", "1wk": "weekly", "1mo": "monthly"}.get(timeframe, timeframe)
        bundle_name = f"{source}_{asset_class}_{tf_normalized}"

    # Auto-detect calendar
    if calendar_name is None:
        if "crypto" in assets:
            calendar_name = "CRYPTO"
        elif "forex" in assets:
            calendar_name = "FOREX"
        else:
            calendar_name = "XNYS"

    # Register custom calendars if needed
    if calendar_name in ["CRYPTO", "FOREX"]:
        register_custom_calendars(calendars=[calendar_name])

    # Set default start date
    if start_date is None:
        if source == "csv":
            start_date = "2020-01-01"  # Default for CSV
        elif tf_info["data_limit_days"]:
            earliest = datetime.now().date() - timedelta(days=tf_info["data_limit_days"])
            start_date = earliest.isoformat()
        else:
            start_date = "2020-01-01"

    # Get Zipline data frequency
    data_frequency = tf_info["data_frequency"]

    # Auto-exclude current day for FOREX intraday (API sources only)
    if (
        calendar_name == "FOREX"
        and data_frequency == "minute"
        and end_date is None
        and source != "csv"
    ):
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        logger.info(
            f"FOREX intraday (API source): Auto-excluding current day. "
            f"Setting end_date to {yesterday} to avoid incomplete session data."
        )
        print(f"Note: FOREX intraday API data excludes current day (end_date set to {yesterday})")
        end_date = yesterday

    # Log ingestion details
    logger.info(
        f"Ingesting {source}/{asset_class} bundle: {bundle_name} "
        f"(timeframe={timeframe}, frequency={data_frequency})"
    )

    if tf_info["requires_aggregation"]:
        logger.info(
            f"Timeframe {timeframe} requires aggregation from {tf_info['yf_interval']} "
            f"to {tf_info['aggregation_target']}"
        )

    # Register and ingest based on source
    if source == "yahoo":
        try:
            register_yahoo_bundle(
                bundle_name=bundle_name,
                symbols=symbols,
                calendar_name=calendar_name,
                start_date=start_date,
                end_date=end_date,
                data_frequency=data_frequency,
                timeframe=timeframe,
                force=force,
            )

            from zipline.data.bundles import ingest

            ingest(bundle_name, show_progress=True)

            return bundle_name

        except Exception as e:
            logger.exception(f"Failed to ingest Yahoo Finance bundle: {bundle_name}")
            raise RuntimeError(f"Failed to ingest Yahoo Finance bundle: {e}") from e

    elif source == "binance":
        raise NotImplementedError("Binance bundle ingestion not yet implemented")

    elif source == "oanda":
        raise NotImplementedError("OANDA bundle ingestion not yet implemented")

    elif source == "csv":
        # CSV bundles must be registered in ~/.zipline/extension.py (v1.12.0+)
        # Check if bundle already registered
        from zipline.data.bundles import bundles, ingest

        if bundle_name not in bundles:
            raise ValueError(
                f"CSV bundle '{bundle_name}' not registered.\n\n"
                f"To register CSV bundles (v1.12.0+):\n"
                f"1. Add data to data/csvdir/{timeframe}/ directory (e.g., data/csvdir/1m/EURUSD.csv)\n"
                f"2. Register bundle in ~/.zipline/extension.py:\n\n"
                f"   from zipline.data.bundles import register\n"
                f"   from zipline.data.bundles.csvdir import csvdir_equities\n"
                f"   import pandas as pd\n\n"
                f"   register(\n"
                f"       '{bundle_name}',\n"
                f"       csvdir_equities(['{'minute' if data_frequency == 'minute' else 'daily'}'], '/path/to/csvdir/{timeframe}'),\n"
                f"       calendar_name='{calendar_name}',\n"
                f"       start_session=pd.Timestamp('2020-01-01', tz='utc'),\n"
                f"       end_session=pd.Timestamp('2025-12-31', tz='utc')\n"
                f"   )\n\n"
                f"3. Then run: zipline ingest -b {bundle_name}\n\n"
                f"See docs/CSV_INGESTION_BEST_PRACTICES.md for details."
            )

        # Bundle already registered, just ingest
        try:
            logger.info(f"Ingesting CSV bundle: {bundle_name} (already registered in extension.py)")
            ingest(bundle_name, show_progress=True)
            return bundle_name
        except Exception as e:
            logger.exception(f"Failed to ingest CSV bundle: {bundle_name}")
            raise RuntimeError(f"Failed to ingest CSV bundle: {e}") from e

    else:
        raise ValueError(
            f"Unsupported data source: {source}. "
            f"Supported sources: yahoo, csv (binance/oanda not yet implemented)"
        )
