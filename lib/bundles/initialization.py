"""
Bundle initialization for The Researcher's Cockpit.

Provides explicit bundle auto-registration that can be called at application startup.
This is more reliable than depending on Zipline's extension.py auto-loading.

Phase 1.1 (v1.11.1+): Explicit initialization approach
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Track if initialization has been done
_initialized = False


def initialize_bundles(force: bool = False) -> List[str]:
    """
    Initialize all bundles from persistent registry.

    This function auto-registers all bundles that exist in the persistent
    registry but aren't yet registered in Zipline's runtime registry.

    Also registers custom calendars (CRYPTO, FOREX) needed for bundles.

    Should be called once at application startup before any bundle operations.

    Args:
        force: If True, re-initialize even if already done

    Returns:
        List of bundle names that were registered

    Example:
        >>> from lib.bundles import initialize_bundles
        >>> registered = initialize_bundles()
        >>> print(f"Auto-registered {len(registered)} bundles")
    """
    global _initialized

    if _initialized and not force:
        logger.debug("Bundles already initialized (skip with force=False)")
        return []

    # Step 1: Register custom calendars first (required for bundle loading)
    try:
        from ..calendars import register_custom_calendars

        register_custom_calendars(["CRYPTO", "FOREX"], force=True)
        logger.info("Registered custom calendars (CRYPTO, FOREX)")
    except Exception as e:
        logger.warning(f"Failed to register custom calendars: {e}")

    # Step 2: Bundles are registered in extension.py (v1.12.0+)
    # No auto-registration from persistent registry needed
    from zipline.data.bundles import bundles

    registered_bundles = []

    # Note: In v1.12.0+, bundles are registered in ~/.zipline/extension.py
    # using direct csvdir_equities(). No persistent registry tracking needed.
    # This function now only ensures calendars are registered.
    logger.info("Bundle registration handled by extension.py (v1.12.0+)")

    # Return list of currently registered bundles (for info only)
    registered_bundles = list(bundles.keys())

    _initialized = True
    logger.info(
        f"Bundle initialization complete: {len(registered_bundles)} bundles found in extension.py"
    )
    return registered_bundles


def ensure_bundles_initialized() -> None:
    """
    Ensure bundles are initialized, initializing if needed.

    This is a convenience function that can be called from any module
    to ensure bundles are initialized before use.

    Example:
        >>> from lib.bundles import ensure_bundles_initialized
        >>> ensure_bundles_initialized()
        >>> # Now bundles are ready to use
    """
    if not _initialized:
        initialize_bundles()


def is_initialized() -> bool:
    """Check if bundle initialization has been performed."""
    return _initialized
