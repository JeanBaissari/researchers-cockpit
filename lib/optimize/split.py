"""
Data splitting utilities for optimization.

Provides train/test split functionality for backtesting optimization.
"""

from typing import Tuple

import pandas as pd


def split_data(start: str, end: str, train_pct: float = 0.7) -> Tuple[Tuple[str, str], Tuple[str, str]]:
    """
    Split date range into training and testing periods.
    
    Args:
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)
        train_pct: Percentage of data for training (default: 0.7)
        
    Returns:
        Tuple of ((train_start, train_end), (test_start, test_end))
    """
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    
    total_days = (end_ts - start_ts).days
    train_days = int(total_days * train_pct)
    
    train_end_ts = start_ts + pd.Timedelta(days=train_days)
    test_start_ts = train_end_ts + pd.Timedelta(days=1)
    
    train_start = start
    train_end = train_end_ts.strftime('%Y-%m-%d')
    test_start = test_start_ts.strftime('%Y-%m-%d')
    test_end = end
    
    return ((train_start, train_end), (test_start, test_end))





