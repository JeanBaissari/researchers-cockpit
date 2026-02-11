# Zipline Logger Integration

Integration guide for Zipline-Reloaded's named loggers (Blotter, ZiplineLog, DataPortal, AlgoWarning) with The Researcher's Cockpit logging system.

**Location:** `docs/api/zipline_loggers.md`

---

## Overview

Zipline-Reloaded uses named loggers for internal operations:
- **`Blotter`** - Order execution and trade management
- **`ZiplineLog`** - General Zipline framework logging
- **`DataPortal`** - Data access and pricing operations
- **`AlgoWarning`** - User-facing warnings (partial fills, cancels, etc.)

This guide shows how to integrate these loggers with The Researcher's Cockpit centralized logging system to capture Zipline's internal operations alongside your strategy logs.

**Key Features:**
- Access Zipline's internal loggers
- Configure log levels for Zipline components
- Route Zipline logs through project's structured logging
- Filter and format Zipline logs consistently
- Debug order execution, data access, and framework operations

---

## Zipline Named Loggers

### Blotter Logger

The `Blotter` logger captures order execution, trade management, and transaction processing.

**Logger Name:** `Blotter`

**Typical Messages:**
- Order placement and cancellation
- Order status changes (OPEN → FILLED, CANCELLED, REJECTED)
- Transaction processing
- Commission and slippage calculations

**Example Log Messages:**
```
Blotter - INFO - Order placed: asset=AAPL, amount=100, style=MarketOrder
Blotter - INFO - Order filled: order_id=abc123, price=150.25, commission=1.00
Blotter - WARNING - Order rejected: order_id=xyz789, reason=Insufficient capital
```

### ZiplineLog Logger

The `ZiplineLog` logger captures general Zipline framework operations.

**Logger Name:** `ZiplineLog`

**Typical Messages:**
- Algorithm initialization
- Trading calendar operations
- Performance tracking
- Framework lifecycle events

**Example Log Messages:**
```
ZiplineLog - INFO - Algorithm initialized: start=2023-01-01, end=2024-01-01
ZiplineLog - INFO - Trading calendar: NYSE, sessions=252
ZiplineLog - DEBUG - Performance tracking started
```

### DataPortal Logger

The `DataPortal` logger captures data access operations and pricing queries.

**Logger Name:** `DataPortal`

**Typical Messages:**
- Data bundle loading
- Price history queries
- Asset lookup operations
- Data cache operations

**Example Log Messages:**
```
DataPortal - INFO - Loading bundle: quandl
DataPortal - DEBUG - Price query: asset=AAPL, fields=['price'], bar_count=100
DataPortal - WARNING - Missing data for asset: XYZ, date=2023-06-15
```

### AlgoWarning Logger

The `AlgoWarning` logger captures user-facing warnings emitted by Zipline-Reloaded (for example, warnings about partial fills or end-of-day cancellations).

**Logger Name:** `AlgoWarning`

**Typical Messages:**
- Partial fill warnings
- End-of-day cancel warnings
- Order-related warnings intended for user action

---

## Basic Integration

### Accessing Zipline Loggers

```python
import logging

# Access Zipline's named loggers
blotter_logger = logging.getLogger('Blotter')
zipline_logger = logging.getLogger('ZiplineLog')
portal_logger = logging.getLogger('DataPortal')
warning_logger = logging.getLogger('AlgoWarning')

# Check current configuration
print(f"Blotter level: {blotter_logger.level}")
print(f"ZiplineLog level: {zipline_logger.level}")
print(f"DataPortal level: {portal_logger.level}")
```

### Setting Log Levels

```python
import logging

# Set log levels for Zipline loggers
logging.getLogger('Blotter').setLevel(logging.INFO)
logging.getLogger('ZiplineLog').setLevel(logging.WARNING)
logging.getLogger('DataPortal').setLevel(logging.DEBUG)
```

---

## Integration with Project Logging

### Option 1: Add Handlers to Zipline Loggers

Route Zipline logs through your project's logging system:

```python
import logging
import sys
from pathlib import Path

from lib.logging import configure_logging, ConsoleFormatter, StructuredFormatter
from lib.logging.config import get_logger

# Configure project logging first
configure_logging(level="INFO", console=True, file=True)

# Get project's root logger handlers
root_logger = logging.getLogger('cockpit')
project_handlers = root_logger.handlers

# Add project handlers to Zipline loggers
zipline_loggers = [
    logging.getLogger('Blotter'),
    logging.getLogger('ZiplineLog'),
    logging.getLogger('DataPortal'),
    logging.getLogger('AlgoWarning'),
]

for zipline_logger in zipline_loggers:
    # Set appropriate log level
    zipline_logger.setLevel(logging.INFO)
    
    # Add project handlers (they'll use project formatters)
    for handler in project_handlers:
        zipline_logger.addHandler(handler)
    
    # Prevent propagation to root logger (avoid duplicates)
    zipline_logger.propagate = False
```

### Option 2: Create Integration Function

Create a reusable function for Zipline logger integration:

```python
"""
Zipline logger integration utilities.
"""

import logging
from typing import Optional, Literal
from lib.logging import configure_logging, ConsoleFormatter, StructuredFormatter
from lib.logging.config import get_logger

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def integrate_zipline_loggers(
    blotter_level: LogLevel = "INFO",
    zipline_level: LogLevel = "WARNING",
    portal_level: LogLevel = "INFO",
    algo_warning_level: LogLevel = "WARNING",
    use_project_handlers: bool = True,
) -> None:
    """
    Integrate Zipline's named loggers with project logging system.
    
    Args:
        blotter_level: Log level for Blotter logger (order execution)
        zipline_level: Log level for ZiplineLog logger (framework)
        portal_level: Log level for DataPortal logger (data access)
        algo_warning_level: Log level for AlgoWarning logger (user-facing warnings)
        use_project_handlers: If True, route through project handlers
        
    Example:
        >>> integrate_zipline_loggers(
        ...     blotter_level="INFO",
        ...     zipline_level="WARNING",
        ...     portal_level="DEBUG"
        ... )
    """
    # Ensure project logging is configured
    root_logger = logging.getLogger('cockpit')
    if not root_logger.handlers:
        configure_logging(level="INFO", console=True, file=True)
        root_logger = logging.getLogger('cockpit')
    
    # Map log level strings to constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    # Configure Zipline loggers
    zipline_loggers = {
        'Blotter': level_map[blotter_level],
        'ZiplineLog': level_map[zipline_level],
        'DataPortal': level_map[portal_level],
        'AlgoWarning': level_map[algo_warning_level],
    }
    
    for logger_name, log_level in zipline_loggers.items():
        zipline_logger = logging.getLogger(logger_name)
        zipline_logger.setLevel(log_level)
        
        if use_project_handlers:
            # Add project handlers
            for handler in root_logger.handlers:
                zipline_logger.addHandler(handler)
            
            # Prevent propagation to avoid duplicate logs
            zipline_logger.propagate = False
        else:
            # Use default propagation (logs go to root logger)
            zipline_logger.propagate = True


def get_zipline_loggers():
    """
    Get references to Zipline's named loggers.
    
    Returns:
        Dict mapping logger names to logger instances.
    """
    return {
        'Blotter': logging.getLogger('Blotter'),
        'ZiplineLog': logging.getLogger('ZiplineLog'),
        'DataPortal': logging.getLogger('DataPortal'),
        'AlgoWarning': logging.getLogger('AlgoWarning'),
    }
```

### Option 3: Integration in Backtest Runner

Integrate Zipline loggers during backtest execution:

```python
# In lib/backtest/runner.py or execution.py

from lib.logging import configure_logging, backtest_logger
import logging

def run_backtest(...):
    """Run backtest with Zipline logger integration."""
    
    # Configure project logging
    configure_logging(
        level="INFO",
        strategy_name=strategy_name,
        run_id=run_id,
        console=True,
        file=True
    )
    
    # Integrate Zipline loggers
    integrate_zipline_loggers(
        blotter_level="INFO",  # Capture order execution
        zipline_level="WARNING",  # Only framework warnings
        portal_level="WARNING",  # Only data access warnings
    )
    
    # Run backtest
    backtest_logger.info("Starting backtest with Zipline logger integration")
    perf = execute_zipline_backtest(...)
    
    return perf
```

---

## Advanced Configuration

### Custom Formatters for Zipline Logs

Add custom formatting to distinguish Zipline logs from project logs:

```python
import logging
from lib.logging import ConsoleFormatter

class ZiplineFormatter(ConsoleFormatter):
    """Custom formatter for Zipline logs."""
    
    def format(self, record):
        # Add [ZIPLINE] prefix to distinguish from project logs
        original_msg = record.getMessage()
        record.msg = f"[ZIPLINE] {original_msg}"
        return super().format(record)

# Apply custom formatter
zipline_formatter = ZiplineFormatter()

for logger_name in ['Blotter', 'ZiplineLog', 'DataPortal']:
    zipline_logger = logging.getLogger(logger_name)
    zipline_logger.setLevel(logging.INFO)
    
    # Create handler with custom formatter
    handler = logging.StreamHandler()
    handler.setFormatter(zipline_formatter)
    zipline_logger.addHandler(handler)
    zipline_logger.propagate = False
```

### Filtering Zipline Logs

Filter specific Zipline log messages:

```python
import logging

class ZiplineFilter(logging.Filter):
    """Filter to include/exclude specific Zipline log messages."""
    
    def __init__(self, include_patterns=None, exclude_patterns=None):
        super().__init__()
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
    
    def filter(self, record):
        msg = record.getMessage()
        
        # Exclude if matches exclude pattern
        if any(pattern in msg for pattern in self.exclude_patterns):
            return False
        
        # Include if matches include pattern (or no include patterns)
        if not self.include_patterns:
            return True
        
        return any(pattern in msg for pattern in self.include_patterns)

# Apply filter
zipline_filter = ZiplineFilter(
    exclude_patterns=['DEBUG', 'cache'],  # Exclude debug and cache messages
    include_patterns=['Order', 'Transaction']  # Only order/transaction messages
)

blotter_logger = logging.getLogger('Blotter')
blotter_logger.addFilter(zipline_filter)
```

### Separate Log Files for Zipline

Route Zipline logs to separate files:

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from lib.paths import get_logs_dir

def setup_zipline_file_logging():
    """Set up separate log files for Zipline loggers."""
    
    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    zipline_loggers = {
        'Blotter': log_dir / 'zipline_blotter.log',
        'ZiplineLog': log_dir / 'zipline_framework.log',
        'DataPortal': log_dir / 'zipline_dataportal.log',
    }
    
    for logger_name, log_file in zipline_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Use structured formatter
        from lib.logging import StructuredFormatter
        handler.setFormatter(StructuredFormatter())
        
        logger.addHandler(handler)
        logger.propagate = False
```

---

## Usage Examples

### Example 1: Basic Integration

```python
from lib.logging import configure_logging
from lib.backtest import run_backtest
import logging

# Configure project logging
configure_logging(level="INFO", console=True, file=True)

# Integrate Zipline loggers
integrate_zipline_loggers(
    blotter_level="INFO",
    zipline_level="WARNING",
    portal_level="INFO"
)

# Run backtest - Zipline logs will appear in project logs
perf, calendar = run_backtest(
    strategy_name="btc_sma_cross",
    start_date="2023-01-01",
    end_date="2024-01-01"
)
```

### Example 2: Debug Order Execution

```python
import logging
from lib.logging import configure_logging

# Configure with DEBUG for Blotter
configure_logging(level="DEBUG", console=True, file=True)

# Set Blotter to DEBUG to see all order operations
blotter_logger = logging.getLogger('Blotter')
blotter_logger.setLevel(logging.DEBUG)

# Add project handlers
root_logger = logging.getLogger('cockpit')
for handler in root_logger.handlers:
    blotter_logger.addHandler(handler)
blotter_logger.propagate = False

# Now all order operations will be logged
from lib.backtest import run_backtest
perf, calendar = run_backtest(...)
```

### Example 3: Monitor Data Access

```python
import logging
from lib.logging import configure_logging

# Configure logging
configure_logging(level="INFO", console=True, file=True)

# Set DataPortal to DEBUG to see all data queries
portal_logger = logging.getLogger('DataPortal')
portal_logger.setLevel(logging.DEBUG)

# Add project handlers
root_logger = logging.getLogger('cockpit')
for handler in root_logger.handlers:
    portal_logger.addHandler(handler)
portal_logger.propagate = False

# Now all data access operations will be logged
from lib.backtest import run_backtest
perf, calendar = run_backtest(...)
```

### Example 4: Complete Integration in Script

```python
#!/usr/bin/env python
"""
Backtest script with full Zipline logger integration.
"""

import logging
from lib.logging import configure_logging, LogContext, backtest_logger
from lib.backtest import run_backtest

def integrate_zipline_loggers():
    """Integrate Zipline loggers with project logging."""
    root_logger = logging.getLogger('cockpit')
    
    zipline_loggers = {
        'Blotter': logging.INFO,
        'ZiplineLog': logging.WARNING,
        'DataPortal': logging.INFO,
    }
    
    for logger_name, log_level in zipline_loggers.items():
        zipline_logger = logging.getLogger(logger_name)
        zipline_logger.setLevel(log_level)
        
        for handler in root_logger.handlers:
            zipline_logger.addHandler(handler)
        
        zipline_logger.propagate = False

def main():
    """Run backtest with integrated logging."""
    strategy_name = "btc_sma_cross"
    
    # Configure project logging
    configure_logging(
        level="INFO",
        strategy_name=strategy_name,
        console=True,
        file=True
    )
    
    # Integrate Zipline loggers
    integrate_zipline_loggers()
    
    # Run backtest with context
    with LogContext(phase="backtest", strategy=strategy_name):
        backtest_logger.info("Starting backtest with Zipline logger integration")
        
        perf, calendar = run_backtest(
            strategy_name=strategy_name,
            start_date="2023-01-01",
            end_date="2024-01-01"
        )
        
        backtest_logger.info("Backtest completed successfully")

if __name__ == '__main__':
    main()
```

---

## Best Practices

### 1. Configure Before Backtest Execution

Always configure Zipline loggers before running backtests:

```python
# ✅ GOOD - Configure before backtest
configure_logging(...)
integrate_zipline_loggers(...)
run_backtest(...)

# ❌ BAD - Configure after backtest (misses early logs)
run_backtest(...)
integrate_zipline_loggers(...)
```

### 2. Use Appropriate Log Levels

Set log levels based on your needs:

```python
# Development: DEBUG for detailed Zipline operations
integrate_zipline_loggers(
    blotter_level="DEBUG",
    zipline_level="INFO",
    portal_level="DEBUG"
)

# Production: INFO/WARNING to reduce noise
integrate_zipline_loggers(
    blotter_level="INFO",
    zipline_level="WARNING",
    portal_level="WARNING"
)
```

### 3. Prevent Duplicate Logs

Always set `propagate=False` when adding custom handlers:

```python
# ✅ GOOD - Prevents duplicates
zipline_logger.propagate = False

# ❌ BAD - Creates duplicate logs
zipline_logger.propagate = True  # Logs appear twice!
```

### 4. Use Context for Zipline Logs

Zipline logs will automatically include project context if using project handlers:

```python
with LogContext(phase="backtest", strategy="btc_sma_cross"):
    # Zipline logs will include context from project handlers
    run_backtest(...)
```

### 5. Separate Files for Debugging

Use separate log files when debugging Zipline issues:

```python
# Create separate files for Zipline logs
setup_zipline_file_logging()

# Now Zipline logs go to:
# - logs/zipline_blotter.log
# - logs/zipline_framework.log
# - logs/zipline_dataportal.log
```

---

## Troubleshooting

### Zipline Logs Not Appearing

**Problem:** Zipline logs don't appear in project logs.

**Solution:**
1. Ensure Zipline loggers are configured before backtest execution
2. Check that handlers are added to Zipline loggers
3. Verify log levels are set appropriately
4. Check that `propagate=False` is set (prevents routing to root logger)

```python
# Debug Zipline logger configuration
blotter_logger = logging.getLogger('Blotter')
print(f"Level: {blotter_logger.level}")
print(f"Handlers: {blotter_logger.handlers}")
print(f"Propagate: {blotter_logger.propagate}")
```

### Too Many Zipline Logs

**Problem:** Zipline logs are too verbose.

**Solution:**
1. Increase log levels (INFO → WARNING)
2. Use filters to exclude specific messages
3. Route to separate files instead of console

```python
# Reduce verbosity
integrate_zipline_loggers(
    blotter_level="WARNING",  # Only warnings/errors
    zipline_level="ERROR",    # Only errors
    portal_level="WARNING"    # Only warnings/errors
)
```

### Duplicate Logs

**Problem:** Zipline logs appear twice.

**Solution:**
Set `propagate=False` on Zipline loggers:

```python
zipline_logger.propagate = False  # Prevents duplicate logs
```

---

## See Also

- [Logging API](logging.md) - Project logging system documentation
- [Backtest API](backtest.md) - Backtest execution (uses logging)
- [Zipline-Reloaded Documentation](https://zipline.ml4trading.io) - Official Zipline documentation
- [Blotter Documentation](../archive/code_patterns/07_finance/blotter.md) - Blotter operations

---

## Implementation Notes

**Zipline Logger Names:**
- These are hardcoded logger names in Zipline-Reloaded
- They are created automatically when Zipline modules are imported
- They use Python's standard `logging` module

**Integration Approach:**
- Project logging system (`lib/logging/`) is separate from Zipline loggers
- Integration is achieved by adding project handlers to Zipline loggers
- This allows Zipline logs to use project formatters and routing

**Performance:**
- Adding handlers to Zipline loggers has minimal performance impact
- Log levels can be adjusted to reduce overhead in production
- Separate log files can be used to isolate Zipline logs

---

**Last Updated:** 2026-01-28
**Version:** v1.12.0+
