"""
The Researcher's Cockpit - Core Library

This package provides the foundational modules for running algorithmic trading
research with Zipline-reloaded.

Main packages (v1.11.0 modular architecture):
- bundles: Data bundle ingestion and management
- validation: Data integrity validation and quality checks
- calendars: Trading calendars (CryptoCalendar, ForexCalendar)
- backtest: Backtest execution and result saving
- metrics: Performance metrics and analytics
- config: Configuration loading and management
- logging: Centralized logging configuration
- optimize: Parameter optimization
- validate: Walk-forward and Monte Carlo validation
- report: Report generation
- plots: Visualization utilities
- data: Data processing utilities
- utils: Core utility functions
- paths: Robust project root resolution
"""

__version__ = "1.11.0"
__author__ = "The Researcher's Cockpit"

# Import all exports from centralized exports module
from ._exports import *

# Configure logging with defaults on import
from .logging import configure_logging
_root_logger = configure_logging(level='INFO', console=False, file=False)
