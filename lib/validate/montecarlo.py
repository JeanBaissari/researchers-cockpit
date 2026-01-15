"""
Monte Carlo simulation for strategy validation.

Provides bootstrap simulation by shuffling trade returns.
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd


def monte_carlo(
    returns: pd.Series,
    n_simulations: int = 1000,
    confidence_levels: List[float] = [0.05, 0.50, 0.95],
    initial_value: float = 100000.0
) -> Dict[str, Any]:
    """
    Perform Monte Carlo simulation by shuffling trade returns.
    
    Args:
        returns: Series of daily returns
        n_simulations: Number of simulation paths (default: 1000)
        confidence_levels: Confidence levels for percentiles (default: [0.05, 0.50, 0.95])
        initial_value: Initial portfolio value (default: 100000)
        
    Returns:
        Dictionary with simulation results
    """
    returns = returns.dropna()
    
    if len(returns) == 0:
        return {
            'simulation_paths': pd.DataFrame(),
            'confidence_intervals': {},
            'final_value_stats': {},
        }
    
    # Generate simulation paths
    np.random.seed(42)  # For reproducibility
    simulation_paths = []
    
    for i in range(n_simulations):
        # Shuffle returns
        shuffled_returns = returns.sample(frac=1.0).reset_index(drop=True)
        
        # Calculate cumulative equity curve
        cumulative = (1 + shuffled_returns).cumprod() * initial_value
        simulation_paths.append(cumulative.values)
    
    # Convert to DataFrame
    paths_df = pd.DataFrame(simulation_paths).T
    paths_df.index = returns.index[:len(paths_df)]
    
    # Calculate final values
    final_values = paths_df.iloc[-1].values
    
    # Calculate confidence intervals
    confidence_intervals = {}
    for level in confidence_levels:
        percentile = level * 100
        confidence_intervals[f'p{percentile:.0f}'] = float(np.percentile(final_values, percentile))
    
    # Calculate statistics
    final_value_stats = {
        'mean': float(np.mean(final_values)),
        'std': float(np.std(final_values)),
        'min': float(np.min(final_values)),
        'max': float(np.max(final_values)),
    }
    
    return {
        'simulation_paths': paths_df,
        'confidence_intervals': confidence_intervals,
        'final_value_stats': final_value_stats,
        'n_simulations': n_simulations,
    }















