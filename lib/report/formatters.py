"""
Formatting utilities for report generation.

Contains shared helpers for formatting YAML, recommendations, and next steps.
"""

from typing import Dict, Any


def format_params_yaml(params: Dict[str, Any], indent: int = 0) -> str:
    """
    Format parameters as YAML string.
    
    Args:
        params: Dictionary of parameters
        indent: Current indentation level
        
    Returns:
        YAML-formatted string
    """
    lines = []
    indent_str = '  ' * indent
    
    for key, value in params.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_params_yaml(value, indent + 1))
        else:
            lines.append(f"{indent_str}{key}: {value}")
    
    return '\n'.join(lines)


def generate_recommendations(metrics: Dict[str, Any], result_type: str) -> str:
    """
    Generate recommendations based on metrics.
    
    Args:
        metrics: Dictionary of performance metrics
        result_type: Type of result ('backtest', 'optimization', 'walkforward')
        
    Returns:
        Markdown-formatted recommendations
    """
    recommendations = []
    
    sharpe = metrics.get('sharpe', 0)
    sortino = metrics.get('sortino', 0)
    max_dd = metrics.get('max_drawdown', 0)
    win_rate = metrics.get('win_rate', 0)
    
    if sharpe < 0.5:
        recommendations.append(
            "- Sharpe ratio is low. Consider optimizing parameters or revisiting hypothesis."
        )
    elif sharpe > 1.5:
        recommendations.append(
            "- Strong Sharpe ratio. Consider walk-forward validation to confirm robustness."
        )
    
    if sortino < sharpe * 0.8:
        recommendations.append(
            "- Sortino ratio significantly lower than Sharpe suggests high downside volatility."
        )
    
    if abs(max_dd) > 0.3:
        recommendations.append(
            "- Maximum drawdown exceeds 30%. Review risk management and position sizing."
        )
    
    if win_rate > 0 and win_rate < 0.4:
        recommendations.append(
            "- Low win rate. Strategy may benefit from better entry/exit criteria."
        )
    
    if result_type == 'backtest':
        recommendations.append(
            "- Run parameter optimization to find better parameter combinations."
        )
        recommendations.append(
            "- Perform walk-forward analysis to validate robustness."
        )
    
    if not recommendations:
        recommendations.append("- Strategy shows promising results. Proceed with validation.")
    
    return '\n'.join(recommendations)


def generate_next_steps(metrics: Dict[str, Any], result_type: str) -> str:
    """
    Generate next steps based on results.
    
    Args:
        metrics: Dictionary of performance metrics
        result_type: Type of result ('backtest', 'optimization', 'walkforward')
        
    Returns:
        Markdown-formatted next steps
    """
    steps = []
    
    if result_type == 'backtest':
        steps.append(
            "1. Run parameter optimization: `python scripts/run_optimization.py --strategy <name>`"
        )
        steps.append("2. Perform walk-forward validation")
        steps.append("3. Run Monte Carlo simulation")
    
    elif result_type == 'optimization':
        steps.append("1. Review best parameters and overfit score")
        steps.append("2. Run walk-forward validation with optimized parameters")
        steps.append("3. Generate final report")
    
    elif result_type == 'walkforward':
        steps.append("1. Review robustness metrics")
        steps.append("2. Run Monte Carlo simulation")
        steps.append("3. Update strategy catalog status")
    
    return '\n'.join(steps)





