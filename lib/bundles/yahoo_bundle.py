"""
Yahoo Finance bundle registration (backward compatibility wrapper).

This module has been refactored into lib/bundles/yahoo/ package.
This wrapper maintains backward compatibility for existing imports.

Refactored in v1.0.11 - use `from lib.bundles.yahoo import register_yahoo_bundle` for new code.
"""

import warnings
from pathlib import Path

from .yahoo import (
    register_yahoo_bundle,
    fetch_yahoo_data,
    fetch_multiple_symbols,
    process_yahoo_data,
    aggregate_to_daily,
)
from .registry import load_bundle_registry
from .utils import extract_symbols_from_bundle, is_valid_date_string


# Deprecation warning
warnings.warn(
    "lib.bundles.yahoo_bundle is deprecated. Use lib.bundles.yahoo instead.",
    DeprecationWarning,
    stacklevel=2
)


def auto_register_yahoo_bundle_if_exists():
    """Auto-register yahoo_equities_daily bundle if data was ingested."""
    import logging

    zipline_data_dir = Path.home() / '.zipline' / 'data' / 'yahoo_equities_daily'
    if not zipline_data_dir.exists():
        return

    try:
        from zipline.data.bundles import bundles

        if 'yahoo_equities_daily' not in bundles:
            # First try to load from registry
            registry = load_bundle_registry()
            if 'yahoo_equities_daily' in registry:
                meta = registry['yahoo_equities_daily']
                # Validate end_date
                end_date = meta.get('end_date')
                if end_date and not is_valid_date_string(end_date):
                    end_date = None
                register_yahoo_bundle(
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
                symbols = extract_symbols_from_bundle('yahoo_equities_daily')
                if symbols:
                    register_yahoo_bundle('yahoo_equities_daily', symbols, 'XNYS')
                else:
                    register_yahoo_bundle('yahoo_equities_daily', ['SPY'], 'XNYS')
    except ImportError:
        pass  # Zipline not installed
    except Exception as e:
        logging.getLogger(__name__).warning(f"Auto-registration failed: {e}")


# Backward compatibility aliases
_register_yahoo_bundle = register_yahoo_bundle
_auto_register_yahoo_bundle_if_exists = auto_register_yahoo_bundle_if_exists


__all__ = [
    'register_yahoo_bundle',
    'fetch_yahoo_data',
    'fetch_multiple_symbols',
    'process_yahoo_data',
    'aggregate_to_daily',
    'auto_register_yahoo_bundle_if_exists',
]
