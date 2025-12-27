"""
Validation module for The Researcher's Cockpit.

Provides walk-forward analysis and Monte Carlo simulation for strategy validation.
"""

# Standard library imports
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
    ensure_dir,
    timestamp_dir,
    save_yaml,
    update_symlink,
)


def walk_forward(
    strategy_name: str,
    start_date: str,
    end_date: str,
    train_period: int = 252,  # days
    test_period: int = 63,    # days
    optimize_params: Optional[Dict[str, Any]] = None,
    objective: str = 'sharpe',
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform walk-forward analysis with rolling train/test windows.
    
    Args:
        strategy_name: Name of strategy to validate
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        train_period: Training period length in days (default: 252 = ~1 year)
        test_period: Testing period length in days (default: 63 = ~3 months)
        optimize_params: Optional parameter grid for optimization in each training period
        objective: Objective metric for optimization (default: 'sharpe')
        capital_base: Starting capital (default: from config)
        bundle: Bundle name (default: auto-detect)
        asset_class: Asset class hint
        
    Returns:
        Dictionary with walk-forward results
    """
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    
    # Generate walk-forward periods
    periods = []
    current_start = start_ts
    
    while current_start + pd.Timedelta(days=train_period + test_period) <= end_ts:
        train_start = current_start
        train_end = train_start + pd.Timedelta(days=train_period - 1)
        test_start = train_end + pd.Timedelta(days=1)
        test_end = test_start + pd.Timedelta(days=test_period - 1)
        
        if test_end > end_ts:
            break
        
        periods.append({
            'train_start': train_start.strftime('%Y-%m-%d'),
            'train_end': train_end.strftime('%Y-%m-%d'),
            'test_start': test_start.strftime('%Y-%m-%d'),
            'test_end': test_end.strftime('%Y-%m-%d'),
        })
        
        # Move forward by test period
        current_start = test_start
    
    if len(periods) == 0:
        raise ValueError("Not enough data for walk-forward analysis")
    
    print(f"Walk-forward analysis: {len(periods)} periods")
    print(f"Train period: {train_period} days, Test period: {test_period} days")
    
    in_sample_results = []
    out_sample_results = []
    
    for i, period in enumerate(periods):
        print(f"\nPeriod {i+1}/{len(periods)}:")
        print(f"  Train: {period['train_start']} to {period['train_end']}")
        print(f"  Test: {period['test_start']} to {period['test_end']}")
        
        # Run backtest on training period
        try:
            train_perf = run_backtest(
                strategy_name=strategy_name,
                start_date=period['train_start'],
                end_date=period['train_end'],
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )
            
            train_returns = train_perf['returns'].dropna()
            train_metrics = calculate_metrics(train_returns)
            train_metrics['period'] = i + 1
            train_metrics['start_date'] = period['train_start']
            train_metrics['end_date'] = period['train_end']
            in_sample_results.append(train_metrics)
            
            # Run backtest on test period
            test_perf = run_backtest(
                strategy_name=strategy_name,
                start_date=period['test_start'],
                end_date=period['test_end'],
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )
            
            test_returns = test_perf['returns'].dropna()
            test_metrics = calculate_metrics(test_returns)
            test_metrics['period'] = i + 1
            test_metrics['start_date'] = period['test_start']
            test_metrics['end_date'] = period['test_end']
            out_sample_results.append(test_metrics)
            
            print(f"  Train Sharpe: {train_metrics.get('sharpe', 0):.4f}, "
                  f"Test Sharpe: {test_metrics.get('sharpe', 0):.4f}")
            
        except Exception as e:
            print(f"  Error in period {i+1}: {e}")
            continue
    
    # Convert to DataFrames
    is_df = pd.DataFrame(in_sample_results)
    oos_df = pd.DataFrame(out_sample_results)
    
    # Calculate robustness metrics
    if len(is_df) > 0 and len(oos_df) > 0:
        robustness = calculate_walk_forward_efficiency(is_df, oos_df)
    else:
        robustness = {
            'efficiency': 0.0,
            'consistency': 0.0,
            'avg_is_sharpe': 0.0,
            'avg_oos_sharpe': 0.0,
            'std_oos_sharpe': 0.0,
        }
    
    # Save results
    result_dir = _save_walk_forward_results(
        strategy_name=strategy_name,
        is_df=is_df,
        oos_df=oos_df,
        robustness=robustness,
        asset_class=asset_class
    )
    
    return {
        'in_sample_results': is_df,
        'out_sample_results': oos_df,
        'robustness': robustness,
        'result_dir': result_dir,
    }


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


def _save_walk_forward_results(
    strategy_name: str,
    is_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    robustness: Dict[str, Any],
    asset_class: Optional[str] = None
) -> Path:
    """
    Save walk-forward results to timestamped directory.
    
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


def _save_monte_carlo_results(
    strategy_name: str,
    simulation_results: Dict[str, Any],
    asset_class: Optional[str] = None
) -> Path:
    """
    Save Monte Carlo simulation results to timestamped directory.
    
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
        from .plots import _plot_monte_carlo_distribution
        _plot_monte_carlo_distribution(simulation_results, result_dir)
    except:
        pass
    
    # Update latest symlink
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)
    
    return result_dir

