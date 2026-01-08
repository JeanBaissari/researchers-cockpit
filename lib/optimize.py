"""
Optimization module for The Researcher's Cockpit.

This is a backward-compatibility wrapper. The actual implementation
has been refactored into the lib/optimize/ package.

New code should import directly from lib.optimize:
    from lib.optimize import grid_search, random_search
"""

# Re-export all public API from the optimize package
from .optimize import (
    # Core optimization functions
    grid_search,
    random_search,
    # Data splitting
    split_data,
    # Overfit detection
    calculate_overfit_score,
    # Results handling
    save_optimization_results,
    deep_copy_dict,
    set_nested_param,
    # Private aliases (backward compat)
    _deep_copy_dict,
    _set_nested_param,
    _save_optimization_results,
)

__all__ = [
    'grid_search',
    'random_search',
    'split_data',
    'calculate_overfit_score',
    'save_optimization_results',
    'deep_copy_dict',
    'set_nested_param',
    '_deep_copy_dict',
    '_set_nested_param',
    '_save_optimization_results',
]
