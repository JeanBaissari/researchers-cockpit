# Debug Issue

## Overview

Debug Python/Zipline issues systematically by analyzing error messages, tracing execution flow, checking data bundles/calendars, and using lib/logging/ for diagnostic information.

## Steps

1. **Problem Analysis**
   - Identify specific error message and traceback
   - Understand expected vs actual behavior (backtest results, data loading, strategy execution)
   - Check common issues: missing bundles, calendar mismatches, parameter validation
   - Review logs/ directory for error context

2. **Debugging Strategy**
   - Add structured logging using lib/logging/ with LogContext
   - Check data bundle existence and date ranges
   - Verify calendar consistency (bundle vs strategy)
   - Validate strategy parameters and symbol lookups
   - Use Python debugger (pdb) for complex issues

3. **Solution Approach**
   - Check docs/troubleshooting/ for known issues
   - Verify data bundle ingestion completed successfully
   - Confirm calendar alignment (CRYPTO/FOREX custom calendars)
   - Validate parameter ranges and types
   - Test with minimal example (1 month of data)

4. **Prevention**
   - Add validation checks for common failure points
   - Improve error messages with actionable suggestions
   - Add unit tests for edge cases
   - Document debugging steps in troubleshooting guide

## Checklist

- [ ] Identified specific error message and traceback
- [ ] Understood expected vs actual behavior
- [ ] Traced execution flow (backtest → data → strategy)
- [ ] Added structured logging with lib/logging/
- [ ] Checked data bundle existence and date ranges
- [ ] Verified calendar consistency
- [ ] Validated strategy parameters
- [ ] Proposed fixes with explanations
- [ ] Provided step-by-step resolution plan
- [ ] Suggested prevention measures

## Common Debugging Scenarios

**Backtest fails with "Bundle not found":**
```python
# Check bundle existence
from lib.bundles.registry import get_bundle_info
info = get_bundle_info('yahoo_crypto_daily')
# If None, run: python scripts/ingest_data.py --source yahoo --assets crypto
```

**Calendar mismatch error:**
```python
# Verify calendar alignment
from lib.calendars.registry import get_calendar
calendar = get_calendar('CRYPTO')
# Check bundle uses same calendar
```

**Parameter validation error:**
```python
# Validate parameters
from lib.config.strategy import load_strategy_params
params = load_strategy_params('btc_sma_cross')
# Check parameters.yaml for required fields
```

**Data loading issues:**
```python
# Add diagnostic logging
from lib.logging.config import get_logger
from lib.logging.context import LogContext

logger = get_logger(__name__)
with LogContext(phase='data_loading', bundle='yahoo_crypto_daily'):
    logger.debug(f"Loading data from {bundle_path}")
    # Check for missing dates, gaps, timezone issues
```

**Strategy execution error:**
```python
# Enable detailed logging
from lib.logging.config import configure_logging
configure_logging(level='DEBUG')
# Run backtest with minimal date range for faster iteration
```

## Debugging Tools

**Check logs:**
```bash
tail -f logs/researchers_cockpit.log
# Look for ERROR/CRITICAL entries with context
```

**Validate data bundle:**
```bash
python scripts/validate_bundles.py --bundle yahoo_crypto_daily
```

**Test strategy syntax:**
```python
# Quick syntax check
import importlib.util
spec = importlib.util.spec_from_file_location("strategy", "strategies/crypto/btc_sma_cross/strategy.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # Will raise SyntaxError if invalid
```

**Minimal backtest test:**
```python
# Test with 1 month of data
from lib.backtest import run_backtest
returns, _ = run_backtest('btc_sma_cross', '2024-01-01', '2024-01-31')
```

## Notes

- Check docs/troubleshooting/ first for known issues
- Use lib/logging/ for all diagnostic output (never print)
- Test with minimal examples before full backtest
- Verify data bundles exist before debugging strategy logic
- Check calendar alignment for custom calendars (CRYPTO, FOREX)

## Related Commands

- add-error-handling.md - For improving error handling
- code-review.md - For reviewing code quality
- run-backtest.md - For backtest execution workflow