"""
CSV bundle ingestion package.

Modular implementation of CSV bundle ingestion with SessionManager integration
for consistent calendar alignment across ingestion and backtest execution.

Main entry point: register_csv_bundle()
"""

from .registration import register_csv_bundle
from .parser import normalize_csv_columns, parse_csv_filename
from .ingestion import load_and_process_csv, create_asset_metadata
from .writer import write_minute_and_daily_bars, write_daily_bars

__all__ = [
    'register_csv_bundle',
    'normalize_csv_columns',
    'parse_csv_filename',
    'load_and_process_csv',
    'create_asset_metadata',
    'write_minute_and_daily_bars',
    'write_daily_bars',
]
