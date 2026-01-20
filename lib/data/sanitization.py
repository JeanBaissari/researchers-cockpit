"""
Data sanitization utilities for handling NaN and Inf values.

Provides functions to sanitize numeric data for safe processing and serialization.
"""

import math
from typing import Any

import numpy as np
import pandas as pd


def sanitize_value(value: float, default: float = 0.0) -> float:
    """
    Replace NaN/Inf with default value for single numeric values.
    
    Args:
        value: Numeric value to sanitize
        default: Default value to use if value is NaN/Inf (default: 0.0)
        
    Returns:
        Sanitized float value
    """
    if value is None or math.isnan(value) or math.isinf(value):
        return default
    return float(value)


def sanitize_series(series: pd.Series) -> pd.Series:
    """
    Sanitize a pandas Series by removing NaN and Inf values.
    
    Args:
        series: Series to sanitize
        
    Returns:
        Series with NaN and Inf values removed
    """
    if series is None:
        raise ValueError("Series cannot be None")
    
    if not isinstance(series, pd.Series):
        raise ValueError(f"Series must be a pandas Series, got {type(series)}")
    
    # Drop NaN values and convert to float
    cleaned = series.dropna().astype(float)
    
    # Replace infinite values with NaN and drop
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan).dropna()
    
    return cleaned


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize values for JSON serialization.
    
    Ensures no NaN/Inf values escape to JSON output, which would
    produce invalid strict JSON (Python's json.dump outputs 'NaN' literal).
    
    Args:
        obj: Any value to sanitize (dict, list, float, etc.)
        
    Returns:
        Sanitized value safe for JSON serialization
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    return obj
