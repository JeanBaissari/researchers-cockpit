"""
Optimization module for The Researcher's Cockpit.

Provides grid search and random search optimization with anti-overfit protocols.
"""

# Standard library imports
import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from .backtest import run_backtest, save_results
from .config import load_strategy_params, load_settings
from .metrics import calculate_metrics
from .utils import (
    get_project_root,
    get_strategy_path,
    timestamp_dir,
    ensure_dir,
    save_yaml,
    load_yaml,
    update_symlink,
)


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
        params = _deep_copy_dict(base_params)
        for param_name, param_value in zip(param_names, combo):
            _set_nested_param(params, param_name, param_value)
        
        # Run backtest on training data
        try:
            train_perf, _ = run_backtest(
                strategy_name=strategy_name,
                start_date=train_start,
                end_date=train_end,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )

            train_returns = train_perf['returns'].dropna()
            train_metrics = calculate_metrics(train_returns)

            # Run backtest on test data
            test_perf, _ = run_backtest(
                strategy_name=strategy_name,
                start_date=test_start,
                end_date=test_end,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )

            test_returns = test_perf['returns'].dropna()
            test_metrics = calculate_metrics(test_returns)
            
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
    result_dir = _save_optimization_results(
        strategy_name=strategy_name,
        results_df=results_df,
        param_grid=param_grid,
        objective=objective,
        train_metrics=train_metrics_agg,
        test_metrics=test_metrics_agg,
        asset_class=asset_class
    )
    
    return results_df


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
        params = _deep_copy_dict(base_params)
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
            
            _set_nested_param(params, param_name, value)
            sampled_params[param_name] = value
        
        # Run backtest on training data
        try:
            train_perf, _ = run_backtest(
                strategy_name=strategy_name,
                start_date=train_start,
                end_date=train_end,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )

            train_returns = train_perf['returns'].dropna()
            train_metrics = calculate_metrics(train_returns)

            # Run backtest on test data
            test_perf, _ = run_backtest(
                strategy_name=strategy_name,
                start_date=test_start,
                end_date=test_end,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )

            test_returns = test_perf['returns'].dropna()
            test_metrics = calculate_metrics(test_returns)
            
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
    result_dir = _save_optimization_results(
        strategy_name=strategy_name,
        results_df=results_df,
        param_grid=param_distributions,
        objective=objective,
        train_metrics=train_metrics if 'train_metrics' in locals() else {},
        test_metrics=test_metrics if 'test_metrics' in locals() else {},
        asset_class=asset_class
    )
    
    return results_df


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


def calculate_overfit_score(
    in_sample_metric: float,
    out_sample_metric: float,
    n_trials: int
) -> Dict[str, Any]:
    """
    Calculate overfit probability score.
    
    Args:
        in_sample_metric: In-sample metric value
        out_sample_metric: Out-of-sample metric value
        n_trials: Number of trials/combinations tested
        
    Returns:
        Dictionary with overfit score and verdict
    """
    # Simple overfit score: ratio of OOS to IS performance
    if abs(in_sample_metric) > 1e-10:
        efficiency = out_sample_metric / in_sample_metric
    else:
        efficiency = 0.0
    
    # Probability of overfitting (simplified)
    # Lower efficiency = higher overfit probability
    if efficiency < 0.3:
        pbo = 0.8  # High probability of overfitting
        verdict = "high_overfit"
    elif efficiency < 0.5:
        pbo = 0.6
        verdict = "moderate_overfit"
    elif efficiency < 0.7:
        pbo = 0.4
        verdict = "acceptable"
    else:
        pbo = 0.2
        verdict = "robust"
    
    return {
        'efficiency': float(efficiency),
        'pbo': float(pbo),
        'verdict': verdict,
        'in_sample': float(in_sample_metric),
        'out_sample': float(out_sample_metric),
    }


def _deep_copy_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Deep copy a dictionary."""
    import copy
    return copy.deepcopy(d)


def _set_nested_param(params: Dict[str, Any], param_path: str, value: Any) -> None:
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


def _save_optimization_results(
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
                _set_nested_param(best_params, param_name, best_row[param_name])
        
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
            from .plots import _plot_optimization_heatmap
            _plot_optimization_heatmap(results_df, param_grid, objective, result_dir)
        except:
            pass
    
    # Update latest symlink
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)
    
    return result_dir

