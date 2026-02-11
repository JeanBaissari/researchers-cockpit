"""
Test Zipline metrics integration in report generation.

Tests for loading and using Zipline's native metrics (MetricsTracker, Performance DataFrame)
in report sections.
"""

# Standard library imports
import sys
import pickle
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.report.sections import (
    load_performance_dataframe,
    build_zipline_metrics_section,
    build_time_series_summary,
)


class TestLoadPerformanceDataFrame:
    """Test loading Zipline performance DataFrame from results directory."""

    def test_load_from_pickle(self):
        """Test loading performance DataFrame from pickle file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create sample performance DataFrame with Zipline metrics
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "returns": np.random.randn(100) * 0.01,
                    "portfolio_value": 100000 + np.cumsum(np.random.randn(100) * 1000),
                    "alpha": np.random.randn(100) * 0.001,
                    "beta": np.ones(100) * 0.8,
                    "sharpe": np.random.randn(100) * 0.5 + 1.0,
                    "gross_leverage": np.random.rand(100) * 0.5,
                },
                index=dates,
            )

            # Save as pickle
            perf_file = results_dir / "performance.pkl"
            with open(perf_file, "wb") as f:
                pickle.dump(perf, f)

            # Load and verify
            loaded = load_performance_dataframe(results_dir)
            assert loaded is not None
            assert isinstance(loaded, pd.DataFrame)
            assert len(loaded) == 100
            assert "alpha" in loaded.columns
            assert "beta" in loaded.columns
            assert "sharpe" in loaded.columns

    def test_load_from_returns_csv(self):
        """Test loading performance DataFrame from returns.csv (fallback)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create returns.csv
            dates = pd.date_range("2020-01-01", periods=50, freq="D")
            returns_df = pd.DataFrame({"returns": np.random.randn(50) * 0.01}, index=dates)
            returns_df.to_csv(results_dir / "returns.csv")

            # Load and verify
            loaded = load_performance_dataframe(results_dir)
            assert loaded is not None
            assert isinstance(loaded, pd.DataFrame)
            assert len(loaded) == 50
            assert "returns" in loaded.columns

    def test_load_none_when_no_files(self):
        """Test that None is returned when no performance data available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            loaded = load_performance_dataframe(results_dir)
            assert loaded is None


class TestZiplineMetricsSection:
    """Test building Zipline native metrics sections."""

    def test_build_benchmark_comparison(self):
        """Test building benchmark comparison section with alpha/beta."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with benchmark metrics
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "alpha": np.full(100, 0.05),
                    "beta": np.full(100, 0.85),
                    "benchmark_period_return": np.full(100, 0.10),
                    "algorithm_period_return": np.full(100, 0.12),
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build section
            section = build_zipline_metrics_section(results_dir)

            assert section != ""
            assert "Benchmark Comparison" in section
            assert "Alpha" in section
            assert "Beta" in section
            assert "0.05" in section or "0.0500" in section
            assert "0.85" in section

    def test_build_leverage_section(self):
        """Test building leverage analysis section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with leverage metrics
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "gross_leverage": np.random.rand(100) * 0.8,
                    "net_leverage": np.random.rand(100) * 0.5,
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build section
            section = build_zipline_metrics_section(results_dir)

            assert section != ""
            assert "Leverage Analysis" in section
            assert "Max Gross Leverage" in section
            assert "Max Net Leverage" in section
            assert "Avg Gross Leverage" in section
            assert "Avg Net Leverage" in section

    def test_build_time_series_metrics(self):
        """Test building time-series metrics summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with rolling metrics
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "sharpe": np.random.randn(100) * 0.3 + 1.0,
                    "sortino": np.random.randn(100) * 0.3 + 1.2,
                    "max_drawdown": -np.abs(np.random.randn(100) * 0.1),
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build section
            section = build_zipline_metrics_section(results_dir)

            assert section != ""
            assert "Time-Series Metrics" in section
            assert "Sharpe Ratio" in section
            assert "Sortino Ratio" in section
            assert "Max Drawdown" in section
            assert "Rolling" in section  # Should mention rolling calculations

    def test_build_empty_when_no_performance_data(self):
        """Test that empty string is returned when no performance data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            section = build_zipline_metrics_section(results_dir)
            assert section == ""

    def test_build_combined_sections(self):
        """Test building section with multiple metric types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with all metric types
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "alpha": np.full(100, 0.03),
                    "beta": np.full(100, 0.9),
                    "gross_leverage": np.random.rand(100) * 0.6,
                    "net_leverage": np.random.rand(100) * 0.4,
                    "sharpe": np.random.randn(100) * 0.2 + 1.0,
                    "sortino": np.random.randn(100) * 0.2 + 1.1,
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build section
            section = build_zipline_metrics_section(results_dir)

            assert section != ""
            assert (
                "Benchmark Comparison" in section
                or "Leverage Analysis" in section
                or "Time-Series Metrics" in section
            )


class TestTimeSeriesSummary:
    """Test building time-series metrics summary."""

    def test_build_sharpe_summary(self):
        """Test building summary for Sharpe ratio time-series."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with Sharpe ratio
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            sharpe_values = np.random.randn(100) * 0.3 + 1.0
            perf = pd.DataFrame(
                {
                    "sharpe": sharpe_values,
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build summary
            summary = build_time_series_summary(results_dir)

            assert summary != ""
            assert "Time-Series Metrics Summary" in summary
            assert "Sharpe Ratio" in summary
            assert "Mean" in summary
            assert "Std Dev" in summary
            assert "Min" in summary
            assert "Max" in summary
            assert "Final" in summary

    def test_build_multiple_metrics_summary(self):
        """Test building summary for multiple time-series metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with multiple metrics
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "sharpe": np.random.randn(100) * 0.3 + 1.0,
                    "sortino": np.random.randn(100) * 0.3 + 1.2,
                    "max_drawdown": -np.abs(np.random.randn(100) * 0.1),
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build summary
            summary = build_time_series_summary(results_dir)

            assert summary != ""
            assert "Sharpe Ratio" in summary
            assert "Sortino Ratio" in summary
            assert "Max Drawdown" in summary

    def test_build_empty_when_no_time_series_metrics(self):
        """Test that empty string is returned when no time-series metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame without time-series metrics
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            perf = pd.DataFrame(
                {
                    "returns": np.random.randn(100) * 0.01,
                    "portfolio_value": np.random.rand(100) * 100000,
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build summary
            summary = build_time_series_summary(results_dir)
            assert summary == ""

    def test_handle_nan_values(self):
        """Test that NaN values in metrics are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir)

            # Create performance DataFrame with some NaN values
            dates = pd.date_range("2020-01-01", periods=100, freq="D")
            sharpe_values = np.random.randn(100) * 0.3 + 1.0
            sharpe_values[10:20] = np.nan  # Add some NaN values
            perf = pd.DataFrame(
                {
                    "sharpe": sharpe_values,
                },
                index=dates,
            )

            # Save as pickle
            with open(results_dir / "performance.pkl", "wb") as f:
                pickle.dump(perf, f)

            # Build summary (should handle NaN gracefully)
            summary = build_time_series_summary(results_dir)

            # Should still produce summary (NaN values dropped)
            assert summary != ""
            assert "Sharpe Ratio" in summary
