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
    - load_documentation_config: Load documentation standards configuration
    - get_doc_zones: Get documentation zone paths
    - get_required_sections: Get required sections for new docs
    - get_index_files: Get documentation index file paths
    - validate_doc_structure: Validate doc file structure
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

# Zipline parameter extraction
from .zipline_params import (
    ZiplineRunParams,
    extract_zipline_params,
    validate_zipline_params,
)

# Documentation configuration
from .documentation import (
    load_documentation_config,
    get_doc_zones,
    get_required_sections,
    get_index_files,
    should_archive_instead_of_delete,
    validate_doc_structure,
)


__all__ = [
    # Core
    "load_settings",
    "clear_config_cache",
    # Assets
    "load_asset_config",
    "get_data_source",
    "get_default_bundle",
    # Strategy
    "load_strategy_params",
    "get_warmup_days",
    # Validation
    "validate_strategy_params",
    # Zipline parameters
    "ZiplineRunParams",
    "extract_zipline_params",
    "validate_zipline_params",
    # Documentation
    "load_documentation_config",
    "get_doc_zones",
    "get_required_sections",
    "get_index_files",
    "should_archive_instead_of_delete",
    "validate_doc_structure",
]
