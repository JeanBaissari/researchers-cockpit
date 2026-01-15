"""
Bundle management for The Researcher's Cockpit.

Provides functions to ingest data from various sources into Zipline bundles
and manage cached API responses. Supports multiple timeframes including:
- daily (1d): Full historical data
- 1h: Up to 730 days (yfinance limit)
- 30m, 15m, 5m: Up to 60 days (yfinance limit)
- 1m: Up to 7 days (yfinance limit)
"""

# Core timeframe configuration
from .timeframes import (
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
from .registry import (
    get_bundle_registry_path,
    load_bundle_registry,
    save_bundle_registry,
    register_bundle_metadata,
    get_bundle_path,
    list_bundles,
    unregister_bundle,
    get_registered_bundles,
    add_registered_bundle,
    discard_registered_bundle,
)

# Bundle utilities
from .utils import (
    aggregate_to_4h,
    is_valid_date_string,
    extract_symbols_from_bundle,
)

# CSV bundle registration
from .csv_bundle import (
    register_csv_bundle,
    normalize_csv_columns,
    parse_csv_filename,
)

# Yahoo Finance bundle registration
from .yahoo_bundle import (
    register_yahoo_bundle,
    auto_register_yahoo_bundle_if_exists,
)

# Caching utilities
from .cache import (
    cache_api_data,
    clear_cache,
)

# Main bundle API
from .api import (
    ingest_bundle,
    load_bundle,
    get_bundle_symbols,
)

# Valid data sources
VALID_SOURCES = ['yahoo', 'binance', 'oanda', 'csv']

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
    # Registry
    'get_bundle_registry_path',
    'load_bundle_registry',
    'save_bundle_registry',
    'register_bundle_metadata',
    'get_bundle_path',
    'list_bundles',
    'unregister_bundle',
    'get_registered_bundles',
    'add_registered_bundle',
    'discard_registered_bundle',
    # Utils
    'aggregate_to_4h',
    'is_valid_date_string',
    'extract_symbols_from_bundle',
    # CSV bundle
    'register_csv_bundle',
    'normalize_csv_columns',
    'parse_csv_filename',
    # Yahoo bundle
    'register_yahoo_bundle',
    'auto_register_yahoo_bundle_if_exists',
    # Cache
    'cache_api_data',
    'clear_cache',
    # Main API
    'ingest_bundle',
    'load_bundle',
    'get_bundle_symbols',
]















