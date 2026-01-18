"""
Yahoo Finance bundle module for The Researcher's Cockpit.

Provides public API for Yahoo Finance data ingestion.
Refactored in v1.0.11 from monolithic yahoo_bundle.py into modular structure.
"""

from .registration import register_yahoo_bundle
from .fetcher import fetch_yahoo_data, fetch_multiple_symbols
from .processor import process_yahoo_data, aggregate_to_daily

__all__ = [
    'register_yahoo_bundle',
    'fetch_yahoo_data',
    'fetch_multiple_symbols',
    'process_yahoo_data',
    'aggregate_to_daily',
]
