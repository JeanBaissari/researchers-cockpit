"""
Utility functions for The Researcher's Cockpit.

Provides file operations, directory management, YAML handling, and strategy creation utilities.
"""

import shutil
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from .paths import get_project_root


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp_dir(base_path: Path, prefix: str) -> Path:
    """
    Create a timestamped directory.

    Args:
        base_path: Base directory path
        prefix: Prefix for directory name (e.g., 'backtest', 'optimization')

    Returns:
        Path to the created directory (e.g., 'results/spy_sma/backtest_20241220_143022')
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dir_path = base_path / f"{prefix}_{timestamp}"
    ensure_dir(dir_path)
    return dir_path


def update_symlink(target: Path, link_path: Path) -> None:
    """Create or update a symlink pointing to target."""
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    link_path.symlink_to(target)
    if not link_path.exists():
        raise OSError(f"Failed to create symlink {link_path} -> {target}")


def load_yaml(path: Path) -> dict:
    """
    Safely load a YAML file.

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {path}: {e}")


def save_yaml(data: dict, path: Path) -> None:
    """Save data to a YAML file with formatting."""
    ensure_dir(path.parent)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)


def get_strategy_path(strategy_name: str, asset_class: Optional[str] = None) -> Path:
    """
    Locate a strategy directory.

    Args:
        strategy_name: Name of strategy (e.g., 'spy_sma_cross')
        asset_class: Optional asset class ('crypto', 'forex', 'equities')
                     If None, searches all asset classes

    Raises:
        FileNotFoundError: If strategy not found
    """
    root = get_project_root()
    strategies_dir = root / 'strategies'

    if asset_class:
        strategy_path = strategies_dir / asset_class / strategy_name
        if strategy_path.exists():
            return strategy_path
    else:
        for ac in ['crypto', 'forex', 'equities']:
            strategy_path = strategies_dir / ac / strategy_name
            if strategy_path.exists():
                return strategy_path

    raise FileNotFoundError(
        f"Strategy '{strategy_name}' not found. "
        f"Searched in: {strategies_dir}/*/{strategy_name}"
    )


def create_strategy(
    strategy_name: str,
    asset_class: str,
    from_template: bool = True
) -> Path:
    """
    Create a new strategy directory.

    Args:
        strategy_name: Name for the new strategy
        asset_class: Asset class ('crypto', 'forex', 'equities')
        from_template: If True, copy from _template

    Raises:
        ValueError: If strategy already exists
        FileNotFoundError: If template doesn't exist
    """
    root = get_project_root()
    strategy_path = root / 'strategies' / asset_class / strategy_name

    if strategy_path.exists():
        raise ValueError(f"Strategy '{strategy_name}' already exists at {strategy_path}")

    if from_template:
        template_path = root / 'strategies' / '_template'
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found at {template_path}")
        shutil.copytree(template_path, strategy_path)
    else:
        ensure_dir(strategy_path)

    return strategy_path


def create_strategy_from_template(
    name: str,
    asset_class: str,
    asset_symbol: str
) -> Path:
    """
    Create a new strategy from template with asset symbol configured.

    Creates strategy, updates parameters.yaml with asset_symbol,
    creates results directory and symlink.
    """
    root = get_project_root()
    strategy_path = create_strategy(name, asset_class, from_template=True)

    # Update parameters.yaml with asset_symbol
    params_path = strategy_path / 'parameters.yaml'
    if params_path.exists():
        params = load_yaml(params_path)
        if 'strategy' not in params:
            params['strategy'] = {}
        params['strategy']['asset_symbol'] = asset_symbol
        save_yaml(params, params_path)

    # Create results directory and symlink
    results_dir = root / 'results' / name
    ensure_dir(results_dir)
    update_symlink(results_dir, strategy_path / 'results')

    return strategy_path


def check_and_fix_symlinks(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> List[Path]:
    """
    Check and fix broken symlinks within a strategy's results directory.

    Returns:
        List of paths to fixed symlinks
    """
    root = get_project_root()
    strategy_path = get_strategy_path(strategy_name, asset_class)
    results_base = root / 'results' / strategy_name
    fixed_links: List[Path] = []

    # Check strategy's own symlink to results
    strategy_results_link = strategy_path / 'results'
    if strategy_results_link.is_symlink() and not strategy_results_link.exists():
        update_symlink(results_base, strategy_results_link)
        fixed_links.append(strategy_results_link)

    # Check the 'latest' symlink in the results base directory
    latest_link = results_base / 'latest'
    if latest_link.is_symlink() and not latest_link.exists():
        subdirs = sorted(
            [d for d in results_base.iterdir() if d.is_dir() and d.name.startswith('backtest_')],
            reverse=True
        )
        if subdirs:
            update_symlink(subdirs[0], latest_link)
            fixed_links.append(latest_link)

    return fixed_links


__all__ = [
    # Core utilities
    'get_project_root',
    'ensure_dir',
    'timestamp_dir',
    'update_symlink',
    'load_yaml',
    'save_yaml',
    'get_strategy_path',
    'create_strategy',
    'create_strategy_from_template',
    'check_and_fix_symlinks',
]
