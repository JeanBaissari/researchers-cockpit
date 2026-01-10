"""
Optimization results handling.

Provides utilities for saving and managing optimization results.
"""

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..utils import (
    get_project_root,
    timestamp_dir,
    ensure_dir,
    save_yaml,
    update_symlink,
)
from .overfit import calculate_overfit_score


def deep_copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Deep copy a dictionary."""
    return copy.deepcopy(d)


def set_nested_param(params: Dict[str, Any], param_path: str, value: Any) -> None:
    """
    Set a nested parameter using dot notation.
    
    Example: 'strategy.fast_period' -> params['strategy']['fast_period'] = value
    """
    parts = param_path.split('.')
    current = params
    
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    
    current[parts[-1]] = value


def save_optimization_results(
    strategy_name: str,
    results_df: pd.DataFrame,
    param_grid: Dict[str, Any],
    objective: str,
    train_metrics: Dict[str, Any],
    test_metrics: Dict[str, Any],
    asset_class: Optional[str] = None
) -> Path:
    """
    Save optimization results to timestamped directory.
    
    Returns:
        Path to results directory
    """
    root = get_project_root()
    results_base = root / 'results' / strategy_name
    ensure_dir(results_base)
    
    # Create timestamped directory
    result_dir = timestamp_dir(results_base, 'optimization')
    
    # Save grid results CSV
    results_df.to_csv(result_dir / 'grid_results.csv', index=False)
    
    # Find best parameters (highest test objective)
    test_obj_col = f'test_{objective}'
    if test_obj_col in results_df.columns:
        best_idx = results_df[test_obj_col].idxmax()
        best_row = results_df.loc[best_idx]
        
        # Extract best parameters
        param_names = list(param_grid.keys())
        best_params = {}
        for param_name in param_names:
            if param_name in best_row:
                set_nested_param(best_params, param_name, best_row[param_name])
        
        # Save best parameters
        save_yaml(best_params, result_dir / 'best_params.yaml')
    
    # Calculate overfit score
    if len(results_df) > 0 and test_obj_col in results_df.columns:
        best_is = results_df[f'train_{objective}'].max()
        best_oos = results_df[test_obj_col].max()
        overfit_score = calculate_overfit_score(best_is, best_oos, len(results_df))
        
        with open(result_dir / 'overfit_score.json', 'w') as f:
            json.dump(overfit_score, f, indent=2)
    
    # Save IS/OOS metrics
    with open(result_dir / 'in_sample_metrics.json', 'w') as f:
        json.dump(train_metrics, f, indent=2)
    
    with open(result_dir / 'out_sample_metrics.json', 'w') as f:
        json.dump(test_metrics, f, indent=2)
    
    # Generate heatmap if 2 parameters
    if len(param_grid) == 2:
        try:
            from ..plots import _plot_optimization_heatmap
            _plot_optimization_heatmap(results_df, param_grid, objective, result_dir)
        except Exception:
            pass
    
    # Update latest symlink
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)
    
    return result_dir


# Backward-compatible aliases (private names)
_deep_copy_dict = deep_copy_dict
_set_nested_param = set_nested_param
_save_optimization_results = save_optimization_results





