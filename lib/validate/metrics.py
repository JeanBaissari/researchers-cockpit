"""
Validation metrics for walk-forward and overfit analysis.

Provides calculation of efficiency, consistency, and overfit probability metrics.
"""

from typing import Dict

import pandas as pd


def calculate_overfit_probability(
    in_sample_sharpe: float,
    out_sample_sharpe: float,
    n_trials: int
) -> float:
    """
    Calculate probability of overfitting (PBO).
    
    Simplified version: lower OOS/IS ratio = higher overfit probability.
    
    Args:
        in_sample_sharpe: In-sample Sharpe ratio
        out_sample_sharpe: Out-of-sample Sharpe ratio
        n_trials: Number of trials/combinations tested
        
    Returns:
        Probability of overfitting (0-1)
    """
    if abs(in_sample_sharpe) < 1e-10:
        return 0.5
    
    efficiency = out_sample_sharpe / in_sample_sharpe
    
    # Simple PBO calculation
    if efficiency < 0.3:
        return 0.8
    elif efficiency < 0.5:
        return 0.6
    elif efficiency < 0.7:
        return 0.4
    else:
        return 0.2


def calculate_walk_forward_efficiency(
    in_sample_metrics: pd.DataFrame,
    out_sample_metrics: pd.DataFrame
) -> Dict[str, float]:
    """
    Calculate walk-forward efficiency and consistency metrics.
    
    Args:
        in_sample_metrics: DataFrame with IS metrics for each period
        out_sample_metrics: DataFrame with OOS metrics for each period
        
    Returns:
        Dictionary with robustness metrics
    """
    if len(in_sample_metrics) == 0 or len(out_sample_metrics) == 0:
        return {
            'efficiency': 0.0,
            'consistency': 0.0,
            'avg_is_sharpe': 0.0,
            'avg_oos_sharpe': 0.0,
            'std_oos_sharpe': 0.0,
        }
    
    # Average Sharpe ratios
    avg_is_sharpe = in_sample_metrics['sharpe'].mean()
    avg_oos_sharpe = out_sample_metrics['sharpe'].mean()
    std_oos_sharpe = out_sample_metrics['sharpe'].std()
    
    # Efficiency: OOS / IS
    if abs(avg_is_sharpe) > 1e-10:
        efficiency = avg_oos_sharpe / avg_is_sharpe
    else:
        efficiency = 0.0
    
    # Consistency: percentage of periods with positive OOS Sharpe
    positive_periods = (out_sample_metrics['sharpe'] > 0).sum()
    consistency = positive_periods / len(out_sample_metrics) if len(out_sample_metrics) > 0 else 0.0
    
    return {
        'efficiency': float(efficiency),
        'consistency': float(consistency),
        'avg_is_sharpe': float(avg_is_sharpe),
        'avg_oos_sharpe': float(avg_oos_sharpe),
        'std_oos_sharpe': float(std_oos_sharpe),
        'n_periods': len(out_sample_metrics),
    }





