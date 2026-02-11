"""
Tests for lib.report.weekly (weekly summary report generation).
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.report.weekly import (
    generate_weekly_summary,
    _collect_strategy_metrics,
    _load_strategy_metrics,
    _build_weekly_summary,
    _format_strategy_row,
    _build_summary_statistics,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def temp_results_with_metrics(tmp_path):
    """Create a temporary results directory with strategy metrics."""
    results_base = tmp_path / "results"
    results_base.mkdir(parents=True)

    # Strategy A: has latest/metrics.json
    strategy_a = results_base / "strategy_a"
    strategy_a.mkdir()
    (strategy_a / "latest").mkdir()
    (strategy_a / "latest" / "metrics.json").write_text(
        json.dumps(
            {
                "sharpe": 1.5,
                "sortino": 2.0,
                "max_drawdown": -0.08,
            }
        )
    )

    # Strategy B: has latest/metrics.json
    strategy_b = results_base / "strategy_b"
    strategy_b.mkdir()
    (strategy_b / "latest").mkdir()
    (strategy_b / "latest" / "metrics.json").write_text(
        json.dumps(
            {
                "sharpe": 0.9,
                "sortino": 1.2,
                "max_drawdown": -0.12,
            }
        )
    )

    # Strategy C: no latest/metrics.json (should be skipped)
    strategy_c = results_base / "strategy_c"
    strategy_c.mkdir()

    return tmp_path


@pytest.fixture
def temp_results_empty(tmp_path):
    """Create an empty results directory."""
    results_base = tmp_path / "results"
    results_base.mkdir(parents=True)
    return tmp_path


# -----------------------------------------------------------------------------
# generate_weekly_summary
# -----------------------------------------------------------------------------


class TestGenerateWeeklySummary:
    """Tests for generate_weekly_summary."""

    @patch("lib.report.weekly.get_project_root")
    @patch("lib.report.weekly.ensure_dir")
    def test_returns_path_to_generated_file(
        self, mock_ensure_dir, mock_get_root, temp_results_with_metrics
    ):
        """generate_weekly_summary returns Path to the generated markdown file."""
        mock_get_root.return_value = temp_results_with_metrics
        mock_ensure_dir.side_effect = lambda p: p.mkdir(parents=True, exist_ok=True)

        result = generate_weekly_summary()

        assert isinstance(result, Path)
        assert result.suffix == ".md"
        assert result.name.startswith("weekly_summary_")
        assert result.exists()
        assert "Weekly Research Summary" in result.read_text()

    @patch("lib.report.weekly.get_project_root")
    @patch("lib.report.weekly.ensure_dir")
    def test_writes_strategy_overview_table(
        self, mock_ensure_dir, mock_get_root, temp_results_with_metrics
    ):
        """Generated report contains strategy overview table with expected strategies."""
        mock_get_root.return_value = temp_results_with_metrics
        mock_ensure_dir.side_effect = lambda p: p.mkdir(parents=True, exist_ok=True)

        result = generate_weekly_summary()
        content = result.read_text()

        assert "## Strategy Overview" in content
        assert "| Strategy | Sharpe | Sortino | MaxDD | Status |" in content
        assert "strategy_a" in content
        assert "strategy_b" in content
        assert "strategy_c" not in content  # no metrics.json

    @patch("lib.report.weekly.get_project_root")
    def test_raises_file_not_found_when_results_missing(self, mock_get_root, tmp_path):
        """generate_weekly_summary raises FileNotFoundError when results dir does not exist."""
        mock_get_root.return_value = tmp_path
        # tmp_path has no "results" subdir

        with pytest.raises(FileNotFoundError) as exc_info:
            generate_weekly_summary()

        assert "Results directory not found" in str(exc_info.value)
        assert "results" in str(exc_info.value)


# -----------------------------------------------------------------------------
# _collect_strategy_metrics
# -----------------------------------------------------------------------------


class TestCollectStrategyMetrics:
    """Tests for _collect_strategy_metrics."""

    def test_collects_strategies_with_metrics(self, temp_results_with_metrics):
        """Collects only strategy dirs that have latest/metrics.json."""
        results_base = temp_results_with_metrics / "results"
        strategies = _collect_strategy_metrics(results_base)

        assert len(strategies) == 2
        names = {s["name"] for s in strategies}
        assert names == {"strategy_a", "strategy_b"}

    def test_returns_empty_list_when_no_metrics(self, temp_results_empty):
        """Returns empty list when no strategy has metrics.json."""
        strategies = _collect_strategy_metrics(temp_results_empty / "results")
        assert strategies == []


# -----------------------------------------------------------------------------
# _load_strategy_metrics
# -----------------------------------------------------------------------------


class TestLoadStrategyMetrics:
    """Tests for _load_strategy_metrics."""

    def test_returns_metrics_when_file_exists(self, temp_results_with_metrics):
        """Returns parsed metrics when latest/metrics.json exists."""
        strategy_dir = temp_results_with_metrics / "results" / "strategy_a"
        metrics = _load_strategy_metrics(strategy_dir)

        assert metrics is not None
        assert metrics["sharpe"] == 1.5
        assert metrics["sortino"] == 2.0
        assert metrics["max_drawdown"] == -0.08

    def test_returns_none_when_no_metrics_file(self, tmp_path):
        """Returns None when latest/metrics.json does not exist."""
        strategy_dir = tmp_path / "no_metrics"
        strategy_dir.mkdir()
        assert _load_strategy_metrics(strategy_dir) is None

    def test_returns_none_when_latest_dir_missing(self, tmp_path):
        """Returns None when latest/ directory does not exist."""
        strategy_dir = tmp_path / "no_latest"
        strategy_dir.mkdir()
        assert _load_strategy_metrics(strategy_dir) is None


# -----------------------------------------------------------------------------
# _build_weekly_summary
# -----------------------------------------------------------------------------


class TestBuildWeeklySummary:
    """Tests for _build_weekly_summary."""

    def test_includes_header_and_week(self):
        """Output includes title and week placeholder."""
        content = _build_weekly_summary([], None, None)
        assert "# Weekly Research Summary" in content
        assert "Week:" in content
        assert "Generated:" in content
        assert "## Strategy Overview" in content

    def test_includes_strategy_rows_sorted_by_sharpe(self):
        """Strategies are sorted by Sharpe descending and included in table."""
        strategies = [
            {
                "name": "low_sharpe",
                "metrics": {"sharpe": 0.5, "sortino": 0.8, "max_drawdown": -0.1},
            },
            {
                "name": "high_sharpe",
                "metrics": {"sharpe": 1.8, "sortino": 2.0, "max_drawdown": -0.05},
            },
        ]
        content = _build_weekly_summary(strategies, None, None)

        # High Sharpe strategy should appear first in table body
        high_pos = content.index("high_sharpe")
        low_pos = content.index("low_sharpe")
        assert high_pos < low_pos


# -----------------------------------------------------------------------------
# _format_strategy_row
# -----------------------------------------------------------------------------


class TestFormatStrategyRow:
    """Tests for _format_strategy_row."""

    def test_formats_full_metrics(self):
        """Row contains strategy name and formatted metrics."""
        strategy = {
            "name": "my_strategy",
            "metrics": {"sharpe": 1.2, "sortino": 1.5, "max_drawdown": -0.09},
        }
        row = _format_strategy_row(strategy)

        assert "| my_strategy |" in row
        assert "1.20" in row
        assert "1.50" in row
        assert "-9.0%" in row
        assert "| Active |" in row
        assert row.endswith("\n")

    def test_uses_na_for_missing_metrics(self):
        """Missing metrics are shown as N/A."""
        strategy = {"name": "minimal", "metrics": {}}
        row = _format_strategy_row(strategy)

        assert "| minimal |" in row
        assert "N/A" in row


# -----------------------------------------------------------------------------
# _build_summary_statistics
# -----------------------------------------------------------------------------


class TestBuildSummaryStatistics:
    """Tests for _build_summary_statistics."""

    def test_empty_strategies(self):
        """Empty list produces zero total and N/A for average and best."""
        content = _build_summary_statistics([], [])

        assert "Total Strategies: 0" in content
        assert "Average Sharpe: N/A" in content
        assert "Best Performer: N/A" in content

    def test_non_empty_strategies(self):
        """Non-empty list shows count, average Sharpe, and best performer."""
        strategies = [
            {"name": "a", "metrics": {"sharpe": 1.0}},
            {"name": "b", "metrics": {"sharpe": 2.0}},
        ]
        sorted_strategies = [
            {"name": "b", "metrics": {"sharpe": 2.0}},
            {"name": "a", "metrics": {"sharpe": 1.0}},
        ]
        content = _build_summary_statistics(strategies, sorted_strategies)

        assert "Total Strategies: 2" in content
        assert "Average Sharpe: 1.50" in content
        assert "Best Performer: b" in content
