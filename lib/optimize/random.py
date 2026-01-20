"""
Random search optimization.

Provides random search over parameter distributions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..backtest import run_backtest
from ..config import load_strategy_params, load_settings
from ..metrics import calculate_metrics
from .split import split_data
from .results import deep_copy_dict, set_nested_param, save_optimization_results

logger = logging.getLogger(__name__)


def random_search(
    strategy_name: str,
    param_distributions: Dict[str, Any],
    n_iter: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    objective: str = 'sharpe',
    train_pct: float = 0.7,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform random search optimization over parameter distributions.
    
    Args:
        strategy_name: Name of strategy to optimize
        param_distributions: Dictionary mapping parameter paths to distributions
                           Example: {'strategy.fast_period': [5, 10, 15, 20], 'strategy.slow_period': np.arange(30, 100, 10)}
        n_iter: Number of random iterations (default: 100)
        start_date: Start date string (default: from config)
        end_date: End date string (default: today)
        objective: Objective metric ('sharpe', 'sortino', 'total_return', 'calmar')
        train_pct: Percentage of data for training (default: 0.7)
        capital_base: Starting capital (default: from config)
        bundle: Bundle name (default: auto-detect)
        asset_class: Asset class hint
        
    Returns:
        DataFrame with all parameter combinations and their metrics
    """
    # Get default dates if not provided
    if start_date is None or end_date is None:
        settings = load_settings()
        if start_date is None:
            start_date = settings['dates']['default_start']
        if end_date is None:
            end_date = settings['dates'].get('default_end')
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Split data into train/test
    train_dates, test_dates = split_data(start_date, end_date, train_pct)
    train_start, train_end = train_dates
    test_start, test_end = test_dates
    
    # Load base parameters
    base_params = load_strategy_params(strategy_name, asset_class)
    
    # Generate random parameter combinations
    np.random.seed(42)  # For reproducibility
    results = []
    
    print(f"Random search: {n_iter} iterations")
    print(f"Train period: {train_start} to {train_end}")
    print(f"Test period: {test_start} to {test_end}")
    
    for i in range(n_iter):
        # Sample random parameter values
        params = deep_copy_dict(base_params)
        sampled_params = {}
        
        for param_name, distribution in param_distributions.items():
            if isinstance(distribution, list):
                value = np.random.choice(distribution)
            elif isinstance(distribution, np.ndarray):
                value = float(np.random.choice(distribution))
            elif isinstance(distribution, tuple) and len(distribution) == 2:
                # Range: (min, max)
                value = np.random.uniform(distribution[0], distribution[1])
            else:
                value = distribution
            
            set_nested_param(params, param_name, value)
            sampled_params[param_name] = value
        
        # Run backtest on training data
        try:
            train_perf, _ = run_backtest(
                strategy_name=strategy_name,
                start_date=train_start,
                end_date=train_end,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class,
                custom_params=params  # Pass modified parameters
            )

            # v1.11.0: Handle missing returns when metrics_set='none' (FOREX calendars)
            if 'returns' in train_perf.columns:
                train_returns = train_perf['returns'].dropna()
            elif 'portfolio_value' in train_perf.columns:
                pv = train_perf['portfolio_value'].dropna()
                train_returns = pv.pct_change().dropna() if len(pv) > 1 else pd.Series(dtype=float)
                logger.debug(f"Calculated train returns from portfolio_value for {train_start} to {train_end}")
            else:
                train_returns = pd.Series(dtype=float)
                logger.warning(f"No returns data available for train period {train_start} to {train_end}")
            
            train_metrics = calculate_metrics(train_returns) if len(train_returns) > 0 else {}

            # Run backtest on test data
            test_perf, _ = run_backtest(
                strategy_name=strategy_name,
                start_date=test_start,
                end_date=test_end,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class,
                custom_params=params  # Pass modified parameters
            )

            # v1.11.0: Handle missing returns when metrics_set='none' (FOREX calendars)
            if 'returns' in test_perf.columns:
                test_returns = test_perf['returns'].dropna()
            elif 'portfolio_value' in test_perf.columns:
                pv = test_perf['portfolio_value'].dropna()
                test_returns = pv.pct_change().dropna() if len(pv) > 1 else pd.Series(dtype=float)
                logger.debug(f"Calculated test returns from portfolio_value for {test_start} to {test_end}")
            else:
                test_returns = pd.Series(dtype=float)
                logger.warning(f"No returns data available for test period {test_start} to {test_end}")
            
            test_metrics = calculate_metrics(test_returns) if len(test_returns) > 0 else {}
            
            # Get objective metric
            train_obj = train_metrics.get(objective, 0.0)
            test_obj = test_metrics.get(objective, 0.0)
            
            # Store result
            result = {
                'iteration': i,
                'train_' + objective: train_obj,
                'test_' + objective: test_obj,
                'train_sharpe': train_metrics.get('sharpe', 0.0),
                'test_sharpe': test_metrics.get('sharpe', 0.0),
                'train_sortino': train_metrics.get('sortino', 0.0),
                'test_sortino': test_metrics.get('sortino', 0.0),
                'train_max_dd': train_metrics.get('max_drawdown', 0.0),
                'test_max_dd': test_metrics.get('max_drawdown', 0.0),
            }
            
            # Add parameter values
            result.update(sampled_params)
            
            results.append(result)
            
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{n_iter}] Train {objective}: {train_obj:.4f}, Test {objective}: {test_obj:.4f}")
            
        except Exception as e:
            print(f"  [{i+1}/{n_iter}] Error: {e}")
            continue
    
    results_df = pd.DataFrame(results)
    
    # Save results
    save_optimization_results(
        strategy_name=strategy_name,
        results_df=results_df,
        param_grid=param_distributions,
        objective=objective,
        train_metrics=train_metrics if 'train_metrics' in locals() else {},
        test_metrics=test_metrics if 'test_metrics' in locals() else {},
        asset_class=asset_class
    )
    
    return results_df

