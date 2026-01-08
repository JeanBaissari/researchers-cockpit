"""
Test that all modern import paths work correctly in v1.0.8.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestModernImports:
    """Test that all modern imports work."""
    
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
    
    def test_import_backtest_package(self):
        """Test importing from lib.backtest."""
        from lib.backtest import (
            run_backtest,
            BacktestConfig,
            BacktestResults,
        )
        assert run_backtest is not None
        assert BacktestConfig is not None
        assert BacktestResults is not None
    
    def test_import_config_package(self):
        """Test importing from lib.config."""
        from lib.config import (
            load_strategy_params,
            load_settings,
        )
        assert load_strategy_params is not None
        assert load_settings is not None
    
    def test_import_metrics_package(self):
        """Test importing from lib.metrics."""
        from lib.metrics import (
            calculate_sharpe_ratio,
            calculate_max_drawdown,
            calculate_sortino_ratio,
        )
        assert calculate_sharpe_ratio is not None
        assert calculate_max_drawdown is not None
        assert calculate_sortino_ratio is not None
    
    def test_import_optimize_package(self):
        """Test importing from lib.optimize."""
        from lib.optimize import (
            GridSearchOptimizer,
            RandomSearchOptimizer,
        )
        assert GridSearchOptimizer is not None
        assert RandomSearchOptimizer is not None
    
    def test_import_validate_package(self):
        """Test importing from lib.validate."""
        from lib.validate import (
            WalkForwardValidator,
            MonteCarloValidator,
        )
        assert WalkForwardValidator is not None
        assert MonteCarloValidator is not None
    
    def test_import_logging_package(self):
        """Test importing from lib.logging."""
        from lib.logging import (
            setup_logging,
            get_logger,
        )
        assert setup_logging is not None
        assert get_logger is not None
    
    def test_import_report_package(self):
        """Test importing from lib.report."""
        from lib.report import (
            generate_strategy_report,
        )
        assert generate_strategy_report is not None
    
    def test_import_plots_package(self):
        """Test importing from lib.plots."""
        from lib.plots import (
            plot_equity_curve,
            plot_returns_distribution,
        )
        assert plot_equity_curve is not None
        assert plot_returns_distribution is not None


class TestLibInitExports:
    """Test that lib.__init__.py exports the modern API."""
    
    def test_lib_exports_bundles(self):
        """Test that lib exports bundle functions."""
        import lib
        assert hasattr(lib, 'ingest_bundle')
        assert hasattr(lib, 'load_bundle')
    
    def test_lib_exports_validation(self):
        """Test that lib exports validation classes."""
        import lib
        assert hasattr(lib, 'DataValidator')
        assert hasattr(lib, 'ValidationResult')
    
    def test_lib_exports_calendars(self):
        """Test that lib exports calendar functions."""
        import lib
        assert hasattr(lib, 'CryptoCalendar')
        assert hasattr(lib, 'ForexCalendar')
        assert hasattr(lib, 'register_custom_calendars')
    
    def test_lib_exports_backtest(self):
        """Test that lib exports backtest functions."""
        import lib
        assert hasattr(lib, 'run_backtest')
    
    def test_lib_exports_config(self):
        """Test that lib exports config functions."""
        import lib
        assert hasattr(lib, 'load_strategy_params')
    
    def test_lib_exports_metrics(self):
        """Test that lib exports metrics functions."""
        import lib
        assert hasattr(lib, 'calculate_sharpe_ratio')
        assert hasattr(lib, 'calculate_max_drawdown')


class TestZiplineExtension:
    """Test that .zipline/extension.py works as thin loader."""
    
    def test_zipline_extension_imports_from_lib_calendars(self):
        """Test that .zipline/extension.py imports from lib.calendars."""
        # Import the extension module
        import importlib.util
        ext_path = project_root / '.zipline' / 'extension.py'
        
        if not ext_path.exists():
            pytest.skip(".zipline/extension.py not found")
        
        spec = importlib.util.spec_from_file_location("extension", ext_path)
        extension = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extension)
        
        # Verify it has the expected exports
        assert hasattr(extension, 'CryptoCalendar')
        assert hasattr(extension, 'ForexCalendar')
        assert hasattr(extension, 'register_custom_calendars')


class TestNoCircularImports:
    """Test that there are no circular import issues."""
    
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

