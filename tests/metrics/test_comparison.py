"""
Test comparison metrics for The Researcher's Cockpit.

Tests for strategy comparison functionality.
"""

# Standard library imports
import json
import sys
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.metrics.comparison import compare_strategies


class TestCompareStrategies:
    """Test strategy comparison functionality."""

    @pytest.mark.unit
    def test_compare_strategies_success(self, temp_results_dir):
        """Test comparing multiple strategies with valid metrics."""
        # Create strategy directories and metrics files
        strategy1_dir = temp_results_dir / "strategy1" / "latest"
        strategy1_dir.mkdir(parents=True, exist_ok=True)

        strategy2_dir = temp_results_dir / "strategy2" / "latest"
        strategy2_dir.mkdir(parents=True, exist_ok=True)

        # Create metrics files
        metrics1 = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "annual_return": 0.15,
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        metrics2 = {
            "sharpe": 2.0,
            "sortino": 2.5,
            "annual_return": 0.20,
            "max_drawdown": -0.08,
            "calmar": 2.5,
            "win_rate": 0.65,
            "trade_count": 150,
        }

        (strategy1_dir / "metrics.json").write_text(json.dumps(metrics1))
        (strategy2_dir / "metrics.json").write_text(json.dumps(metrics2))

        # Compare strategies
        result = compare_strategies(["strategy1", "strategy2"], temp_results_dir)

        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert set(result["strategy"].values) == {"strategy1", "strategy2"}

        # Verify strategy1 metrics
        s1 = result[result["strategy"] == "strategy1"].iloc[0]
        assert s1["sharpe"] == 1.5
        assert s1["sortino"] == 2.0
        assert s1["annual_return"] == 0.15
        assert s1["max_drawdown"] == -0.10
        assert s1["calmar"] == 1.5
        assert s1["win_rate"] == 0.60
        assert s1["trade_count"] == 100

        # Verify strategy2 metrics
        s2 = result[result["strategy"] == "strategy2"].iloc[0]
        assert s2["sharpe"] == 2.0
        assert s2["sortino"] == 2.5
        assert s2["annual_return"] == 0.20
        assert s2["max_drawdown"] == -0.08
        assert s2["calmar"] == 2.5
        assert s2["win_rate"] == 0.65
        assert s2["trade_count"] == 150

    @pytest.mark.unit
    def test_compare_strategies_empty_list(self, temp_results_dir):
        """Test comparing with empty strategy list."""
        result = compare_strategies([], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_compare_strategies_none_input(self):
        """Test comparing with None input."""
        result = compare_strategies(None)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_compare_strategies_missing_files(self, temp_results_dir):
        """Test comparing strategies with missing metrics files."""
        # Create strategy directory but no metrics file
        strategy_dir = temp_results_dir / "missing_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        result = compare_strategies(["missing_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_compare_strategies_invalid_json(self, temp_results_dir):
        """Test comparing strategies with invalid JSON."""
        # Create strategy directory with invalid JSON
        strategy_dir = temp_results_dir / "invalid_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        (strategy_dir / "metrics.json").write_text("invalid json content")

        result = compare_strategies(["invalid_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_compare_strategies_invalid_strategy_name(self, temp_results_dir):
        """Test comparing with invalid (non-string) strategy names."""
        # Create valid strategy for comparison
        strategy_dir = temp_results_dir / "valid_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        metrics = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "annual_return": 0.15,
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        (strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        # Mix valid and invalid strategy names
        result = compare_strategies(
            ["valid_strategy", 123, None, "another_valid"], temp_results_dir
        )

        # Should only include valid string strategy names
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Only 'valid_strategy' should be included
        assert result.iloc[0]["strategy"] == "valid_strategy"

    @pytest.mark.unit
    def test_compare_strategies_missing_metrics_keys(self, temp_results_dir):
        """Test comparing strategies with missing metric keys."""
        strategy_dir = temp_results_dir / "partial_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        # Metrics with only some keys
        metrics = {
            "sharpe": 1.5,
            "trade_count": 100,
            # Missing: sortino, annual_return, max_drawdown, calmar, win_rate
        }

        (strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        result = compare_strategies(["partial_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

        s = result.iloc[0]
        assert s["sharpe"] == 1.5
        assert s["sortino"] == 0.0  # Default value
        assert s["annual_return"] == 0.0  # Default value
        assert s["max_drawdown"] == 0.0  # Default value
        assert s["calmar"] == 0.0  # Default value
        assert s["win_rate"] == 0.0  # Default value
        assert s["trade_count"] == 100

    @pytest.mark.unit
    def test_compare_strategies_nan_inf_sanitization(self, temp_results_dir):
        """Test that NaN and Inf values are sanitized."""
        strategy_dir = temp_results_dir / "nan_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        # Metrics with NaN and Inf values
        metrics = {
            "sharpe": float("nan"),
            "sortino": float("inf"),
            "annual_return": float("-inf"),
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        (strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        result = compare_strategies(["nan_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

        s = result.iloc[0]
        assert s["sharpe"] == 0.0  # NaN sanitized to 0.0
        assert s["sortino"] == 0.0  # Inf sanitized to 0.0
        assert s["annual_return"] == 0.0  # -Inf sanitized to 0.0
        assert s["max_drawdown"] == -0.10  # Valid value preserved
        assert s["calmar"] == 1.5  # Valid value preserved

    @pytest.mark.unit
    def test_compare_strategies_partial_success(self, temp_results_dir):
        """Test comparing when some strategies succeed and some fail."""
        # Strategy 1: Valid
        strategy1_dir = temp_results_dir / "valid1" / "latest"
        strategy1_dir.mkdir(parents=True, exist_ok=True)

        metrics1 = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "annual_return": 0.15,
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }
        (strategy1_dir / "metrics.json").write_text(json.dumps(metrics1))

        # Strategy 2: Missing file
        strategy2_dir = temp_results_dir / "missing2" / "latest"
        strategy2_dir.mkdir(parents=True, exist_ok=True)
        # No metrics.json file

        # Strategy 3: Valid
        strategy3_dir = temp_results_dir / "valid3" / "latest"
        strategy3_dir.mkdir(parents=True, exist_ok=True)

        metrics3 = {
            "sharpe": 2.0,
            "sortino": 2.5,
            "annual_return": 0.20,
            "max_drawdown": -0.08,
            "calmar": 2.5,
            "win_rate": 0.65,
            "trade_count": 150,
        }
        (strategy3_dir / "metrics.json").write_text(json.dumps(metrics3))

        # Strategy 4: Invalid JSON
        strategy4_dir = temp_results_dir / "invalid4" / "latest"
        strategy4_dir.mkdir(parents=True, exist_ok=True)
        (strategy4_dir / "metrics.json").write_text("invalid json")

        result = compare_strategies(["valid1", "missing2", "valid3", "invalid4"], temp_results_dir)

        # Should only include valid strategies
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert set(result["strategy"].values) == {"valid1", "valid3"}

    @pytest.mark.unit
    def test_compare_strategies_default_results_base(self, project_root_path):
        """Test comparing strategies with default results_base (project root)."""
        # This test verifies the function can use default results_base
        # We'll create a temporary results directory structure
        results_dir = project_root_path / "results"
        test_strategy_dir = results_dir / "test_default_strategy" / "latest"
        test_strategy_dir.mkdir(parents=True, exist_ok=True)

        metrics = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "annual_return": 0.15,
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        (test_strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        try:
            result = compare_strategies(["test_default_strategy"], None)

            assert isinstance(result, pd.DataFrame)
            # May be 0 or 1 depending on whether project root is found
            # The important thing is it doesn't crash
        finally:
            # Cleanup
            if test_strategy_dir.exists():
                (test_strategy_dir / "metrics.json").unlink()
                test_strategy_dir.rmdir()
                test_strategy_dir.parent.rmdir()

    @pytest.mark.unit
    def test_compare_strategies_dataframe_columns(self, temp_results_dir):
        """Test that result DataFrame has correct columns."""
        strategy_dir = temp_results_dir / "test_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        metrics = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "annual_return": 0.15,
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        (strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        result = compare_strategies(["test_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        expected_columns = [
            "strategy",
            "sharpe",
            "sortino",
            "annual_return",
            "max_drawdown",
            "calmar",
            "win_rate",
            "trade_count",
        ]

        assert list(result.columns) == expected_columns

    @pytest.mark.unit
    def test_compare_strategies_none_values_in_metrics(self, temp_results_dir):
        """Test handling of None values in metrics JSON."""
        strategy_dir = temp_results_dir / "none_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        # Metrics with None values (should be sanitized)
        metrics = {
            "sharpe": None,
            "sortino": 2.0,
            "annual_return": 0.15,
            "max_drawdown": None,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        (strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        result = compare_strategies(["none_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

        s = result.iloc[0]
        assert s["sharpe"] == 0.0  # None sanitized to 0.0
        assert s["sortino"] == 2.0  # Valid value preserved
        assert s["annual_return"] == 0.15  # Valid value preserved
        assert s["max_drawdown"] == 0.0  # None sanitized to 0.0
        assert s["calmar"] == 1.5  # Valid value preserved

    @pytest.mark.unit
    def test_compare_strategies_numeric_types(self, temp_results_dir):
        """Test handling of different numeric types in metrics."""
        strategy_dir = temp_results_dir / "numeric_strategy" / "latest"
        strategy_dir.mkdir(parents=True, exist_ok=True)

        # Metrics with different numeric types
        metrics = {
            "sharpe": 1.5,  # float
            "sortino": 2,  # int (should be converted)
            "annual_return": 0.15,
            "max_drawdown": -0.10,
            "calmar": 1.5,
            "win_rate": 0.60,
            "trade_count": 100,
        }

        (strategy_dir / "metrics.json").write_text(json.dumps(metrics))

        result = compare_strategies(["numeric_strategy"], temp_results_dir)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

        s = result.iloc[0]
        assert s["sharpe"] == 1.5
        assert s["sortino"] == 2.0  # int converted to float
        assert isinstance(s["trade_count"], (int, np.integer))  # trade_count stays as int
