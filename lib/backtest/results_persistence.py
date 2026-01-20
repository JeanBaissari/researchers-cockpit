"""
Results persistence module for The Researcher's Cockpit.

Handles filesystem operations for backtest results:
- Directory creation and management
- Symlink updates
- Result catalog operations
"""

import logging
from pathlib import Path
from typing import Optional

from ..paths import get_project_root
from ..utils import (
    ensure_dir,
    timestamp_dir,
    update_symlink,
)
from ..strategies import (
    get_strategy_path,
    check_and_fix_symlinks,
)

# Module-level logger
logger = logging.getLogger(__name__)


def create_results_directory(strategy_name: str, result_type: str = 'backtest') -> Path:
    """
    Create timestamped results directory for a strategy.
    
    Args:
        strategy_name: Name of strategy
        result_type: Type of result ('backtest', 'optimization', etc.)
        
    Returns:
        Path: Path to created results directory
    """
    root = get_project_root()
    results_base = root / 'results' / strategy_name
    ensure_dir(results_base)
    
    # Create timestamped directory
    result_dir = timestamp_dir(results_base, result_type)
    return result_dir


def update_latest_symlink(result_dir: Path, strategy_name: str) -> None:
    """
    Update the 'latest' symlink to point to the most recent results directory.
    
    Args:
        result_dir: Path to the results directory
        strategy_name: Name of strategy
    """
    root = get_project_root()
    results_base = root / 'results' / strategy_name
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)


def check_and_fix_strategy_symlinks(strategy_name: str) -> list[Path]:
    """
    Check and fix broken symlinks for a strategy.
    
    Args:
        strategy_name: Name of strategy
        
    Returns:
        List of paths to fixed symlinks
    """
    try:
        asset_class = None
        try:
            strategy_path = get_strategy_path(strategy_name)
            asset_class = strategy_path.parent.name
            if asset_class not in ['crypto', 'forex', 'equities']:
                asset_class = None
        except FileNotFoundError:
            pass
        
        fixed_links = check_and_fix_symlinks(strategy_name, asset_class)
        if fixed_links:
            logger.info(f"Fixed {len(fixed_links)} broken symlink(s): {fixed_links}")
        return fixed_links
    except Exception as e:
        logger.warning(f"Symlink check failed: {e}")
        return []
