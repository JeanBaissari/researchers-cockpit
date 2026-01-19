"""
Result saving utilities for validation analysis.

Handles saving walk-forward and Monte Carlo simulation results.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..utils import (
    get_project_root,
    ensure_dir,
    timestamp_dir,
    update_symlink,
)


def save_walk_forward_results(
    strategy_name: str,
    is_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    robustness: Dict[str, Any],
    asset_class: Optional[str] = None
) -> Path:
    """
    Save walk-forward results to timestamped directory.
    
    Args:
        strategy_name: Name of the strategy
        is_df: In-sample results DataFrame
        oos_df: Out-of-sample results DataFrame
        robustness: Robustness metrics dictionary
        asset_class: Optional asset class hint
    
    Returns:
        Path to results directory
    """
    root = get_project_root()
    results_base = root / 'results' / strategy_name
    ensure_dir(results_base)
    
    # Create timestamped directory
    result_dir = timestamp_dir(results_base, 'walkforward')
    
    # Save DataFrames
    if len(is_df) > 0:
        is_df.to_csv(result_dir / 'in_sample_results.csv', index=False)
    
    if len(oos_df) > 0:
        oos_df.to_csv(result_dir / 'out_sample_results.csv', index=False)
    
    # Save robustness score
    with open(result_dir / 'robustness_score.json', 'w') as f:
        json.dump(robustness, f, indent=2)
    
    # Update latest symlink
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)
    
    return result_dir


def save_monte_carlo_results(
    strategy_name: str,
    simulation_results: Dict[str, Any],
    asset_class: Optional[str] = None
) -> Path:
    """
    Save Monte Carlo simulation results to timestamped directory.
    
    Args:
        strategy_name: Name of the strategy
        simulation_results: Dictionary containing simulation paths, confidence intervals, and stats
        asset_class: Optional asset class hint
    
    Returns:
        Path to results directory
    """
    root = get_project_root()
    results_base = root / 'results' / strategy_name
    ensure_dir(results_base)
    
    # Create timestamped directory
    result_dir = timestamp_dir(results_base, 'montecarlo')
    
    # Save simulation paths
    if 'simulation_paths' in simulation_results:
        simulation_results['simulation_paths'].to_csv(result_dir / 'simulation_paths.csv')
    
    # Save confidence intervals
    if 'confidence_intervals' in simulation_results:
        with open(result_dir / 'confidence_intervals.json', 'w') as f:
            json.dump(simulation_results['confidence_intervals'], f, indent=2)
    
    # Save final value stats
    if 'final_value_stats' in simulation_results:
        with open(result_dir / 'final_value_stats.json', 'w') as f:
            json.dump(simulation_results['final_value_stats'], f, indent=2)
    
    # Generate distribution plot
    try:
        from ..plots import _plot_monte_carlo_distribution
        _plot_monte_carlo_distribution(simulation_results, result_dir)
    except Exception:
        pass
    
    # Update latest symlink
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)
    
    return result_dir















