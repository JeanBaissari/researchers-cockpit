"""
Centralized path resolution for The Researcher's Cockpit.

Provides robust project root discovery using marker files, with caching
for performance. This module ensures consistent path resolution regardless
of where code is executed from (notebooks, scripts, library calls, etc.).
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional, List


class ProjectRootNotFoundError(Exception):
    """Raised when project root cannot be determined."""
    pass


# Project marker files in priority order
PROJECT_MARKERS = [
    'pyproject.toml',      # Primary Python project marker
    '.git',                # Git repository root
    'config/settings.yaml', # Project-specific marker
    'CLAUDE.md',           # This project's documentation
    '.project_root',       # Explicit marker (optional)
]


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    """
    Find the project root directory using marker-based discovery.

    Searches upward from the current file's location for known project markers.
    Results are cached for performance.

    Returns:
        Path: Absolute path to project root

    Raises:
        ProjectRootNotFoundError: If no project markers are found

    Priority order for markers:
        1. pyproject.toml
        2. .git directory
        3. config/settings.yaml
        4. CLAUDE.md
        5. .project_root

    Environment variable override:
        Set PROJECT_ROOT environment variable to override automatic detection.
    """
    # Check for environment variable override
    env_root = os.environ.get('PROJECT_ROOT')
    if env_root:
        env_path = Path(env_root)
        if env_path.exists():
            return env_path.resolve()

    # Start from this file's directory and search upward
    current = Path(__file__).resolve().parent

    # Track searched paths for error message
    searched_paths = []

    while current != current.parent:  # Stop at filesystem root
        searched_paths.append(current)

        for marker in PROJECT_MARKERS:
            marker_path = current / marker
            if marker_path.exists():
                return current

        current = current.parent

    # No marker found
    raise ProjectRootNotFoundError(
        f"Could not find project root. Searched for markers {PROJECT_MARKERS} "
        f"in directories: {searched_paths[:5]}... "
        f"Set PROJECT_ROOT environment variable to override."
    )


def get_strategies_dir() -> Path:
    """Get the strategies directory path."""
    return get_project_root() / 'strategies'


def get_results_dir() -> Path:
    """Get the results directory path."""
    return get_project_root() / 'results'


def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_project_root() / 'data'


def get_config_dir() -> Path:
    """Get the config directory path."""
    return get_project_root() / 'config'


def get_logs_dir() -> Path:
    """Get the logs directory path."""
    return get_project_root() / 'logs'


def get_reports_dir() -> Path:
    """Get the reports directory path."""
    return get_project_root() / 'reports'


def resolve_strategy_path(strategy_name: str, asset_class: Optional[str] = None) -> Path:
    """
    Resolve the full path to a strategy directory.

    Args:
        strategy_name: Name of the strategy (e.g., 'spy_sma_cross')
        asset_class: Optional asset class hint ('crypto', 'forex', 'equities')
                    If None, searches all asset classes

    Returns:
        Path: Full path to strategy directory

    Raises:
        FileNotFoundError: If strategy not found
    """
    strategies_dir = get_strategies_dir()

    if asset_class:
        # Direct path with asset class
        strategy_path = strategies_dir / asset_class / strategy_name
        if strategy_path.exists():
            return strategy_path
    else:
        # Search all asset classes
        for asset_class in ['crypto', 'forex', 'equities']:
            strategy_path = strategies_dir / asset_class / strategy_name
            if strategy_path.exists():
                return strategy_path

    raise FileNotFoundError(
        f"Strategy '{strategy_name}' not found. "
        f"Searched in: {strategies_dir}/*/{strategy_name}"
    )


def validate_project_structure() -> List[str]:
    """
    Validate that expected project directories exist.

    Returns:
        List of warning messages for missing optional components.
        Empty list if all required components exist.

    Note:
        This does not raise exceptions for missing optional components,
        only returns warnings.
    """
    warnings = []
    root = get_project_root()

    # Required directories
    required_dirs = [
        'strategies',
        'results',
        'data',
        'config',
        'lib',
    ]

    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            warnings.append(f"Required directory missing: {dir_path}")

    # Required config files
    required_configs = [
        'config/settings.yaml',
    ]

    for config_file in required_configs:
        config_path = root / config_file
        if not config_path.exists():
            warnings.append(f"Required config file missing: {config_path}")

    # Optional but recommended
    optional_items = [
        ('strategies/_template', 'Strategy template'),
        ('logs', 'Logs directory'),
        ('reports', 'Reports directory'),
    ]

    for item_path, item_name in optional_items:
        if not (root / item_path).exists():
            warnings.append(f"Optional component missing: {item_name} ({item_path})")

    return warnings


def ensure_project_dirs() -> None:
    """
    Ensure all required project directories exist.

    Creates directories if they don't exist.
    """
    root = get_project_root()

    required_dirs = [
        'strategies',
        'strategies/_template',
        'strategies/crypto',
        'strategies/forex',
        'strategies/equities',
        'results',
        'data',
        'data/bundles',
        'data/cache',
        'data/exports',
        'config',
        'logs',
        'reports',
    ]

    for dir_name in required_dirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)


def clear_cache() -> None:
    """Clear the cached project root. Useful for testing."""
    get_project_root.cache_clear()
