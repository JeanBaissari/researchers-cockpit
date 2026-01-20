"""
Test that all modern import paths work correctly.

Tests for import path compatibility and verification.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestModernImports:
    """Test that all modern imports work."""
    
    @pytest.mark.unit
    def test_import_bundles_package(self):
        """Test importing from lib.bundles."""
        from lib.bundles import (
            ingest_bundle,
            load_bundle,
            get_bundle_symbols,
            list_bundles,
            VALID_TIMEFRAMES,
            VALID_SOURCES,
        )
        assert ingest_bundle is not None
        assert load_bundle is not None
        assert get_bundle_symbols is not None
        assert list_bundles is not None
        assert isinstance(VALID_TIMEFRAMES, list)
        assert isinstance(VALID_SOURCES, list)
    
    @pytest.mark.unit
    def test_import_validation_package(self):
        """Test importing from lib.validation."""
        from lib.validation import (
            DataValidator,
            BundleValidator,
            BacktestValidator,
            ValidationResult,
            ValidationConfig,
            ValidationSeverity,
        )
        assert DataValidator is not None
        assert BundleValidator is not None
        assert BacktestValidator is not None
        assert ValidationResult is not None
        assert ValidationConfig is not None
        assert ValidationSeverity is not None
    
    @pytest.mark.unit
    def test_import_calendars_package(self):
        """Test importing from lib.calendars."""
        from lib.calendars import (
            CryptoCalendar,
            ForexCalendar,
            register_custom_calendars,
            get_calendar_for_asset_class,
            get_available_calendars,
        )
        assert CryptoCalendar is not None
        assert ForexCalendar is not None
        assert register_custom_calendars is not None
        assert get_calendar_for_asset_class is not None
        assert get_available_calendars is not None
    
    @pytest.mark.unit
    def test_import_backtest_package(self):
        """Test importing from lib.backtest."""
        from lib.backtest import (
            run_backtest,
            BacktestConfig,
            save_results,
        )
        assert run_backtest is not None
        assert BacktestConfig is not None
        assert save_results is not None
    
    @pytest.mark.unit
    def test_import_config_package(self):
        """Test importing from lib.config."""
        from lib.config import (
            load_strategy_params,
            load_settings,
        )
        assert load_strategy_params is not None
        assert load_settings is not None
    
    @pytest.mark.unit
    def test_import_metrics_package(self):
        """Test importing from lib.metrics."""
        from lib.metrics import calculate_metrics
        import pandas as pd
        import numpy as np
        
        assert calculate_metrics is not None
        
        # Test that calculate_metrics returns dict with expected keys
        # Create sample returns data
        returns = pd.Series(np.random.randn(100) * 0.01)
        metrics = calculate_metrics(returns)
        
        assert isinstance(metrics, dict)
        assert 'sharpe' in metrics or 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'sortino' in metrics or 'sortino_ratio' in metrics
    
    @pytest.mark.unit
    def test_import_optimize_package(self):
        """Test importing from lib.optimize."""
        from lib.optimize import (
            grid_search,
            random_search,
        )
        assert grid_search is not None
        assert random_search is not None
        # Verify they are functions, not classes
        import inspect
        assert inspect.isfunction(grid_search) or inspect.ismethod(grid_search)
        assert inspect.isfunction(random_search) or inspect.ismethod(random_search)
    
    @pytest.mark.unit
    def test_import_validate_package(self):
        """Test importing from lib.validate."""
        from lib.validate import (
            walk_forward,
            monte_carlo,
        )
        assert walk_forward is not None
        assert monte_carlo is not None
        # Verify they are functions, not classes
        import inspect
        assert inspect.isfunction(walk_forward) or inspect.ismethod(walk_forward)
        assert inspect.isfunction(monte_carlo) or inspect.ismethod(monte_carlo)
    
    @pytest.mark.unit
    def test_import_logging_package(self):
        """Test importing from lib.logging."""
        from lib.logging import (
            configure_logging,
            get_logger,
        )
        assert configure_logging is not None
        assert get_logger is not None
    
    @pytest.mark.unit
    def test_import_report_package(self):
        """Test importing from lib.report."""
        from lib.report import (
            generate_report,
        )
        assert generate_report is not None
    
    @pytest.mark.unit
    def test_import_plots_package(self):
        """Test importing from lib.plots."""
        from lib.plots import (
            plot_equity_curve,
            plot_drawdown,
            plot_monthly_returns,
            plot_trade_analysis,
            plot_rolling_metrics,
        )
        assert plot_equity_curve is not None
        assert plot_drawdown is not None
        assert plot_monthly_returns is not None
        assert plot_trade_analysis is not None
        assert plot_rolling_metrics is not None


class TestLibInitExports:
    """Test that lib.__init__.py exports the modern API."""
    
    @pytest.mark.unit
    def test_lib_exports_bundles(self):
        """Test that lib exports bundle functions."""
        import lib
        assert hasattr(lib, 'ingest_bundle')
        assert hasattr(lib, 'load_bundle')
    
    @pytest.mark.unit
    def test_lib_exports_validation(self):
        """Test that lib exports validation classes."""
        import lib
        assert hasattr(lib, 'DataValidator')
        assert hasattr(lib, 'ValidationResult')
    
    @pytest.mark.unit
    def test_lib_exports_calendars(self):
        """Test that lib exports calendar functions."""
        import lib
        assert hasattr(lib, 'CryptoCalendar')
        assert hasattr(lib, 'ForexCalendar')
        assert hasattr(lib, 'register_custom_calendars')
    
    @pytest.mark.unit
    def test_lib_exports_backtest(self):
        """Test that lib exports backtest functions."""
        import lib
        assert hasattr(lib, 'run_backtest')
    
    @pytest.mark.unit
    def test_lib_exports_config(self):
        """Test that lib exports config functions."""
        import lib
        assert hasattr(lib, 'load_strategy_params')
    
    @pytest.mark.unit
    def test_lib_exports_metrics(self):
        """Test that lib exports metrics functions."""
        import lib
        assert hasattr(lib, 'calculate_metrics')


class TestNoCircularImports:
    """Test that there are no circular import issues."""
    
    @pytest.mark.unit
    def test_import_all_modules_together(self):
        """Test importing all modules at once doesn't cause circular imports."""
        from lib import (
            bundles,
            validation,
            calendars,
            backtest,
            config,
            metrics,
            optimize,
            validate,
            logging,
            report,
            plots,
        )
        
        # If we get here without ImportError, circular imports are resolved
        assert bundles is not None
        assert validation is not None
        assert calendars is not None
        assert backtest is not None
        assert config is not None
        assert metrics is not None
        assert optimize is not None
        assert validate is not None
        assert logging is not None
        assert report is not None
        assert plots is not None

