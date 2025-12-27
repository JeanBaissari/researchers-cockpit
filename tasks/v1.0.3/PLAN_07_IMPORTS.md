# Import Path Correction

Fix incorrect import paths that reference the project as a package.

## Problem Statement

`lib/backtest.py` has an incorrect import:

```python
from v1_researchers_cockpit.zipline.extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)
```

This assumes the project is installed as a package named `v1_researchers_cockpit`, which:
1. Requires `pip install -e .` or similar installation
2. References a non-existent path (`zipline/extension.py` vs `lib/extension.py`)
3. Will fail in most execution contexts

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Identify all incorrect import paths

## Future Tasks

### Fix backtest.py Imports
- [ ] Change import from `v1_researchers_cockpit.zipline.extension` to `lib.extension`
- [ ] Or use relative import: `from .extension import ...`

### Verify All Imports
- [ ] Check all lib/ modules for absolute package imports
- [ ] Ensure relative imports work correctly
- [ ] Test imports from different execution contexts

### Package Structure Decision
- [ ] Decide if project should be installable package
- [ ] If yes, create proper `setup.py` or `pyproject.toml`
- [ ] If no, ensure all imports are relative or path-based

## Implementation Plan

### Step 1: Fix Immediate Import Error

In `lib/backtest.py`, line 33-36:

```python
# BEFORE (incorrect):
from v1_researchers_cockpit.zipline.extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)

# AFTER (correct - relative import):
from .extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)
```

### Step 2: Verify extension.py Location

The file should be at `lib/extension.py`, not `zipline/extension.py`.

Current structure:
```
v1_researchers_cockpit/
├── lib/
│   ├── __init__.py
│   ├── backtest.py
│   ├── config.py
│   ├── data_loader.py
│   ├── extension.py      ← Calendar definitions HERE
│   └── ...
├── strategies/
├── results/
└── ...
```

### Step 3: Check Other Imports in backtest.py

Verify these imports are correct:

```python
# Local imports (should use relative)
from .config import load_settings, load_strategy_params, get_default_bundle, validate_strategy_params
from .utils import (
    get_project_root,
    get_strategy_path,
    timestamp_dir,
    update_symlink,
    save_yaml,
    ensure_dir,
    check_and_fix_symlinks,
    normalize_to_calendar_timezone,
)
from .extension import (  # FIXED
    register_custom_calendars,
    get_calendar_for_asset_class,
)
```

### Step 4: Verify Imports Across All Modules

Check each file in `lib/`:

| File | Status | Notes |
|------|--------|-------|
| `__init__.py` | ✓ | Uses relative imports correctly |
| `backtest.py` | ✗ | Has incorrect v1_researchers_cockpit import |
| `config.py` | ✓ | Uses relative imports |
| `data_loader.py` | ✓ | Uses relative imports |
| `data_integrity.py` | ? | Check for issues |
| `extension.py` | ✓ | No local imports |
| `metrics.py` | ✓ | No local imports |
| `optimize.py` | ✓ | Uses relative imports |
| `plots.py` | ✓ | Uses relative imports |
| `report.py` | ✓ | Uses relative imports |
| `utils.py` | ✓ | No local imports |
| `validate.py` | ✓ | Uses relative imports |

### Step 5: Test Import Resolution

Create a test script to verify imports work:

```python
#!/usr/bin/env python3
"""Test import resolution for lib/ modules."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all lib imports work correctly."""
    errors = []
    
    # Test each module
    try:
        from lib import config
        print("✓ lib.config")
    except ImportError as e:
        errors.append(f"✗ lib.config: {e}")
    
    try:
        from lib import utils
        print("✓ lib.utils")
    except ImportError as e:
        errors.append(f"✗ lib.utils: {e}")
    
    try:
        from lib import extension
        print("✓ lib.extension")
    except ImportError as e:
        errors.append(f"✗ lib.extension: {e}")
    
    try:
        from lib import data_loader
        print("✓ lib.data_loader")
    except ImportError as e:
        errors.append(f"✗ lib.data_loader: {e}")
    
    try:
        from lib import backtest
        print("✓ lib.backtest")
    except ImportError as e:
        errors.append(f"✗ lib.backtest: {e}")
    
    try:
        from lib import metrics
        print("✓ lib.metrics")
    except ImportError as e:
        errors.append(f"✗ lib.metrics: {e}")
    
    try:
        from lib import optimize
        print("✓ lib.optimize")
    except ImportError as e:
        errors.append(f"✗ lib.optimize: {e}")
    
    try:
        from lib import validate
        print("✓ lib.validate")
    except ImportError as e:
        errors.append(f"✗ lib.validate: {e}")
    
    try:
        from lib import report
        print("✓ lib.report")
    except ImportError as e:
        errors.append(f"✗ lib.report: {e}")
    
    try:
        from lib import plots
        print("✓ lib.plots")
    except ImportError as e:
        errors.append(f"✗ lib.plots: {e}")
    
    # Print summary
    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(e)
        return False
    else:
        print("\n✓ All imports successful")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
```

## Relevant Files

- `lib/backtest.py` - Line 33-36 (incorrect import)

## One-Line Fix

The entire fix is changing one import statement:

```python
# In lib/backtest.py, change line 33-36 from:
from v1_researchers_cockpit.zipline.extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)

# To:
from .extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)
```

## Testing

```bash
# Quick test
python -c "from lib.backtest import run_backtest; print('Import OK')"

# Full test
python scripts/test_imports.py
```
