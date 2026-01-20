"""
Grid search optimization.

Provides exhaustive grid search over parameter combinations.
"""

import itertools
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..backtest import run_backtest
from ..config import load_strategy_params
from ..metrics import calculate_metrics
from .split import split_data
from .results import deep_copy_dict, set_nested_param, save_optimization_results

logger = logging.getLogger(__name__)


def grid_search(
    strategy_name: str,
    param_grid: Dict[str, List[Any]],
    start_date: str,
    end_date: str,
    objective: str = 'sharpe',
    train_pct: float = 0.7,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> pd.DataFrame:
    """
    Perform grid search optimization over parameter combinations.
    
    Args:
        strategy_name: Name of strategy to optimize
        param_grid: Dictionary mapping parameter paths to lists of values
                   Example: {'strategy.fast_period': [5, 10, 15], 'strategy.slow_period': [30, 50]}
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        objective: Objective metric ('sharpe', 'sortino', 'total_return', 'calmar')
        train_pct: Percentage of data for training (default: 0.7)
        capital_base: Starting capital (default: from config)
        bundle: Bundle name (default: auto-detect)
        asset_class: Asset class hint
        
    Returns:
        DataFrame with all parameter combinations and their metrics
    """
    # Split data into train/test
    train_dates, test_dates = split_data(start_date, end_date, train_pct)
    train_start, train_end = train_dates
    test_start, test_end = test_dates
    
    # Load base parameters
    base_params = load_strategy_params(strategy_name, asset_class)
    
    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = list(itertools.product(*param_values))
    
    results = []
    
    print(f"Grid search: {len(combinations)} combinations to test")
    print(f"Train period: {train_start} to {train_end}")
    print(f"Test period: {test_start} to {test_end}")
    
    for i, combo in enumerate(combinations):
        # Create parameter dict for this combination
        params = deep_copy_dict(base_params)
        for param_name, param_value in zip(param_names, combo):
            set_nested_param(params, param_name, param_value)
        
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
                'combination': i,
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
            for param_name, param_value in zip(param_names, combo):
                result[param_name] = param_value
            
            results.append(result)
            
            print(f"  [{i+1}/{len(combinations)}] Train {objective}: {train_obj:.4f}, Test {objective}: {test_obj:.4f}")
            
        except Exception as e:
            print(f"  [{i+1}/{len(combinations)}] Error: {e}")
            continue
    
    results_df = pd.DataFrame(results)
    
    # Calculate aggregate IS/OOS metrics from best result
    if len(results_df) > 0:
        best_idx = results_df[f'test_{objective}'].idxmax() if f'test_{objective}' in results_df.columns else 0
        best_row = results_df.loc[best_idx]
        train_metrics_agg = {
            'sharpe': best_row.get('train_sharpe', 0.0),
            'sortino': best_row.get('train_sortino', 0.0),
            'max_drawdown': best_row.get('train_max_dd', 0.0),
        }
        test_metrics_agg = {
            'sharpe': best_row.get('test_sharpe', 0.0),
            'sortino': best_row.get('test_sortino', 0.0),
            'max_drawdown': best_row.get('test_max_dd', 0.0),
        }
    else:
        train_metrics_agg = {}
        test_metrics_agg = {}
    
    # Save results
    save_optimization_results(
        strategy_name=strategy_name,
        results_df=results_df,
        param_grid=param_grid,
        objective=objective,
        train_metrics=train_metrics_agg,
        test_metrics=test_metrics_agg,
        asset_class=asset_class
    )
    
    return results_df

