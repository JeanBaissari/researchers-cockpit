"""
Configuration loading and management for The Researcher's Cockpit.

Provides functions to load YAML configuration files with caching to avoid
repeated file I/O operations.
"""

from __future__ import annotations

# Standard library imports
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Local imports
from .utils import get_project_root, load_yaml


# Configure logging
logger = logging.getLogger(__name__)

# Cache for loaded configs
_config_cache: Dict[str, Any] = {}

# Date format regex for YYYY-MM-DD validation
_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _get_config_path(filename: str) -> Path:
    """Get path to config file."""
    return get_project_root() / 'config' / filename


def _validate_date_format(date_str: str) -> bool:
    """
    Validate that a date string is in YYYY-MM-DD format and represents a valid date.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not _DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def _parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


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
    
    cache_key = f'asset_{asset_class}'
    if cache_key in _config_cache:
        logger.debug(f"Returning cached asset config for '{asset_class}'")
        return _config_cache[cache_key]
    
    asset_path = _get_config_path(f'assets/{asset_class}.yaml')
    if not asset_path.exists():
        raise FileNotFoundError(
            f"Asset config not found: {asset_path}. "
            f"Expected path: config/assets/{asset_class}.yaml"
        )
    
    logger.debug(f"Loading asset config from {asset_path}")
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
    
    logger.debug(f"Loading strategy params from {params_path}")
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
        logger.debug(f"Loading data sources from {data_sources_path}")
        _config_cache[cache_key] = load_yaml(data_sources_path)
    else:
        logger.debug("Returning cached data sources")
    
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


def clear_config_cache() -> None:
    """Clear the configuration cache. Useful for testing or reloading configs."""
    global _config_cache
    cache_size = len(_config_cache)
    _config_cache.clear()
    logger.debug(f"Cleared config cache ({cache_size} entries)")


def get_warmup_days(params: Dict[str, Any]) -> int:
    """
    Get required warmup days for a strategy.

    The warmup period is the number of trading days required before the strategy
    can generate valid signals. This is typically determined by the longest
    indicator period used in the strategy.

    Resolution order:
    1. Explicit 'warmup_days' in backtest section
    2. Dynamic calculation from strategy parameters (max of all *_period params)
    3. Default fallback of 30 days

    Args:
        params: Strategy parameters dictionary

    Returns:
        int: Required warmup days
    """
    # Check for explicit warmup_days in backtest section
    backtest_config = params.get('backtest', {}) or {}
    explicit_warmup = backtest_config.get('warmup_days')

    if explicit_warmup is not None:
        logger.debug(f"Using explicit warmup_days: {explicit_warmup}")
        return int(explicit_warmup)

    # Dynamic calculation: find max of all *_period parameters
    strategy_config = params.get('strategy', {}) or {}
    period_values: set[int] = set()

    # Collect all keys ending with '_period' (covers all common patterns)
    for key, value in strategy_config.items():
        if key.endswith('_period') and isinstance(value, (int, float)) and value > 0:
            period_values.add(int(value))

    if period_values:
        max_period = max(period_values)
        logger.debug(f"Calculated warmup_days from periods: {max_period} (from {len(period_values)} period params)")
        return max_period

    # Default fallback
    logger.debug("Using default warmup_days: 30")
    return 30


def validate_strategy_params(params: Dict[str, Any], strategy_name: str) -> Tuple[bool, List[str]]:
    """
    Validate strategy parameters.
    
    Checks:
    - Required fields exist
    - Type correctness
    - Range validity
    - Enum values
    - Backtest section validity (dates, capital, warmup)
    - Date order validation (start_date < end_date)
    
    Args:
        params: Strategy parameters dictionary
        strategy_name: Name of strategy (for error messages)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        - is_valid: True if all validations pass
        - list_of_errors: List of error messages (empty if valid)
    """
    errors: List[str] = []
    
    # Check required fields
    if 'strategy' not in params:
        errors.append("Missing required section: 'strategy'")
        logger.warning(f"Validation failed for '{strategy_name}': missing 'strategy' section")
        return False, errors
    
    strategy = params['strategy']
    
    # Guard against strategy being None
    if strategy is None:
        errors.append("'strategy' section is null/None")
        logger.warning(f"Validation failed for '{strategy_name}': 'strategy' section is None")
        return False, errors
    
    # Ensure strategy is a dict
    if not isinstance(strategy, dict):
        errors.append(f"'strategy' section must be a dictionary, got {type(strategy).__name__}")
        logger.warning(f"Validation failed for '{strategy_name}': 'strategy' is not a dict")
        return False, errors
    
    # Required: asset_symbol
    if 'asset_symbol' not in strategy or not strategy['asset_symbol']:
        errors.append("Missing required parameter: 'strategy.asset_symbol'")
    elif not isinstance(strategy['asset_symbol'], str):
        errors.append("'strategy.asset_symbol' must be a string")
    
    # Required: rebalance_frequency
    valid_frequencies = ['daily', 'weekly', 'monthly']
    if 'rebalance_frequency' not in strategy:
        errors.append("Missing required parameter: 'strategy.rebalance_frequency'")
    elif strategy['rebalance_frequency'] not in valid_frequencies:
        errors.append(
            f"'strategy.rebalance_frequency' must be one of: {valid_frequencies}. "
            f"Got: {strategy['rebalance_frequency']}"
        )
    
    # Validate backtest section
    if 'backtest' in params:
        backtest = params['backtest']
        
        # Guard against backtest being None
        if backtest is None:
            errors.append("'backtest' section is null/None")
        elif not isinstance(backtest, dict):
            errors.append(f"'backtest' section must be a dictionary, got {type(backtest).__name__}")
        else:
            start_date_valid = False
            end_date_valid = False
            parsed_start = None
            parsed_end = None
            
            # Validate start_date if present
            if 'start_date' in backtest:
                start_date = backtest['start_date']
                if not isinstance(start_date, str):
                    errors.append("'backtest.start_date' must be a string in YYYY-MM-DD format")
                elif not _validate_date_format(start_date):
                    errors.append(
                        f"'backtest.start_date' must be a valid date in YYYY-MM-DD format. "
                        f"Got: '{start_date}'"
                    )
                else:
                    start_date_valid = True
                    parsed_start = _parse_date(start_date)
            
            # Validate end_date if present
            if 'end_date' in backtest:
                end_date = backtest['end_date']
                if not isinstance(end_date, str):
                    errors.append("'backtest.end_date' must be a string in YYYY-MM-DD format")
                elif not _validate_date_format(end_date):
                    errors.append(
                        f"'backtest.end_date' must be a valid date in YYYY-MM-DD format. "
                        f"Got: '{end_date}'"
                    )
                else:
                    end_date_valid = True
                    parsed_end = _parse_date(end_date)
            
            # Cross-validate: start_date must be before end_date
            if start_date_valid and end_date_valid and parsed_start and parsed_end:
                if parsed_start >= parsed_end:
                    errors.append(
                        f"'backtest.start_date' ({backtest['start_date']}) must be before "
                        f"'backtest.end_date' ({backtest['end_date']})"
                    )
            
            # Validate capital if present
            if 'capital' in backtest:
                capital = backtest['capital']
                if not isinstance(capital, (int, float)):
                    errors.append("'backtest.capital' must be a number")
                elif capital <= 0:
                    errors.append(f"'backtest.capital' must be positive. Got: {capital}")
            
            # Validate warmup_days if present
            if 'warmup_days' in backtest:
                warmup = backtest['warmup_days']
                if not isinstance(warmup, int):
                    errors.append("'backtest.warmup_days' must be an integer")
                elif warmup < 0:
                    errors.append(f"'backtest.warmup_days' must be non-negative. Got: {warmup}")
    
    # Validate position_sizing
    if 'position_sizing' in params:
        ps = params['position_sizing']
        
        # Guard against position_sizing being None
        if ps is None:
            errors.append("'position_sizing' section is null/None")
        elif not isinstance(ps, dict):
            errors.append(f"'position_sizing' section must be a dictionary, got {type(ps).__name__}")
        else:
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
        
        # Guard against risk being None
        if risk is None:
            errors.append("'risk' section is null/None")
        elif not isinstance(risk, dict):
            errors.append(f"'risk' section must be a dictionary, got {type(risk).__name__}")
        else:
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
    
    # Log validation result
    if errors:
        logger.warning(f"Validation failed for '{strategy_name}': {len(errors)} error(s)")
        for error in errors:
            logger.debug(f"  - {error}")
    else:
        logger.debug(f"Validation passed for '{strategy_name}'")
    
    return len(errors) == 0, errors
