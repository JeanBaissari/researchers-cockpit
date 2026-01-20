"""
Results handling module for The Researcher's Cockpit.

Orchestrates serialization and persistence operations for backtest results.
"""

from pathlib import Path
from typing import Dict, Any

import pandas as pd

from .results_serialization import (
    normalize_performance_dataframe,
    extract_positions_dataframe,
    extract_transactions_dataframe,
    save_returns_csv,
    save_positions_csv,
    save_transactions_csv,
    calculate_and_save_metrics,
    save_parameters_yaml,
    generate_plots,
)
from .results_persistence import (
    create_results_directory,
    update_latest_symlink,
    check_and_fix_strategy_symlinks,
)
from .verification import _verify_data_integrity


def save_results(
    strategy_name: str,
    perf: pd.DataFrame,
    params: Dict[str, Any],
    trading_calendar: Any,
    result_type: str = 'backtest',
    verify_integrity: bool = False
) -> Path:
    """
    Save backtest results to timestamped directory.
    
    Creates:
    - results/{strategy}/{result_type}_{timestamp}/
      - returns.csv
      - positions.csv
      - transactions.csv
      - metrics.json (basic)
      - parameters_used.yaml
      - equity_curve.png (if matplotlib available)
    
    Updates:
    - results/{strategy}/latest -> new directory
    
    Args:
        strategy_name: Name of strategy
        perf: Performance DataFrame from Zipline
        params: Strategy parameters dictionary
        trading_calendar: Trading calendar object
        result_type: Type of result ('backtest', 'optimization', etc.)
        verify_integrity: If True, run data integrity checks (default: False)
        
    Returns:
        Path: Path to created results directory
    """
    # Create results directory
    result_dir = create_results_directory(strategy_name, result_type)
    
    # Normalize DataFrame index to timezone-naive
    perf_normalized = normalize_performance_dataframe(perf)
    
    # Serialize data to CSV files
    save_returns_csv(perf_normalized, result_dir)
    
    # Extract and save positions
    positions_df = extract_positions_dataframe(perf_normalized)
    save_positions_csv(positions_df, result_dir)
    
    # Extract and save transactions
    transactions_df = extract_transactions_dataframe(perf_normalized)
    save_transactions_csv(transactions_df, result_dir)
    
    # Calculate and save metrics
    # v1.11.0: Extract initial_capital from params for portfolio_value reconstruction
    initial_capital = None
    if params:
        initial_capital = params.get('backtest', {}).get('capital_base')
    
    # Calculate metrics (this may modify perf_normalized by adding portfolio_value/returns)
    metrics = calculate_and_save_metrics(
        perf_normalized, 
        transactions_df, 
        result_dir, 
        trading_calendar,
        initial_capital=initial_capital
    )
    
    # Optional data integrity verification
    if verify_integrity:
        _verify_data_integrity(perf_normalized, transactions_df, metrics)
    
    # Save parameters used
    save_parameters_yaml(params, result_dir)
    
    # Generate plots (perf_normalized may now have portfolio_value/returns from reconstruction)
    generate_plots(perf_normalized, transactions_df, result_dir, strategy_name, trading_calendar)
    
    # Check and fix any broken symlinks before updating
    check_and_fix_strategy_symlinks(strategy_name)
    
    # Update latest symlink
    update_latest_symlink(result_dir, strategy_name)
    
    return result_dir
