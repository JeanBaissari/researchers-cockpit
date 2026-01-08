"""
Core configuration loading and cache management.

Provides settings loading and cache management functions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

from ..utils import get_project_root, load_yaml


# Configure logging
logger = logging.getLogger(__name__)

# Cache for loaded configs
_config_cache: Dict[str, Any] = {}


def _get_config_path(filename: str) -> Path:
    """Get path to config file."""
    return get_project_root() / 'config' / filename


def get_config_cache() -> Dict[str, Any]:
    """
    Get the configuration cache dictionary.
    
    This function provides access to the shared cache for other config modules.
    
    Returns:
        dict: The configuration cache dictionary
    """
    return _config_cache


def load_settings() -> Dict[str, Any]:
    """
    Load global settings from config/settings.yaml.
    
    Returns:
        dict: Settings dictionary
        
    Raises:
        FileNotFoundError: If settings.yaml doesn't exist
    """
    cache_key = 'settings'
    if cache_key in _config_cache:
        logger.debug("Returning cached settings")
        return _config_cache[cache_key]
    
    settings_path = _get_config_path('settings.yaml')
    logger.debug(f"Loading settings from {settings_path}")
    settings = load_yaml(settings_path)
    _config_cache[cache_key] = settings
    return settings


def clear_config_cache() -> None:
    """Clear the configuration cache. Useful for testing or reloading configs."""
    global _config_cache
    cache_size = len(_config_cache)
    _config_cache.clear()
    logger.debug(f"Cleared config cache ({cache_size} entries)")

