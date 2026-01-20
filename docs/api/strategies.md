# Strategies API

Module for strategy management, path resolution, and symlink handling in The Researcher's Cockpit.

**Location:** `lib/strategies/`  
**CLI Equivalent:** N/A (used internally by backtest and scripts)  
**Version:** v1.11.0

---

## Overview

The strategies module provides utilities for managing strategy directories, resolving strategy paths, creating strategies from templates, and managing result symlinks.

**Key Features:**
- Strategy path resolution across asset classes
- Strategy creation from templates
- Automatic symlink management for results
- Asset class-aware strategy discovery

**Strategy Directory Structure:**
```
strategies/
├── _template/              # Template for new strategies
│   ├── strategy.py
│   ├── parameters.yaml
│   └── hypothesis.md
├── crypto/                 # Crypto strategies
│   └── {strategy_name}/
├── forex/                  # Forex strategies
│   └── {strategy_name}/
└── equities/              # Equity strategies
    └── {strategy_name}/
```

---

## Installation/Dependencies

**Required:**
- `pathlib` (standard library)
- `shutil` (standard library)

**Note:** This module uses `lib.paths` for project root resolution and `lib.utils` for directory operations.

---

## Quick Start

### Get Strategy Path

```python
from lib.strategies import get_strategy_path

# Find strategy (searches all asset classes)
strategy_path = get_strategy_path('spy_sma_cross')
print(strategy_path)  # /path/to/strategies/equities/spy_sma_cross

# Find strategy in specific asset class
strategy_path = get_strategy_path('btc_sma_cross', asset_class='crypto')
```

### Create Strategy from Template

```python
from lib.strategies import create_strategy_from_template

# Create new strategy with asset symbol configured
strategy_path = create_strategy_from_template(
    name='my_new_strategy',
    asset_class='crypto',
    asset_symbol='BTC-USD'
)
print(f"Created strategy at: {strategy_path}")
```

### Fix Broken Symlinks

```python
from lib.strategies import check_and_fix_symlinks

# Check and fix symlinks for a strategy
fixed_links = check_and_fix_symlinks('spy_sma_cross')
print(f"Fixed {len(fixed_links)} symlinks")
```

---

## Public API Reference

### Strategy Path Resolution

#### `get_strategy_path()`

Locate a strategy directory.

**Signature:**
```python
def get_strategy_path(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy (e.g., `'spy_sma_cross'`) |
| `asset_class` | str | None | Optional asset class (`'crypto'`, `'forex'`, `'equities'`). If None, searches all asset classes |

**Returns:**
- `Path`: Path to strategy directory

**Raises:**
- `FileNotFoundError`: If strategy not found

**Search Order:**
1. If `asset_class` provided: `strategies/{asset_class}/{strategy_name}`
2. If `asset_class` is None: searches `strategies/crypto/`, `strategies/forex/`, `strategies/equities/`

**Example:**
```python
from lib.strategies import get_strategy_path

# Search all asset classes
strategy_path = get_strategy_path('spy_sma_cross')
# Searches: strategies/crypto/spy_sma_cross
#          strategies/forex/spy_sma_cross
#          strategies/equities/spy_sma_cross

# Search specific asset class
strategy_path = get_strategy_path('btc_sma_cross', asset_class='crypto')
# Only searches: strategies/crypto/btc_sma_cross
```

---

### Strategy Creation

#### `create_strategy()`

Create a new strategy directory.

**Signature:**
```python
def create_strategy(
    strategy_name: str,
    asset_class: str,
    from_template: bool = True
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name for the new strategy |
| `asset_class` | str | required | Asset class (`'crypto'`, `'forex'`, `'equities'`) |
| `from_template` | bool | True | If True, copy from `_template` directory |

**Returns:**
- `Path`: Path to created strategy directory

**Raises:**
- `ValueError`: If strategy already exists
- `FileNotFoundError`: If template doesn't exist (when `from_template=True`)

**Example:**
```python
from lib.strategies import create_strategy

# Create strategy from template
strategy_path = create_strategy(
    strategy_name='my_strategy',
    asset_class='crypto',
    from_template=True
)
# Copies strategies/_template/ to strategies/crypto/my_strategy/

# Create empty strategy directory
strategy_path = create_strategy(
    strategy_name='my_strategy',
    asset_class='crypto',
    from_template=False
)
# Creates empty strategies/crypto/my_strategy/ directory
```

---

#### `create_strategy_from_template()`

Create a new strategy from template with asset symbol configured.

**Signature:**
```python
def create_strategy_from_template(
    name: str,
    asset_class: str,
    asset_symbol: str
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Strategy name |
| `asset_class` | str | required | Asset class (`'crypto'`, `'forex'`, `'equities'`) |
| `asset_symbol` | str | required | Asset symbol to configure in `parameters.yaml` |

**Returns:**
- `Path`: Path to created strategy directory

**What This Function Does:**
1. Creates strategy directory from template
2. Updates `parameters.yaml` with `asset_symbol`
3. Creates results directory (`results/{name}/`)
4. Creates symlink from strategy to results directory

**Example:**
```python
from lib.strategies import create_strategy_from_template

# Create strategy with BTC-USD configured
strategy_path = create_strategy_from_template(
    name='btc_momentum',
    asset_class='crypto',
    asset_symbol='BTC-USD'
)

# Strategy is ready to use:
# - parameters.yaml has asset_symbol: BTC-USD
# - Results directory created
# - Symlinks set up
```

---

### Symlink Management

#### `check_and_fix_symlinks()`

Check and fix broken symlinks within a strategy's results directory.

**Signature:**
```python
def check_and_fix_symlinks(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> List[Path]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `asset_class` | str | None | Optional asset class hint |

**Returns:**
- `List[Path]`: List of paths to fixed symlinks

**Symlinks Checked:**
1. `strategies/{asset_class}/{strategy_name}/results` → `results/{strategy_name}/`
2. `results/{strategy_name}/latest` → Most recent backtest result directory

**Example:**
```python
from lib.strategies import check_and_fix_symlinks

# Check and fix symlinks
fixed_links = check_and_fix_symlinks('spy_sma_cross')
print(f"Fixed {len(fixed_links)} symlinks")

# Output: ['/path/to/strategies/equities/spy_sma_cross/results',
#          '/path/to/results/spy_sma_cross/latest']
```

**Use Case:** Run this after moving or reorganizing results directories to fix broken symlinks.

---

## Module Structure

The strategies package is organized as:

```
lib/strategies/
├── __init__.py         # Public API exports
└── manager.py          # Strategy management functions
```

**Note:** This module was extracted from `lib/utils.py` in v1.11.0 Phase 2 to follow single responsibility principle.

---

## Examples

### Strategy Discovery Workflow

```python
from lib.strategies import get_strategy_path

# Find strategy without knowing asset class
try:
    strategy_path = get_strategy_path('spy_sma_cross')
    print(f"Found strategy at: {strategy_path}")
except FileNotFoundError:
    print("Strategy not found in any asset class")
```

### Create New Strategy

```python
from lib.strategies import create_strategy_from_template

# Create crypto strategy
strategy_path = create_strategy_from_template(
    name='eth_breakout',
    asset_class='crypto',
    asset_symbol='ETH-USD'
)

# Strategy is now ready:
# - Template files copied
# - parameters.yaml configured with ETH-USD
# - Results directory created
# - Symlinks set up
```

### Strategy Path Resolution

```python
from lib.strategies import get_strategy_path

# Resolve strategy path for backtest
strategy_name = 'spy_sma_cross'
try:
    strategy_path = get_strategy_path(strategy_name)
    strategy_file = strategy_path / 'strategy.py'
    
    if strategy_file.exists():
        print(f"Strategy file: {strategy_file}")
    else:
        print(f"Strategy directory exists but strategy.py not found")
except FileNotFoundError as e:
    print(f"Strategy not found: {e}")
```

### Fix Broken Symlinks After Reorganization

```python
from lib.strategies import check_and_fix_symlinks

# After moving results directories, fix symlinks
strategies = ['spy_sma_cross', 'btc_sma_cross', 'eurusd_breakout']

for strategy_name in strategies:
    fixed = check_and_fix_symlinks(strategy_name)
    if fixed:
        print(f"{strategy_name}: Fixed {len(fixed)} symlinks")
    else:
        print(f"{strategy_name}: No broken symlinks")
```

---

## Configuration

### Strategy Directory Structure

Each strategy directory should contain:

```
strategies/{asset_class}/{strategy_name}/
├── strategy.py          # Strategy implementation
├── parameters.yaml      # Strategy parameters
├── hypothesis.md        # Trading hypothesis documentation
└── results -> ../../results/{strategy_name}/  # Symlink to results
```

### Asset Class Support

Supported asset classes:
- `'crypto'` - Cryptocurrency strategies
- `'forex'` - Foreign exchange strategies
- `'equities'` - Equity/stock strategies

### Template System

The `strategies/_template/` directory contains:
- `strategy.py` - Template strategy implementation
- `parameters.yaml` - Template parameter configuration
- `hypothesis.md` - Template hypothesis documentation

**Note:** When creating a new strategy with `from_template=True`, all files from `_template/` are copied to the new strategy directory.

---

## Error Handling

### Common Errors and Solutions

#### `FileNotFoundError: Strategy 'my_strategy' not found`

**Cause:** Strategy doesn't exist in any asset class directory.

**Solution:**
```python
# Check if strategy exists
from lib.strategies import get_strategy_path

try:
    path = get_strategy_path('my_strategy')
except FileNotFoundError:
    # Create strategy if it doesn't exist
    from lib.strategies import create_strategy
    path = create_strategy('my_strategy', asset_class='crypto')
```

#### `ValueError: Strategy 'my_strategy' already exists`

**Cause:** Trying to create a strategy that already exists.

**Solution:**
```python
from lib.strategies import get_strategy_path, create_strategy

# Check if strategy exists first
try:
    path = get_strategy_path('my_strategy')
    print(f"Strategy already exists at: {path}")
except FileNotFoundError:
    # Create if it doesn't exist
    path = create_strategy('my_strategy', asset_class='crypto')
```

#### `FileNotFoundError: Template not found at ...`

**Cause:** `strategies/_template/` directory doesn't exist.

**Solution:**
```python
# Ensure template directory exists
from pathlib import Path
from lib.paths import get_project_root

template_path = get_project_root() / 'strategies' / '_template'
if not template_path.exists():
    raise FileNotFoundError(
        f"Template directory not found. "
        f"Expected at: {template_path}"
    )
```

---

## See Also

- [Backtest API](backtest.md) - Strategy execution
- [Config API](config.md) - Strategy parameter loading
- [Paths API](../utils.md) - Project root resolution
- [Strategy Template](../../strategies/_template/) - Template files

---

## Version History

- **v1.11.0**: Extracted from `lib/utils.py` to follow single responsibility principle
- **v1.0.0**: Initial strategy management support
