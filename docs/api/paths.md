# Paths API

Centralized path resolution for The Researcher's Cockpit.

Provides robust project root discovery using marker files, with caching for performance. This module ensures consistent path resolution regardless of where code is executed from (notebooks, scripts, library calls, etc.).

**Location:** `lib/paths.py`

---

## Overview

The `lib/paths` module provides a marker-based project root discovery system that works reliably across different execution contexts. It uses a priority-ordered list of marker files to identify the project root, with environment variable override support and LRU caching for performance.

**Key Features:**
- Marker-based root detection (no hardcoded paths)
- Environment variable override support
- LRU caching for performance
- Directory structure validation
- Automatic directory creation

---

## Installation/Dependencies

No special dependencies required. Uses only Python standard library:
- `pathlib.Path` for path operations
- `functools.lru_cache` for caching
- `os` for environment variables

---

## Quick Start

```python
from lib.paths import get_project_root, get_strategies_dir, get_results_dir

# Get project root
root = get_project_root()
print(f"Project root: {root}")

# Get standard directories
strategies_dir = get_strategies_dir()
results_dir = get_results_dir()
```

---

## Public API Reference

### get_project_root()

Find the project root directory using marker-based discovery.

**Signature:**
```python
def get_project_root() -> Path
```

**Returns:**
- `Path`: Absolute path to project root

**Raises:**
- `ProjectRootNotFoundError`: If no project markers are found

**Marker Priority Order:**
1. `pyproject.toml` - Primary Python project marker
2. `.git` - Git repository root
3. `config/settings.yaml` - Project-specific marker
4. `CLAUDE.md` - This project's documentation
5. `.project_root` - Explicit marker (optional)

**Environment Variable Override:**
Set `PROJECT_ROOT` environment variable to override automatic detection:
```bash
export PROJECT_ROOT=/path/to/project
```

**Caching:**
Results are cached using `@lru_cache` for performance. Use `clear_cache()` to reset.

**Example:**
```python
from lib.paths import get_project_root

root = get_project_root()
# Returns: /home/user/projects/researchers-cockpit

# With environment variable override
import os
os.environ['PROJECT_ROOT'] = '/custom/path'
root = get_project_root()  # Returns: /custom/path
```

---

### get_strategies_dir()

Get the strategies directory path.

**Signature:**
```python
def get_strategies_dir() -> Path
```

**Returns:**
- `Path`: Path to `strategies/` directory

**Example:**
```python
from lib.paths import get_strategies_dir

strategies_dir = get_strategies_dir()
# Returns: /project/strategies
```

---

### get_results_dir()

Get the results directory path.

**Signature:**
```python
def get_results_dir() -> Path
```

**Returns:**
- `Path`: Path to `results/` directory

**Example:**
```python
from lib.paths import get_results_dir

results_dir = get_results_dir()
# Returns: /project/results
```

---

### get_data_dir()

Get the data directory path.

**Signature:**
```python
def get_data_dir() -> Path
```

**Returns:**
- `Path`: Path to `data/` directory

**Example:**
```python
from lib.paths import get_data_dir

data_dir = get_data_dir()
# Returns: /project/data
```

---

### get_config_dir()

Get the config directory path.

**Signature:**
```python
def get_config_dir() -> Path
```

**Returns:**
- `Path`: Path to `config/` directory

**Example:**
```python
from lib.paths import get_config_dir

config_dir = get_config_dir()
# Returns: /project/config
```

---

### get_logs_dir()

Get the logs directory path.

**Signature:**
```python
def get_logs_dir() -> Path
```

**Returns:**
- `Path`: Path to `logs/` directory

**Example:**
```python
from lib.paths import get_logs_dir

logs_dir = get_logs_dir()
# Returns: /project/logs
```

---

### get_reports_dir()

Get the reports directory path.

**Signature:**
```python
def get_reports_dir() -> Path
```

**Returns:**
- `Path`: Path to `reports/` directory

**Example:**
```python
from lib.paths import get_reports_dir

reports_dir = get_reports_dir()
# Returns: /project/reports
```

---

### validate_project_structure()

Validate that expected project directories exist.

**Signature:**
```python
def validate_project_structure() -> List[str]
```

**Returns:**
- `List[str]`: List of warning messages for missing optional components. Empty list if all required components exist.

**Note:**
This function does not raise exceptions for missing optional components, only returns warnings.

**Required Directories:**
- `strategies/`
- `results/`
- `data/`
- `config/`
- `lib/`

**Required Config Files:**
- `config/settings.yaml`

**Optional Components (warnings only):**
- `strategies/_template/` - Strategy template
- `logs/` - Logs directory
- `reports/` - Reports directory

**Example:**
```python
from lib.paths import validate_project_structure

warnings = validate_project_structure()
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")
else:
    print("All required components present")
```

---

### ensure_project_dirs()

Ensure all required project directories exist.

**Signature:**
```python
def ensure_project_dirs() -> None
```

**Creates Directories:**
- `strategies/` and subdirectories (`_template/`, `crypto/`, `forex/`, `equities/`)
- `results/`
- `data/` and subdirectories (`bundles/`, `cache/`, `processed/`, `exports/`)
- `config/`
- `logs/`
- `reports/`

**Note:**
Creates directories with `parents=True, exist_ok=True`, so it's safe to call multiple times.

**Example:**
```python
from lib.paths import ensure_project_dirs

# Create all required directories
ensure_project_dirs()
```

---

### clear_cache()

Clear the cached project root. Useful for testing.

**Signature:**
```python
def clear_cache() -> None
```

**Example:**
```python
from lib.paths import get_project_root, clear_cache

# Get cached root
root1 = get_project_root()

# Clear cache
clear_cache()

# Next call will re-discover root
root2 = get_project_root()
```

---

## Module Structure

The `lib/paths` module consists of:

1. **Root Discovery** (`get_project_root()`)
   - Marker-based detection
   - Environment variable override
   - LRU caching

2. **Directory Paths** (6 functions)
   - `get_strategies_dir()`
   - `get_results_dir()`
   - `get_data_dir()`
   - `get_config_dir()`
   - `get_logs_dir()`
   - `get_reports_dir()`

3. **Structure Validation** (`validate_project_structure()`)
   - Required directory checks
   - Required config file checks
   - Optional component warnings

4. **Directory Creation** (`ensure_project_dirs()`)
   - Automatic directory creation
   - Safe for repeated calls

5. **Cache Management** (`clear_cache()`)
   - Cache invalidation for testing

---

## Examples

### Basic Path Resolution

```python
from lib.paths import (
    get_project_root,
    get_strategies_dir,
    get_results_dir
)

# Get project root
root = get_project_root()

# Get standard directories
strategies = get_strategies_dir()
results = get_results_dir()

# Use in file operations
strategy_file = strategies / 'equities' / 'my_strategy' / 'strategy.py'
```

### Directory Structure Validation

```python
from lib.paths import validate_project_structure, ensure_project_dirs

# Check if structure is valid
warnings = validate_project_structure()
if warnings:
    print("Missing components:")
    for warning in warnings:
        print(f"  - {warning}")
    
    # Create missing directories
    ensure_project_dirs()
```

### Environment Variable Override

```python
import os
from lib.paths import get_project_root, clear_cache

# Override project root
os.environ['PROJECT_ROOT'] = '/custom/project/path'

# Clear cache to pick up new value
clear_cache()

# Get overridden root
root = get_project_root()
# Returns: /custom/project/path
```

### Complete Directory Setup

```python
from lib.paths import (
    ensure_project_dirs,
    validate_project_structure,
    get_project_root
)

# Ensure all directories exist
ensure_project_dirs()

# Validate structure
warnings = validate_project_structure()
if not warnings:
    print(f"Project structure valid at: {get_project_root()}")
```

---

## Configuration

### Marker Files

The module searches for these marker files in priority order:

1. **`pyproject.toml`** - Primary Python project marker
2. **`.git`** - Git repository root
3. **`config/settings.yaml`** - Project-specific marker
4. **`CLAUDE.md`** - This project's documentation
5. **`.project_root`** - Explicit marker (optional, create if needed)

### Environment Variable

Set `PROJECT_ROOT` environment variable to override automatic detection:

```bash
export PROJECT_ROOT=/path/to/project
```

---

## Error Handling

### ProjectRootNotFoundError

Raised when project root cannot be determined.

**Example:**
```python
from lib.paths import get_project_root, ProjectRootNotFoundError

try:
    root = get_project_root()
except ProjectRootNotFoundError as e:
    print(f"Error: {e}")
    # Error message includes:
    # - List of markers searched
    # - Directories searched
    # - Suggestion to set PROJECT_ROOT
```

**Error Message Format:**
```
Could not find project root. Searched for markers ['pyproject.toml', '.git', ...] 
in directories: [/path1, /path2, ...]. 
Set PROJECT_ROOT environment variable to override.
```

---

## See Also

- [Utils API](utils.md) - General utility functions
- [Config API](config.md) - Configuration loading
- [Strategies API](strategies.md) - Strategy path resolution
- [Project Structure](../project-structure.md) - Directory organization
