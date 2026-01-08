"""
Pre-configured module loggers.

Provides pre-configured loggers for common namespaces across
The Researcher's Cockpit.
"""

from .config import get_logger


# Module-level loggers for common namespaces
data_logger = get_logger('data')
strategy_logger = get_logger('strategy')
backtest_logger = get_logger('backtest')
metrics_logger = get_logger('metrics')
validation_logger = get_logger('validation')
report_logger = get_logger('report')
optimization_logger = get_logger('optimization')
pipeline_logger = get_logger('pipeline')
ingestion_logger = get_logger('ingestion')


# Public exports
__all__ = [
    "data_logger",
    "strategy_logger",
    "backtest_logger",
    "metrics_logger",
    "validation_logger",
    "report_logger",
    "optimization_logger",
    "pipeline_logger",
    "ingestion_logger",
]

