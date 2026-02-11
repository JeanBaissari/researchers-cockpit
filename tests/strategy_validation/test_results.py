"""
Tests for strategy validation result persistence utilities.

Focused on `lib.strategy_validation.results` functions that save artifacts to disk
and maintain a `latest` symlink.
"""

# Standard library imports
import json
import sys
from pathlib import Path

# Third-party imports
import pandas as pd
import pytest

# Local imports
from lib.strategy_validation import results as results_module


@pytest.mark.unit
def test_save_walk_forward_results_writes_expected_artifacts_and_latest_symlink(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(results_module, "get_project_root", lambda: tmp_path)

    fixed_dir = tmp_path / "results" / "my_strategy" / "walkforward_20990101_000000"

    def _timestamp_dir_stub(base_path: Path, prefix: str) -> Path:
        assert prefix == "walkforward"
        fixed_dir.mkdir(parents=True, exist_ok=True)
        return fixed_dir

    monkeypatch.setattr(results_module, "timestamp_dir", _timestamp_dir_stub)

    is_df = pd.DataFrame([{"a": 1, "b": 2}])
    oos_df = pd.DataFrame([{"c": 3, "d": 4}])
    robustness = {"score": 0.88, "notes": "ok"}

    out_dir = results_module.save_walk_forward_results(
        strategy_name="my_strategy",
        is_df=is_df,
        oos_df=oos_df,
        robustness=robustness,
        asset_class="forex",
    )

    assert out_dir == fixed_dir

    assert (fixed_dir / "in_sample_results.csv").exists()
    assert (fixed_dir / "out_sample_results.csv").exists()
    assert (fixed_dir / "robustness_score.json").exists()

    # Robustness JSON should match exactly.
    loaded = json.loads((fixed_dir / "robustness_score.json").read_text())
    assert loaded == robustness

    # Latest symlink should point to the created directory.
    latest_link = tmp_path / "results" / "my_strategy" / "latest"
    assert latest_link.is_symlink()
    assert latest_link.resolve() == fixed_dir.resolve()


@pytest.mark.unit
def test_save_walk_forward_results_skips_csv_writes_for_empty_dataframes(tmp_path, monkeypatch):
    monkeypatch.setattr(results_module, "get_project_root", lambda: tmp_path)

    fixed_dir = tmp_path / "results" / "my_strategy" / "walkforward_20990101_000001"

    def _timestamp_dir_stub(base_path: Path, prefix: str) -> Path:
        fixed_dir.mkdir(parents=True, exist_ok=True)
        return fixed_dir

    monkeypatch.setattr(results_module, "timestamp_dir", _timestamp_dir_stub)

    out_dir = results_module.save_walk_forward_results(
        strategy_name="my_strategy",
        is_df=pd.DataFrame(),
        oos_df=pd.DataFrame(),
        robustness={"score": 0.0},
    )

    assert out_dir == fixed_dir
    assert not (fixed_dir / "in_sample_results.csv").exists()
    assert not (fixed_dir / "out_sample_results.csv").exists()
    assert (fixed_dir / "robustness_score.json").exists()


@pytest.mark.unit
def test_save_monte_carlo_results_writes_expected_artifacts_and_calls_plot_hook(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(results_module, "get_project_root", lambda: tmp_path)

    fixed_dir = tmp_path / "results" / "my_strategy" / "montecarlo_20990101_000000"

    def _timestamp_dir_stub(base_path: Path, prefix: str) -> Path:
        assert prefix == "montecarlo"
        fixed_dir.mkdir(parents=True, exist_ok=True)
        return fixed_dir

    monkeypatch.setattr(results_module, "timestamp_dir", _timestamp_dir_stub)

    plot_calls = {"count": 0}

    class _PlotsStub:
        @staticmethod
        def _plot_monte_carlo_distribution(simulation_results, out_dir: Path) -> None:
            plot_calls["count"] += 1
            assert out_dir == fixed_dir
            assert "simulation_paths" in simulation_results

    # Ensure the relative import in results.py (`from ..plots import ...`) resolves.
    monkeypatch.setitem(sys.modules, "lib.plots", _PlotsStub)

    idx = pd.date_range("2020-01-01", periods=3, freq="D", tz="UTC")
    simulation_paths = pd.DataFrame(
        {"sim_0": [100.0, 101.0, 102.0], "sim_1": [100.0, 99.0, 98.0]},
        index=idx,
    )

    simulation_results = {
        "simulation_paths": simulation_paths,
        "confidence_intervals": {"p5": 95.0, "p50": 100.0, "p95": 105.0},
        "final_value_stats": {"mean": 100.0, "std": 1.0, "min": 98.0, "max": 102.0},
    }

    out_dir = results_module.save_monte_carlo_results(
        strategy_name="my_strategy",
        simulation_results=simulation_results,
        asset_class="crypto",
    )

    assert out_dir == fixed_dir
    assert (fixed_dir / "simulation_paths.csv").exists()
    assert (fixed_dir / "confidence_intervals.json").exists()
    assert (fixed_dir / "final_value_stats.json").exists()
    assert plot_calls["count"] == 1

    latest_link = tmp_path / "results" / "my_strategy" / "latest"
    assert latest_link.is_symlink()
    assert latest_link.resolve() == fixed_dir.resolve()


@pytest.mark.unit
def test_save_monte_carlo_results_swallow_plot_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(results_module, "get_project_root", lambda: tmp_path)

    fixed_dir = tmp_path / "results" / "my_strategy" / "montecarlo_20990101_000001"

    def _timestamp_dir_stub(base_path: Path, prefix: str) -> Path:
        fixed_dir.mkdir(parents=True, exist_ok=True)
        return fixed_dir

    monkeypatch.setattr(results_module, "timestamp_dir", _timestamp_dir_stub)

    class _PlotsStub:
        @staticmethod
        def _plot_monte_carlo_distribution(simulation_results, out_dir: Path) -> None:
            raise RuntimeError("plot failed")

    monkeypatch.setitem(sys.modules, "lib.plots", _PlotsStub)

    idx = pd.date_range("2020-01-01", periods=2, freq="D", tz="UTC")
    simulation_results = {"simulation_paths": pd.DataFrame({"sim_0": [1.0, 2.0]}, index=idx)}

    out_dir = results_module.save_monte_carlo_results(
        strategy_name="my_strategy",
        simulation_results=simulation_results,
    )

    assert out_dir == fixed_dir
    assert (fixed_dir / "simulation_paths.csv").exists()
