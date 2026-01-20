# Logging API

Centralized logging system for The Researcher's Cockpit.

Provides structured logging with consistent formatting across all modules. Supports both console output (human-readable) and file output (structured JSON).

**Location:** `lib/logging/`

---

## Overview

The `lib/logging` package provides a centralized logging system with structured logging, context management, and specialized loggers for different components. It follows the Single Responsibility Principle by focusing solely on logging configuration and management.

**Key Features:**
- Centralized logging configuration
- Structured logging with JSON format for file logs
- Context management for adding contextual information to logs
- Specialized loggers for different components (data, backtest, strategy, etc.)
- Thread-safe context operations
- Automatic log rotation (10MB files, 5 backups)
- Error code support for structured error tracking

**Module Structure:**
- `config.py` - Core logging configuration
- `context.py` - Context management (LogContext)
- `loggers.py` - Pre-configured specialized loggers
- `formatters.py` - Custom formatters (JSON, console)
- `error_codes.py` - Error code definitions
- `utils.py` - Logging utility functions

---

## Installation/Dependencies

**Required:**
- Python standard library (`logging`, `logging.handlers`, `threading`)
- `pathlib` - For log file path management

---

## Quick Start

```python
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging at application start
configure_logging(level="INFO", console=True, file=True)

# Get a logger
logger = get_logger('my_module')
logger.info("Operation completed")

# Use context for enhanced logging
with LogContext(phase="backtest", strategy="btc_sma_cross"):
    logger.info("Running backtest...")  # Includes context info automatically
```

---

## Public API Reference

### configure_logging()

Configure centralized logging for the application.

**Signature:**
```python
def configure_logging(
    strategy_name: Optional[str] = None,
    run_id: Optional[str] = None,
    level: LogLevel = "INFO",
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True,
    structured: bool = True,
    asset_type: Optional[str] = None,
    bundle_name: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> logging.Logger
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | Optional[str] | None | Optional strategy name for context |
| `run_id` | Optional[str] | None | Optional run ID for context |
| `level` | LogLevel | "INFO" | Logging level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" |
| `log_dir` | Optional[Path] | None | Directory for log files (default: PROJECT_ROOT/logs) |
| `console` | bool | True | Enable console output (human-readable format) |
| `file` | bool | True | Enable file output (structured JSON format) |
| `structured` | bool | True | Use JSON structured format for file logs |
| `asset_type` | Optional[str] | None | Optional asset type for context (equity, forex, crypto) |
| `bundle_name` | Optional[str] | None | Optional bundle name for context |
| `timeframe` | Optional[str] | None | Optional timeframe for context (1m, 5m, 15m, 30m, 1h, daily) |

**Returns:**
- `logging.Logger`: Root logger for the 'cockpit' namespace

**Raises:**
- `ValueError`: If level is not a valid log level

**Log Levels:**
- `"DEBUG"` - Detailed debugging information
- `"INFO"` - General informational messages
- `"WARNING"` - Warning messages for non-critical issues
- `"ERROR"` - Error messages for failures
- `"CRITICAL"` - Critical errors that may cause system failure

**Log File Configuration:**
- **Location**: `PROJECT_ROOT/logs/cockpit_YYYYMMDD.log` (UTC timestamp)
- **Rotation**: 10MB max file size, 5 backup files
- **Format**: JSON structured format (if `structured=True`) or console format

**Example:**
```python
from lib.logging import configure_logging

# Basic configuration
configure_logging(level="INFO", console=True, file=True)

# Configuration with context
configure_logging(
    level="DEBUG",
    strategy_name="btc_sma_cross",
    run_id="20241220_143000",
    asset_type="crypto",
    bundle_name="yahoo_crypto_daily",
    timeframe="daily"
)
```

---

### get_logger()

Get a logger with the cockpit namespace prefix.

**Signature:**
```python
def get_logger(name: str) -> logging.Logger
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Logger name (e.g., 'data', 'backtest', 'metrics') |

**Returns:**
- `logging.Logger`: Logger instance with name `cockpit.{name}`

**Example:**
```python
from lib.logging import get_logger

# Get a logger for your module
logger = get_logger('my_module')
logger.info("Operation started")
logger.error("Operation failed", exc_info=True)
```

---

### LogContext()

Context manager for adding context to all logs within the block.

**Signature:**
```python
@contextmanager
def LogContext(
    phase: str,
    strategy: Optional[str] = None,
    run_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    bundle_name: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> Generator[None, None, None]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `phase` | str | required | Pipeline phase (e.g., "hypothesis", "backtest", "optimize", "validate") |
| `strategy` | Optional[str] | None | Optional strategy name |
| `run_id` | Optional[str] | None | Optional run identifier |
| `asset_type` | Optional[str] | None | Optional asset type (equity, forex, crypto) |
| `bundle_name` | Optional[str] | None | Optional bundle name |
| `timeframe` | Optional[str] | None | Optional timeframe (1m, 5m, 15m, 30m, 1h, daily) |

**Returns:**
- Context manager that automatically adds context to all logs within the block

**Thread Safety:**
- Thread-safe context management with automatic cleanup on exit
- Previous context values are restored when the context manager exits

**Example:**
```python
from lib.logging import LogContext, get_logger

logger = get_logger('backtest')

# Use LogContext to add context to all logs
with LogContext(
    phase="backtest",
    strategy="btc_sma_cross",
    run_id="20241220_143000",
    asset_type="crypto",
    bundle_name="yahoo_crypto_daily",
    timeframe="daily"
):
    logger.info("Starting backtest")  # Includes all context info
    logger.info("Loading data")  # Includes all context info
    logger.info("Backtest complete")  # Includes all context info
# Context automatically cleared on exit
```

**Nested Context Example:**
```python
# Outer context
with LogContext(phase="backtest", strategy="btc_sma_cross"):
    logger.info("Outer context log")
    
    # Inner context (overrides phase, adds run_id)
    with LogContext(phase="optimize", run_id="20241220_143000"):
        logger.info("Inner context log")  # Uses phase="optimize", includes run_id
    
    logger.info("Back to outer context")  # Uses phase="backtest" again
```

---

### Pre-configured Loggers

Specialized loggers for different components.

**Available Loggers:**
- `data_logger` - Data operations (ingestion, validation)
- `strategy_logger` - Strategy execution
- `backtest_logger` - Backtest execution
- `metrics_logger` - Metrics calculation
- `validation_logger` - Data validation
- `report_logger` - Report generation
- `optimization_logger` - Parameter optimization
- `pipeline_logger` - Pipeline operations
- `ingestion_logger` - Data ingestion

**Example:**
```python
from lib.logging import data_logger, backtest_logger, strategy_logger

# Use specialized loggers
data_logger.info("Ingesting bundle: btc_1d")
backtest_logger.info("Running backtest: btc_sma_cross")
strategy_logger.info("Strategy initialized")
```

---

### Context Management Functions

Functions for managing logging context programmatically.

**Functions:**
- `reset_context()` - Clear all context values at once
- `get_context_value(key: str)` - Get a context value
- `set_context_value(key: str, value: Any)` - Set a context value
- `clear_context_value(key: str)` - Clear a context value
- `has_context_value(key: str)` - Check if context value exists

**Example:**
```python
from lib.logging import set_context_value, get_context_value, reset_context

# Set context programmatically
set_context_value('strategy', 'btc_sma_cross')
set_context_value('run_id', '20241220_143000')

# Get context value
strategy = get_context_value('strategy')  # Returns 'btc_sma_cross'

# Clear all context
reset_context()
```

---

### Logging Utility Functions

Helper functions for structured logging.

#### log_with_context()

Log a message with additional context fields.

**Signature:**
```python
def log_with_context(
    logger: logging.Logger,
    level: Union[int, LogLevel],
    message: str,
    error_code: Optional[ErrorCode] = None,
    **kwargs: Any,
) -> None
```

**Example:**
```python
from lib.logging import log_with_context, get_logger
from lib.logging.error_codes import ErrorCode

logger = get_logger('data')

log_with_context(
    logger,
    logging.INFO,
    "Bundle ingestion started",
    bundle_name="btc_1d",
    record_count=1000,
    source="yahoo"
)
```

#### log_exception()

Log an exception with consistent traceback formatting.

**Signature:**
```python
def log_exception(
    logger: logging.Logger,
    message: str,
    exc: Optional[BaseException] = None,
    error_code: Optional[ErrorCode] = None,
    include_traceback: bool = True,
    **kwargs: Any,
) -> None
```

**Example:**
```python
from lib.logging import log_exception, get_logger
from lib.logging.error_codes import ErrorCode

logger = get_logger('backtest')

try:
    risky_operation()
except ValueError as e:
    log_exception(
        logger,
        "Failed to process data",
        exc=e,
        error_code=ErrorCode.VALIDATION_ERROR,
        data_source="yahoo",
    )
```

#### log_validation_result()

Log a ValidationResult with appropriate log levels.

**Signature:**
```python
def log_validation_result(
    logger: logging.Logger,
    result: Any,  # ValidationResult from lib.validation
    include_details: bool = True,
) -> None
```

**Example:**
```python
from lib.logging import log_validation_result, validation_logger
from lib.validation import validate_bundle

result = validate_bundle('btc_1d')
log_validation_result(validation_logger, result, include_details=True)
```

---

## Module Structure

The `lib/logging` package contains:

**Core Configuration** (`config.py`):
- `configure_logging()` - Main configuration function
- `shutdown_logging()` - Properly shutdown logging
- `get_logger()` - Get logger with namespace prefix
- `LogLevel` - Type alias for log levels

**Context Management** (`context.py`):
- `LogContext()` - Context manager for structured logging
- `reset_context()` - Clear all context values
- `get_context_value()` - Get context value
- `set_context_value()` - Set context value
- `clear_context_value()` - Clear context value
- `has_context_value()` - Check if context value exists

**Pre-configured Loggers** (`loggers.py`):
- `data_logger`, `strategy_logger`, `backtest_logger`, etc.

**Formatters** (`formatters.py`):
- `StructuredFormatter` - JSON format for file logs
- `ConsoleFormatter` - Human-readable format for console logs

**Error Codes** (`error_codes.py`):
- `ErrorCode` - Error code definitions
- `ErrorCodeInfo` - Error code information

**Utilities** (`utils.py`):
- `log_with_context()` - Log with additional context fields
- `log_exception()` - Log exceptions with traceback
- `log_validation_result()` - Log validation results

---

## Examples

### Basic Logging Setup

```python
from lib.logging import configure_logging, get_logger

# Configure logging at application start
configure_logging(level="INFO", console=True, file=True)

# Get a logger
logger = get_logger('my_module')
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error message")
```

### Logging with Context

```python
from lib.logging import LogContext, get_logger

logger = get_logger('backtest')

# Use LogContext to add context to all logs
with LogContext(phase="backtest", strategy="btc_sma_cross"):
    logger.info("Starting backtest")
    logger.info("Loading data")
    logger.info("Backtest complete")
```

### Complete Backtest Logging Example

```python
from lib.logging import configure_logging, LogContext, backtest_logger
from lib.backtest import run_backtest

# Configure logging with context
configure_logging(
    level="INFO",
    strategy_name="btc_sma_cross",
    asset_type="crypto"
)

# Use LogContext for structured logging
with LogContext(
    phase="backtest",
    strategy="btc_sma_cross",
    run_id="20241220_143000",
    asset_type="crypto",
    bundle_name="yahoo_crypto_daily",
    timeframe="daily"
):
    backtest_logger.info("Starting backtest")
    
    try:
        perf = run_backtest(
            strategy_name="btc_sma_cross",
            start_date="2023-01-01",
            end_date="2024-01-01"
        )
        backtest_logger.info("Backtest completed successfully")
    except Exception as e:
        backtest_logger.error("Backtest failed", exc_info=True)
        raise
```

### Using Specialized Loggers

```python
from lib.logging import (
    data_logger,
    backtest_logger,
    strategy_logger,
    metrics_logger
)

# Data operations
data_logger.info("Ingesting bundle: btc_1d")
data_logger.warning("Missing data for dates: 2024-01-01")

# Backtest operations
backtest_logger.info("Backtest started: btc_sma_cross")
backtest_logger.info("Backtest completed")

# Strategy operations
strategy_logger.info("Strategy initialized")
strategy_logger.debug("Signal generated: BUY")

# Metrics operations
metrics_logger.info("Calculating metrics")
metrics_logger.info("Sharpe ratio: 1.25")
```

### Exception Logging

```python
from lib.logging import log_exception, get_logger
from lib.logging.error_codes import ErrorCode

logger = get_logger('data')

try:
    risky_operation()
except ValueError as e:
    log_exception(
        logger,
        "Failed to process data",
        exc=e,
        error_code=ErrorCode.VALIDATION_ERROR,
        data_source="yahoo",
        bundle_name="btc_1d"
    )
```

### Validation Result Logging

```python
from lib.logging import log_validation_result, validation_logger
from lib.validation import validate_bundle

# Validate bundle
result = validate_bundle('btc_1d')

# Log validation result
log_validation_result(validation_logger, result, include_details=True)
```

---

## Configuration

### Log Levels

Configure log levels based on environment:

```python
import os

# Development: DEBUG level
if os.getenv('ENV') == 'development':
    configure_logging(level="DEBUG", console=True, file=True)

# Production: INFO level
else:
    configure_logging(level="INFO", console=True, file=False)
```

### Log File Location

Log files are stored in `PROJECT_ROOT/logs/` by default:

```
logs/
├── cockpit_20241220.log      # Current log file
├── cockpit_20241220.log.1    # Backup 1
├── cockpit_20241220.log.2    # Backup 2
└── ...
```

### Structured vs Console Format

**Structured Format (JSON)** - For file logs:
```json
{
  "timestamp": "2024-12-20T14:30:00Z",
  "level": "INFO",
  "logger": "cockpit.backtest",
  "message": "Backtest started",
  "phase": "backtest",
  "strategy": "btc_sma_cross",
  "run_id": "20241220_143000"
}
```

**Console Format** - For human-readable output:
```
2024-12-20 14:30:00 - cockpit.backtest - INFO - Backtest started [phase=backtest, strategy=btc_sma_cross]
```

---

## Error Handling

**Log Level Validation:**
- Invalid log levels raise `ValueError` with valid options listed
- Log levels are case-insensitive (normalized to uppercase)

**Thread Safety:**
- All context operations are thread-safe using `threading.RLock()`
- Context values are automatically restored when `LogContext` exits

**Shutdown:**
- `shutdown_logging()` is automatically registered with `atexit`
- All handlers are properly flushed and closed on application exit

---

## Best Practices

1. **Configure Logging Early:**
   ```python
   # At application start
   configure_logging(level="INFO", console=True, file=True)
   ```

2. **Use LogContext for Operations:**
   ```python
   with LogContext(phase="backtest", strategy="btc_sma_cross"):
       # All logs within include context
       logger.info("Operation started")
   ```

3. **Use Specialized Loggers:**
   ```python
   # Use specialized loggers for component-specific logging
   from lib.logging import data_logger, backtest_logger
   data_logger.info("Data operation")
   backtest_logger.info("Backtest operation")
   ```

4. **Log Exceptions Properly:**
   ```python
   try:
       risky_operation()
   except Exception as e:
       log_exception(logger, "Operation failed", exc=e, error_code=ErrorCode.VALIDATION_ERROR)
   ```

5. **Use Appropriate Log Levels:**
   - `DEBUG` - Detailed debugging information
   - `INFO` - General informational messages
   - `WARNING` - Non-critical issues
   - `ERROR` - Operation failures
   - `CRITICAL` - System cannot continue

---

## See Also

- [Error Handling Standards](../.cursor/rules/error-handling.mdc) - Error handling patterns
- [Logging Standards](../.cursor/rules/logging.mdc) - Logging patterns and standards
- [Backtest API](backtest.md) - Backtest execution (uses logging)
- [Validation API](validation.md) - Data validation (uses logging)
- [Bundles API](bundles.md) - Data ingestion (uses logging)
