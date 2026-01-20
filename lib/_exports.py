"""
Centralized exports for lib package.

All public API exports organized by functional area for maintainability.
This module contains all imports and re-exports. The main __init__.py
imports everything from here to keep it clean and minimal.
"""

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
    ensure_dir,
    timestamp_dir,
    update_symlink,
    load_yaml,
    save_yaml,
)

# Strategy management
from .strategies import (
    create_strategy,
    get_strategy_path,
    create_strategy_from_template,
    check_and_fix_symlinks,
)

# Paths
from .paths import (
    get_project_root,
    get_strategies_dir,
    get_results_dir,
    get_data_dir,
    get_config_dir,
    get_logs_dir,
    get_reports_dir,
    validate_project_structure,
    ensure_project_dirs,
    ProjectRootNotFoundError,
)

# Calendars (custom trading calendars)
from .calendars import (
    register_custom_calendars,
    get_calendar_for_asset_class,
    get_available_calendars,
    get_registered_calendars,
    CryptoCalendar,
    ForexCalendar,
)

# Logging
from .logging import (
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
# DATA PACKAGES (modern modular imports)
# =============================================================================

# Validation package
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

# Bundles package
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
