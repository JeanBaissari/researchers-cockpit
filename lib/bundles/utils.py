"""
Utility functions for bundle management.

Provides helper functions for data aggregation, date validation,
and symbol extraction from bundles.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def is_valid_date_string(date_str: str) -> bool:
    """
    Check if a string is a valid YYYY-MM-DD date.

    Args:
        date_str: String to validate

    Returns:
        True if valid date format, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def aggregate_to_4h(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate 1-hour OHLCV data to 4-hour bars.
    
    yfinance does not natively support 4h intervals. This function takes
    1h data and aggregates it to 4h bars using standard OHLCV aggregation rules.
    
    Args:
        df: DataFrame with 1h OHLCV data (columns: open, high, low, close, volume)
            Index must be a DatetimeIndex
            
    Returns:
        DataFrame with 4h OHLCV data
    """
    if df.empty:
        return df
    
    # Ensure we have the required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns for 4h aggregation: {missing}")
    
    # Resample to 4h using standard OHLCV aggregation
    agg_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }
    
    # Use label='left' to label bars by their start time
    result = df.resample('4h', label='left', closed='left').agg(agg_rules)
    
    # Drop any rows where all values are NaN (incomplete periods)
    result = result.dropna(how='all')
    
    return result


def extract_symbols_from_bundle(bundle_name: str) -> List[str]:
    """
    Extract symbol list from an existing bundle's SQLite asset database.

    Args:
        bundle_name: Name of the bundle

    Returns:
        List of symbols, or empty list if extraction fails
    """
    bundle_data_path = Path.home() / '.zipline' / 'data' / bundle_name
    if not bundle_data_path.exists():
        return []

    # Find the most recent ingestion directory
    ingestion_dirs = sorted(bundle_data_path.glob('*'), reverse=True)
    for ingestion_dir in ingestion_dirs:
        asset_db_path = ingestion_dir / 'assets-8.sqlite'
        if not asset_db_path.exists():
            # Try older versions
            for version in range(7, 0, -1):
                asset_db_path = ingestion_dir / f'assets-{version}.sqlite'
                if asset_db_path.exists():
                    break

        if asset_db_path.exists():
            try:
                conn = sqlite3.connect(str(asset_db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT symbol FROM equity_symbol_mappings")
                symbols = [row[0] for row in cursor.fetchall()]
                conn.close()
                if symbols:
                    return list(set(symbols))  # Remove duplicates
            except (sqlite3.Error, Exception) as e:
                logger.warning(f"Failed to extract symbols from {asset_db_path}: {e}")
                continue

    return []


# Backward compatibility aliases (private functions with underscore prefix)
_is_valid_date_string = is_valid_date_string
_aggregate_to_4h = aggregate_to_4h
_extract_symbols_from_bundle = extract_symbols_from_bundle















