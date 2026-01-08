"""
Data loading and bundle management for The Researcher's Cockpit.

This module provides backward compatibility imports from the new
lib/bundles/ package structure.

Provides functions to ingest data from various sources into Zipline bundles
and manage cached API responses. Supports multiple timeframes including:
- daily (1d): Full historical data
- 1h: Up to 730 days (yfinance limit)
- 30m, 15m, 5m: Up to 60 days (yfinance limit)
- 1m: Up to 7 days (yfinance limit)

DEPRECATION NOTICE:
    This module is deprecated. Please import from lib.bundles instead:
    
    # Old (deprecated):
    from lib.data_loader import ingest_bundle, VALID_TIMEFRAMES
    
    # New (recommended):
    from lib.bundles import ingest_bundle, VALID_TIMEFRAMES
"""

import logging

# Re-export get_project_root from utils for backward compatibility
from .utils import get_project_root

# Re-export everything from the bundles package for backward compatibility

# Timeframe configuration
from .bundles.timeframes import (
    TIMEFRAME_TO_YF_INTERVAL,
    TIMEFRAMES_REQUIRING_AGGREGATION,
    TIMEFRAME_DATA_LIMITS,
    TIMEFRAME_TO_DATA_FREQUENCY,
    VALID_TIMEFRAMES,
    CALENDAR_MINUTES_PER_DAY,
    get_minutes_per_day,
    get_timeframe_info,
    validate_timeframe_date_range,
)

# Bundle registry management
from .bundles.registry import (
    get_bundle_registry_path as _get_bundle_registry_path,
    load_bundle_registry as _load_bundle_registry,
    save_bundle_registry as _save_bundle_registry,
    register_bundle_metadata as _register_bundle_metadata,
    get_bundle_path,
    list_bundles,
    unregister_bundle,
    get_registered_bundles,
    add_registered_bundle,
    discard_registered_bundle,
)

# Bundle utilities
from .bundles.utils import (
    aggregate_to_4h as _aggregate_to_4h,
    is_valid_date_string as _is_valid_date_string,
    extract_symbols_from_bundle as _extract_symbols_from_bundle,
)

# CSV bundle registration
from .bundles.csv_bundle import (
    register_csv_bundle as _register_csv_bundle,
    normalize_csv_columns as _normalize_csv_columns,
    parse_csv_filename as _parse_csv_filename,
)

# Yahoo Finance bundle registration
from .bundles.yahoo_bundle import (
    register_yahoo_bundle as _register_yahoo_bundle,
    auto_register_yahoo_bundle_if_exists as _auto_register_yahoo_bundle_if_exists,
)

# Caching utilities
from .bundles.cache import (
    cache_api_data,
    clear_cache,
)

# Main bundle API
from .bundles.api import (
    ingest_bundle,
    load_bundle,
    get_bundle_symbols,
)

# Valid data sources
from .bundles import VALID_SOURCES

# Module-level logger (for backward compatibility)
logger = logging.getLogger(__name__)

# Re-export _registered_bundles for backward compatibility
# This is now managed by the registry module
_registered_bundles = get_registered_bundles()

# Try to auto-register on import (for MVP convenience)
try:
    _auto_register_yahoo_bundle_if_exists()
except Exception:
    pass

__all__ = [
    # Timeframe configuration
    'TIMEFRAME_TO_YF_INTERVAL',
    'TIMEFRAMES_REQUIRING_AGGREGATION',
    'TIMEFRAME_DATA_LIMITS',
    'TIMEFRAME_TO_DATA_FREQUENCY',
    'VALID_TIMEFRAMES',
    'CALENDAR_MINUTES_PER_DAY',
    'VALID_SOURCES',
    'get_minutes_per_day',
    'get_timeframe_info',
    'validate_timeframe_date_range',
    # Registry (public)
    'get_bundle_path',
    'list_bundles',
    'unregister_bundle',
    # Registry (private, for backward compatibility)
    '_get_bundle_registry_path',
    '_load_bundle_registry',
    '_save_bundle_registry',
    '_register_bundle_metadata',
    # Utils (private, for backward compatibility)
    '_aggregate_to_4h',
    '_is_valid_date_string',
    '_extract_symbols_from_bundle',
    # CSV bundle (private, for backward compatibility)
    '_register_csv_bundle',
    '_normalize_csv_columns',
    '_parse_csv_filename',
    # Yahoo bundle (private, for backward compatibility)
    '_register_yahoo_bundle',
    '_auto_register_yahoo_bundle_if_exists',
    # Cache
    'cache_api_data',
    'clear_cache',
    # Main API
    'ingest_bundle',
    'load_bundle',
    'get_bundle_symbols',
    # Backward compatibility
    '_registered_bundles',
    'get_project_root',
]
