# Code Review

## Overview

Perform thorough code review for Python/Zipline code verifying functionality, SOLID/DRY compliance, modularity thresholds, and Zipline-reloaded 3.1.0 patterns.

## Steps

1. **Understand the change**
   - Read PR description and related issues
   - Identify scope: lib/ modules, strategies, scripts, or configs
   - Note assumptions about data bundles, calendars, or parameters

2. **Validate functionality**
   - Confirm code delivers intended behavior for backtests/optimization
   - Check edge cases: missing data, invalid parameters, calendar mismatches
   - Verify error handling uses lib/logging/ with proper context

3. **Assess architecture (SOLID/DRY)**
   - Check lib/ file sizes (< 150 lines) - flag if approaching limit
   - Verify single responsibility per module
   - Check for code duplication - should use lib/ modules
   - Ensure dependencies on abstractions (lib/config, lib/paths)

4. **Review Zipline patterns**
   - Verify UTC timezone normalization
   - Check custom calendar usage (CRYPTO, FOREX)
   - Validate Pipeline API patterns (EquityPricing)
   - Ensure no hardcoded paths (use lib/paths.py)

## Review Checklist

### Functionality

- [ ] Intended behavior works (backtest/optimization/validation)
- [ ] Edge cases handled (missing data, invalid params, calendar errors)
- [ ] Error handling uses lib/logging/ with context
- [ ] Results saved to correct locations with proper naming

### Architecture (SOLID/DRY)

- [ ] lib/ files < 150 lines (flag if > 120)
- [ ] Single responsibility per module
- [ ] No code duplication (reuses lib/ modules)
- [ ] Uses lib/config.py for settings (not hardcoded)
- [ ] Uses lib/paths.py for paths (not hardcoded)
- [ ] Functions < 50 lines, < 5 parameters

### Zipline Patterns

- [ ] UTC timezone normalization (normalize_to_utc)
- [ ] Custom calendar usage correct (CRYPTO, FOREX)
- [ ] Pipeline API uses EquityPricing patterns
- [ ] No hardcoded paths or settings
- [ ] Strategy parameters externalized (parameters.yaml)

### Code Quality

- [ ] Functions focused, names descriptive
- [ ] No dead code or unused imports
- [ ] Tests updated for new functionality
- [ ] Documentation (docstrings) added/updated
- [ ] Google-style docstrings with Args/Returns/Raises

## Architecture Violations to Flag

**File size violation:**
```python
# ❌ Flag: lib/metrics.py is 180 lines
# Should split into lib/metrics/core.py, lib/metrics/trade.py
```

**Hardcoded path:**
```python
# ❌ Flag: Hardcoded path
data_dir = '/home/user/project/data'

# ✅ Should use:
from lib.paths import get_project_root
data_dir = get_project_root() / 'data'
```

**Code duplication:**
```python
# ❌ Flag: Duplicated timestamp logic
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# ✅ Should use:
from lib.utils import timestamp_dir
result_dir = timestamp_dir(base_path, 'backtest')
```

**Missing timezone normalization:**
```python
# ❌ Flag: No UTC normalization
df['timestamp'] = pd.to_datetime(df['timestamp'])

# ✅ Should use:
from lib.data.normalization import normalize_to_utc
df['timestamp'] = normalize_to_utc(df['timestamp'])
```

## Notes

- Flag lib/ files approaching 150-line limit for proactive splitting
- Verify all paths use lib/paths.py (never hardcode)
- Check that strategies use parameters.yaml (no hardcoded params)
- Ensure error handling uses lib/logging/ (not basic logging)
- Review Zipline patterns against docs/code_patterns/

## Related Commands

- add-error-handling.md - For improving error handling
- add-documentation.md - For adding missing docs
- debug-issue.md - For debugging issues found in review