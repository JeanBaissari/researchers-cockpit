# Utils API

Core utility functions for file operations, directory management, and YAML handling.

**Location:** `lib/utils.py`

**Note:** OHLCV aggregation, normalization, and data processing functions have been moved to [Data API](data.md) (`lib/data/`). Path resolution functions are in [Paths API](paths.md) (`lib/paths.py`). Strategy management functions are in [Strategies API](strategies.md) (`lib/strategies/`).

---

## File Operations

## Path Resolution

Path resolution functions have been moved to the dedicated [Paths API](paths.md) module.

**See:** [Paths API](paths.md) for:
- `get_project_root()` - Project root discovery
- `get_strategies_dir()`, `get_results_dir()`, etc. - Directory paths
- `validate_project_structure()` - Structure validation
- `ensure_project_dirs()` - Directory creation

**Note:** Strategy path resolution is in the [Strategies API](strategies.md):
- `get_strategy_path()` - Strategy directory resolution

---

## File Operations

### ensure_dir()

Create directory if it doesn't exist.

**Signature:**
```python
def ensure_dir(path: Path) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | Path | required | Directory path to create |

**Returns:** `Path` - The created directory path

**Example:**
```python
from lib.utils import ensure_dir
from pathlib import Path

dir_path = ensure_dir(Path('results/my_strategy'))
# Creates directory if it doesn't exist
```

---

### timestamp_dir()

Create a timestamped directory.

**Signature:**
```python
def timestamp_dir(base_path: Path, prefix: str) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_path` | Path | required | Base directory path |
| `prefix` | str | required | Prefix for directory name (e.g., 'backtest', 'optimization') |

**Returns:** `Path` - Path to the created directory

**Example:**
```python
from lib.utils import timestamp_dir
from pathlib import Path

dir_path = timestamp_dir(Path('results/my_strategy'), 'backtest')
# Returns: results/my_strategy/backtest_20241228_143022
```

---

### update_symlink()

Create or update a symlink.

**Signature:**
```python
def update_symlink(target: Path, link_path: Path) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target` | Path | required | Target path for symlink |
| `link_path` | Path | required | Symlink path to create/update |

**Raises:**
- `OSError`: If symlink creation fails

**Example:**
```python
from lib.utils import update_symlink
from pathlib import Path

# Create/update 'latest' symlink
update_symlink(
    target=Path('results/my_strategy/backtest_20241228_143022'),
    link_path=Path('results/my_strategy/latest')
)
```

---

### load_yaml()

Load a YAML file with safe parsing.

**Signature:**
```python
def load_yaml(path: Path) -> dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | Path | required | Path to YAML file |

**Returns:** `dict` - Parsed YAML data (empty dict if file is empty)

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `yaml.YAMLError`: If YAML is invalid

**Example:**
```python
from lib.utils import load_yaml
from pathlib import Path

config = load_yaml(Path('config/settings.yaml'))
```

---

### save_yaml()

Save data to a YAML file with formatting.

**Signature:**
```python
def save_yaml(data: dict, path: Path) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | dict | required | Data to save |
| `path` | Path | required | Path to YAML file |

**Example:**
```python
from lib.utils import save_yaml
from pathlib import Path

data = {'key': 'value', 'nested': {'item': 123}}
save_yaml(data, Path('output/config.yaml'))
```

---

## See Also

- [Data API](data.md) - OHLCV aggregation, normalization, and data processing
- [Paths API](paths.md) - Path resolution and project root discovery
- [Strategies API](strategies.md) - Strategy path resolution and management
- [Bundles API](bundles.md) - Data bundle management
- [Backtest API](backtest.md) - Backtest execution
