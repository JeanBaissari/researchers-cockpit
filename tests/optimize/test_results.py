"""
Tests for optimization results handling.

Focused on `lib.optimize.results` utilities that persist optimization artifacts.
"""

# Standard library imports
import json
import sys
from pathlib import Path

# Third-party imports
import pandas as pd
import pytest
import yaml

# Local imports (match existing test pattern)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.optimize import results as results_module


class TestOptimizeResults:
    """Tests for `lib.optimize.results` module."""

    @pytest.mark.unit
    def test_deep_copy_dict_is_deep(self):
        original = {"a": {"b": [1, 2, 3]}, "c": 4}
        copied = results_module.deep_copy_dict(original)

        assert copied == original
        assert copied is not original
        assert copied["a"] is not original["a"]
        assert copied["a"]["b"] is not original["a"]["b"]

        copied["a"]["b"].append(999)
        assert original["a"]["b"] == [1, 2, 3]

    @pytest.mark.unit
    def test_set_nested_param_creates_nested_dicts(self):
        params: dict = {}
        results_module.set_nested_param(params, "strategy.fast_period", 10)
        results_module.set_nested_param(params, "strategy.slow_period", 30)
        results_module.set_nested_param(params, "risk.max_drawdown", 0.2)

        assert params == {
            "strategy": {"fast_period": 10, "slow_period": 30},
            "risk": {"max_drawdown": 0.2},
        }

    @pytest.mark.unit
    def test_save_optimization_results_writes_expected_artifacts(self, tmp_path, monkeypatch):
        # Make project root deterministic and avoid timestamp variability.
        monkeypatch.setattr(results_module, "get_project_root", lambda: tmp_path)

        fixed_dir = tmp_path / "results" / "my_strategy" / "optimization_20990101_000000"

        def _timestamp_dir_stub(base, prefix):
            fixed_dir.mkdir(parents=True, exist_ok=True)
            return fixed_dir

        monkeypatch.setattr(results_module, "timestamp_dir", _timestamp_dir_stub)

        # Provide a stub plotter to ensure the heatmap branch runs without being swallowed.
        plot_calls = {"count": 0}

        class _PlotsStub:
            @staticmethod
            def _plot_optimization_heatmap(results_df, param_grid, objective, out_dir):
                plot_calls["count"] += 1
                assert out_dir == fixed_dir

        monkeypatch.setitem(sys.modules, "lib.plots", _PlotsStub)

        param_grid = {"strategy.fast_period": [5, 10], "strategy.slow_period": [20, 30]}
        results_df = pd.DataFrame(
            [
                {
                    "strategy.fast_period": 5,
                    "strategy.slow_period": 20,
                    "train_sharpe": 0.7,
                    "test_sharpe": 0.2,
                },
                {
                    "strategy.fast_period": 10,
                    "strategy.slow_period": 30,
                    "train_sharpe": 1.2,
                    "test_sharpe": 0.9,
                },
            ]
        )

        result_dir = results_module.save_optimization_results(
            strategy_name="my_strategy",
            results_df=results_df,
            param_grid=param_grid,
            objective="sharpe",
            train_metrics={"train_key": 1},
            test_metrics={"test_key": 2},
            asset_class="forex",
        )

        assert result_dir == fixed_dir
        assert (fixed_dir / "grid_results.csv").exists()
        assert (fixed_dir / "in_sample_metrics.json").exists()
        assert (fixed_dir / "out_sample_metrics.json").exists()
        assert (fixed_dir / "overfit_score.json").exists()
        assert (fixed_dir / "best_params.yaml").exists()

        # Best params should be nested per dot-notation.
        best_params = yaml.safe_load((fixed_dir / "best_params.yaml").read_text())
        assert best_params == {"strategy": {"fast_period": 10, "slow_period": 30}}

        overfit = json.loads((fixed_dir / "overfit_score.json").read_text())
        assert "pbo" in overfit
        assert "efficiency" in overfit
        assert overfit["in_sample"] == pytest.approx(1.2)
        assert overfit["out_sample"] == pytest.approx(0.9)

        # Heatmap branch should be exercised once for 2-parameter grids.
        assert plot_calls["count"] == 1

        # Latest symlink should point to the created directory.
        latest_link = tmp_path / "results" / "my_strategy" / "latest"
        assert latest_link.is_symlink()
        assert latest_link.resolve() == fixed_dir.resolve()

    @pytest.mark.unit
    def test_save_optimization_results_skips_best_params_when_objective_missing(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(results_module, "get_project_root", lambda: tmp_path)

        fixed_dir = tmp_path / "results" / "my_strategy" / "optimization_20990101_000001"

        def _timestamp_dir_stub(base, prefix):
            fixed_dir.mkdir(parents=True, exist_ok=True)
            return fixed_dir

        monkeypatch.setattr(results_module, "timestamp_dir", _timestamp_dir_stub)

        # Objective columns are missing; should still write core artifacts.
        results_df = pd.DataFrame([{"strategy.fast_period": 5, "train_sharpe": 0.1}])

        result_dir = results_module.save_optimization_results(
            strategy_name="my_strategy",
            results_df=results_df,
            param_grid={"strategy.fast_period": [5]},
            objective="sharpe",
            train_metrics={"train_key": 1},
            test_metrics={"test_key": 2},
        )

        assert result_dir == fixed_dir
        assert (fixed_dir / "grid_results.csv").exists()
        assert (fixed_dir / "in_sample_metrics.json").exists()
        assert (fixed_dir / "out_sample_metrics.json").exists()

        # Since `test_{objective}` is absent, these should not be written.
        assert not (fixed_dir / "best_params.yaml").exists()
        assert not (fixed_dir / "overfit_score.json").exists()
