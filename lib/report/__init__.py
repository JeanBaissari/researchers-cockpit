"""
Report generation package for The Researcher's Cockpit.

Generates human-readable markdown reports from backtest results.

Modules:
- strategy_report: Individual strategy report generation
- catalog: Strategy catalog management
- weekly: Weekly summary reports
- formatters: Shared formatting utilities
"""

# Public API
from .strategy_report import generate_report
from .catalog import update_catalog
from .weekly import generate_weekly_summary

__all__ = [
    # Main functions
    'generate_report',
    'update_catalog',
    'generate_weekly_summary',
]















