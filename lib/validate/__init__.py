"""
Validation package for The Researcher's Cockpit.

Provides walk-forward analysis and Monte Carlo simulation for strategy validation.

Usage:
    from lib.validate import walk_forward, monte_carlo
    from lib.validate import calculate_walk_forward_efficiency, calculate_overfit_probability
"""

# Main validation functions
from .walkforward import walk_forward
from .montecarlo import monte_carlo

# Metrics functions
from .metrics import (
    calculate_walk_forward_efficiency,
    calculate_overfit_probability,
)

# Results saving functions
from .results import (
    save_walk_forward_results,
    save_monte_carlo_results,
    # Backward compatibility aliases
    _save_walk_forward_results,
    _save_monte_carlo_results,
)

__all__ = [
    # Main functions
    'walk_forward',
    'monte_carlo',
    # Metrics
    'calculate_walk_forward_efficiency',
    'calculate_overfit_probability',
    # Results saving
    'save_walk_forward_results',
    'save_monte_carlo_results',
    # Backward compatibility
    '_save_walk_forward_results',
    '_save_monte_carlo_results',
]





