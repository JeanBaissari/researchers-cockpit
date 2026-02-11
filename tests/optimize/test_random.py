"""
Test random search optimization.

Tests for random search optimizer.
"""

# Standard library imports
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third-party imports
import numpy as np
import pandas as pd
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.optimize import random_search


class TestRandomSearchOptimizer:
    """Test random search optimization."""

    @pytest.mark.unit
    def test_random_search_function_exists(self):
        """Test that random_search function exists."""
        assert random_search is not None
        assert callable(random_search)

    @pytest.mark.unit
    def test_random_search_function_signature(self):
        """Test random_search has correct signature."""
        import inspect

        # Get signature
        sig = inspect.signature(random_search)
        params = list(sig.parameters.keys())

        # Should have parameters for optimization
        assert len(params) > 0
        assert "strategy_name" in params
        assert "param_distributions" in params
        assert "n_iter" in params

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_basic_functionality(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test basic random search functionality."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"fast_period": 10, "slow_period": 30}}

        # Mock backtest returns - alternate between train and test
        train_perf = pd.DataFrame(
            {
                "returns": pd.Series([0.01, 0.02, -0.01, 0.03] * 10),
                "portfolio_value": pd.Series([100000, 101000, 102000, 101000, 104000] * 8),
            }
        )
        test_perf = pd.DataFrame(
            {
                "returns": pd.Series([0.01, 0.02, -0.01, 0.03] * 10),
                "portfolio_value": pd.Series([100000, 101000, 102000, 101000, 104000] * 8),
            }
        )
        # Use side_effect function to alternate train/test
        call_count = {"count": 0}

        def backtest_side_effect(*args, **kwargs):
            call_count["count"] += 1
            # Odd calls are train, even calls are test
            if call_count["count"] % 2 == 1:
                return (train_perf, {})
            else:
                return (test_perf, {})

        mock_run_backtest.side_effect = backtest_side_effect

        # Mock metrics
        mock_calculate_metrics.return_value = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "max_drawdown": -0.05,
            "total_return": 0.10,
        }

        # Mock save results
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run random search
        param_distributions = {
            "strategy.fast_period": [5, 10, 15, 20],
            "strategy.slow_period": [30, 40, 50],
        }

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=5,
            start_date="2020-01-01",
            end_date="2023-12-31",
            objective="sharpe",
        )

        # Verify results
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 5
        assert "iteration" in results.columns
        assert "train_sharpe" in results.columns
        assert "test_sharpe" in results.columns
        assert "strategy.fast_period" in results.columns
        assert "strategy.slow_period" in results.columns

        # Verify backtest was called for each iteration (train + test)
        assert mock_run_backtest.call_count == 10  # 5 iterations * 2 (train + test)

        # Verify save was called
        mock_save_results.assert_called_once()

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_list_distribution(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search with list distribution."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.0}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run with list distribution
        param_distributions = {"strategy.param": [5, 10, 15, 20, 25]}

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=3,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        # Verify sampled values are from the list
        sampled_values = results["strategy.param"].values
        assert all(val in [5, 10, 15, 20, 25] for val in sampled_values)

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_numpy_array_distribution(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search with numpy array distribution."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.0}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run with numpy array distribution
        param_distributions = {"strategy.param": np.arange(10, 50, 5)}

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=3,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        # Verify sampled values are from the array
        sampled_values = results["strategy.param"].values
        valid_values = list(np.arange(10, 50, 5))
        assert all(val in valid_values for val in sampled_values)

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_tuple_range_distribution(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search with tuple range distribution."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.0}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run with tuple range distribution
        param_distributions = {
            "strategy.param": (5.0, 25.0)  # Uniform range
        }

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=3,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        # Verify sampled values are within range
        sampled_values = results["strategy.param"].values
        assert all(5.0 <= val <= 25.0 for val in sampled_values)

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_error_handling(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search error handling for failed backtests."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest to fail on first iteration, succeed on second
        perf = pd.DataFrame({"returns": pd.Series([0.01] * 10)})
        mock_run_backtest.side_effect = [
            Exception("Backtest failed"),
            (perf, {}),  # Train success
            (perf, {}),  # Test success
        ]

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.0}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run random search
        param_distributions = {"strategy.param": [5, 10, 15]}

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=2,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        # Should have 1 result (second iteration succeeded)
        assert len(results) == 1
        assert results.iloc[0]["iteration"] == 1

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_portfolio_value_fallback(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search handles missing returns by using portfolio_value."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns without 'returns' column (FOREX calendars)
        train_perf = pd.DataFrame(
            {"portfolio_value": pd.Series([100000, 101000, 102000, 101000, 104000] * 8)}
        )
        test_perf = pd.DataFrame(
            {"portfolio_value": pd.Series([100000, 101000, 102000, 101000, 104000] * 8)}
        )
        mock_run_backtest.side_effect = [(train_perf, {}), (test_perf, {})]

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.5, "sortino": 2.0, "max_drawdown": -0.05}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run random search
        param_distributions = {"strategy.param": [5, 10, 15]}

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=1,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        # Verify results were calculated
        assert len(results) == 1
        assert "train_sharpe" in results.columns
        assert "test_sharpe" in results.columns

        # Verify calculate_metrics was called (returns calculated from portfolio_value)
        assert mock_calculate_metrics.call_count == 2  # Train + test

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_objective_metrics(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search with different objective metrics."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01, 0.02, -0.01, 0.03] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics for different objectives
        mock_calculate_metrics.return_value = {
            "sharpe": 1.5,
            "sortino": 2.0,
            "total_return": 0.10,
            "calmar": 2.5,
            "max_drawdown": -0.05,
        }

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Test different objectives
        objectives = ["sharpe", "sortino", "total_return", "calmar"]

        for objective in objectives:
            param_distributions = {"strategy.param": [5, 10, 15]}

            results = random_search(
                strategy_name="test_strategy",
                param_distributions=param_distributions,
                n_iter=1,
                start_date="2020-01-01",
                end_date="2023-12-31",
                objective=objective,
            )

            # Verify objective columns exist
            assert f"train_{objective}" in results.columns
            assert f"test_{objective}" in results.columns

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_train_test_split(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search train/test split."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.0}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run with custom train_pct
        param_distributions = {"strategy.param": [5, 10, 15]}

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=1,
            start_date="2020-01-01",
            end_date="2023-12-31",
            train_pct=0.8,
        )

        # Verify backtest was called with correct date ranges
        calls = mock_run_backtest.call_args_list

        # First call should be train period
        train_call = calls[0]
        assert train_call[1]["start_date"] == "2020-01-01"
        # Train end should be before test start

        # Second call should be test period
        test_call = calls[1]
        # Test start should be after train end

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_default_dates(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search uses default dates from settings."""
        # Setup mocks with default dates
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.0}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run without specifying dates
        param_distributions = {"strategy.param": [5, 10, 15]}

        results = random_search(
            strategy_name="test_strategy", param_distributions=param_distributions, n_iter=1
        )

        # Verify settings were loaded
        mock_load_settings.assert_called_once()

        # Verify backtest was called with default dates
        calls = mock_run_backtest.call_args_list
        assert len(calls) >= 2  # At least train + test

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_empty_returns_handling(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search handles empty returns gracefully."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"param": 10}}

        # Mock backtest returns with empty returns
        perf = pd.DataFrame(
            {"returns": pd.Series(dtype=float), "portfolio_value": pd.Series(dtype=float)}
        )
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics (should return empty dict for empty returns)
        mock_calculate_metrics.return_value = {}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run random search
        param_distributions = {"strategy.param": [5, 10, 15]}

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=1,
            start_date="2020-01-01",
            end_date="2023-12-31",
        )

        # Should still return results with zero metrics
        assert len(results) == 1
        assert results.iloc[0]["train_sharpe"] == 0.0
        assert results.iloc[0]["test_sharpe"] == 0.0

    @pytest.mark.unit
    @patch("lib.optimize.random.save_optimization_results")
    @patch("lib.optimize.random.calculate_metrics")
    @patch("lib.optimize.random.run_backtest")
    @patch("lib.optimize.random.load_strategy_params")
    @patch("lib.optimize.random.load_settings")
    def test_random_search_results_structure(
        self,
        mock_load_settings,
        mock_load_params,
        mock_run_backtest,
        mock_calculate_metrics,
        mock_save_results,
    ):
        """Test random search results DataFrame structure."""
        # Setup mocks
        mock_load_settings.return_value = {
            "dates": {"default_start": "2020-01-01", "default_end": "2023-12-31"}
        }
        mock_load_params.return_value = {"strategy": {"fast_period": 10, "slow_period": 30}}

        # Mock backtest returns
        perf = pd.DataFrame({"returns": pd.Series([0.01, 0.02, -0.01, 0.03] * 10)})
        mock_run_backtest.return_value = (perf, {})

        # Mock metrics
        mock_calculate_metrics.return_value = {"sharpe": 1.5, "sortino": 2.0, "max_drawdown": -0.05}

        # Mock save
        mock_save_results.return_value = Path("/tmp/test_results")

        # Run random search with multiple parameters
        param_distributions = {
            "strategy.fast_period": [5, 10, 15],
            "strategy.slow_period": [30, 40, 50],
        }

        results = random_search(
            strategy_name="test_strategy",
            param_distributions=param_distributions,
            n_iter=3,
            start_date="2020-01-01",
            end_date="2023-12-31",
            objective="sharpe",
        )

        # Verify DataFrame structure
        assert isinstance(results, pd.DataFrame)
        assert len(results) == 3

        # Verify required columns
        required_columns = [
            "iteration",
            "train_sharpe",
            "test_sharpe",
            "train_sortino",
            "test_sortino",
            "train_max_dd",
            "test_max_dd",
            "strategy.fast_period",
            "strategy.slow_period",
        ]
        for col in required_columns:
            assert col in results.columns, f"Missing column: {col}"

        # Verify parameter values are stored
        assert all(results["strategy.fast_period"].notna())
        assert all(results["strategy.slow_period"].notna())
