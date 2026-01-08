"""
Validation module for The Researcher's Cockpit.

This module provides backward compatibility for imports from lib.validate.
The implementation has been refactored into the lib/validate/ package.

Usage:
    # Both import styles work:
    from lib.validate import walk_forward, monte_carlo
    from lib.validate import calculate_walk_forward_efficiency
"""

# Re-export everything from the validate package
from .validate import (
    # Main validation functions
    walk_forward,
    monte_carlo,
    # Metrics functions
    calculate_walk_forward_efficiency,
    calculate_overfit_probability,
    # Results saving functions
    save_walk_forward_results,
    save_monte_carlo_results,
    # Backward compatibility aliases
    _save_walk_forward_results,
    _save_monte_carlo_results,
)

__all__ = [
    'walk_forward',
    'monte_carlo',
    'calculate_walk_forward_efficiency',
    'calculate_overfit_probability',
    'save_walk_forward_results',
    'save_monte_carlo_results',
    '_save_walk_forward_results',
    '_save_monte_carlo_results',
]
