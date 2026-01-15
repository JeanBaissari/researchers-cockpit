"""
Configuration loading and management for The Researcher's Cockpit.

This package provides functions to load YAML configuration files with caching
to avoid repeated file I/O operations.

Public API:
    - load_settings: Load global settings from settings.yaml
    - load_asset_config: Load asset class configuration
    - load_strategy_params: Load strategy parameters
    - get_data_source: Get data source configuration
    - get_default_bundle: Get default bundle for asset class
    - get_warmup_days: Calculate warmup days from strategy params
    - validate_strategy_params: Validate strategy parameters
    - clear_config_cache: Clear the configuration cache
"""

from __future__ import annotations

# Core configuration
from .core import (
    load_settings,
    clear_config_cache,
    get_config_cache,
    _get_config_path,
)

# Asset configuration
from .assets import (
    load_asset_config,
    get_data_source,
    get_default_bundle,
)

# Strategy configuration
from .strategy import (
    load_strategy_params,
    get_warmup_days,
)

# Validation
from .validation import (
    validate_strategy_params,
)


__all__ = [
    # Core
    'load_settings',
    'clear_config_cache',
    # Assets
    'load_asset_config',
    'get_data_source',
    'get_default_bundle',
    # Strategy
    'load_strategy_params',
    'get_warmup_days',
    # Validation
    'validate_strategy_params',
]















