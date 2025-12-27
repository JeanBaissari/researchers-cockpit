# Conventions & Standards — The Researcher's Cockpit

> **CRITICAL:** Follow these conventions strictly. Consistency enables automation and reduces errors.

---

## Naming Conventions

### Strategy Names

**Format:** `{asset}_{strategy_type}`

**Rules:**
- Lowercase only
- Underscores for word separation
- Maximum 30 characters
- No spaces, hyphens, or special characters

**Examples:**
- ✅ `btc_sma_cross`
- ✅ `eth_mean_reversion`
- ✅ `eurusd_london_breakout`
- ✅ `spy_dual_momentum`
- ❌ `BTC-SMA-Cross` (uppercase, hyphens)
- ❌ `btc sma cross` (spaces)
- ❌ `btc_sma_cross_strategy_v2_final` (too long)

### Result Directory Names

**Format:** `{run_type}_{YYYYMMDD}_{HHMMSS}`

**Run Types:**
- `backtest` — Standard backtest execution
- `optimization` — Parameter optimization run
- `walkforward` — Walk-forward validation
- `montecarlo` — Monte Carlo simulation

**Examples:**
- `backtest_20241220_143022`
- `optimization_20241221_091500`
- `walkforward_20241222_160033`

**Rules:**
- Always use UTC timestamps
- Zero-padded (2 digits for hours/minutes/seconds)
- Chronological sorting works automatically

### File Names

**Python files:** `snake_case.py`
- `strategy.py`
- `data_loader.py`
- `run_backtest.py`

**Config files:** `kebab-case.yaml` or `snake_case.yaml`
- `settings.yaml`
- `data_sources.yaml`
- `parameters.yaml`

**Documentation:** `kebab-case.md`
- `hypothesis.md`
- `strategy_catalog.md`
- `quickstart.md`

---

## Directory Structure Rules

### Strategy Directory Structure

Every strategy MUST have this structure:

```
strategies/{asset_class}/{strategy_name}/
├── strategy.py          # REQUIRED: The algorithm
├── hypothesis.md        # REQUIRED: Trading rationale
├── parameters.yaml     # REQUIRED: All tunable parameters
└── results -> ../../results/{strategy_name}/  # Symlink (auto-created)
```

**Required Files:**
- `strategy.py` — Cannot be missing
- `hypothesis.md` — Cannot be missing
- `parameters.yaml` — Cannot be missing

### Results Directory Structure

```
results/{strategy_name}/
├── backtest_{timestamp}/
│   ├── returns.csv
│   ├── positions.csv
│   ├── transactions.csv
│   ├── metrics.json
│   ├── parameters_used.yaml
│   └── equity_curve.png
├── optimization_{timestamp}/
│   └── ...
└── latest -> backtest_{timestamp}/  # Symlink to most recent
```

**Rules:**
- Never overwrite existing result directories
- Always create new timestamped directory
- Update `latest` symlink after each run
- Keep all results (don't delete old runs)

---

## Code Style

### Python Style Guide

**Follow PEP 8 with these specifics:**

- **Line length:** 100 characters max
- **Imports:** Grouped (stdlib, third-party, local)
- **Docstrings:** Google style for all functions
- **Type hints:** Optional but encouraged for public APIs

**Example:**
```python
from zipline.api import symbol, order_target_percent
import numpy as np
import pandas as pd

from lib.config import load_settings


def compute_signals(context, data):
    """
    Compute trading signals based on strategy logic.
    
    Args:
        context: Zipline context object
        data: Zipline data object
        
    Returns:
        int: Signal (1=buy, -1=sell, 0=hold)
        dict: Additional metrics to record
    """
    # Implementation here
    return signal, metrics
```

### Parameter Loading Pattern

**ALWAYS load from YAML, never hardcode:**

```python
# ✅ CORRECT
def initialize(context):
    params = load_params()  # From parameters.yaml
    context.fast = params['strategy']['fast_period']
    context.slow = params['strategy']['slow_period']

# ❌ WRONG
def initialize(context):
    context.fast = 10  # Hardcoded!
    context.slow = 30  # Hardcoded!
```

### File Size Limits

**Library files:** Maximum 150 lines per file
- If a file exceeds 150 lines, split into multiple files
- Each file should have a single, clear responsibility

**Strategy files:** No hard limit, but keep focused
- Strategy logic only
- No data loading, no optimization code
- Use `lib/` for shared functionality

---

## YAML Configuration Standards

### Indentation

**Always use 2 spaces, never tabs**

```yaml
# ✅ CORRECT
strategy:
  asset_symbol: SPY
  fast_period: 10

# ❌ WRONG (tabs)
strategy:
	asset_symbol: SPY
	fast_period: 10
```

### Key Naming

**Use snake_case for keys:**

```yaml
# ✅ CORRECT
max_position_pct: 0.95
stop_loss_pct: 0.05

# ❌ WRONG
maxPositionPct: 0.95
stop-loss-pct: 0.05
```

### Comments

**Use `#` for comments:**

```yaml
strategy:
  asset_symbol: SPY  # Primary asset to trade
  fast_period: 10     # Fast SMA lookback (5-20)
```

---

## Error Handling Patterns

### Missing Files

**Always check file existence before loading:**

```python
from pathlib import Path

def load_params():
    params_path = Path(__file__).parent / 'parameters.yaml'
    if not params_path.exists():
        raise FileNotFoundError(
            f"parameters.yaml not found at {params_path}. "
            "Every strategy must have a parameters.yaml file."
        )
    # Load file...
```

### Invalid Configuration

**Validate and provide helpful error messages:**

```python
def validate_params(params):
    required_keys = ['strategy', 'position_sizing', 'risk']
    for key in required_keys:
        if key not in params:
            raise ValueError(
                f"Missing required parameter section: {key}. "
                f"See strategies/_template/parameters.yaml for structure."
            )
```

### Data Availability

**Check data before using:**

```python
def compute_signals(context, data):
    if not data.can_trade(context.asset):
        return 0, {}  # Return neutral signal
    
    # Need enough history
    lookback = 50
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return 0, {}  # Not enough data yet
    
    # Proceed with calculation...
```

---

## Logging Standards

### Log Levels

- **DEBUG** — Detailed diagnostic information
- **INFO** — General informational messages
- **WARNING** — Warning messages (non-fatal)
- **ERROR** — Error messages (recoverable)
- **CRITICAL** — Critical errors (may abort)

### Log Format

**Use structured logging:**

```python
import logging

logger = logging.getLogger(__name__)

def run_backtest(strategy_name):
    logger.info(f"Starting backtest for strategy: {strategy_name}")
    
    try:
        # Execute backtest
        logger.debug(f"Loaded parameters: {params}")
        logger.info("Backtest completed successfully")
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise
```

---

## Git Workflow

### What to Commit

**Commit:**
- Strategy code (`strategies/`)
- Library code (`lib/`)
- Configuration templates (`config/`)
- Documentation (`docs/`, `.agent/`)
- Scripts (`scripts/`)

**Don't Commit:**
- Results (`results/`)
- Data bundles (`data/bundles/`)
- Cache (`data/cache/`)
- Logs (`logs/`)
- Generated reports (`reports/`)

### Commit Messages

**Format:** `{type}: {description}`

**Types:**
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `refactor:` — Code refactoring
- `test:` — Tests

**Examples:**
- `feat: Add volatility scaling to position sizing`
- `fix: Correct parameter loading in strategy template`
- `docs: Update backtest runner instructions`

---

## Testing Conventions

### Smoke Tests

**Every phase should have a smoke test:**

```python
# Test parameter loading
python -c "from lib.config import load_settings; load_settings()"

# Test strategy import
python -c "import sys; sys.path.insert(0, 'strategies/crypto/btc_sma_cross'); import strategy"
```

### Validation Checks

**Before running backtest:**
1. Strategy file syntax valid
2. Parameters YAML valid
3. Hypothesis file exists
4. Data bundle available
5. Required imports available

---

## Documentation Standards

### Docstrings

**All public functions need docstrings:**

```python
def calculate_sharpe(returns, risk_free_rate=0.04):
    """
    Calculate annualized Sharpe ratio.
    
    Args:
        returns: Series of daily returns
        risk_free_rate: Annual risk-free rate (default: 0.04)
        
    Returns:
        float: Annualized Sharpe ratio
    """
    # Implementation...
```

### README Files

**Every major directory should have a README.md:**
- Purpose of the directory
- File structure
- Usage examples
- Related files/directories

---

## Summary Checklist

Before completing any task, verify:

- [ ] Naming follows conventions
- [ ] No hardcoded parameters
- [ ] Required files present (strategy.py, hypothesis.md, parameters.yaml)
- [ ] YAML uses 2-space indentation, no tabs
- [ ] Error handling includes helpful messages
- [ ] Logging uses appropriate levels
- [ ] Code follows PEP 8 style
- [ ] Documentation updated if needed

---

## Questions?

If conventions are unclear:
1. Check existing code for examples
2. Review `strategies/_template/` for reference
3. Ask for clarification rather than guessing

**Consistency is more important than perfection.**

