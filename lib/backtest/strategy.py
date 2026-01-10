"""
Strategy loading module for The Researcher's Cockpit.

Provides functions to load strategy modules and extract required functions.
"""

import sys
import importlib.util
import logging
from dataclasses import dataclass
from typing import Optional, Callable

from ..utils import get_project_root, get_strategy_path


# Module-level logger
logger = logging.getLogger(__name__)


@dataclass
class StrategyModule:
    """Container for strategy functions."""
    initialize: Callable
    handle_data: Optional[Callable] = None
    analyze: Optional[Callable] = None
    before_trading_start: Optional[Callable] = None


def _load_strategy_module(strategy_name: str, asset_class: Optional[str] = None) -> StrategyModule:
    """
    Load strategy module and extract required functions.
    
    Args:
        strategy_name: Name of strategy
        asset_class: Optional asset class hint
        
    Returns:
        StrategyModule: Container with strategy functions
        
    Raises:
        FileNotFoundError: If strategy file not found
        ImportError: If module can't be loaded
        ValueError: If required functions missing
    """
    strategy_path = get_strategy_path(strategy_name, asset_class)
    strategy_file = strategy_path / 'strategy.py'
    
    if not strategy_file.exists():
        raise FileNotFoundError(
            f"Strategy file not found: {strategy_file}. "
            f"Expected: strategies/{asset_class}/{strategy_name}/strategy.py"
        )
    
    # Load strategy module
    spec = importlib.util.spec_from_file_location(
        f"strategy_{strategy_name}",
        strategy_file
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to create module spec for {strategy_file}")
    
    # Add project root to path for lib imports
    project_root = get_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)
    
    # Extract strategy functions
    initialize_func = getattr(strategy_module, 'initialize', None)
    if initialize_func is None:
        raise ValueError(
            f"Strategy {strategy_name} must have an 'initialize' function"
        )
    
    return StrategyModule(
        initialize=initialize_func,
        handle_data=getattr(strategy_module, 'handle_data', None),
        analyze=getattr(strategy_module, 'analyze', None),
        before_trading_start=getattr(strategy_module, 'before_trading_start', None)
    )





