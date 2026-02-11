"""
The Researcher's Cockpit - Core Library

v1.12.0 - Direct Zipline Usage Architecture (NO WRAPPERS)

This package provides minimal utilities for algorithmic trading research.
Most functionality uses Zipline Reloaded APIs directly.

Main packages:
- calendars → Custom FOREX (24/5 Sun-Fri) and CRYPTO (24/7) calendars
- config → Parameter loading from YAML
- logging → Centralized logging system
- metrics → Performance metrics calculation
- plots → Visualization utilities
- backtest → Backtest execution
- optimize → Parameter optimization
- validate → Walk-forward and Monte Carlo validation (strategy robustness)
- validation → Data quality validation (OHLCV checks)
- report → Report generation
- research → Hypothesis lifecycle tracking (draft → testing → validated/rejected)
- data → Data processing utilities (normalization, filters)
- bundles → Bundle management utilities
- utils → Core utility functions
- paths → Robust project root resolution

For bundle management, use Zipline directly:
    from zipline.data.bundles import bundles, ingest
    from zipline.data.bundles.csvdir import csvdir_equities

For calendar access, use Zipline directly:
    from zipline.utils.calendar_utils import get_calendar
    calendar = get_calendar('FOREX')

v1.12.0 Changes:
- Removed lib.bundles.csv.* → Use csvdir_equities() in extension.py
- Removed lib.bundles.registry.* → Use Zipline's bundles dict
- Removed lib.calendars.sessions.SessionManager → Use get_calendar() directly
- Removed lib.data.aggregation.aggregate_ohlcv() → Use pandas.resample()
- Bundle naming: {symbol}_{timeframe} (e.g., eurusd_1m, spy_daily)

Architecture: NO WRAPPERS - Direct Zipline/pandas usage encouraged
"""

__version__ = "1.12.0"
__author__ = "The Researcher's Cockpit"

# Import all exports from centralized exports module
from ._exports import *

# Configure logging with defaults on import
from .logging import configure_logging

_root_logger = configure_logging(level="INFO", console=False, file=False)
