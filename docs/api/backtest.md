# Backtest API

Module for executing Zipline backtests and saving results in standardized format.

**Location:** `lib/backtest.py`
**CLI Equivalent:** `scripts/run_backtest.py`

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
print(f"Final value: ${perf['portfolio_value'].iloc[-1]:,.2f}")
print(f"Total return: {perf['returns'].sum():.2%}")

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

**Validation Steps Performed:**
1. Load and validate strategy module (must have `initialize()`)
2. Load and validate `parameters.yaml`
3. Validate warmup period (sufficient data for indicators)
4. Validate strategy symbols exist in bundle
5. Register custom calendars if needed
6. Validate calendar consistency (bundle vs backtest)
7. Validate bundle date range covers requested dates

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
├── returns.csv          # Daily/minute returns
├── positions.csv        # Position history
├── transactions.csv     # All trades
├── metrics.json         # Performance metrics
├── parameters_used.yaml # Strategy config snapshot
└── equity_curve.png     # Performance visualization
```

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

## Internal Functions

### _load_strategy_module()

Load strategy module and extract required functions.

**Returns:** `StrategyModule` dataclass with:
- `initialize` - Required initialization function
- `handle_data` - Optional bar handler
- `analyze` - Optional post-backtest analysis
- `before_trading_start` - Optional daily setup

### _prepare_backtest_config()

Prepare and validate backtest configuration, resolving defaults.

### _validate_warmup_period()

Pre-flight validation for sufficient warmup data.

### _validate_calendar_consistency()

Check bundle calendar matches backtest calendar.

### _validate_bundle_date_range()

Ensure bundle covers requested date range.

### _get_trading_calendar()

Extract trading calendar from bundle.

---

## Metrics Calculated

The `save_results()` function calculates these metrics:

| Metric | Description |
|--------|-------------|
| `total_return` | Total cumulative return |
| `annual_return` | Annualized return |
| `annual_volatility` | Annualized volatility |
| `sharpe` | Sharpe ratio |
| `sortino` | Sortino ratio |
| `max_drawdown` | Maximum drawdown |
| `calmar` | Calmar ratio |
| `trade_count` | Number of trades |
| `win_rate` | Winning trade percentage |
| `profit_factor` | Gross profit / gross loss |

---

## See Also

- [Troubleshooting: Backtesting](../troubleshooting/backtesting.md)
- [Metrics API](metrics.md)
- [Config API](config.md)
