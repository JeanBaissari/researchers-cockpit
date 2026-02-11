"""
Bundle management for The Researcher's Cockpit (v1.12.0+).

Note: v1.12.0 removed wrapper modules in favor of direct Zipline usage.
- lib.bundles.csv.* → Use csvdir_equities() in extension.py
- lib.bundles.registry.* → Use Zipline's bundles dict directly
- lib.bundles.guard.* → Zipline validates during ingestion

For bundle registration, edit ~/.zipline/extension.py to use csvdir_equities() directly.

Remaining utilities:
- Timeframe configuration (VALID_TIMEFRAMES, TIMEFRAME_DATA_LIMITS)
- Bundle ingestion helper (ingest_bundle from api.py)
- Yahoo Finance bundle support (register_yahoo_bundle)
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

# Bundle utilities
from .utils import (
    aggregate_to_4h,
    is_valid_date_string,
    extract_symbols_from_bundle,
    validate_bundle_exists,
    ensure_bundle_registered,
)

# Yahoo Finance bundle registration
from .yahoo import (
    register_yahoo_bundle,
    auto_register_yahoo_bundle_if_exists,
)

# Caching utilities (optional - module may not exist)
try:
    from .cache import (
        cache_api_data,
        clear_cache,
    )
except ImportError:
    # Cache module not available
    cache_api_data = None
    clear_cache = None

# Main bundle API
from .api import (
    ingest_bundle,
)
from .access import (
    load_bundle,
    list_bundles,
    get_bundle_symbols,
)

# Valid data sources
VALID_SOURCES = ["yahoo", "binance", "oanda", "csv"]

__all__ = [
    # Timeframe configuration
    "TIMEFRAME_TO_YF_INTERVAL",
    "TIMEFRAMES_REQUIRING_AGGREGATION",
    "TIMEFRAME_DATA_LIMITS",
    "TIMEFRAME_TO_DATA_FREQUENCY",
    "VALID_TIMEFRAMES",
    "CALENDAR_MINUTES_PER_DAY",
    "VALID_SOURCES",
    "get_minutes_per_day",
    "get_timeframe_info",
    "validate_timeframe_date_range",
    # Utils
    "aggregate_to_4h",
    "is_valid_date_string",
    "extract_symbols_from_bundle",
    "validate_bundle_exists",
    "ensure_bundle_registered",
    # Yahoo bundle
    "register_yahoo_bundle",
    "auto_register_yahoo_bundle_if_exists",
    # Main API
    "ingest_bundle",
    "load_bundle",
    "list_bundles",
    "get_bundle_symbols",
]
