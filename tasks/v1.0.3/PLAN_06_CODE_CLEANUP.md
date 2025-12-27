# Code Cleanup & Standards

Remove debug logs, fix error handling, and apply consistent coding standards.

## Problem Statement

The current codebase has several code quality issues:

1. **Debug Logs:** Hardcoded debug log writes to `/home/jeanbaissari/.cursor/debug.log`
2. **Bare Except Clauses:** Multiple `except:` without specific exceptions
3. **Inconsistent Error Handling:** Mix of raise, log, and silent failures
4. **Missing Type Hints:** Inconsistent use of type annotations
5. **Print Statements:** Should use logging instead

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Identify all debug log blocks
- [ ] Identify all bare except clauses

## Future Tasks

### Debug Log Removal
- [ ] Remove all `#region agent log` blocks from backtest.py
- [ ] Count: approximately 15+ debug log blocks to remove
- [ ] Ensure no hardcoded paths remain in codebase

### Error Handling Standardization
- [ ] Replace bare `except:` with specific exceptions
- [ ] Add proper logging instead of print statements
- [ ] Standardize error message format
- [ ] Add context to raised exceptions

### Logging Setup
- [ ] Create centralized logging configuration
- [ ] Add log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Configure log format with timestamps
- [ ] Add optional file logging

### Code Standards
- [ ] Add type hints to public functions
- [ ] Add docstrings to all public functions
- [ ] Remove unused imports
- [ ] Fix line length issues (>100 chars)

## Implementation Plan

### Step 1: Remove Debug Log Blocks

The debug logs follow this pattern:

```python
# #region agent log
with open('/home/jeanbaissari/.cursor/debug.log', 'a') as f:
    f.write(json.dumps({...}) + '\n')
# #endregion
```

**Files with debug logs:**
- `lib/backtest.py` - Multiple blocks (lines 143-146, 186-189, 204-207, etc.)

**Removal approach:**
1. Search for `#region agent log`
2. Delete from `# #region` to `# #endregion` inclusive
3. Verify no references to debug.log remain

### Step 2: Create Logging Configuration

Create `lib/logging_config.py`:

```python
"""Centralized logging configuration for The Researcher's Cockpit."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_file: Optional file path for file logging
        format_string: Custom format string
        
    Returns:
        Configured root logger
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    root_logger = logging.getLogger('researchers_cockpit')
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(format_string))
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(format_string))
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module."""
    return logging.getLogger(f'researchers_cockpit.{name}')
```

### Step 3: Fix Bare Except Clauses

**Pattern to fix:**

```python
# BAD
try:
    _auto_register_yahoo_bundle_if_exists()
except:
    pass

# GOOD
try:
    _auto_register_yahoo_bundle_if_exists()
except ImportError:
    # Zipline not installed, skip registration
    pass
except Exception as e:
    logger.warning(f"Auto-registration failed: {e}")
```

**Files with bare excepts:**
- `lib/data_loader.py` - lines 33, 39
- `lib/__init__.py` - multiple try/except blocks
- `lib/backtest.py` - several fallback patterns

### Step 4: Replace Print with Logging

**Pattern:**

```python
# BAD
print(f"Fetching data for {len(symbols)} symbols...")

# GOOD
logger.info(f"Fetching data for {len(symbols)} symbols")
```

**Files needing updates:**
- `lib/data_loader.py` - print in yahoo_ingest
- `lib/validate.py` - print in walk_forward
- `lib/optimize.py` - print in grid_search, random_search

### Step 5: Add Type Hints

**Priority functions to annotate:**

```python
# backtest.py
def run_backtest(
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    data_frequency: str = 'daily',
    asset_class: Optional[str] = None
) -> pd.DataFrame:

# data_loader.py
def ingest_bundle(
    source: str,
    assets: List[str],
    bundle_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    data_frequency: str = 'daily',
    **kwargs: Any
) -> str:
```

## Debug Log Locations (Complete List)

From `backtest.py`:
1. Lines 143-146: `_prepare_backtest_config entry`
2. Lines 186-189: `_prepare_backtest_config exit`
3. Lines 204-207: `_validate_bundle_date_range entry`
4. Lines 217-220: `_validate_bundle_date_range timezone normalization`
5. Lines 225-228: `_validate_bundle_date_range normalized timestamps`
6. Lines 247-250: `_validate_bundle_date_range bundle date range`
7. Lines 269-272: `_validate_bundle_date_range AttributeError`
8. Lines 276-279: `_validate_bundle_date_range FileNotFoundError`
9. Lines 285-288: `_validate_bundle_date_range exit`
10. Lines 310-313: `_get_trading_calendar entry`
11. Lines 324-327: `_get_trading_calendar custom calendar found`
12. Lines 331-334: `_get_trading_calendar custom calendar failed`
13. Lines 340-343: `_get_trading_calendar equity_daily_bar_reader`
14. Lines 347-350: `_get_trading_calendar direct trading_calendar`
15. Lines 353-356: `_get_trading_calendar failed to extract`
16. Lines 361-364: `_get_trading_calendar AttributeError`
17. Lines 576-579: `_calculate_and_save_metrics entry`
18. Lines 603-606: `_calculate_and_save_metrics trading_days_per_year`
19. Lines 629-632: `_calculate_and_save_metrics exit`

**Total: 19 debug log blocks to remove**

## Relevant Files

- `lib/backtest.py` - 19 debug log blocks, some bare excepts
- `lib/data_loader.py` - Bare excepts, print statements
- `lib/__init__.py` - Import try/except blocks
- `lib/validate.py` - Print statements
- `lib/optimize.py` - Print statements
- `lib/logging_config.py` - New file to create

## Testing

After cleanup:

```bash
# Verify no debug paths remain
grep -r "debug.log" lib/
grep -r "jeanbaissari" lib/

# Verify no bare excepts
grep -n "except:" lib/*.py

# Test logging works
python -c "
from lib.logging_config import setup_logging, get_logger
setup_logging(level='DEBUG')
logger = get_logger('test')
logger.info('Test message')
"
```
