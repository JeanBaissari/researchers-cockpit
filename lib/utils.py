"""
Utility functions for The Researcher's Cockpit.

Provides file operations, directory management, and YAML handling utilities.
"""

import yaml
from pathlib import Path
from datetime import datetime

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


__all__ = [
    # Core utilities
    'get_project_root',
    'ensure_dir',
    'timestamp_dir',
    'update_symlink',
    'load_yaml',
    'save_yaml',
]
