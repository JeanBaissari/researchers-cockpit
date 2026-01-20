# Backtest API

Module for executing Zipline backtests and saving results in standardized format.

**Location:** `lib/backtest/`  
**CLI Equivalent:** `scripts/run_backtest.py`

---

## Module Structure

The backtest package is organized into focused modules (v1.11.0 modular architecture):

```
lib/backtest/
├── runner.py                 # Main run_backtest() function
├── results.py                # save_results() orchestrator
├── results_serialization.py  # JSON/CSV serialization
├── results_persistence.py    # File I/O operations
├── config.py                 # BacktestConfig dataclass
├── execution.py              # Zipline algorithm setup
├── preprocessing.py          # Pre-flight validation
├── strategy.py               # StrategyModule loader
└── verification.py           # Post-backtest verification
```

**Key Modules:**
- **runner.py**: Main entry point, orchestrates backtest execution
- **preprocessing.py**: Validates dates, calendar alignment, bundle availability
- **execution.py**: Sets up Zipline algorithm and trading engine
- **results.py**: Orchestrates result saving (delegates to serialization/persistence)
- **results_serialization.py**: Converts DataFrames to CSV/JSON files
- **results_persistence.py**: Creates directories, updates symlinks
- **verification.py**: Post-backtest data integrity checks
- **config.py**: BacktestConfig dataclass for configuration

---

## run_backtest()

Execute a Zipline backtest for a strategy.

**Signature:**
```python
def run_backtest(
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    data_frequency: str = 'daily',
    asset_class: Optional[str] = None
) -> Tuple[pd.DataFrame, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy (e.g., `'spy_sma_cross'`) |
| `start_date` | str | None | Start date `YYYY-MM-DD` (uses config default if None) |
| `end_date` | str | None | End date `YYYY-MM-DD` (uses today if None) |
| `capital_base` | float | None | Starting capital (uses config default if None) |
| `bundle` | str | None | Bundle name (auto-detected from asset_class if None) |
| `data_frequency` | str | `'daily'` | Data frequency (`'daily'` or `'minute'`) |
| `asset_class` | str | None | Asset class hint (`'crypto'`, `'forex'`, `'equities'`) |

**Returns:** `Tuple[pd.DataFrame, Any]` - (Performance DataFrame, trading calendar)

**Note (v1.11.0):** For FOREX strategies, Zipline's built-in metrics are disabled (`metrics_set='none'`) to avoid known metrics tracker bugs. The performance DataFrame may not include `returns` or `portfolio_value` columns initially. These are automatically reconstructed from transactions during `save_results()`.

**Raises:**
- `FileNotFoundError`: If strategy not found
- `ImportError`: If strategy module can't be loaded
- `ValueError`: If dates, bundle, or parameters invalid

**Example:**
```python
from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params

# Run backtest
perf, calendar = run_backtest(
    strategy_name='spy_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01',
    capital_base=100000
)

# Access results
# v1.11.0: Handle missing columns when metrics_set='none' (FOREX)
if 'portfolio_value' in perf.columns:
    print(f"Final value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
if 'returns' in perf.columns:
    print(f"Total return: {perf['returns'].sum():.2%}")
else:
    # Returns will be calculated during save_results()
    print("Returns will be calculated from portfolio_value during save_results()")

# Save results
params = load_strategy_params('spy_sma_cross')
result_dir = save_results('spy_sma_cross', perf, params, calendar)
```

**CLI Equivalent:**
```bash
# Basic backtest
python scripts/run_backtest.py --strategy spy_sma_cross

# With custom parameters
python scripts/run_backtest.py --strategy spy_sma_cross \
    --start 2020-01-01 \
    --end 2024-01-01 \
    --capital 100000 \
    --bundle yahoo_equities_daily
```

**Preprocessing Steps** (performed automatically):
1. Load and validate strategy module (must have `initialize()`)
2. Load and validate `parameters.yaml`
3. Validate warmup period (sufficient data for indicators) - via `preprocessing.py`
4. Validate strategy symbols exist in bundle - via `preprocessing.py`
5. Register custom calendars if needed - via `calendars/registry.py`
6. Validate calendar consistency (bundle vs backtest) - via `preprocessing.py`
7. Validate bundle date range covers requested dates - via `preprocessing.py`
8. Calendar alignment validation - via `calendars/sessions/` (v1.1.0)

**Post-Backtest Verification** (optional):
- Data integrity checks via `verification.py`
- Metrics calculation verification
- Returns calculation verification
- Position/transaction consistency checks

---

## save_results()

Save backtest results to timestamped directory.

**Signature:**
```python
def save_results(
    strategy_name: str,
    perf: pd.DataFrame,
    params: Dict[str, Any],
    trading_calendar: Any,
    result_type: str = 'backtest',
    verify_integrity: bool = False
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `perf` | pd.DataFrame | required | Performance DataFrame from Zipline |
| `params` | Dict | required | Strategy parameters dictionary |
| `trading_calendar` | Any | required | Trading calendar object |
| `result_type` | str | `'backtest'` | Type prefix (`'backtest'`, `'optimization'`, etc.) |
| `verify_integrity` | bool | False | Run data integrity checks |

**Returns:** `Path` - Path to created results directory

**Output Structure:**
```
results/{strategy}/backtest_{YYYYMMDD}_{HHMMSS}/
├── returns.csv          # Daily/minute returns (serialization.py)
├── positions.csv        # Position history (serialization.py)
├── transactions.csv     # All trades (serialization.py)
├── metrics.json         # Performance metrics (serialization.py)
├── parameters_used.yaml # Strategy config snapshot (serialization.py)
└── equity_curve.png     # Performance visualization (serialization.py)
```

**Result Saving Process:**
1. **Serialization** (`results_serialization.py`): Converts DataFrames to CSV/JSON
2. **Persistence** (`results_persistence.py`): Creates directory, updates symlinks
3. **Metrics Calculation**: Uses `lib/metrics/` for performance metrics
4. **Plot Generation**: Uses `lib/plots/` for equity curve visualization

**Example:**
```python
from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params

perf, calendar = run_backtest('spy_sma_cross')
params = load_strategy_params('spy_sma_cross')

result_dir = save_results(
    strategy_name='spy_sma_cross',
    perf=perf,
    params=params,
    trading_calendar=calendar,
    verify_integrity=True  # Run data checks
)

print(f"Results saved to: {result_dir}")
# Results saved to: results/spy_sma_cross/backtest_20241228_143022
```

**Notes:**
- Automatically updates `results/{strategy}/latest` symlink
- Generates equity curve plot if matplotlib available
- Calculates metrics using empyrical-reloaded library
- Trading days per year: 365 (CRYPTO), 260 (FOREX), 252 (equities)

---

## validate_strategy_symbols()

Pre-flight validation that strategy symbols exist in bundle.

**Signature:**
```python
def validate_strategy_symbols(
    strategy_name: str,
    bundle_name: str,
    asset_class: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `bundle_name` | str | required | Bundle to check against |
| `asset_class` | str | None | Asset class for strategy lookup |

**Raises:**
- `ValueError`: If required symbol not in bundle
- `FileNotFoundError`: If strategy/bundle not found

**Example:**
```python
from lib.backtest import validate_strategy_symbols

# Will raise ValueError if SPY not in bundle
validate_strategy_symbols('spy_sma_cross', 'yahoo_equities_daily')
```

---

## BacktestConfig

Configuration dataclass for backtest execution.

**Location:** `lib/backtest/config.py`

**Signature:**
```python
@dataclass
class BacktestConfig:
    strategy_name: str
    start_date: str
    end_date: str
    capital_base: float
    bundle: str
    data_frequency: str
    asset_class: Optional[str] = None
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `strategy_name` | str | Name of strategy |
| `start_date` | str | Start date (YYYY-MM-DD) |
| `end_date` | str | End date (YYYY-MM-DD) |
| `capital_base` | float | Starting capital |
| `bundle` | str | Bundle name |
| `data_frequency` | str | 'daily' or 'minute' |
| `asset_class` | str | Optional asset class hint |

**Example:**
```python
from lib.backtest import BacktestConfig

config = BacktestConfig(
    strategy_name='spy_sma_cross',
    start_date='2020-01-01',
    end_date='2024-01-01',
    capital_base=100000,
    bundle='yahoo_equities_daily',
    data_frequency='daily',
    asset_class='equities'
)
```

---

## Preprocessing

Pre-flight validation performed before backtest execution.

**Location:** `lib/backtest/preprocessing.py`

### validate_calendar_consistency()

Validate that the trading calendar used for backtest matches the calendar the bundle was ingested with.

**Signature:**
```python
def validate_calendar_consistency(bundle: str, trading_calendar: Any) -> None
```

**Raises:**
- Logs warning if calendars don't match

### validate_bundle_date_range()

Ensure bundle covers requested date range.

**Signature:**
```python
def validate_bundle_date_range(
    bundle_name: str,
    start_date: str,
    end_date: str
) -> None
```

**Raises:**
- `ValueError`: If bundle doesn't cover date range

### validate_warmup_period()

Pre-flight validation for sufficient warmup data.

**Location:** `lib/backtest/config.py`

**Signature:**
```python
def _validate_warmup_period(
    start_date: str,
    end_date: str,
    params: Dict[str, Any],
    strategy_name: str
) -> None
```

**Raises:**
- `ValueError`: If backtest period is shorter than required warmup

---

## Verification

Post-backtest data integrity verification.

**Location:** `lib/backtest/verification.py`

### _verify_data_integrity()

Run optional data integrity checks on backtest results.

**Signature:**
```python
def _verify_data_integrity(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    metrics: Dict[str, Any]
) -> None
```

**Checks Performed:**
- Metrics calculation verification (via `lib.validation`)
- Returns calculation verification
- Position/transaction consistency checks

**Note:** Verification is optional and controlled by `verify_integrity` parameter in `save_results()`.

---

## Internal Functions

### StrategyModule

Strategy function container dataclass.

**Location:** `lib/backtest/strategy.py`

**Fields:**
- `initialize` - Required initialization function
- `handle_data` - Optional bar handler
- `analyze` - Optional post-backtest analysis
- `before_trading_start` - Optional daily setup

### Results Serialization

**Location:** `lib/backtest/results_serialization.py`

Functions for converting DataFrames to CSV/JSON:
- `normalize_performance_dataframe()` - Normalize timezone to UTC
- `serialize_returns()` - Convert returns to CSV
- `serialize_positions()` - Convert positions to CSV
- `serialize_transactions()` - Convert transactions to CSV
- `serialize_metrics()` - Convert metrics to JSON
- `serialize_parameters()` - Convert parameters to YAML

### Results Persistence

**Location:** `lib/backtest/results_persistence.py`

Functions for filesystem operations:
- `create_results_directory()` - Create timestamped directory
- `update_symlinks()` - Update `latest/` symlink
- `ensure_results_structure()` - Ensure directory structure exists

---

## Metrics Calculated

The `save_results()` function calculates these metrics:

| Metric | Description |
|--------|-------------|
| `total_return` | Total cumulative return |
| `annual_return` | Annualized return |
| `annual_volatility` | Annualized volatility |

**v1.11.0 - Portfolio Value Reconstruction:**

When `metrics_set='none'` is used (automatically for FOREX strategies), Zipline doesn't populate `returns` or `portfolio_value` columns. The `save_results()` function automatically:

1. **Reconstructs portfolio_value** from transactions and positions:
   - Tracks cash balance from buy/sell transactions
   - Calculates position values from positions DataFrame
   - Portfolio value = cash + sum(position_values)

2. **Calculates returns** from reconstructed portfolio_value:
   - Returns = portfolio_value.pct_change()
   - Used for all metric calculations

3. **Adds columns to perf DataFrame** for plotting:
   - `perf['portfolio_value']` - Reconstructed equity curve
   - `perf['returns']` - Calculated returns

This ensures all metrics are calculated correctly even when Zipline's metrics are disabled.
| `sharpe` | Sharpe ratio |
| `sortino` | Sortino ratio |
| `max_drawdown` | Maximum drawdown |
| `calmar` | Calmar ratio |
| `trade_count` | Number of trades |
| `win_rate` | Winning trade percentage |
| `profit_factor` | Gross profit / gross loss |

---

## See Also

**Related API Documentation:**
- [Bundles API](bundles.md) - Data bundle management
- [Calendars API](calendars.md) - Trading calendar system
- [Validation API](validation.md) - Data validation
- [Metrics API](metrics.md) - Performance metrics
- [Config API](config.md) - Configuration loading

**Troubleshooting:**
- [Troubleshooting: Backtesting](../troubleshooting/backtesting.md)

**Internal Modules:**
- `lib/backtest/preprocessing.py` - Pre-flight validation
- `lib/backtest/verification.py` - Post-backtest verification
- `lib/backtest/results_serialization.py` - Result serialization
- `lib/backtest/results_persistence.py` - Result persistence
- `lib/calendars/sessions/` - Session alignment validation
