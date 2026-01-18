"""
Bundle access functions for The Researcher's Cockpit.

Provides functions to query bundle metadata, symbols, and data ranges.
Extracted from api.py as part of v1.0.11 refactoring.
"""

import logging
from pathlib import Path
from typing import Any, List

from .registry import load_bundle_registry, add_registered_bundle
from .utils import extract_symbols_from_bundle
from .yahoo import register_yahoo_bundle
from ..calendars import register_custom_calendars

logger = logging.getLogger(__name__)


def load_bundle(bundle_name: str) -> Any:
    """
    Verify that a bundle exists and is loadable.

    For dynamically registered bundles, this will attempt to re-register them
    if they're not in the registry but data exists. Uses persistent bundle
    registry to restore metadata across sessions.

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
        # Check persistent bundle registry
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
                register_custom_calendars(calendars=[calendar_name])

            # Re-register the bundle
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
                    register_custom_calendars(calendars=['CRYPTO'])
                elif 'forex' in bundle_name:
                    calendar_name = 'FOREX'
                    register_custom_calendars(calendars=['FOREX'])
                else:
                    calendar_name = 'XNYS'

                # Try to extract symbols from database
                symbols = extract_symbols_from_bundle(bundle_name)

                if symbols:
                    register_yahoo_bundle(
                        bundle_name=bundle_name,
                        symbols=symbols,
                        calendar_name=calendar_name
                    )
                else:
                    # Register no-op ingest function
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

    # Check if bundle data directory exists
    bundle_data_path = Path.home() / '.zipline' / 'data' / bundle_name
    if not bundle_data_path.exists():
        raise FileNotFoundError(
            f"Bundle '{bundle_name}' not found. "
            f"Run: python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS> --bundle-name {bundle_name}"
        )

    # Bundle exists but couldn't extract symbols
    logger.warning(
        f"Could not extract symbols from bundle '{bundle_name}'. "
        f"Bundle may be empty or corrupted."
    )
    return []
