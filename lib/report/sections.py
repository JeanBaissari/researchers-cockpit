"""
Report section builders.

Contains helpers for building specific sections of strategy reports.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd


def build_trade_section(metrics: Dict[str, Any]) -> str:
    """
    Build trade analysis section if trade metrics available.

    Args:
        metrics: Dictionary of performance metrics

    Returns:
        Markdown-formatted trade section or empty string
    """
    if "trade_count" not in metrics or metrics["trade_count"] <= 0:
        return ""

    return f"""
## Trade Analysis

| Metric | Value |
|--------|-------|
| Total Trades | {metrics.get("trade_count", 0)} |
| Win Rate | {metrics.get("win_rate", 0):.2%} |
| Profit Factor | {metrics.get("profit_factor", 0):.3f} |
| Avg Trade Return | {metrics.get("avg_trade_return", 0):.2%} |
| Avg Win | {metrics.get("avg_win", 0):.2%} |
| Avg Loss | {metrics.get("avg_loss", 0):.2%} |
| Max Win | {metrics.get("max_win", 0):.2%} |
| Max Loss | {metrics.get("max_loss", 0):.2%} |
| Max Consecutive Losses | {metrics.get("max_consecutive_losses", 0)} |
| Avg Trade Duration | {metrics.get("avg_trade_duration", 0):.1f} days |
| Trades Per Month | {metrics.get("trades_per_month", 0):.1f} |
"""


def build_validation_section(results_dir: Path) -> str:
    """
    Build validation results section if available.

    Args:
        results_dir: Path to results directory

    Returns:
        Markdown-formatted validation section or empty string
    """
    robustness_file = results_dir / "robustness_score.json"
    if not robustness_file.exists():
        return ""

    with open(robustness_file) as f:
        robustness = json.load(f)

    return f"""
## Validation Results

| Metric | Value |
|--------|-------|
| Walk-Forward Efficiency | {robustness.get("efficiency", 0):.3f} |
| Consistency | {robustness.get("consistency", 0):.2%} |
| Avg IS Sharpe | {robustness.get("avg_is_sharpe", 0):.3f} |
| Avg OOS Sharpe | {robustness.get("avg_oos_sharpe", 0):.3f} |
| Std OOS Sharpe | {robustness.get("std_oos_sharpe", 0):.3f} |
"""


def build_overfit_section(results_dir: Path) -> str:
    """
    Build overfit analysis section if available.

    Args:
        results_dir: Path to results directory

    Returns:
        Markdown-formatted overfit section or empty string
    """
    overfit_file = results_dir / "overfit_score.json"
    if not overfit_file.exists():
        return ""

    with open(overfit_file) as f:
        overfit = json.load(f)

    return f"""
## Overfit Analysis

| Metric | Value |
|--------|-------|
| Efficiency (OOS/IS) | {overfit.get("efficiency", 0):.3f} |
| Probability of Overfitting | {overfit.get("pbo", 0):.2f} |
| Verdict | {overfit.get("verdict", "unknown")} |
"""


def load_performance_dataframe(results_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load Zipline performance DataFrame from results directory.

    Attempts to load from:
    1. performance.pkl (if available)
    2. returns.csv (reconstructs minimal DataFrame)

    Args:
        results_dir: Path to results directory

    Returns:
        Performance DataFrame or None if not available
    """
    # Try to load pickle file first (full performance DataFrame)
    perf_pickle = results_dir / "performance.pkl"
    if perf_pickle.exists():
        try:
            import pickle

            with open(perf_pickle, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass

    # Fallback: Try to reconstruct from returns.csv
    returns_csv = results_dir / "returns.csv"
    if returns_csv.exists():
        try:
            returns_df = pd.read_csv(returns_csv, index_col=0, parse_dates=True)
            # Create minimal performance DataFrame with returns
            perf = pd.DataFrame(index=returns_df.index)
            perf["returns"] = returns_df["returns"]
            return perf
        except Exception:
            pass

    return None


def build_zipline_metrics_section(results_dir: Path) -> str:
    """
    Build section using Zipline's native metrics from performance DataFrame.

    Extracts metrics like alpha, beta, leverage, benchmark comparison
    that are calculated by Zipline's MetricsTracker.

    Args:
        results_dir: Path to results directory

    Returns:
        Markdown-formatted Zipline metrics section or empty string
    """
    perf = load_performance_dataframe(results_dir)
    if perf is None:
        return ""

    sections = []

    # Benchmark comparison (alpha, beta)
    if "alpha" in perf.columns or "beta" in perf.columns:
        alpha = perf["alpha"].iloc[-1] if "alpha" in perf.columns else None
        beta = perf["beta"].iloc[-1] if "beta" in perf.columns else None
        benchmark_return = (
            perf["benchmark_period_return"].iloc[-1]
            if "benchmark_period_return" in perf.columns
            else None
        )
        algo_return = (
            perf["algorithm_period_return"].iloc[-1]
            if "algorithm_period_return" in perf.columns
            else None
        )

        if alpha is not None or beta is not None:
            sections.append("## Benchmark Comparison (Zipline Metrics)")
            sections.append("")
            sections.append("| Metric | Value |")
            sections.append("|--------|-------|")
            if alpha is not None:
                sections.append(f"| Alpha (Jensen's Alpha) | {alpha:.4f} |")
            if beta is not None:
                sections.append(f"| Beta (Market Exposure) | {beta:.3f} |")
            if benchmark_return is not None:
                sections.append(f"| Benchmark Return | {benchmark_return:.2%} |")
            if algo_return is not None:
                sections.append(f"| Algorithm Return | {algo_return:.2%} |")
            sections.append("")

    # Leverage metrics
    if "gross_leverage" in perf.columns or "net_leverage" in perf.columns:
        max_gross = perf["gross_leverage"].max() if "gross_leverage" in perf.columns else None
        max_net = perf["net_leverage"].max() if "net_leverage" in perf.columns else None
        avg_gross = perf["gross_leverage"].mean() if "gross_leverage" in perf.columns else None
        avg_net = perf["net_leverage"].mean() if "net_leverage" in perf.columns else None

        if max_gross is not None or max_net is not None:
            if not sections:  # Add header if this is first section
                sections.append("## Zipline Native Metrics")
                sections.append("")
            sections.append("### Leverage Analysis")
            sections.append("")
            sections.append("| Metric | Value |")
            sections.append("|--------|-------|")
            if max_gross is not None:
                sections.append(f"| Max Gross Leverage | {max_gross:.3f} |")
            if max_net is not None:
                sections.append(f"| Max Net Leverage | {max_net:.3f} |")
            if avg_gross is not None:
                sections.append(f"| Avg Gross Leverage | {avg_gross:.3f} |")
            if avg_net is not None:
                sections.append(f"| Avg Net Leverage | {avg_net:.3f} |")
            sections.append("")

    # Time-series metrics summary (final values from Zipline)
    zipline_metrics = {}
    for col in ["sharpe", "sortino", "max_drawdown"]:
        if col in perf.columns:
            # Get final value (Zipline calculates rolling metrics)
            final_value = perf[col].iloc[-1]
            if pd.notna(final_value):
                zipline_metrics[col] = final_value

    if zipline_metrics:
        if not sections:  # Add header if this is first section
            sections.append("## Zipline Native Metrics")
            sections.append("")
        sections.append("### Time-Series Metrics (Final Values)")
        sections.append("")
        sections.append("| Metric | Final Value |")
        sections.append("|--------|-------------|")
        if "sharpe" in zipline_metrics:
            sections.append(f"| Sharpe Ratio (Rolling) | {zipline_metrics['sharpe']:.3f} |")
        if "sortino" in zipline_metrics:
            sections.append(f"| Sortino Ratio (Rolling) | {zipline_metrics['sortino']:.3f} |")
        if "max_drawdown" in zipline_metrics:
            sections.append(f"| Max Drawdown (Rolling) | {zipline_metrics['max_drawdown']:.2%} |")
        sections.append("")
        sections.append(
            "*Note: These are rolling calculations from Zipline's MetricsTracker. "
            + "For full-period metrics, see Performance Summary section.*"
        )
        sections.append("")

    return "\n".join(sections) if sections else ""


def build_time_series_summary(results_dir: Path) -> str:
    """
    Build summary of time-series metrics from Zipline performance DataFrame.

    Shows statistics about rolling metrics over the backtest period.

    Args:
        results_dir: Path to results directory

    Returns:
        Markdown-formatted time-series summary or empty string
    """
    perf = load_performance_dataframe(results_dir)
    if perf is None:
        return ""

    sections = []

    # Analyze rolling metrics if available
    for metric_name, display_name in [
        ("sharpe", "Sharpe Ratio"),
        ("sortino", "Sortino Ratio"),
        ("max_drawdown", "Max Drawdown"),
    ]:
        if metric_name in perf.columns:
            series = perf[metric_name].dropna()
            if len(series) > 0:
                if not sections:
                    sections.append("## Time-Series Metrics Summary (Zipline)")
                    sections.append("")
                    sections.append("*Rolling metrics calculated by Zipline's MetricsTracker*")
                    sections.append("")

                sections.append(f"### {display_name}")
                sections.append("")
                sections.append("| Statistic | Value |")
                sections.append("|-----------|-------|")
                sections.append(f"| Mean | {series.mean():.3f} |")
                sections.append(f"| Std Dev | {series.std():.3f} |")
                sections.append(f"| Min | {series.min():.3f} |")
                sections.append(f"| Max | {series.max():.3f} |")
                sections.append(f"| Final | {series.iloc[-1]:.3f} |")
                sections.append("")

    return "\n".join(sections) if sections else ""
