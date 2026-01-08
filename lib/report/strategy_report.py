"""
Strategy report generation module.

Generates individual strategy reports from backtest results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..utils import get_project_root, get_strategy_path, load_yaml, ensure_dir
from .formatters import format_params_yaml, generate_recommendations, generate_next_steps
from .sections import build_trade_section, build_validation_section, build_overfit_section
from .templates import build_report_header, build_performance_summary, build_report_footer


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
    results_dir = root / 'results' / strategy_name / 'latest'
    
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    # Load data
    metrics = _load_metrics(results_dir)
    params = _load_params(results_dir)
    hypothesis = _load_hypothesis(strategy_name, asset_class)
    
    # Generate report content
    report_content = _build_report_content(
        strategy_name, metrics, params, hypothesis, result_type, results_dir
    )
    
    # Write report
    output_path = _get_output_path(root, strategy_name, output_path)
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    return output_path


def _load_metrics(results_dir: Path) -> Dict[str, Any]:
    """Load metrics from results directory."""
    metrics_file = results_dir / 'metrics.json'
    if not metrics_file.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
    with open(metrics_file) as f:
        return json.load(f)


def _load_params(results_dir: Path) -> Dict[str, Any]:
    """Load parameters from results directory."""
    params_file = results_dir / 'parameters_used.yaml'
    return load_yaml(params_file) if params_file.exists() else {}


def _load_hypothesis(strategy_name: str, asset_class: Optional[str]) -> str:
    """Load hypothesis from strategy directory."""
    try:
        strategy_path = get_strategy_path(strategy_name, asset_class)
        hypothesis_file = strategy_path / 'hypothesis.md'
        if hypothesis_file.exists():
            return hypothesis_file.read_text()
    except:
        pass
    return "Hypothesis not found."


def _get_output_path(root: Path, strategy_name: str, output_path: Optional[Path]) -> Path:
    """Determine output path for report."""
    if output_path:
        return output_path
    reports_dir = root / 'reports'
    ensure_dir(reports_dir)
    date_str = datetime.now().strftime('%Y%m%d')
    return reports_dir / f'{strategy_name}_report_{date_str}.md'


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
    
    content = build_report_header(strategy_name, date_str, hypothesis)
    content += build_performance_summary(metrics)
    content += build_trade_section(metrics)
    content += build_validation_section(results_dir)
    content += build_overfit_section(results_dir)
    content += build_report_footer(
        strategy_name,
        format_params_yaml(params),
        generate_recommendations(metrics, result_type),
        generate_next_steps(metrics, result_type)
    )
    
    return content
