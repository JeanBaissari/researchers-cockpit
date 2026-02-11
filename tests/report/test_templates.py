"""
Test report templates.

Tests for lib/report/templates.py: build_performance_summary, build_report_header, build_report_footer.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.report.templates import (
    build_performance_summary,
    build_report_header,
    build_report_footer,
)


class TestBuildPerformanceSummary:
    """Tests for build_performance_summary."""

    def test_returns_markdown_table_structure(self):
        """Output contains markdown table header and separator."""
        metrics = {"total_return": 0.1, "sharpe": 1.0}
        result = build_performance_summary(metrics)
        assert "| Metric | Value |" in result
        assert "|--------|-------|" in result

    def test_includes_all_expected_metrics(self):
        """Output includes rows for total_return, annual_return, sharpe, sortino, max_drawdown, calmar, annual_volatility."""
        metrics = {
            "total_return": 0.12,
            "annual_return": 0.15,
            "sharpe": 1.5,
            "sortino": 2.0,
            "max_drawdown": -0.08,
            "calmar": 1.8,
            "annual_volatility": 0.18,
        }
        result = build_performance_summary(metrics)
        assert "Total Return" in result
        assert "12.00%" in result
        assert "Annual Return" in result
        assert "15.00%" in result
        assert "Sharpe Ratio" in result
        assert "1.500" in result
        assert "Sortino Ratio" in result
        assert "2.000" in result
        assert "Max Drawdown" in result
        assert "-8.00%" in result
        assert "Calmar Ratio" in result
        assert "1.800" in result
        assert "Annual Volatility" in result
        assert "18.00%" in result

    def test_empty_metrics_uses_defaults_zero(self):
        """Missing metrics default to 0 and render as 0.00% or 0.000."""
        result = build_performance_summary({})
        assert "0.00%" in result
        assert "0.000" in result

    def test_partial_metrics_mixed_with_defaults(self):
        """Provided metrics appear; missing keys use 0."""
        metrics = {"total_return": 0.05, "max_drawdown": -0.03}
        result = build_performance_summary(metrics)
        assert "5.00%" in result
        assert "-3.00%" in result
        assert "Sharpe Ratio" in result
        assert "0.000" in result

    def test_none_metrics_raises_type_error(self):
        """Explicit None for a metric value causes TypeError when formatting (no default applied)."""
        metrics = {"total_return": None, "sharpe": None}
        with pytest.raises(TypeError):
            build_performance_summary(metrics)


class TestBuildReportHeader:
    """Tests for build_report_header."""

    def test_title_replaces_underscores_with_spaces_and_title_cases(self):
        """Strategy name is formatted: underscores to spaces, title case."""
        result = build_report_header("btc_sma_cross", "2026-01-28", "Test hypothesis.")
        assert "Btc Sma Cross" in result
        assert "btc_sma_cross" not in result

    def test_contains_date_str(self):
        """Generated header includes the given date string."""
        date_str = "2026-01-28 14:30:00"
        result = build_report_header("my_strategy", date_str, "Hypothesis text.")
        assert date_str in result
        assert "Generated:" in result

    def test_contains_hypothesis(self):
        """Generated header includes the hypothesis section and text."""
        hypothesis = "Momentum signals improve risk-adjusted returns."
        result = build_report_header("test_strategy", "2026-01-28", hypothesis)
        assert "## Hypothesis" in result
        assert hypothesis in result

    def test_contains_performance_summary_section_heading(self):
        """Header ends with Performance Summary section heading."""
        result = build_report_header("s", "d", "h")
        assert "## Performance Summary" in result
        assert "---" in result


class TestBuildReportFooter:
    """Tests for build_report_footer."""

    def test_contains_parameters_yaml_block(self):
        """Footer includes a YAML code block with params_yaml content."""
        params = "name: test\nsymbols: [SPY, QQQ]"
        result = build_report_footer("test_strategy", params, "Rec.", "Steps.")
        assert "```yaml" in result
        assert "```" in result
        assert "name: test" in result
        assert "symbols: [SPY, QQQ]" in result

    def test_contains_recommendations_and_next_steps(self):
        """Footer includes Recommendations and Next Steps sections with given text."""
        recommendations = "Increase lookback period."
        next_steps = "Run walk-forward validation."
        result = build_report_footer("s", "params", recommendations, next_steps)
        assert "## Recommendations" in result
        assert recommendations in result
        assert "## Next Steps" in result
        assert next_steps in result

    def test_files_section_uses_strategy_name(self):
        """Files section links results and metrics paths using strategy_name."""
        strategy_name = "forex_breakout"
        result = build_report_footer(strategy_name, "", "", "")
        assert f"results/{strategy_name}/latest/" in result
        assert f"results/{strategy_name}/latest/metrics.json" in result
        assert f"results/{strategy_name}/latest/parameters_used.yaml" in result

    def test_empty_params_recommendations_next_steps_still_valid_structure(self):
        """Footer structure is valid when params, recommendations, next_steps are empty strings."""
        result = build_report_footer("s", "", "", "")
        assert "## Parameters" in result
        assert "## Recommendations" in result
        assert "## Next Steps" in result
        assert "## Files" in result
