# Config API

Configuration loading and management with caching.

**Location:** `lib/config/`

---

## Module Structure

The config package is organized into focused modules (v1.11.0 modular architecture):

```
lib/config/
├── core.py                   # Main config loader (load_settings, cache)
├── assets.py                 # Asset configuration (load_asset_config)
├── strategy.py               # Strategy parameter loading
├── validation.py             # Main validation orchestrator
├── validation_backtest.py     # Backtest config validation (v1.11.0)
├── validation_position_sizing.py  # Position sizing validation (v1.11.0)
└── validation_risk.py        # Risk config validation (v1.11.0)
```

**Key Modules:**
- **core.py**: Main configuration loader with caching
- **assets.py**: Asset class configuration loading
- **strategy.py**: Strategy parameter loading and warmup calculation
- **validation.py**: Orchestrator that coordinates all validation
- **validation_backtest.py**: Validates backtest section (dates, warmup, capital)
- **validation_position_sizing.py**: Validates position sizing section
- **validation_risk.py**: Validates risk management section

---

## load_settings()

Load global settings from `config/settings.yaml`.

**Signature:**
```python
def load_settings() -> Dict[str, Any]
```

**Returns:** `Dict[str, Any]` - Settings dictionary

**Raises:**
- `FileNotFoundError`: If settings.yaml doesn't exist

**Example:**
```python
from lib.config import load_settings

settings = load_settings()

# Access settings
capital = settings['capital']['default_initial']
start_date = settings['dates']['default_start']
risk_free_rate = settings['metrics']['risk_free_rate']
```

**Settings Structure:**
```yaml
# config/settings.yaml
capital:
  default_initial: 100000
  currency: USD

dates:
  default_start: "2020-01-01"
  default_end: null  # null = today

backtesting:
  data_frequency: daily
  benchmark: SPY

metrics:
  risk_free_rate: 0.04
  trading_days_per_year: 252

data:
  bundles:
    default_equities: yahoo_equities_daily
    default_crypto: yahoo_crypto_daily
    default_forex: yahoo_forex_daily
```

**Notes:**
- Results are cached for performance
- Use `clear_config_cache()` to reload

---

## load_strategy_params()

Load parameters from a strategy's `parameters.yaml` file.

**Signature:**
```python
def load_strategy_params(
    strategy_name: str,
    asset_class: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Strategy name (e.g., `'spy_sma_cross'`) |
| `asset_class` | str | None | Asset class hint |

**Returns:** `Dict[str, Any]` - Strategy parameters

**Raises:**
- `FileNotFoundError`: If strategy or parameters.yaml not found

**Example:**
```python
from lib.config import load_strategy_params

params = load_strategy_params('spy_sma_cross')

# Access parameters
symbol = params['strategy']['asset_symbol']
fast_period = params['strategy']['fast_period']
stop_loss = params['risk']['stop_loss_pct']
```

**Strategy Parameters Structure:**
```yaml
# strategies/equities/spy_sma_cross/parameters.yaml
strategy:
  asset_symbol: SPY
  rebalance_frequency: daily
  fast_period: 10
  slow_period: 50
  minutes_after_open: 30

position_sizing:
  method: fixed
  max_position_pct: 1.0

risk:
  use_stop_loss: true
  stop_loss_pct: 0.02
  use_trailing_stop: false
  use_take_profit: false

backtest:
  validate_warmup: true
  warmup_days: 50  # Optional: override auto-calculation
```

---

## validate_strategy_params()

Validate strategy parameters for correctness.

**Location:** `lib/config/validation.py` (orchestrator)

**Signature:**
```python
def validate_strategy_params(
    params: dict,
    strategy_name: str
) -> Tuple[bool, List[str]]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `params` | dict | required | Strategy parameters |
| `strategy_name` | str | required | Strategy name (for error messages) |

**Returns:** `Tuple[bool, List[str]]` - (is_valid, list_of_errors)

**Internal Architecture:**

The `validate_strategy_params()` function orchestrates validation across three specialized modules:

- **Backtest Validation** (`lib/config/validation_backtest.py`):
  - Validates `backtest` section
  - Date format validation (YYYY-MM-DD)
  - Date order validation (start_date < end_date)
  - Warmup days validation
  - Capital base validation

- **Position Sizing Validation** (`lib/config/validation_position_sizing.py`):
  - Validates `position_sizing` section
  - `max_position_pct` range validation (0.0-1.0)
  - `method` enum validation (`'fixed'`, `'volatility_scaled'`, `'kelly'`)
  - Method-specific parameter validation

- **Risk Validation** (`lib/config/validation_risk.py`):
  - Validates `risk` section
  - `stop_loss_pct` validation (positive, typically <= 1.0)
  - `take_profit_pct` validation (must be > stop_loss_pct)
  - Trailing stop validation
  - Risk management flag validation

**Validation Rules:**

**Strategy Section:**
- `strategy.asset_symbol`: Required, must be string
- `strategy.rebalance_frequency`: Must be `'daily'`, `'weekly'`, or `'monthly'`
- `strategy.minutes_after_open`: Must be 0-60

**Position Sizing Section:**
- `position_sizing.max_position_pct`: Must be 0.0-1.0
- `position_sizing.method`: Must be `'fixed'`, `'volatility_scaled'`, or `'kelly'`

**Risk Section:**
- `risk.stop_loss_pct`: Must be positive, typically <= 1.0
- `risk.take_profit_pct`: Must be > `stop_loss_pct`

**Backtest Section:**
- `backtest.start_date`: Must be YYYY-MM-DD format
- `backtest.end_date`: Must be YYYY-MM-DD format
- `backtest.start_date` < `backtest.end_date` (date order validation)

**Example:**
```python
from lib.config import load_strategy_params, validate_strategy_params

params = load_strategy_params('spy_sma_cross')
is_valid, errors = validate_strategy_params(params, 'spy_sma_cross')

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

**Direct Module Access:**

For advanced use cases, you can import directly from specific validation modules:

```python
# Direct access to specific validators
from lib.config.validation_backtest import validate_backtest_section
from lib.config.validation_position_sizing import validate_position_sizing_section
from lib.config.validation_risk import validate_risk_section

# Use individual validators
errors = []
validate_backtest_section(params.get('backtest'), errors)
validate_position_sizing_section(params.get('position_sizing'), errors)
validate_risk_section(params.get('risk'), errors)
```

---

## get_warmup_days()

Get required warmup days for a strategy.

**Signature:**
```python
def get_warmup_days(params: Dict[str, Any]) -> int
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `params` | Dict | required | Strategy parameters |

**Returns:** `int` - Required warmup days

**Resolution Order:**
1. Explicit `backtest.warmup_days` if specified
2. Dynamic calculation from max of all `*_period` parameters
3. Default fallback of 30 days

**Period Parameters Checked:**
- `lookback_period`, `fast_period`, `slow_period`
- `trend_filter_period`, `sma_period`, `ema_period`
- `rsi_period`, `atr_period`, `macd_slow_period`
- `bollinger_period`, `momentum_period`, `volatility_period`
- Any key ending with `_period`

**Example:**
```python
from lib.config import load_strategy_params, get_warmup_days

params = load_strategy_params('spy_sma_cross')
warmup = get_warmup_days(params)

print(f"Strategy requires {warmup} days warmup")
# If params has slow_period=50, returns 50
```

---

## load_asset_config()

Load asset configuration for a specific asset class.

**Signature:**
```python
def load_asset_config(asset_class: str) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `asset_class` | str | required | `'crypto'`, `'forex'`, or `'equities'` |

**Returns:** `Dict[str, Any]` - Asset configuration

**Raises:**
- `ValueError`: If asset_class invalid
- `FileNotFoundError`: If config file not found

**Example:**
```python
from lib.config import load_asset_config

crypto_config = load_asset_config('crypto')
symbols = crypto_config['symbols']
calendar = crypto_config['calendar']
```

---

## get_data_source()

Load data source configuration.

**Signature:**
```python
def get_data_source(source_name: str) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_name` | str | required | `'yahoo'`, `'binance'`, `'oanda'` |

**Returns:** `Dict[str, Any]` - Data source configuration

**Raises:**
- `KeyError`: If source_name not found

**Example:**
```python
from lib.config import get_data_source

yahoo_config = get_data_source('yahoo')
enabled = yahoo_config['enabled']
```

---

## get_default_bundle()

Get default bundle name for an asset class.

**Signature:**
```python
def get_default_bundle(asset_class: str) -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `asset_class` | str | required | Asset class |

**Returns:** `str` - Default bundle name

**Fallback Defaults:**
- `equities`: `yahoo_equities_daily`
- `crypto`: `yahoo_crypto_daily`
- `forex`: `yahoo_forex_daily`

**Example:**
```python
from lib.config import get_default_bundle

bundle = get_default_bundle('crypto')
# Returns: 'yahoo_crypto_daily'
```

---

## clear_config_cache()

Clear the configuration cache. Useful for testing or reloading configs.

**Signature:**
```python
def clear_config_cache() -> None
```

**Example:**
```python
from lib.config import clear_config_cache, load_settings

# After modifying settings.yaml
clear_config_cache()
settings = load_settings()  # Reloads from disk
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/settings.yaml` | Global settings |
| `config/data_sources.yaml` | Data source configs |
| `config/assets/crypto.yaml` | Crypto asset config |
| `config/assets/forex.yaml` | Forex asset config |
| `config/assets/equities.yaml` | Equities asset config |
| `strategies/*/parameters.yaml` | Strategy-specific params |

---

## Validation Module Organization

**Validation Split (v1.11.0):**

The validation module was refactored in v1.11.0 to separate validation concerns:

- **validation.py** (orchestrator): Coordinates all validation
  - Calls specialized validators
  - Aggregates errors
  - Provides unified `validate_strategy_params()` interface

- **validation_backtest.py**: Backtest configuration validation
  - Date format and order validation
  - Warmup period validation
  - Capital base validation

- **validation_position_sizing.py**: Position sizing validation
  - Position size range validation
  - Method enum validation
  - Method-specific parameter validation

- **validation_risk.py**: Risk management validation
  - Stop loss validation
  - Take profit validation
  - Risk management flag validation

---

## See Also

**Related API Documentation:**
- [Backtest API](backtest.md) - Uses config for backtest setup
- [Optimize API](optimize.md) - Uses config for optimization parameters
- [Strategies API](strategies.md) - Strategy path resolution

**Internal Modules:**
- `lib/config/core.py` - Main config loader
- `lib/config/assets.py` - Asset configuration
- `lib/config/strategy.py` - Strategy parameter loading
- `lib/config/validation.py` - Validation orchestrator
- `lib/config/validation_backtest.py` - Backtest validation
- `lib/config/validation_position_sizing.py` - Position sizing validation
- `lib/config/validation_risk.py` - Risk validation
