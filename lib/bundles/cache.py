"""
API data caching utilities.

Provides functions to cache and manage API response data.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from ..utils import get_project_root, ensure_dir

logger = logging.getLogger(__name__)


def cache_api_data(
    source: str,
    symbols: list,
    start_date: str,
    end_date: str = None
) -> Path:
    """
    Cache API response data to disk.
    
    Args:
        source: Data source name
        symbols: List of symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD) or None for today
        
    Returns:
        Path: Path to cached file
    """
    root = get_project_root()
    cache_dir = root / 'data' / 'cache'
    ensure_dir(cache_dir)
    
    # Generate cache filename
    date_str = datetime.now().strftime('%Y%m%d')
    symbols_str = '_'.join(symbols[:3])  # First 3 symbols
    if len(symbols) > 3:
        symbols_str += f"_and_{len(symbols)-3}_more"
    
    cache_file = cache_dir / f"{source}_{symbols_str}_{date_str}.parquet"
    
    # Fetch and cache data
    if source == 'yahoo':
        try:
            data_list = []
            for symbol in symbols:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                hist['symbol'] = symbol
                data_list.append(hist)
            
            if data_list:
                combined = pd.concat(data_list)
                combined.to_parquet(cache_file)
                return cache_file
        except Exception as e:
            logger.exception(f"Failed to cache Yahoo Finance data")
            raise RuntimeError(f"Failed to cache Yahoo Finance data: {e}") from e
    
    raise ValueError(f"Caching not implemented for source: {source}")


def clear_cache(older_than_days: int = 7) -> int:
    """
    Clean expired cache files.
    
    Args:
        older_than_days: Delete files older than this many days
        
    Returns:
        int: Number of files deleted
    """
    root = get_project_root()
    cache_dir = root / 'data' / 'cache'
    
    if not cache_dir.exists():
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=older_than_days)
    deleted_count = 0
    
    for cache_file in cache_dir.glob('*.parquet'):
        if cache_file.stat().st_mtime < cutoff_date.timestamp():
            cache_file.unlink()
            deleted_count += 1
    
    return deleted_count

