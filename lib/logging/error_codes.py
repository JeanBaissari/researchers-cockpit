"""
Error codes for structured error tracking.

Provides categorized error codes for consistent error logging and monitoring
across The Researcher's Cockpit.
"""

from enum import Enum
from typing import NamedTuple


class ErrorCodeInfo(NamedTuple):
    """Container for error code information."""
    code: str
    category: str
    description: str


class ErrorCode(Enum):
    """
    Enumeration of error codes for structured logging.
    
    Each error code has:
    - code: Unique identifier (e.g., "DATA_001")
    - category: Error category (e.g., "data", "validation")
    - description: Human-readable description
    
    Usage:
        log_exception(
            logger,
            "Failed to load data",
            exc=e,
            error_code=ErrorCode.DATA_LOAD_FAILED,
        )
    """
    
    # Data errors (DATA_xxx)
    DATA_LOAD_FAILED = ErrorCodeInfo("DATA_001", "data", "Failed to load data from source")
    DATA_MISSING = ErrorCodeInfo("DATA_002", "data", "Required data is missing")
    DATA_INVALID_FORMAT = ErrorCodeInfo("DATA_003", "data", "Data format is invalid")
    DATA_PARSE_ERROR = ErrorCodeInfo("DATA_004", "data", "Failed to parse data")
    DATA_INTEGRITY_ERROR = ErrorCodeInfo("DATA_005", "data", "Data integrity check failed")
    
    # Validation errors (VAL_xxx)
    VALIDATION_ERROR = ErrorCodeInfo("VAL_001", "validation", "Validation failed")
    VALIDATION_SCHEMA_ERROR = ErrorCodeInfo("VAL_002", "validation", "Schema validation failed")
    VALIDATION_RANGE_ERROR = ErrorCodeInfo("VAL_003", "validation", "Value out of valid range")
    VALIDATION_TYPE_ERROR = ErrorCodeInfo("VAL_004", "validation", "Incorrect data type")
    VALIDATION_MISSING_FIELD = ErrorCodeInfo("VAL_005", "validation", "Required field is missing")
    
    # Configuration errors (CFG_xxx)
    CONFIG_LOAD_ERROR = ErrorCodeInfo("CFG_001", "config", "Failed to load configuration")
    CONFIG_INVALID = ErrorCodeInfo("CFG_002", "config", "Configuration is invalid")
    CONFIG_MISSING = ErrorCodeInfo("CFG_003", "config", "Required configuration is missing")
    
    # Strategy errors (STR_xxx)
    STRATEGY_LOAD_ERROR = ErrorCodeInfo("STR_001", "strategy", "Failed to load strategy")
    STRATEGY_INVALID = ErrorCodeInfo("STR_002", "strategy", "Strategy definition is invalid")
    STRATEGY_EXECUTION_ERROR = ErrorCodeInfo("STR_003", "strategy", "Strategy execution failed")
    
    # Backtest errors (BT_xxx)
    BACKTEST_INIT_ERROR = ErrorCodeInfo("BT_001", "backtest", "Backtest initialization failed")
    BACKTEST_RUN_ERROR = ErrorCodeInfo("BT_002", "backtest", "Backtest execution failed")
    BACKTEST_RESULT_ERROR = ErrorCodeInfo("BT_003", "backtest", "Failed to process backtest results")
    
    # Optimization errors (OPT_xxx)
    OPTIMIZATION_ERROR = ErrorCodeInfo("OPT_001", "optimization", "Optimization failed")
    OPTIMIZATION_CONVERGENCE = ErrorCodeInfo("OPT_002", "optimization", "Optimization did not converge")
    OPTIMIZATION_INVALID_PARAMS = ErrorCodeInfo("OPT_003", "optimization", "Invalid optimization parameters")
    
    # Metrics errors (MET_xxx)
    METRICS_CALCULATION_ERROR = ErrorCodeInfo("MET_001", "metrics", "Failed to calculate metrics")
    METRICS_INVALID_INPUT = ErrorCodeInfo("MET_002", "metrics", "Invalid input for metrics calculation")
    
    # File/IO errors (IO_xxx)
    IO_READ_ERROR = ErrorCodeInfo("IO_001", "io", "Failed to read file")
    IO_WRITE_ERROR = ErrorCodeInfo("IO_002", "io", "Failed to write file")
    IO_PATH_ERROR = ErrorCodeInfo("IO_003", "io", "Invalid or missing path")
    
    # Network errors (NET_xxx)
    NETWORK_ERROR = ErrorCodeInfo("NET_001", "network", "Network request failed")
    NETWORK_TIMEOUT = ErrorCodeInfo("NET_002", "network", "Network request timed out")
    API_ERROR = ErrorCodeInfo("NET_003", "network", "API returned an error")
    
    # General errors (GEN_xxx)
    UNKNOWN_ERROR = ErrorCodeInfo("GEN_001", "general", "An unknown error occurred")
    INTERNAL_ERROR = ErrorCodeInfo("GEN_002", "general", "An internal error occurred")
    
    @property
    def code(self) -> str:
        """Get the error code identifier."""
        return self.value.code
    
    @property
    def category(self) -> str:
        """Get the error category."""
        return self.value.category
    
    @property
    def description(self) -> str:
        """Get the error description."""
        return self.value.description
    
    def __str__(self) -> str:
        return f"{self.code}: {self.description}"


# Public exports
__all__ = [
    "ErrorCode",
    "ErrorCodeInfo",
]















