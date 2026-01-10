# Cleanup Unused Code

## Overview

Remove unused code from Researcher's Cockpit to improve maintainability, reduce complexity, and eliminate dead code in lib/ modules, strategies, and scripts.

## Steps

1. **Find Unused Files** - Identify files not imported anywhere
2. **Find Unused Functions** - Functions/classes not used in lib/ or strategies
3. **Remove Dead Code** - Delete commented code, unused variables
4. **Remove Unused Dependencies** - Check requirements.txt for unused packages
5. **Clean Imports** - Remove unused imports using autoflake
6. **Update Tests** - Remove tests for deleted code
7. **Verify Functionality** - Run tests and backtests to ensure nothing breaks

## Checklist

- [ ] Unused files identified
- [ ] Unused functions/classes found
- [ ] Commented code removed
- [ ] Unused dependencies removed
- [ ] Unused imports cleaned
- [ ] Tests updated
- [ ] All tests pass
- [ ] Backtests still work

## Find Unused Code

**Find unused imports:**
```bash
# Install autoflake if needed
pip install autoflake

# Check for unused imports
autoflake --check --recursive lib/ strategies/ scripts/

# Remove unused imports (dry-run first)
autoflake --remove-all-unused-imports --in-place lib/
```

**Find unused functions:**
```bash
# Use grep to find function definitions
grep -r "^def " lib/ | grep -v "__pycache__"

# Then search for usage
grep -r "function_name" lib/ strategies/
```

**Find commented code:**
```bash
# Search for commented Python code
grep -r "^\\s*#.*def\\|^\\s*#.*class" lib/ strategies/

# Find large comment blocks
grep -r "^\\s*#.*TODO.*DONE" lib/
```

**Find unused dependencies:**
```bash
# Check requirements.txt
pipreqs --print  # Generate requirements from actual imports
# Compare with existing requirements.txt
```

## Remove Unused Dependencies

```bash
# Check what's actually imported
pip install pipdeptree
pipdeptree

# Remove unused package
pip uninstall unused-package
# Update requirements.txt
```

## Clean Imports

```python
# ❌ Unused imports
import pandas as pd
import numpy as np
from lib.metrics import calculate_sharpe_ratio, calculate_sortino_ratio  # sortino never used

# ✅ Clean
import pandas as pd
import numpy as np
from lib.metrics import calculate_sharpe_ratio
```

**Auto-clean with autoflake:**
```bash
# Remove unused imports
autoflake --remove-all-unused-imports --in-place lib/metrics/core.py

# Remove unused variables too
autoflake --remove-unused-variables --in-place lib/
```

## Remove Dead Code

```python
# ❌ Commented code
# def old_calculate_metrics(returns):
#     # Old implementation
#     pass

# ❌ Unused function
def never_called_helper():
    return 'unused'

# ✅ Remove both
```

## Safe Cleanup Process

1. Find unused code
2. Create branch: `chore/cleanup-unused-code`
3. Remove code incrementally (one module at a time)
4. Run tests after each removal: `pytest tests/`
5. Test backtest still works: `python scripts/run_backtest.py --strategy test_strategy`
6. Commit: `chore: remove unused code from lib/metrics`
7. Create PR for review

## What to Remove

- [ ] Unused files in lib/ (not imported anywhere)
- [ ] Unused functions in lib/ modules
- [ ] Commented code blocks
- [ ] Unused imports (use autoflake)
- [ ] Unused dependencies in requirements.txt
- [ ] Old TODO comments (if completed)
- [ ] Duplicate code (extract to lib/ if used 2+ times)

## What NOT to Remove

- Code used in other branches
- Commented code with "TODO" if still valid
- Dependencies used indirectly (e.g., zipline-reloaded dependencies)
- Strategy files (even if unused - may be research in progress)
- Test fixtures in tests/conftest.py (used by multiple tests)

## Notes

- Test thoroughly after cleanup (pytest + manual backtest)
- Use git for safety (can revert)
- Check lib/ file sizes - splitting may be better than deletion
- Verify imports in strategies/ before removing lib/ functions
- Keep backward compatibility if function is in public API

## Related Commands

- code-review.md - For reviewing code before cleanup
- optimize-performance.md - For performance improvements