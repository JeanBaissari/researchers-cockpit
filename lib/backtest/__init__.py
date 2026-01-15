"""
Backtest package for The Researcher's Cockpit.

This package provides modular backtest execution functionality:
- strategy: Strategy loading and module extraction
- config: Backtest configuration and validation
- runner: Main backtest execution
- results: Result saving and metrics calculation
- verification: Data integrity verification

Main exports:
- run_backtest: Execute a backtest for a strategy
- save_results: Save backtest results to timestamped directory
- validate_strategy_symbols: Pre-flight symbol validation
- BacktestConfig: Configuration dataclass
- StrategyModule: Strategy function container
"""

from .runner import run_backtest, validate_strategy_symbols
from .results import save_results
from .config import BacktestConfig
from .strategy import StrategyModule

__all__ = [
    'run_backtest',
    'save_results',
    'validate_strategy_symbols',
    'BacktestConfig',
    'StrategyModule',
]















