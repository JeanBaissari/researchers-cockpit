"""
Strategy comparison for The Researcher's Cockpit.

Provides functions for comparing multiple strategies by loading their metrics.

v1.0.4 Fixes Applied:
- Added input validation
- Improved error handling for missing files
"""

# Standard library imports
import json
from pathlib import Path
from typing import List, Optional

# Third-party imports
import pandas as pd

# Local imports
from .core import _sanitize_value


def compare_strategies(strategy_names: List[str], results_base: Optional[Path] = None) -> pd.DataFrame:
    """
    Compare multiple strategies by loading their latest metrics.
    
    v1.0.4 Fixes:
    - Added input validation
    - Improved error handling for missing files
    
    Args:
        strategy_names: List of strategy names to compare
        results_base: Base path to results directory (default: project_root/results)
        
    Returns:
        DataFrame with strategy comparison metrics
    """
    from ..utils import get_project_root
    
    # v1.0.4: Input validation
    if strategy_names is None or not isinstance(strategy_names, list):
        return pd.DataFrame()
    
    if results_base is None:
        try:
            results_base = get_project_root() / 'results'
        except Exception:
            return pd.DataFrame()
    
    comparison_data = []
    
    for strategy_name in strategy_names:
        try:
            if not isinstance(strategy_name, str):
                continue
                
            latest_dir = results_base / strategy_name / 'latest'
            metrics_file = latest_dir / 'metrics.json'
            
            if not metrics_file.exists():
                continue
            
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            comparison_data.append({
                'strategy': strategy_name,
                'sharpe': _sanitize_value(metrics.get('sharpe', 0.0)),
                'sortino': _sanitize_value(metrics.get('sortino', 0.0)),
                'annual_return': _sanitize_value(metrics.get('annual_return', 0.0)),
                'max_drawdown': _sanitize_value(metrics.get('max_drawdown', 0.0)),
                'calmar': _sanitize_value(metrics.get('calmar', 0.0)),
                'win_rate': _sanitize_value(metrics.get('win_rate', 0.0)),
                'trade_count': int(metrics.get('trade_count', 0)),
            })
        except Exception:
            # v1.0.4: Skip strategies that fail to load
            continue
    
    return pd.DataFrame(comparison_data)





