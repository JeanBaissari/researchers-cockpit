"""
Optimization package for The Researcher's Cockpit.

Provides grid search and random search optimization with anti-overfit protocols.

Usage:
    from lib.optimize import grid_search, random_search, split_data
    
    # Grid search over parameter combinations
    results = grid_search(
        strategy_name='my_strategy',
        param_grid={'strategy.fast_period': [5, 10, 15]},
        start_date='2020-01-01',
        end_date='2023-12-31'
    )
    
    # Random search over parameter distributions
    results = random_search(
        strategy_name='my_strategy',
        param_distributions={'strategy.fast_period': [5, 10, 15, 20]},
        n_iter=100
    )
"""

# Core optimization functions
from .grid import grid_search
from .random import random_search

# Data splitting
from .split import split_data

# Overfit detection
from .overfit import calculate_overfit_score

# Results handling (public API)
from .results import (
    save_optimization_results,
    deep_copy_dict,
    set_nested_param,
)

__all__ = [
    # Core functions
    'grid_search',
    'random_search',
    'split_data',
    'calculate_overfit_score',
    # Results handling
    'save_optimization_results',
    'deep_copy_dict',
    'set_nested_param',
]















