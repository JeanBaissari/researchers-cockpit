# Broken Symlink Detection and Auto-Fix

## Problem

Symlinks in the results directory can become broken if:
- Target directories are moved or deleted
- Results are archived or cleaned up
- Manual directory operations break symlinks

## Solution

**Implemented:** `lib/utils.py::check_and_fix_symlinks()`

This function automatically detects and fixes broken symlinks:

1. **Checks `results/{strategy}/latest` symlink**
   - If broken, finds most recent timestamped directory
   - Recreates symlink pointing to most recent results

2. **Checks `strategies/{asset_class}/{strategy}/results` symlink**
   - If broken, recreates pointing to `results/{strategy}/`

## Usage

```python
from lib.utils import check_and_fix_symlinks

# Check and fix symlinks for a strategy
fixed_links = check_and_fix_symlinks('spy_sma_cross', asset_class='equities')
print(f"Fixed {len(fixed_links)} symlink(s)")
```

## Automatic Integration

The function is automatically called in `lib/backtest.py::save_results()` before updating symlinks, ensuring broken symlinks are fixed during normal operations.

## Manual Fix

If you need to manually fix a broken symlink:

```bash
# Find broken symlinks
find results/ -type l ! -exec test -e {} \; -print

# Fix latest symlink
cd results/spy_sma_cross
rm latest
ln -s $(ls -td backtest_* | head -1) latest
```

## Date Fixed

2025-01-23



