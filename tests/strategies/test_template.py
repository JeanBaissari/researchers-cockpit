"""
Tests for strategy template validation.

Validates that the strategy template follows Zipline-Reloaded API patterns
and project conventions.
"""

import inspect
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Suppress warnings during template import
warnings.filterwarnings("ignore")


class TestStrategyTemplate:
    """Test suite for strategy template validation."""

    @pytest.fixture
    def template_path(self):
        """Path to strategy template."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "strategies" / "_template" / "strategy.py"

    @pytest.fixture
    def template_module(self, template_path):
        """Import strategy template module."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("strategy_template", template_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_template_file_exists(self, template_path):
        """Verify template file exists."""
        assert template_path.exists(), f"Template file not found: {template_path}"

    def test_template_can_be_imported(self, template_module):
        """Verify template can be imported without syntax errors."""
        assert template_module is not None
        assert hasattr(template_module, "__file__")

    def test_required_functions_exist(self, template_module):
        """Verify all required strategy functions exist."""
        required_functions = [
            "initialize",
            "compute_signals",
            "rebalance",
            "load_params",
            "make_pipeline",
            "before_trading_start",
            "check_stop_loss",
            "handle_data",
            "analyze",
        ]

        for func_name in required_functions:
            assert hasattr(template_module, func_name), (
                f"Required function '{func_name}' not found in template"
            )
            func = getattr(template_module, func_name)
            assert callable(func), f"'{func_name}' is not callable"

    def test_zipline_imports_are_direct(self, template_module):
        """Verify Zipline imports use direct APIs (no wrappers)."""
        source = inspect.getsource(template_module)

        # Should import from zipline.api directly
        assert "from zipline.api import" in source, (
            "Template should import directly from zipline.api"
        )

        # Should NOT import wrapper functions (removed in v1.12.0)
        # Check actual import statements, not docstring examples
        import_lines = [
            line.strip()
            for line in source.split("\n")
            if line.strip().startswith("from ") or line.strip().startswith("import ")
        ]
        wrapper_imports = [
            line for line in import_lines if "aggregate_ohlcv" in line or "SessionManager" in line
        ]
        assert len(wrapper_imports) == 0, (
            f"Template should NOT import wrapper functions. Found: {wrapper_imports}"
        )

        # Should use direct pandas for aggregation
        assert "resample(" in source, "Template should use direct pandas resample() for aggregation"

    def test_data_history_api_usage(self, template_module):
        """Verify data.history() is used correctly."""
        source = inspect.getsource(template_module)

        # Should use data.history() with correct signature
        assert "data.history(" in source, "Template should use data.history() API"

        # Should use positional arguments (Zipline-Reloaded pattern)
        # Pattern: data.history(asset, field, bar_count, frequency)
        assert (
            "data.history(context.asset, 'price'" in source
            or "data.history(context.asset, ['open'" in source
        ), "Template should use data.history() with correct signature"

    def test_data_current_api_usage(self, template_module):
        """Verify data.current() is used correctly."""
        source = inspect.getsource(template_module)

        # Should use data.current() API
        assert "data.current(" in source, "Template should use data.current() API"

        # Should use 'price' field (adjusted close)
        assert "data.current(context.asset, 'price')" in source, (
            "Template should use 'price' field for current price"
        )

    def test_pipeline_api_fallback(self, template_module):
        """Verify Pipeline API has proper fallback pattern."""
        source = inspect.getsource(template_module)

        # Should have two-level fallback for EquityPricing
        assert "EquityPricing" in source, (
            "Template should import EquityPricing (Zipline-Reloaded 3.x)"
        )
        assert "USEquityPricing" in source, "Template should have fallback to USEquityPricing"

        # Should use try/except for Pipeline imports
        assert "try:" in source and "except ImportError:" in source, (
            "Template should handle Pipeline API availability gracefully"
        )

    def test_no_hardcoded_parameters(self, template_module):
        """Verify no hardcoded parameters in template."""
        source = inspect.getsource(template_module)

        # Should load parameters from YAML
        assert "load_strategy_params" in source, "Template should load parameters from YAML"

        # Should access parameters via context.params
        assert "context.params" in source, "Template should access parameters via context.params"

    def test_pandas_aggregation_pattern(self, template_module):
        """Verify pandas aggregation uses direct resample().agg()."""
        source = inspect.getsource(template_module)

        # Should use direct pandas resample().agg()
        assert "resample(" in source and ".agg({" in source, (
            "Template should use direct pandas resample().agg() for aggregation"
        )

        # Should NOT use wrapper function (check actual function calls, not docstring examples)
        # Parse AST to find actual function calls, excluding docstrings
        import ast

        try:
            tree = ast.parse(source)
            wrapper_calls = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "aggregate_ohlcv":
                        wrapper_calls.append(ast.get_source_segment(source, node))
                    elif (
                        isinstance(node.func, ast.Attribute) and node.func.attr == "aggregate_ohlcv"
                    ):
                        wrapper_calls.append(ast.get_source_segment(source, node))
            assert len(wrapper_calls) == 0, (
                f"Template should NOT call aggregate_ohlcv() wrapper. Found: {wrapper_calls}"
            )
        except SyntaxError:
            # Fallback: check code lines excluding docstrings and comments
            in_docstring = False
            code_lines = []
            for line in source.split("\n"):
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = not in_docstring
                    continue
                if in_docstring:
                    continue
                if not stripped.startswith("#") and stripped and "aggregate_ohlcv(" in stripped:
                    # Check if it's a real call (not in a string)
                    if "=" in stripped or "(" in stripped:
                        code_lines.append(stripped)
            assert len(code_lines) == 0, (
                f"Template should NOT call aggregate_ohlcv() wrapper. Found: {code_lines}"
            )

    def test_calendar_access_pattern(self, template_module):
        """Verify calendar access uses direct get_calendar()."""
        source = inspect.getsource(template_module)

        # Should use direct get_calendar() if calendars are accessed
        # Note: Template may not access calendars directly, so this is optional
        if "get_calendar" in source:
            assert "from zipline.utils.calendar_utils import get_calendar" in source, (
                "Template should import get_calendar from zipline.utils.calendar_utils"
            )
            # Check actual code usage, not docstring examples
            import ast

            try:
                tree = ast.parse(source)
                session_manager_usage = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == "SessionManager":
                        session_manager_usage.append(ast.get_source_segment(source, node))
                    elif isinstance(node, ast.Attribute) and node.attr == "SessionManager":
                        session_manager_usage.append(ast.get_source_segment(source, node))
                assert len(session_manager_usage) == 0, (
                    f"Template should NOT use SessionManager (removed in v1.12.0). Found: {session_manager_usage}"
                )
            except SyntaxError:
                # Fallback: simple check excluding docstrings
                in_docstring = False
                code_lines = []
                for line in source.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        in_docstring = not in_docstring
                        continue
                    if in_docstring or stripped.startswith("#"):
                        continue
                    if "SessionManager" in stripped and (
                        "=" in stripped or "(" in stripped or "import" in stripped
                    ):
                        code_lines.append(stripped)
                assert len(code_lines) == 0, (
                    f"Template should NOT use SessionManager (removed in v1.12.0). Found: {code_lines}"
                )

    def test_error_handling(self, template_module):
        """Verify proper error handling patterns."""
        source = inspect.getsource(template_module)

        # Should handle exceptions in compute_signals
        if "compute_signals" in source:
            assert "try:" in source or "except" in source, (
                "Template should handle errors in compute_signals"
            )

        # Should check for NaN values
        assert "pd.isna(" in source or "isnan" in source, (
            "Template should check for NaN values when appropriate"
        )

    def test_load_params_function(self, template_module):
        """Verify load_params() function structure."""
        source = inspect.getsource(template_module)

        # Should have load_params function
        assert "def load_params():" in source, "Template should have load_params() function"

        # Should use lib.config.load_strategy_params
        assert "load_strategy_params" in source, (
            "Template should use lib.config.load_strategy_params()"
        )

    def test_initialize_function_signature(self, template_module):
        """Verify initialize() function has correct signature."""
        init_func = getattr(template_module, "initialize")
        sig = inspect.signature(init_func)

        # Should accept context parameter
        assert "context" in sig.parameters, "initialize() should accept 'context' parameter"

        # Should not require data parameter (it's not passed to initialize)
        assert "data" not in sig.parameters, "initialize() should NOT accept 'data' parameter"

    def test_compute_signals_function_signature(self, template_module):
        """Verify compute_signals() function has correct signature."""
        signals_func = getattr(template_module, "compute_signals")
        sig = inspect.signature(signals_func)

        # Should accept context and data parameters
        assert "context" in sig.parameters, "compute_signals() should accept 'context' parameter"
        assert "data" in sig.parameters, "compute_signals() should accept 'data' parameter"

    def test_rebalance_function_signature(self, template_module):
        """Verify rebalance() function has correct signature."""
        rebalance_func = getattr(template_module, "rebalance")
        sig = inspect.signature(rebalance_func)

        # Should accept context and data parameters
        assert "context" in sig.parameters, "rebalance() should accept 'context' parameter"
        assert "data" in sig.parameters, "rebalance() should accept 'data' parameter"

    def test_analyze_multi_timeframe_function(self, template_module):
        """Verify analyze_multi_timeframe() uses direct pandas."""
        source = inspect.getsource(template_module)

        if "analyze_multi_timeframe" in source:
            # Should use direct pandas resample().agg()
            assert "resample(" in source and ".agg({" in source, (
                "analyze_multi_timeframe() should use direct pandas resample().agg()"
            )

            # Should NOT use wrapper function (check actual function calls using AST)
            import ast

            try:
                tree = ast.parse(source)
                wrapper_calls = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id == "aggregate_ohlcv":
                            wrapper_calls.append(ast.get_source_segment(source, node))
                        elif (
                            isinstance(node.func, ast.Attribute)
                            and node.func.attr == "aggregate_ohlcv"
                        ):
                            wrapper_calls.append(ast.get_source_segment(source, node))
                assert len(wrapper_calls) == 0, (
                    f"analyze_multi_timeframe() should NOT use aggregate_ohlcv() wrapper. Found: {wrapper_calls}"
                )
            except SyntaxError:
                # Fallback: simple check
                in_docstring = False
                code_lines = []
                for line in source.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        in_docstring = not in_docstring
                        continue
                    if in_docstring or stripped.startswith("#"):
                        continue
                    if "aggregate_ohlcv(" in stripped and ("=" in stripped or "(" in stripped):
                        code_lines.append(stripped)
                assert len(code_lines) == 0, (
                    f"analyze_multi_timeframe() should NOT use aggregate_ohlcv() wrapper. Found: {code_lines}"
                )

    def test_template_docstring(self, template_module):
        """Verify template has comprehensive docstring."""
        docstring = template_module.__doc__

        assert docstring is not None, "Template should have module-level docstring"
        assert len(docstring) > 100, "Template docstring should be comprehensive"
        assert "v1.12.0" in docstring or "NO WRAPPERS" in docstring, (
            "Template docstring should mention v1.12.0 or NO WRAPPERS directive"
        )
