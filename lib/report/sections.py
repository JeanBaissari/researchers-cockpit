"""
Report section builders.

Contains helpers for building specific sections of strategy reports.
"""

import json
from pathlib import Path
from typing import Dict, Any


def build_trade_section(metrics: Dict[str, Any]) -> str:
    """
    Build trade analysis section if trade metrics available.
    
    Args:
        metrics: Dictionary of performance metrics
        
    Returns:
        Markdown-formatted trade section or empty string
    """
    if 'trade_count' not in metrics or metrics['trade_count'] <= 0:
        return ""
    
    return f"""
## Trade Analysis

| Metric | Value |
|--------|-------|
| Total Trades | {metrics.get('trade_count', 0)} |
| Win Rate | {metrics.get('win_rate', 0):.2%} |
| Profit Factor | {metrics.get('profit_factor', 0):.3f} |
| Avg Trade Return | {metrics.get('avg_trade_return', 0):.2%} |
| Avg Win | {metrics.get('avg_win', 0):.2%} |
| Avg Loss | {metrics.get('avg_loss', 0):.2%} |
| Max Win | {metrics.get('max_win', 0):.2%} |
| Max Loss | {metrics.get('max_loss', 0):.2%} |
| Max Consecutive Losses | {metrics.get('max_consecutive_losses', 0)} |
| Avg Trade Duration | {metrics.get('avg_trade_duration', 0):.1f} days |
| Trades Per Month | {metrics.get('trades_per_month', 0):.1f} |
"""


def build_validation_section(results_dir: Path) -> str:
    """
    Build validation results section if available.
    
    Args:
        results_dir: Path to results directory
        
    Returns:
        Markdown-formatted validation section or empty string
    """
    robustness_file = results_dir / 'robustness_score.json'
    if not robustness_file.exists():
        return ""
    
    with open(robustness_file) as f:
        robustness = json.load(f)
    
    return f"""
## Validation Results

| Metric | Value |
|--------|-------|
| Walk-Forward Efficiency | {robustness.get('efficiency', 0):.3f} |
| Consistency | {robustness.get('consistency', 0):.2%} |
| Avg IS Sharpe | {robustness.get('avg_is_sharpe', 0):.3f} |
| Avg OOS Sharpe | {robustness.get('avg_oos_sharpe', 0):.3f} |
| Std OOS Sharpe | {robustness.get('std_oos_sharpe', 0):.3f} |
"""


def build_overfit_section(results_dir: Path) -> str:
    """
    Build overfit analysis section if available.
    
    Args:
        results_dir: Path to results directory
        
    Returns:
        Markdown-formatted overfit section or empty string
    """
    overfit_file = results_dir / 'overfit_score.json'
    if not overfit_file.exists():
        return ""
    
    with open(overfit_file) as f:
        overfit = json.load(f)
    
    return f"""
## Overfit Analysis

| Metric | Value |
|--------|-------|
| Efficiency (OOS/IS) | {overfit.get('efficiency', 0):.3f} |
| Probability of Overfitting | {overfit.get('pbo', 0):.2f} |
| Verdict | {overfit.get('verdict', 'unknown')} |
"""















