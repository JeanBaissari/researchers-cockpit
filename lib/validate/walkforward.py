"""
Walk-forward analysis for strategy validation.

Provides rolling train/test window analysis for robustness testing.
"""

from typing import Any, Dict, Optional

import pandas as pd

from ..backtest import run_backtest
from ..metrics import calculate_metrics
from .metrics import calculate_walk_forward_efficiency
from .results import save_walk_forward_results


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
    periods = _generate_periods(start_ts, end_ts, train_period, test_period)
    
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
            train_metrics = _run_period_backtest(
                strategy_name=strategy_name,
                start_date=period['train_start'],
                end_date=period['train_end'],
                period_num=i + 1,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )
            in_sample_results.append(train_metrics)

            # Run backtest on test period
            test_metrics = _run_period_backtest(
                strategy_name=strategy_name,
                start_date=period['test_start'],
                end_date=period['test_end'],
                period_num=i + 1,
                capital_base=capital_base,
                bundle=bundle,
                asset_class=asset_class
            )
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
    result_dir = save_walk_forward_results(
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


def _generate_periods(
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    train_period: int,
    test_period: int
) -> list:
    """
    Generate walk-forward period definitions.
    
    Args:
        start_ts: Start timestamp
        end_ts: End timestamp
        train_period: Training period length in days
        test_period: Testing period length in days
        
    Returns:
        List of period dictionaries with train/test date ranges
    """
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
    
    return periods


def _run_period_backtest(
    strategy_name: str,
    start_date: str,
    end_date: str,
    period_num: int,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    asset_class: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run backtest for a single period and return metrics.
    
    Args:
        strategy_name: Name of strategy
        start_date: Period start date
        end_date: Period end date
        period_num: Period number for labeling
        capital_base: Starting capital
        bundle: Bundle name
        asset_class: Asset class hint
        
    Returns:
        Dictionary with period metrics
    """
    perf, _ = run_backtest(
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        capital_base=capital_base,
        bundle=bundle,
        asset_class=asset_class
    )

    returns = perf['returns'].dropna()
    metrics = calculate_metrics(returns)
    metrics['period'] = period_num
    metrics['start_date'] = start_date
    metrics['end_date'] = end_date
    
    return metrics

