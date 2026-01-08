"""
The Researcher's Cockpit - Core Library

This package provides the foundational modules for running algorithmic trading
research with Zipline-reloaded.

Main exports:
- config: Configuration loading and management
- data_loader: Data bundle ingestion and management
- utils: Utility functions for file operations, strategy creation
- backtest: Backtest execution and result saving
- logging_config: Centralized logging configuration
- data_validation: Data integrity validation
- paths: Robust project root resolution
"""

__version__ = "1.0.8"
__author__ = "The Researcher's Cockpit"

# =============================================================================
# CORE MODULES (always available)
# =============================================================================

# Configuration
from .config import (
    load_settings,
    load_asset_config,
    load_strategy_params,
    validate_strategy_params,
    get_data_source,
    get_default_bundle,
)

# Utilities
from .utils import (
    create_strategy,
    get_strategy_path,
    ensure_dir,
    timestamp_dir,
    update_symlink,
    load_yaml,
    save_yaml,
    create_strategy_from_template,
    check_and_fix_symlinks,
)

# Paths
from .paths import (
    get_project_root as paths_get_project_root,
    get_strategies_dir,
    get_results_dir,
    get_data_dir,
    get_config_dir,
    get_logs_dir,
    get_reports_dir,
    resolve_strategy_path,
    validate_project_structure,
    ensure_project_dirs,
    ProjectRootNotFoundError,
)

# Extension (custom calendars)
from .extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
    get_available_calendars,
    get_registered_calendars,
)

# =============================================================================
# LOGGING (auto-configure on import)
# =============================================================================

try:
    from .logging_config import (
        configure_logging,
        get_logger,
        LogContext,
        log_with_context,
        data_logger,
        strategy_logger,
        backtest_logger,
        metrics_logger,
        validation_logger,
        report_logger,
    )
    # Configure with defaults - can be reconfigured later
    _root_logger = configure_logging(level='INFO', console=False, file=False)
except ImportError:
    pass

# =============================================================================
# OPTIONAL MODULES (may require additional dependencies)
# =============================================================================

# Backtest (requires zipline-reloaded)
try:
    from .backtest import run_backtest, save_results
except ImportError:
    pass

# Metrics (requires empyrical-reloaded)
try:
    from .metrics import (
        calculate_metrics,
        calculate_trade_metrics,
        calculate_rolling_metrics,
        compare_strategies,
    )
except ImportError:
    pass

# Plots (requires matplotlib)
try:
    from .plots import (
        plot_equity_curve,
        plot_drawdown,
        plot_monthly_returns,
        plot_trade_analysis,
        plot_rolling_metrics,
        plot_all,
    )
except ImportError:
    pass

# Optimization
try:
    from .optimize import grid_search, random_search, split_data, calculate_overfit_score
except ImportError:
    pass

# Validation methods
try:
    from .validate import walk_forward, monte_carlo, calculate_overfit_probability, calculate_walk_forward_efficiency
except ImportError:
    pass

# Reporting
try:
    from .report import generate_report, update_catalog, generate_weekly_summary
except ImportError:
    pass

# =============================================================================
# DATA PACKAGES (with backward-compat fallbacks)
# =============================================================================

# Validation package
try:
    from .validation import (
        DataValidator,
        ValidationResult,
        ValidationConfig,
        ValidationSeverity,
        ValidationCheck,
        BundleValidator,
        BacktestValidator,
        SchemaValidator,
        CompositeValidator,
        validate_before_ingest,
        validate_bundle,
        validate_backtest_results,
        verify_metrics_calculation,
        verify_returns_calculation,
        verify_positions_match_transactions,
        save_validation_report,
        load_validation_report,
    )
except ImportError:
    try:
        from .data_validation import (
            DataValidator,
            ValidationResult,
            validate_bundle,
            verify_metrics_calculation,
            verify_returns_calculation,
            verify_positions_match_transactions,
            save_validation_report,
        )
    except ImportError:
        pass

# Bundles package
try:
    from .bundles import (
        ingest_bundle,
        load_bundle,
        list_bundles,
        unregister_bundle,
        get_bundle_symbols,
        VALID_TIMEFRAMES,
        TIMEFRAME_DATA_LIMITS,
        VALID_SOURCES,
    )
except ImportError:
    try:
        from .data_loader import (
            ingest_bundle,
            load_bundle,
            list_bundles,
            unregister_bundle,
            get_bundle_symbols,
            VALID_TIMEFRAMES,
            TIMEFRAME_DATA_LIMITS,
        )
    except ImportError:
        pass

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Config
    'load_settings', 'load_asset_config', 'load_strategy_params',
    'validate_strategy_params', 'get_data_source', 'get_default_bundle',
    # Utils
    'create_strategy', 'get_strategy_path', 'ensure_dir', 'timestamp_dir',
    'update_symlink', 'check_and_fix_symlinks', 'load_yaml', 'save_yaml',
    'create_strategy_from_template',
    # Paths
    'get_strategies_dir', 'get_results_dir', 'get_data_dir', 'get_config_dir',
    'get_logs_dir', 'get_reports_dir', 'resolve_strategy_path',
    'validate_project_structure', 'ensure_project_dirs', 'ProjectRootNotFoundError',
    # Extension
    'register_custom_calendars', 'get_calendar_for_asset_class',
    'get_available_calendars', 'get_registered_calendars',
    # Logging
    'configure_logging', 'get_logger', 'LogContext', 'log_with_context',
    'data_logger', 'strategy_logger', 'backtest_logger', 'metrics_logger',
    'validation_logger', 'report_logger',
    # Backtest
    'run_backtest', 'save_results',
    # Metrics
    'calculate_metrics', 'calculate_trade_metrics', 'calculate_rolling_metrics',
    'compare_strategies',
    # Plots
    'plot_equity_curve', 'plot_drawdown', 'plot_monthly_returns',
    'plot_trade_analysis', 'plot_rolling_metrics', 'plot_all',
    # Optimization
    'grid_search', 'random_search', 'split_data', 'calculate_overfit_score',
    # Validation methods
    'walk_forward', 'monte_carlo', 'calculate_overfit_probability',
    'calculate_walk_forward_efficiency',
    # Reporting
    'generate_report', 'update_catalog', 'generate_weekly_summary',
    # Data Validation
    'DataValidator', 'ValidationResult', 'ValidationConfig', 'ValidationSeverity',
    'ValidationCheck', 'BundleValidator', 'BacktestValidator', 'SchemaValidator',
    'CompositeValidator', 'validate_before_ingest', 'validate_bundle',
    'validate_backtest_results', 'verify_metrics_calculation',
    'verify_returns_calculation', 'verify_positions_match_transactions',
    'save_validation_report', 'load_validation_report',
    # Data Loader
    'ingest_bundle', 'load_bundle', 'list_bundles', 'unregister_bundle',
    'get_bundle_symbols', 'VALID_TIMEFRAMES', 'TIMEFRAME_DATA_LIMITS', 'VALID_SOURCES',
]
