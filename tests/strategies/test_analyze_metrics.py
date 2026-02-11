"""
Tests for strategy analyze() functions using lib/metrics.

Validates that all strategy analyze() functions use lib/metrics
instead of empyrical for metric calculations.
"""

import inspect
import warnings
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
import pytest

# Suppress warnings during imports
warnings.filterwarnings("ignore")


class TestAnalyzeMetrics:
    """Test suite for analyze() function metric calculations."""

    @pytest.fixture
    def project_root(self):
        """Project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def template_module(self, project_root):
        """Import strategy template module."""
        import importlib.util

        template_path = project_root / "strategies" / "_template" / "strategy.py"
        spec = importlib.util.spec_from_file_location("strategy_template", template_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @pytest.fixture
    def breakout_module(self, project_root):
        """Import breakout intraday strategy module."""
        import importlib.util

        breakout_path = project_root / "strategies" / "forex" / "breakout_intraday" / "strategy.py"
        spec = importlib.util.spec_from_file_location("breakout_strategy", breakout_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @pytest.fixture
    def forex_breakout_test_module(self, project_root):
        """Import forex_breakout_test strategy module."""
        import importlib.util

        test_path = project_root / "strategies" / "forex_breakout_test" / "strategy.py"
        spec = importlib.util.spec_from_file_location("forex_breakout_test", test_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_template_analyze_uses_lib_metrics(self, template_module):
        """Verify template analyze() uses lib/metrics instead of empyrical."""
        source = inspect.getsource(template_module.analyze)

        # Should import from lib/metrics
        assert "from lib.metrics" in inspect.getsource(template_module), (
            "Template should import from lib/metrics"
        )
        assert "calculate_sharpe_ratio" in source, (
            "Template analyze() should use calculate_sharpe_ratio from lib/metrics"
        )
        assert "calculate_sortino_ratio" in source, (
            "Template analyze() should use calculate_sortino_ratio from lib/metrics"
        )
        assert "calculate_max_drawdown" in source, (
            "Template analyze() should use calculate_max_drawdown from lib/metrics"
        )

        # Should NOT import empyrical directly
        assert "import empyrical" not in source, (
            "Template analyze() should NOT import empyrical directly"
        )
        assert "ep.sharpe_ratio" not in source, (
            "Template analyze() should NOT use empyrical.sharpe_ratio()"
        )
        assert "ep.sortino_ratio" not in source, (
            "Template analyze() should NOT use empyrical.sortino_ratio()"
        )
        assert "ep.max_drawdown" not in source, (
            "Template analyze() should NOT use empyrical.max_drawdown()"
        )

    def test_breakout_analyze_uses_lib_metrics(self, breakout_module):
        """Verify breakout strategy analyze() uses lib/metrics instead of empyrical."""
        source = inspect.getsource(breakout_module.analyze)

        # Should import from lib/metrics
        assert "from lib.metrics" in inspect.getsource(breakout_module), (
            "Breakout strategy should import from lib/metrics"
        )
        assert "calculate_sharpe_ratio" in source, (
            "Breakout analyze() should use calculate_sharpe_ratio from lib/metrics"
        )
        assert "calculate_sortino_ratio" in source, (
            "Breakout analyze() should use calculate_sortino_ratio from lib/metrics"
        )
        assert "calculate_max_drawdown" in source, (
            "Breakout analyze() should use calculate_max_drawdown from lib/metrics"
        )

        # Should NOT import empyrical directly
        assert "import empyrical" not in source, (
            "Breakout analyze() should NOT import empyrical directly"
        )
        assert "ep.sharpe_ratio" not in source, (
            "Breakout analyze() should NOT use empyrical.sharpe_ratio()"
        )
        assert "ep.sortino_ratio" not in source, (
            "Breakout analyze() should NOT use empyrical.sortino_ratio()"
        )
        assert "ep.max_drawdown" not in source, (
            "Breakout analyze() should NOT use empyrical.max_drawdown()"
        )

    def test_forex_breakout_test_analyze_uses_lib_metrics(self, forex_breakout_test_module):
        """Verify forex_breakout_test strategy analyze() uses lib/metrics instead of empyrical."""
        source = inspect.getsource(forex_breakout_test_module.analyze)

        # Should import from lib/metrics
        assert "from lib.metrics" in inspect.getsource(forex_breakout_test_module), (
            "Forex breakout test strategy should import from lib/metrics"
        )
        assert "calculate_sharpe_ratio" in source, (
            "Forex breakout test analyze() should use calculate_sharpe_ratio from lib/metrics"
        )
        assert "calculate_sortino_ratio" in source, (
            "Forex breakout test analyze() should use calculate_sortino_ratio from lib/metrics"
        )
        assert "calculate_max_drawdown" in source, (
            "Forex breakout test analyze() should use calculate_max_drawdown from lib/metrics"
        )

        # Should NOT import empyrical directly
        assert "import empyrical" not in source, (
            "Forex breakout test analyze() should NOT import empyrical directly"
        )
        assert "ep.sharpe_ratio" not in source, (
            "Forex breakout test analyze() should NOT use empyrical.sharpe_ratio()"
        )
        assert "ep.sortino_ratio" not in source, (
            "Forex breakout test analyze() should NOT use empyrical.sortino_ratio()"
        )
        assert "ep.max_drawdown" not in source, (
            "Forex breakout test analyze() should NOT use empyrical.max_drawdown()"
        )

    def test_template_analyze_function_signature(self, template_module):
        """Verify template analyze() function has correct signature."""
        analyze_func = getattr(template_module, "analyze")
        sig = inspect.signature(analyze_func)

        # Should accept context and perf parameters
        assert "context" in sig.parameters, "analyze() should accept 'context' parameter"
        assert "perf" in sig.parameters, "analyze() should accept 'perf' parameter"

    def test_template_analyze_calls_lib_metrics_functions(self, template_module):
        """Verify template analyze() actually calls lib/metrics functions."""
        source = inspect.getsource(template_module.analyze)

        # Should call lib/metrics functions with correct parameters
        assert "calculate_sharpe_ratio(" in source, "analyze() should call calculate_sharpe_ratio()"
        assert "risk_free_rate=" in source or "risk_free_rate:" in source, (
            "analyze() should pass risk_free_rate to calculate_sharpe_ratio()"
        )
        assert "trading_days_per_year=" in source or "trading_days_per_year:" in source, (
            "analyze() should pass trading_days_per_year to calculate_sharpe_ratio()"
        )

        assert "calculate_sortino_ratio(" in source, (
            "analyze() should call calculate_sortino_ratio()"
        )
        assert "calculate_max_drawdown(" in source, "analyze() should call calculate_max_drawdown()"

    def test_template_analyze_handles_empty_returns(self, template_module):
        """Verify template analyze() handles empty returns gracefully."""
        # Mock context and perf with empty returns
        mock_context = Mock()
        mock_context.portfolio = Mock()
        mock_context.portfolio.starting_cash = 100000
        mock_context.portfolio.portfolio_value = 100000

        # Create perf DataFrame with minimal data (one row with matching index)
        dates = pd.date_range("2020-01-01", periods=1, freq="D")
        perf = pd.DataFrame(
            {"portfolio_value": [100000], "returns": pd.Series([], dtype=float)}, index=dates
        )

        # Mock load_params to return test params
        with patch.object(
            template_module,
            "load_params",
            return_value={
                "strategy": {"asset_symbol": "SPY", "asset_class": "equities"},
                "backtest": {"risk_free_rate": 0.04, "trading_days_per_year": 252},
            },
        ):
            # Should not raise exception - empty returns should result in zero metrics
            try:
                template_module.analyze(mock_context, perf)
            except Exception as e:
                pytest.fail(f"analyze() should handle empty returns gracefully. Error: {e}")

    def test_template_analyze_passes_correct_parameters(self, template_module):
        """Verify template analyze() passes correct parameters to lib/metrics functions."""
        source = inspect.getsource(template_module.analyze)

        # Verify that risk_free_rate and trading_days_per_year are passed
        assert "risk_free_rate=" in source or "risk_free_rate:" in source, (
            "analyze() should pass risk_free_rate to calculate_sharpe_ratio()"
        )
        assert "trading_days_per_year=" in source or "trading_days_per_year:" in source, (
            "analyze() should pass trading_days_per_year to calculate_sharpe_ratio()"
        )

        # Verify all three functions are called with returns
        assert "calculate_sharpe_ratio(" in source and "returns" in source, (
            "analyze() should call calculate_sharpe_ratio() with returns"
        )
        assert "calculate_sortino_ratio(" in source and "returns" in source, (
            "analyze() should call calculate_sortino_ratio() with returns"
        )
        assert "calculate_max_drawdown(" in source and "returns" in source, (
            "analyze() should call calculate_max_drawdown() with returns"
        )
