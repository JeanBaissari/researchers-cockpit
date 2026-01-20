"""
Strategy management module for The Researcher's Cockpit.

Provides functions for strategy path resolution, creation, and symlink management.
"""

from .manager import (
    get_strategy_path,
    create_strategy,
    create_strategy_from_template,
    check_and_fix_symlinks,
)

__all__ = [
    'get_strategy_path',
    'create_strategy',
    'create_strategy_from_template',
    'check_and_fix_symlinks',
]
