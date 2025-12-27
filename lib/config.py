"""
Configuration loading and management for The Researcher's Cockpit.

Provides functions to load YAML configuration files with caching to avoid
repeated file I/O operations.
"""

# Standard library imports
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Local imports
from .utils import get_project_root, load_yaml


# Cache for loaded configs
_config_cache = {}


def _get_config_path(filename: str) -> Path:
    """Get path to config file."""
    return get_project_root() / 'config' / filename


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
        return _config_cache[cache_key]
    
    settings_path = _get_config_path('settings.yaml')
    settings = load_yaml(settings_path)
    _config_cache[cache_key] = settings
    return settings


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
    if asset_class not in ['crypto', 'forex', 'equities']:
        raise ValueError(
            f"Invalid asset_class: {asset_class}. "
            "Must be one of: 'crypto', 'forex', 'equities'"
        )
    
    cache_key = f'asset_{asset_class}'
    if cache_key in _config_cache:
        return _config_cache[cache_key]
    
    asset_path = _get_config_path(f'assets/{asset_class}.yaml')
    if not asset_path.exists():
        raise FileNotFoundError(
            f"Asset config not found: {asset_path}. "
            f"Expected path: config/assets/{asset_class}.yaml"
        )
    
    config = load_yaml(asset_path)
    _config_cache[cache_key] = config
    return config


def load_strategy_params(strategy_name: str, asset_class: Optional[str] = None) -> Dict[str, Any]:
    """
    Load parameters from a strategy's parameters.yaml file.
    
    Args:
        strategy_name: Name of strategy (e.g., 'spy_sma_cross')
        asset_class: Optional asset class. If None, searches all asset classes
        
    Returns:
        dict: Strategy parameters dictionary
        
    Raises:
        FileNotFoundError: If strategy or parameters.yaml not found
    """
    from .utils import get_strategy_path
    
    strategy_path = get_strategy_path(strategy_name, asset_class)
    params_path = strategy_path / 'parameters.yaml'
    
    if not params_path.exists():
        raise FileNotFoundError(
            f"parameters.yaml not found for strategy '{strategy_name}'. "
            f"Expected at: {params_path}"
        )
    
    return load_yaml(params_path)


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
    cache_key = 'data_sources'
    if cache_key not in _config_cache:
        data_sources_path = _get_config_path('data_sources.yaml')
        _config_cache[cache_key] = load_yaml(data_sources_path)
    
    data_sources = _config_cache[cache_key]
    
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
        return settings['data']['bundles'][bundle_key]
    except KeyError:
        # Fallback to common names
        defaults = {
            'equities': 'yahoo_equities_daily',
            'crypto': 'yahoo_crypto',
            'forex': 'oanda_forex',
        }
        return defaults.get(asset_class, 'quandl')


def clear_config_cache():
    """Clear the configuration cache. Useful for testing or reloading configs."""
    global _config_cache
    _config_cache.clear()


def validate_strategy_params(params: dict, strategy_name: str) -> Tuple[bool, List[str]]:
    """
    Validate strategy parameters.
    
    Checks:
    - Required fields exist
    - Type correctness
    - Range validity
    - Enum values
    
    Args:
        params: Strategy parameters dictionary
        strategy_name: Name of strategy (for error messages)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        - is_valid: True if all validations pass
        - list_of_errors: List of error messages (empty if valid)
    """
    errors = []
    
    # Check required fields
    if 'strategy' not in params:
        errors.append("Missing required section: 'strategy'")
        return False, errors
    
    strategy = params['strategy']
    
    # Required: asset_symbol
    if 'asset_symbol' not in strategy or not strategy['asset_symbol']:
        errors.append("Missing required parameter: 'strategy.asset_symbol'")
    elif not isinstance(strategy['asset_symbol'], str):
        errors.append("'strategy.asset_symbol' must be a string")
    
    # Required: rebalance_frequency
    if 'rebalance_frequency' not in strategy:
        errors.append("Missing required parameter: 'strategy.rebalance_frequency'")
    elif strategy['rebalance_frequency'] not in ['daily', 'weekly', 'monthly']:
        errors.append(
            f"'strategy.rebalance_frequency' must be one of: 'daily', 'weekly', 'monthly'. "
            f"Got: {strategy['rebalance_frequency']}"
        )
    
    # Validate position_sizing
    if 'position_sizing' in params:
        ps = params['position_sizing']
        
        if 'max_position_pct' in ps:
            max_pos = ps['max_position_pct']
            if not isinstance(max_pos, (int, float)):
                errors.append("'position_sizing.max_position_pct' must be a number")
            elif not (0.0 <= max_pos <= 1.0):
                errors.append(
                    f"'position_sizing.max_position_pct' must be between 0.0 and 1.0. "
                    f"Got: {max_pos}"
                )
        
        if 'method' in ps:
            valid_methods = ['fixed', 'volatility_scaled', 'kelly']
            if ps['method'] not in valid_methods:
                errors.append(
                    f"'position_sizing.method' must be one of: {valid_methods}. "
                    f"Got: {ps['method']}"
                )
    
    # Validate risk management
    if 'risk' in params:
        risk = params['risk']
        
        if 'stop_loss_pct' in risk:
            stop_loss = risk['stop_loss_pct']
            if not isinstance(stop_loss, (int, float)):
                errors.append("'risk.stop_loss_pct' must be a number")
            elif stop_loss <= 0:
                errors.append(
                    f"'risk.stop_loss_pct' must be positive. Got: {stop_loss}"
                )
            elif stop_loss > 1.0:
                errors.append(
                    f"'risk.stop_loss_pct' should typically be <= 1.0 (100%). Got: {stop_loss}"
                )
        
        if 'take_profit_pct' in risk and 'stop_loss_pct' in risk:
            take_profit = risk['take_profit_pct']
            stop_loss = risk['stop_loss_pct']
            if isinstance(take_profit, (int, float)) and isinstance(stop_loss, (int, float)):
                if take_profit <= stop_loss:
                    errors.append(
                        f"'risk.take_profit_pct' ({take_profit}) should be greater than "
                        f"'risk.stop_loss_pct' ({stop_loss})"
                    )
        
        if 'use_stop_loss' in risk:
            if not isinstance(risk['use_stop_loss'], bool):
                errors.append("'risk.use_stop_loss' must be a boolean")
        
        if 'use_trailing_stop' in risk:
            if not isinstance(risk['use_trailing_stop'], bool):
                errors.append("'risk.use_trailing_stop' must be a boolean")
        
        if 'use_take_profit' in risk:
            if not isinstance(risk['use_take_profit'], bool):
                errors.append("'risk.use_take_profit' must be a boolean")
    
    # Validate minutes_after_open
    if 'minutes_after_open' in strategy:
        minutes = strategy['minutes_after_open']
        if not isinstance(minutes, int):
            errors.append("'strategy.minutes_after_open' must be an integer")
        elif not (0 <= minutes <= 60):
            errors.append(
                f"'strategy.minutes_after_open' must be between 0 and 60. Got: {minutes}"
            )
    
    return len(errors) == 0, errors

