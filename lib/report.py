"""
Report generation module for The Researcher's Cockpit.

Generates human-readable markdown reports from backtest results.
"""

# Standard library imports
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Local imports
from .utils import (
    get_project_root,
    get_strategy_path,
    load_yaml,
    ensure_dir,
)


def generate_report(
    strategy_name: str,
    result_type: str = 'backtest',
    output_path: Optional[Path] = None,
    asset_class: Optional[str] = None
) -> Path:
    """
    Generate a markdown report from strategy results.
    
    Args:
        strategy_name: Name of strategy
        result_type: Type of result ('backtest', 'optimization', 'walkforward')
        output_path: Optional output path (default: reports/{strategy}_report_{date}.md)
        asset_class: Optional asset class hint
        
    Returns:
        Path to generated report file
    """
    root = get_project_root()
    
    # Load results from latest directory
    results_dir = root / 'results' / strategy_name / 'latest'
    
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    # Load metrics
    metrics_file = results_dir / 'metrics.json'
    if not metrics_file.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
    
    with open(metrics_file) as f:
        metrics = json.load(f)
    
    # Load parameters
    params_file = results_dir / 'parameters_used.yaml'
    params = {}
    if params_file.exists():
        params = load_yaml(params_file)
    
    # Load hypothesis
    hypothesis = ""
    try:
        strategy_path = get_strategy_path(strategy_name, asset_class)
        hypothesis_file = strategy_path / 'hypothesis.md'
        if hypothesis_file.exists():
            with open(hypothesis_file) as f:
                hypothesis = f.read()
    except:
        hypothesis = "Hypothesis not found."
    
    # Generate report content
    report_content = _build_report_content(
        strategy_name=strategy_name,
        metrics=metrics,
        params=params,
        hypothesis=hypothesis,
        result_type=result_type,
        results_dir=results_dir
    )
    
    # Determine output path
    if output_path is None:
        reports_dir = root / 'reports'
        ensure_dir(reports_dir)
        date_str = datetime.now().strftime('%Y%m%d')
        output_path = reports_dir / f'{strategy_name}_report_{date_str}.md'
    
    # Write report
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    return output_path


def update_catalog(
    strategy_name: str,
    status: str,
    metrics: Dict[str, Any],
    asset_class: Optional[str] = None
) -> None:
    """
    Update strategy catalog with strategy status and metrics.
    
    Args:
        strategy_name: Name of strategy
        status: Status ('testing', 'validated', 'abandoned')
        metrics: Dictionary of metrics
        asset_class: Optional asset class hint
    """
    root = get_project_root()
    catalog_file = root / 'docs' / 'strategy_catalog.md'
    
    # Load existing catalog or create new
    if catalog_file.exists():
        catalog_content = catalog_file.read_text()
    else:
        catalog_content = _create_catalog_template()
    
    # Update or add strategy entry
    catalog_content = _update_catalog_entry(
        catalog_content=catalog_content,
        strategy_name=strategy_name,
        status=status,
        metrics=metrics,
        asset_class=asset_class
    )
    
    # Write updated catalog
    ensure_dir(catalog_file.parent)
    catalog_file.write_text(catalog_content)


def generate_weekly_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Path:
    """
    Generate weekly summary report of all strategies.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Path to generated summary file
    """
    root = get_project_root()
    results_base = root / 'results'
    
    if not results_base.exists():
        raise FileNotFoundError(f"Results directory not found: {results_base}")
    
    # Find all strategies with latest results
    strategies = []
    for strategy_dir in results_base.iterdir():
        if strategy_dir.is_dir():
            latest_dir = strategy_dir / 'latest'
            metrics_file = latest_dir / 'metrics.json'
            
            if metrics_file.exists():
                with open(metrics_file) as f:
                    metrics = json.load(f)
                
                strategies.append({
                    'name': strategy_dir.name,
                    'metrics': metrics,
                })
    
    # Generate summary content
    summary_content = _build_weekly_summary(strategies, start_date, end_date)
    
    # Save summary
    reports_dir = root / 'reports'
    ensure_dir(reports_dir)
    date_str = datetime.now().strftime('%Y%m%d')
    week_str = datetime.now().strftime('%YW%U')
    summary_path = reports_dir / f'weekly_summary_{week_str}.md'
    
    with open(summary_path, 'w') as f:
        f.write(summary_content)
    
    return summary_path


def _build_report_content(
    strategy_name: str,
    metrics: Dict[str, Any],
    params: Dict[str, Any],
    hypothesis: str,
    result_type: str,
    results_dir: Path
) -> str:
    """Build markdown report content."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    content = f"""# {strategy_name.replace('_', ' ').title()} Research Report

Generated: {date_str}

## Hypothesis

{hypothesis}

---

## Performance Summary

| Metric | Value |
|--------|-------|
| Total Return | {metrics.get('total_return', 0):.2%} |
| Annual Return | {metrics.get('annual_return', 0):.2%} |
| Sharpe Ratio | {metrics.get('sharpe', 0):.3f} |
| Sortino Ratio | {metrics.get('sortino', 0):.3f} |
| Max Drawdown | {metrics.get('max_drawdown', 0):.2%} |
| Calmar Ratio | {metrics.get('calmar', 0):.3f} |
| Annual Volatility | {metrics.get('annual_volatility', 0):.2%} |
"""
    
    # Add trade metrics if available
    if 'trade_count' in metrics and metrics['trade_count'] > 0:
        content += f"""
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
    
    # Add validation results if available
    robustness_file = results_dir / 'robustness_score.json'
    if robustness_file.exists():
        with open(robustness_file) as f:
            robustness = json.load(f)
        
        content += f"""
## Validation Results

| Metric | Value |
|--------|-------|
| Walk-Forward Efficiency | {robustness.get('efficiency', 0):.3f} |
| Consistency | {robustness.get('consistency', 0):.2%} |
| Avg IS Sharpe | {robustness.get('avg_is_sharpe', 0):.3f} |
| Avg OOS Sharpe | {robustness.get('avg_oos_sharpe', 0):.3f} |
| Std OOS Sharpe | {robustness.get('std_oos_sharpe', 0):.3f} |
"""
    
    # Add overfit score if available
    overfit_file = results_dir / 'overfit_score.json'
    if overfit_file.exists():
        with open(overfit_file) as f:
            overfit = json.load(f)
        
        content += f"""
## Overfit Analysis

| Metric | Value |
|--------|-------|
| Efficiency (OOS/IS) | {overfit.get('efficiency', 0):.3f} |
| Probability of Overfitting | {overfit.get('pbo', 0):.2f} |
| Verdict | {overfit.get('verdict', 'unknown')} |
"""
    
    # Add parameters
    content += f"""
## Parameters

```yaml
{_format_params_yaml(params)}
```

---

## Recommendations

{_generate_recommendations(metrics, result_type)}

---

## Next Steps

{_generate_next_steps(metrics, result_type)}

---

## Files

- Results: `results/{strategy_name}/latest/`
- Metrics: `results/{strategy_name}/latest/metrics.json`
- Parameters: `results/{strategy_name}/latest/parameters_used.yaml`
"""
    
    return content


def _format_params_yaml(params: Dict[str, Any], indent: int = 0) -> str:
    """Format parameters as YAML string."""
    lines = []
    indent_str = '  ' * indent
    
    for key, value in params.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(_format_params_yaml(value, indent + 1))
        else:
            lines.append(f"{indent_str}{key}: {value}")
    
    return '\n'.join(lines)


def _generate_recommendations(metrics: Dict[str, Any], result_type: str) -> str:
    """Generate recommendations based on metrics."""
    recommendations = []
    
    sharpe = metrics.get('sharpe', 0)
    sortino = metrics.get('sortino', 0)
    max_dd = metrics.get('max_drawdown', 0)
    win_rate = metrics.get('win_rate', 0)
    
    if sharpe < 0.5:
        recommendations.append("- Sharpe ratio is low. Consider optimizing parameters or revisiting hypothesis.")
    elif sharpe > 1.5:
        recommendations.append("- Strong Sharpe ratio. Consider walk-forward validation to confirm robustness.")
    
    if sortino < sharpe * 0.8:
        recommendations.append("- Sortino ratio significantly lower than Sharpe suggests high downside volatility.")
    
    if abs(max_dd) > 0.3:
        recommendations.append("- Maximum drawdown exceeds 30%. Review risk management and position sizing.")
    
    if win_rate > 0 and win_rate < 0.4:
        recommendations.append("- Low win rate. Strategy may benefit from better entry/exit criteria.")
    
    if result_type == 'backtest':
        recommendations.append("- Run parameter optimization to find better parameter combinations.")
        recommendations.append("- Perform walk-forward analysis to validate robustness.")
    
    if not recommendations:
        recommendations.append("- Strategy shows promising results. Proceed with validation.")
    
    return '\n'.join(recommendations)


def _generate_next_steps(metrics: Dict[str, Any], result_type: str) -> str:
    """Generate next steps based on results."""
    steps = []
    
    if result_type == 'backtest':
        steps.append("1. Run parameter optimization: `python scripts/run_optimization.py --strategy <name>`")
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


def _create_catalog_template() -> str:
    """Create catalog template."""
    return """# Strategy Catalog

> Index of all strategies with status and performance metrics.

| Strategy | Asset | Status | Sharpe | Sortino | MaxDD | Last Updated |
|----------|-------|--------|--------|---------|-------|--------------|
"""


def _update_catalog_entry(
    catalog_content: str,
    strategy_name: str,
    status: str,
    metrics: Dict[str, Any],
    asset_class: Optional[str] = None
) -> str:
    """Update or add catalog entry."""
    # Extract asset class from strategy name if not provided
    if asset_class is None:
        # Try to infer from strategy path
        try:
            strategy_path = get_strategy_path(strategy_name)
            asset_class = strategy_path.parent.name
        except:
            asset_class = 'unknown'
    
    sharpe = metrics.get('sharpe', 0)
    sortino = metrics.get('sortino', 0)
    max_dd = metrics.get('max_drawdown', 0)
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Format metrics
    sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
    sortino_str = f"{sortino:.2f}" if sortino else "N/A"
    max_dd_str = f"{max_dd:.1%}" if max_dd else "N/A"
    
    # Check if entry exists
    lines = catalog_content.split('\n')
    entry_line = f"| {strategy_name} | {asset_class} | {status} | {sharpe_str} | {sortino_str} | {max_dd_str} | {date_str} |"
    
    # Find existing entry
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"| {strategy_name} |"):
            lines[i] = entry_line
            found = True
            break
    
    # Add new entry if not found
    if not found:
        # Find table end (before any non-table lines)
        table_end = len(lines)
        for i, line in enumerate(lines):
            if line.startswith('|') and 'Strategy' in line:
                continue
            elif line.startswith('|'):
                continue
            else:
                table_end = i
                break
        
        lines.insert(table_end, entry_line)
    
    return '\n'.join(lines)


def _build_weekly_summary(strategies: List[Dict[str, Any]], start_date: Optional[str], end_date: Optional[str]) -> str:
    """Build weekly summary content."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    week_str = datetime.now().strftime('%YW%U')
    
    content = f"""# Weekly Research Summary

Week: {week_str}  
Generated: {date_str}

## Strategy Overview

| Strategy | Sharpe | Sortino | MaxDD | Status |
|----------|--------|---------|-------|--------|
"""
    
    # Sort by Sharpe
    strategies_sorted = sorted(strategies, key=lambda x: x['metrics'].get('sharpe', 0), reverse=True)
    
    for strategy in strategies_sorted:
        name = strategy['name']
        metrics = strategy['metrics']
        sharpe = metrics.get('sharpe', 0)
        sortino = metrics.get('sortino', 0)
        max_dd = metrics.get('max_drawdown', 0)
        
        sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
        sortino_str = f"{sortino:.2f}" if sortino else "N/A"
        max_dd_str = f"{max_dd:.1%}" if max_dd else "N/A"
        
        content += f"| {name} | {sharpe_str} | {sortino_str} | {max_dd_str} | Active |\n"
    
    content += f"""
## Summary Statistics

- Total Strategies: {len(strategies)}
- Average Sharpe: {sum(s['metrics'].get('sharpe', 0) for s in strategies) / len(strategies) if strategies else 0:.2f}
- Best Performer: {strategies_sorted[0]['name'] if strategies_sorted else 'N/A'}
"""
    
    return content

