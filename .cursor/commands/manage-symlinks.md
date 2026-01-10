# Manage Symlinks

## Overview

Fix broken symlinks, update latest pointers, and verify symlink integrity across strategy results directories.

## Steps

1. **Find Broken Symlinks** - Identify broken symlinks in results directories
2. **Fix Strategy Symlinks** - Recreate `strategies/{asset_class}/{strategy}/results` symlinks
3. **Update Latest Pointers** - Recreate `results/{strategy}/latest` symlinks pointing to most recent results
4. **Verify Integrity** - Check all symlinks are valid and point to existing directories
5. **Batch Fix** - Fix symlinks for all strategies or specific asset classes

## Checklist

- [ ] Broken symlinks identified
- [ ] Strategy results symlinks fixed (strategies/{asset_class}/{strategy}/results)
- [ ] Latest symlinks updated (results/{strategy}/latest)
- [ ] All symlinks verified and working
- [ ] Batch operations completed if needed

## Symlink Management Patterns

**Fix symlinks for a strategy:**
```python
from lib.utils import check_and_fix_symlinks

# Fix symlinks for a specific strategy
fixed_links = check_and_fix_symlinks('btc_sma_cross', asset_class='crypto')
print(f"Fixed {len(fixed_links)} symlink(s)")
for link in fixed_links:
    print(f"  - {link}")
```

**Update latest symlink manually:**
```python
from lib.utils import update_symlink, get_project_root
from pathlib import Path

root = get_project_root()
strategy_name = 'btc_sma_cross'
results_base = root / 'results' / strategy_name

# Find most recent backtest directory
backtest_dirs = sorted(
    [d for d in results_base.iterdir() if d.is_dir() and d.name.startswith('backtest_')],
    reverse=True
)

if backtest_dirs:
    latest_link = results_base / 'latest'
    update_symlink(backtest_dirs[0], latest_link)
    print(f"Updated latest symlink: {latest_link} -> {backtest_dirs[0]}")
```

**Find and fix all broken symlinks:**
```python
from lib.utils import get_project_root, check_and_fix_symlinks
from pathlib import Path

root = get_project_root()
results_base = root / 'results'

# Find all strategies
for strategy_dir in results_base.iterdir():
    if strategy_dir.is_dir():
        # Try to fix symlinks (handles missing asset_class gracefully)
        try:
            fixed = check_and_fix_symlinks(strategy_dir.name)
            if fixed:
                print(f"Fixed {len(fixed)} symlink(s) for {strategy_dir.name}")
        except Exception as e:
            print(f"Error fixing {strategy_dir.name}: {e}")
```

**Verify symlink integrity:**
```bash
# Find broken symlinks
find results/ -type l ! -exec test -e {} \; -print

# Find broken symlinks in strategies
find strategies/ -type l ! -exec test -e {} \; -print
```

**Script (CLI):**
```python
# Create script to batch fix symlinks
from lib.utils import get_project_root, check_and_fix_symlinks
from pathlib import Path

root = get_project_root()
results_base = root / 'results'

all_fixed = []
for strategy_dir in results_base.iterdir():
    if strategy_dir.is_dir():
        fixed = check_and_fix_symlinks(strategy_dir.name)
        all_fixed.extend(fixed)

print(f"Fixed {len(all_fixed)} symlink(s) total")
```

## Common Issues

- **Broken latest symlink** - Points to deleted directory
- **Broken strategy results symlink** - Points to non-existent results directory
- **Missing symlinks** - Symlinks not created during backtest

## Notes

- Use `lib/utils.py:check_and_fix_symlinks()` (don't duplicate symlink logic)
- Use `lib/utils.py:update_symlink()` for manual symlink updates
- Symlinks are automatically fixed during `save_results()` operations
- Always verify symlinks point to existing directories
- Use `get_project_root()` for path resolution (never hardcode)

## Related Commands

- run-backtest.md - Backtests automatically create/update symlinks
