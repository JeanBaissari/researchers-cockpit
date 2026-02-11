"""
Bundle access functions for The Researcher's Cockpit.

Provides functions to query bundle metadata, symbols, and data ranges.
Extracted from api.py as part of v1.0.11 refactoring.
"""

from pathlib import Path
from typing import Any, List

from .utils import extract_symbols_from_bundle, ensure_bundle_registered
from .errors import format_bundle_load_failure_message
from .yahoo import register_yahoo_bundle
from ..calendars import register_custom_calendars

import logging

logger = logging.getLogger(__name__)


def load_bundle(bundle_name: str) -> Any:
    """
    Load a bundle from Zipline's registry.

    Phase 1.2 (v1.11.1+): Simplified - bundles are auto-registered at startup
    via ~/.zipline/extension.py, so reactive registration is no longer needed.

    Args:
        bundle_name: Name of bundle to load

    Returns:
        BundleData: Bundle data object from Zipline

    Raises:
        FileNotFoundError: If bundle doesn't exist or isn't registered
        RuntimeError: If bundle loading fails

    Note:
        If you see "bundle not found" errors, ensure:
        1. Bundle is ingested (see the command printed in the error message)
        2. Bundle is registered by your `~/.zipline/extension.py`
        3. Restart Python session to trigger auto-registration from extension.py
    """
    from zipline.data.bundles import load
    from .initialization import ensure_bundles_initialized

    # Ensure bundles are initialized from persistent registry
    # Phase 1.1 (v1.11.1+): Explicit initialization approach
    ensure_bundles_initialized()

    # Check if bundle is registered (v1.12.0+: Direct Zipline API only)
    # Uses shared error handling from utils.py
    ensure_bundle_registered(bundle_name, raise_on_missing=True, exception_type=FileNotFoundError)

    # Load the bundle
    try:
        bundle_data = load(bundle_name)
        logger.info(f"Loaded bundle '{bundle_name}' successfully")
        return bundle_data
    except Exception as e:
        logger.exception(f"Failed to load bundle '{bundle_name}'")
        raise RuntimeError(
            format_bundle_load_failure_message(bundle_name=bundle_name, exc=e)
        ) from e


def list_bundles() -> List[str]:
    """
    List all available bundles from Zipline's registry.

    v1.12.0+: Uses Zipline's bundles dict directly (NO WRAPPERS).

    Returns:
        List of bundle names (strings)

    Example:
        >>> from lib.bundles import list_bundles
        >>> bundles = list_bundles()
        >>> print(f"Available bundles: {bundles}")
    """
    from zipline.data.bundles import bundles
    from .initialization import ensure_bundles_initialized

    # Ensure bundles are initialized
    ensure_bundles_initialized()

    # Return list of registered bundle names (v1.12.0+: Direct Zipline API)
    return list(bundles.keys())


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
    # Check if bundle is registered using shared error handling
    ensure_bundle_registered(bundle_name, raise_on_missing=True, exception_type=FileNotFoundError)

    # Extract symbols directly from bundle data (v1.12.0+: No registry tracking)
    symbols = extract_symbols_from_bundle(bundle_name)
    if symbols:
        return symbols

    # Bundle exists but couldn't extract symbols
    logger.warning(
        f"Could not extract symbols from bundle '{bundle_name}'. Bundle may be empty or corrupted."
    )
    return []
