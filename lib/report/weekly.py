"""
Weekly summary report generation module.

Generates weekly summary reports aggregating all strategy results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..utils import get_project_root, ensure_dir


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
    strategies = _collect_strategy_metrics(results_base)
    
    # Generate summary content
    summary_content = _build_weekly_summary(strategies, start_date, end_date)
    
    # Save summary
    reports_dir = root / 'reports'
    ensure_dir(reports_dir)
    week_str = datetime.now().strftime('%YW%U')
    summary_path = reports_dir / f'weekly_summary_{week_str}.md'
    
    with open(summary_path, 'w') as f:
        f.write(summary_content)
    
    return summary_path


def _collect_strategy_metrics(results_base: Path) -> List[Dict[str, Any]]:
    """Collect metrics from all strategies."""
    strategies = []
    
    for strategy_dir in results_base.iterdir():
        if strategy_dir.is_dir():
            metrics = _load_strategy_metrics(strategy_dir)
            if metrics:
                strategies.append({
                    'name': strategy_dir.name,
                    'metrics': metrics,
                })
    
    return strategies


def _load_strategy_metrics(strategy_dir: Path) -> Optional[Dict[str, Any]]:
    """Load metrics for a single strategy."""
    metrics_file = strategy_dir / 'latest' / 'metrics.json'
    if not metrics_file.exists():
        return None
    
    with open(metrics_file) as f:
        return json.load(f)


def _build_weekly_summary(
    strategies: List[Dict[str, Any]],
    start_date: Optional[str],
    end_date: Optional[str]
) -> str:
    """Build weekly summary content."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    week_str = datetime.now().strftime('%YW%U')
    
    strategies_sorted = sorted(
        strategies, 
        key=lambda x: x['metrics'].get('sharpe', 0), 
        reverse=True
    )
    
    content = f"""# Weekly Research Summary

Week: {week_str}  
Generated: {date_str}

## Strategy Overview

| Strategy | Sharpe | Sortino | MaxDD | Status |
|----------|--------|---------|-------|--------|
"""
    
    for strategy in strategies_sorted:
        content += _format_strategy_row(strategy)
    
    content += _build_summary_statistics(strategies, strategies_sorted)
    
    return content


def _format_strategy_row(strategy: Dict[str, Any]) -> str:
    """Format a single strategy row for the table."""
    name = strategy['name']
    m = strategy['metrics']
    sharpe = f"{m.get('sharpe', 0):.2f}" if m.get('sharpe') else "N/A"
    sortino = f"{m.get('sortino', 0):.2f}" if m.get('sortino') else "N/A"
    max_dd = f"{m.get('max_drawdown', 0):.1%}" if m.get('max_drawdown') else "N/A"
    return f"| {name} | {sharpe} | {sortino} | {max_dd} | Active |\n"


def _build_summary_statistics(
    strategies: List[Dict[str, Any]],
    strategies_sorted: List[Dict[str, Any]]
) -> str:
    """Build summary statistics section."""
    if not strategies:
        return "\n## Summary Statistics\n\n- Total Strategies: 0\n- Average Sharpe: N/A\n- Best Performer: N/A\n"
    
    avg_sharpe = sum(s['metrics'].get('sharpe', 0) for s in strategies) / len(strategies)
    best = strategies_sorted[0]['name'] if strategies_sorted else 'N/A'
    
    return f"\n## Summary Statistics\n\n- Total Strategies: {len(strategies)}\n- Average Sharpe: {avg_sharpe:.2f}\n- Best Performer: {best}\n"
