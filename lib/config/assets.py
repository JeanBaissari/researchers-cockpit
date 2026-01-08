"""
Asset configuration loading.

Provides functions to load asset class configurations and data source settings.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from ..utils import load_yaml
from .core import _get_config_path, get_config_cache, load_settings


# Configure logging
logger = logging.getLogger(__name__)


def load_asset_config(asset_class: str) -> Dict[str, Any]:
    """
    Load asset configuration for a specific asset class.
    
    Args:
        asset_class: Asset class ('crypto', 'forex', 'equities')
        
    Returns:
        dict: Asset configuration dictionary
        
    Raises:
        FileNotFoundError: If asset config file doesn't exist
        ValueError: If asset_class is invalid
    """
    valid_asset_classes = ['crypto', 'forex', 'equities']
    if asset_class not in valid_asset_classes:
        raise ValueError(
            f"Invalid asset_class: {asset_class}. "
            f"Must be one of: {valid_asset_classes}"
        )
    
    cache = get_config_cache()
    cache_key = f'asset_{asset_class}'
    if cache_key in cache:
        logger.debug(f"Returning cached asset config for '{asset_class}'")
        return cache[cache_key]
    
    asset_path = _get_config_path(f'assets/{asset_class}.yaml')
    if not asset_path.exists():
        raise FileNotFoundError(
            f"Asset config not found: {asset_path}. "
            f"Expected path: config/assets/{asset_class}.yaml"
        )
    
    logger.debug(f"Loading asset config from {asset_path}")
    config = load_yaml(asset_path)
    cache[cache_key] = config
    return config


def get_data_source(source_name: str) -> Dict[str, Any]:
    """
    Load data source configuration from config/data_sources.yaml.
    
    Args:
        source_name: Name of data source (e.g., 'yahoo', 'binance', 'oanda')
        
    Returns:
        dict: Data source configuration
        
    Raises:
        FileNotFoundError: If data_sources.yaml doesn't exist
        KeyError: If source_name not found in config
    """
    cache = get_config_cache()
    cache_key = 'data_sources'
    if cache_key not in cache:
        data_sources_path = _get_config_path('data_sources.yaml')
        logger.debug(f"Loading data sources from {data_sources_path}")
        cache[cache_key] = load_yaml(data_sources_path)
    else:
        logger.debug("Returning cached data sources")
    
    data_sources = cache[cache_key]
    
    if source_name not in data_sources:
        available = ', '.join(data_sources.keys())
        raise KeyError(
            f"Data source '{source_name}' not found in config/data_sources.yaml. "
            f"Available sources: {available}"
        )
    
    return data_sources[source_name]


def get_default_bundle(asset_class: str) -> str:
    """
    Get the default bundle name for an asset class.
    
    Args:
        asset_class: Asset class ('crypto', 'forex', 'equities')
        
    Returns:
        str: Default bundle name
        
    Raises:
        KeyError: If default bundle not configured
    """
    settings = load_settings()
    bundle_key = f'default_{asset_class}'
    
    try:
        bundle = settings['data']['bundles'][bundle_key]
        logger.debug(f"Found default bundle for '{asset_class}': {bundle}")
        return bundle
    except KeyError:
        # Fallback to common names (must match settings.yaml convention)
        defaults = {
            'equities': 'yahoo_equities_daily',
            'crypto': 'yahoo_crypto_daily',
            'forex': 'yahoo_forex_daily',
        }
        fallback = defaults.get(asset_class, 'yahoo_equities_daily')
        logger.warning(
            f"Default bundle for '{asset_class}' not found in settings.yaml. "
            f"Using fallback: '{fallback}'. Consider adding 'data.bundles.{bundle_key}' "
            f"to config/settings.yaml."
        )
        return fallback

