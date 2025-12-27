"""
The Researcher's Cockpit - Core Library

This package provides the foundational modules for running algorithmic trading
research with Zipline-reloaded.

Main exports:
- config: Configuration loading and management
- data_loader: Data bundle ingestion and management
- utils: Utility functions for file operations, strategy creation
- backtest: Backtest execution and result saving
"""

__version__ = "0.1.0"
__author__ = "The Researcher's Cockpit"

# Main exports
from .config import (
    load_settings,
    load_asset_config,
    load_strategy_params,
    validate_strategy_params,
    get_data_source,
    get_default_bundle,
)

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

# Backtest will be imported when available
try:
    from .backtest import run_backtest, save_results
except ImportError:
    pass

# Metrics and plots
try:
    from .metrics import (
        calculate_metrics,
        calculate_trade_metrics,
        calculate_rolling_metrics,
        compare_strategies,
    )
except ImportError:
    pass

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

# Validation
try:
    from .validate import walk_forward, monte_carlo, calculate_overfit_probability, calculate_walk_forward_efficiency
except ImportError:
    pass

# Reporting
try:
    from .report import generate_report, update_catalog, generate_weekly_summary
except ImportError:
    pass

# Extension (custom calendars)
try:
    from .extension import (
        register_custom_calendars,
        get_calendar_for_asset_class,
        get_available_calendars,
        get_registered_calendars,
    )
except ImportError:
    pass

__all__ = [
    # Config
    'load_settings',
    'load_asset_config',
    'load_strategy_params',
    'validate_strategy_params',
    'get_data_source',
    'get_default_bundle',
    # Utils
    'create_strategy',
    'get_strategy_path',
    'ensure_dir',
    'timestamp_dir',
    'update_symlink',
    'check_and_fix_symlinks',
    'load_yaml',
    'save_yaml',
    'create_strategy_from_template',
    # Backtest (when available)
    'run_backtest',
    'save_results',
    # Metrics
    'calculate_metrics',
    'calculate_trade_metrics',
    'calculate_rolling_metrics',
    'compare_strategies',
    # Plots
    'plot_equity_curve',
    'plot_drawdown',
    'plot_monthly_returns',
    'plot_trade_analysis',
    'plot_rolling_metrics',
    'plot_all',
    # Optimization
    'grid_search',
    'random_search',
    'split_data',
    'calculate_overfit_score',
    # Validation
    'walk_forward',
    'monte_carlo',
    'calculate_overfit_probability',
    'calculate_walk_forward_efficiency',
    # Reporting
    'generate_report',
    'update_catalog',
    'generate_weekly_summary',
    # Extension
    'register_custom_calendars',
    'get_calendar_for_asset_class',
    'get_available_calendars',
    'get_registered_calendars',
]

