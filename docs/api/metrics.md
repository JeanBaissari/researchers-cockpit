# Metrics API

Comprehensive performance metrics calculation using empyrical-reloaded library.

**Location:** `lib/metrics/`

---

## Module Structure

The metrics package is organized into focused modules (v1.11.0 modular architecture):

```
lib/metrics/
├── core.py                   # Orchestrator (calculate_metrics)
├── performance.py            # Sharpe, Sortino, returns (v1.11.0)
├── risk.py                   # Drawdown, alpha/beta, VaR (v1.11.0)
├── trade.py                  # Trade-level metrics
├── rolling.py                # Rolling window metrics
└── comparison.py             # Multi-strategy comparison
```

**Key Modules:**
- **core.py**: Main orchestrator that coordinates all metric calculations
- **performance.py**: Performance metrics (Sharpe, Sortino, returns, CAGR)
- **risk.py**: Risk metrics (drawdown, alpha, beta, VaR, CVaR)
- **trade.py**: Trade-level analysis (win rate, profit factor, trade statistics)
- **rolling.py**: Rolling window metrics over time
- **comparison.py**: Multi-strategy comparison utilities

---

## calculate_metrics()

Calculate comprehensive performance metrics from returns.

**Location:** `lib/metrics/core.py` (orchestrator)

**Signature:**
```python
def calculate_metrics(
    returns: pd.Series,
    transactions: Optional[pd.DataFrame] = None,
    benchmark_returns: Optional[pd.Series] = None,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252
) -> Dict[str, float]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Daily returns series |
| `transactions` | pd.DataFrame | None | Transactions for trade-level metrics |
| `benchmark_returns` | pd.Series | None | Benchmark returns for alpha/beta |
| `risk_free_rate` | float | 0.04 | Annual risk-free rate |
| `trading_days_per_year` | int | 252 | Trading days per year |

**Returns:** `Dict[str, float]` - Dictionary of calculated metrics

**Note (v1.11.0):** When `returns` is missing (e.g., when `metrics_set='none'` is used for FOREX), `save_results()` automatically calculates returns from `portfolio_value` before calling `calculate_metrics()`. See [Backtest API](backtest.md) for details on portfolio_value reconstruction.

**Internal Architecture:**

The `calculate_metrics()` function orchestrates calls to specialized modules:

- **Performance Metrics** (`lib/metrics/performance.py`):
  - `calculate_sharpe_ratio()` - Sharpe ratio calculation
  - `calculate_sortino_ratio()` - Sortino ratio calculation
  - `calculate_calmar_ratio()` - Calmar ratio calculation
  - `calculate_annual_return()` - Annualized return
  - `calculate_total_return()` - Total cumulative return
  - `calculate_annual_volatility()` - Annualized volatility

- **Risk Metrics** (`lib/metrics/risk.py`):
  - `calculate_max_drawdown()` - Maximum drawdown
  - `calculate_recovery_time()` - Time to recover from max drawdown
  - `calculate_alpha_beta()` - Alpha and beta (requires benchmark)
  - `calculate_omega_ratio()` - Omega ratio
  - `calculate_tail_ratio()` - Tail ratio
  - `calculate_max_drawdown_duration()` - Drawdown duration

- **Trade Metrics** (`lib/metrics/trade.py`):
  - `calculate_trade_metrics()` - Trade-level analysis (if transactions provided)

**Example:**
```python
from lib.metrics import calculate_metrics

# Basic usage
metrics = calculate_metrics(returns)
print(f"Sharpe: {metrics['sharpe']:.2f}")
print(f"Sortino: {metrics['sortino']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")

# With transactions for trade metrics
metrics = calculate_metrics(
    returns,
    transactions=transactions_df,
    risk_free_rate=0.05,
    trading_days_per_year=365  # For crypto
)
print(f"Win Rate: {metrics['win_rate']:.1%}")
print(f"Profit Factor: {metrics['profit_factor']:.2f}")
```

**Returned Metrics:**

**Performance Metrics** (from `performance.py`):

| Metric | Description |
|--------|-------------|
| `total_return` | Total cumulative return |
| `annual_return` | Annualized return |
| `annual_volatility` | Annualized volatility |
| `sharpe` | Sharpe ratio (excess return / volatility) |
| `sortino` | Sortino ratio (excess return / downside deviation) |
| `calmar` | Calmar ratio (annual return / max drawdown) |

**Risk Metrics** (from `risk.py`):

| Metric | Description |
|--------|-------------|
| `max_drawdown` | Maximum peak-to-trough drawdown |
| `alpha` | Jensen's alpha (requires benchmark) |
| `beta` | Beta to benchmark (requires benchmark) |
| `omega` | Omega ratio |
| `tail_ratio` | Tail ratio |
| `max_drawdown_duration` | Max drawdown duration in days |
| `recovery_time` | Time to recover from max drawdown |

**Trade-Level Metrics** (from `trade.py`, requires transactions):

| Metric | Description |
|--------|-------------|
| `trade_count` | Number of completed trades |
| `win_rate` | Percentage of winning trades |
| `profit_factor` | Gross profit / gross loss |
| `avg_trade_return` | Average return per trade |
| `avg_win` | Average winning trade return |
| `avg_loss` | Average losing trade return |
| `max_win` | Maximum single trade return |
| `max_loss` | Maximum single trade loss |
| `max_consecutive_losses` | Longest losing streak |
| `avg_trade_duration` | Average trade holding period |
| `trades_per_month` | Average trades per month |

**Notes:**
- All output values are guaranteed valid floats (no NaN/Inf)
- Requires minimum 20 periods for reliable Sharpe/Sortino
- Uses empyrical-reloaded when available, manual fallback otherwise
- Performance and risk metrics are calculated independently for modularity

---

## Performance Metrics Module

**Location:** `lib/metrics/performance.py`

Provides performance-focused metrics: Sharpe, Sortino, returns, and volatility.

### calculate_sharpe_ratio()

Calculate Sharpe ratio with proper edge case handling.

**Signature:**
```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252,
    annual_return: Optional[float] = None,
    annual_volatility: Optional[float] = None
) -> float
```

### calculate_sortino_ratio()

Calculate Sortino ratio using downside deviation.

**Signature:**
```python
def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252,
    annual_return: Optional[float] = None
) -> float
```

### calculate_calmar_ratio()

Calculate Calmar ratio (annual return / max drawdown).

**Signature:**
```python
def calculate_calmar_ratio(
    annual_return: float,
    max_drawdown: float
) -> float
```

### calculate_annual_return()

Calculate annualized return.

**Signature:**
```python
def calculate_annual_return(
    returns: pd.Series,
    trading_days_per_year: int = 252
) -> float
```

### calculate_total_return()

Calculate total cumulative return.

**Signature:**
```python
def calculate_total_return(returns: pd.Series) -> float
```

### calculate_annual_volatility()

Calculate annualized volatility.

**Signature:**
```python
def calculate_annual_volatility(
    returns: pd.Series,
    trading_days_per_year: int = 252
) -> float
```

---

## Risk Metrics Module

**Location:** `lib/metrics/risk.py`

Provides risk-focused metrics: drawdown, alpha, beta, VaR, and related risk measures.

### calculate_max_drawdown()

Calculate maximum drawdown.

**Signature:**
```python
def calculate_max_drawdown(returns: pd.Series) -> float
```

### calculate_recovery_time()

Calculate time to recover from maximum drawdown.

**Signature:**
```python
def calculate_recovery_time(returns: pd.Series) -> Optional[pd.Timedelta]
```

### calculate_alpha_beta()

Calculate Jensen's alpha and beta to benchmark.

**Signature:**
```python
def calculate_alpha_beta(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252
) -> Tuple[float, float]
```

**Returns:** `Tuple[float, float]` - (alpha, beta)

### calculate_omega_ratio()

Calculate Omega ratio.

**Signature:**
```python
def calculate_omega_ratio(returns: pd.Series) -> float
```

### calculate_tail_ratio()

Calculate tail ratio (95th percentile / 5th percentile).

**Signature:**
```python
def calculate_tail_ratio(returns: pd.Series) -> float
```

### calculate_max_drawdown_duration()

Calculate maximum drawdown duration in days.

**Signature:**
```python
def calculate_max_drawdown_duration(returns: pd.Series) -> float
```

---

## Trade Metrics Module

**Location:** `lib/metrics/trade.py`

Provides trade-level analysis from transaction data.

### calculate_trade_metrics()

Calculate trade-level metrics from transactions DataFrame.

**Signature:**
```python
def calculate_trade_metrics(
    transactions: pd.DataFrame,
    as_percentages: bool = False
) -> Dict[str, float]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transactions` | pd.DataFrame | required | Transactions with columns: date, sid, amount, price, commission |
| `as_percentages` | bool | False | Convert decimal values to percentages |

**Returns:** `Dict[str, float]` - Trade-level metrics

**Example:**
```python
from lib.metrics import calculate_trade_metrics

trade_metrics = calculate_trade_metrics(transactions_df)
print(f"Total trades: {trade_metrics['trade_count']}")
print(f"Win rate: {trade_metrics['win_rate']:.1%}")
```

---

## Rolling Metrics Module

**Location:** `lib/metrics/rolling.py`

Provides rolling window metrics over time.

### calculate_rolling_metrics()

Calculate rolling metrics over a specified window.

**Signature:**
```python
def calculate_rolling_metrics(
    returns: pd.Series,
    window: int = 63,
    risk_free_rate: float = 0.04
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `returns` | pd.Series | required | Daily returns series |
| `window` | int | 63 | Rolling window size in days (~3 months) |
| `risk_free_rate` | float | 0.04 | Annual risk-free rate |

**Returns:** `pd.DataFrame` - DataFrame with rolling metrics columns

**Columns:**
- `rolling_sharpe`
- `rolling_sortino`
- `rolling_return`
- `rolling_volatility`
- `rolling_max_dd`

**Example:**
```python
from lib.metrics import calculate_rolling_metrics

rolling = calculate_rolling_metrics(returns, window=63)

# Plot rolling Sharpe
import matplotlib.pyplot as plt
plt.plot(rolling.index, rolling['rolling_sharpe'])
plt.axhline(y=0, color='r', linestyle='--')
plt.title('Rolling 3-Month Sharpe Ratio')
plt.show()
```

---

## Comparison Module

**Location:** `lib/metrics/comparison.py`

Provides multi-strategy comparison utilities.

### compare_strategies()

Compare multiple strategies by loading their latest metrics.

**Signature:**
```python
def compare_strategies(
    strategy_names: List[str],
    results_base: Optional[Path] = None
) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_names` | List[str] | required | List of strategy names |
| `results_base` | Path | None | Base results directory |

**Returns:** `pd.DataFrame` - Comparison table

**Example:**
```python
from lib.metrics import compare_strategies

comparison = compare_strategies([
    'spy_sma_cross',
    'btc_momentum',
    'eur_usd_trend'
])

print(comparison.to_string())
```

**Output columns:**
- `strategy`
- `sharpe`
- `sortino`
- `annual_return`
- `max_drawdown`
- `calmar`
- `win_rate`
- `trade_count`

---

## Trading Days Configuration

| Calendar | Trading Days/Year | Use Case |
|----------|-------------------|----------|
| XNYS | 252 | US Equities |
| FOREX | 260 | Foreign Exchange |
| CRYPTO | 365 | Cryptocurrency |

The `save_results()` function automatically selects the correct value based on the trading calendar.

---

## Sharpe Ratio Calculation

The Sharpe ratio is calculated using empyrical-reloaded:

```python
sharpe = (annual_return - risk_free_rate) / annual_volatility
```

**Edge Cases Handled:**
- Zero volatility: Returns 0 (unrealistic scenario)
- Insufficient data (<20 periods): Returns 0
- NaN/Inf values: Sanitized to 0

---

## Sortino Ratio Calculation

The Sortino ratio uses downside deviation:

```python
downside_returns = returns[returns < daily_risk_free_rate]
downside_std = sqrt(mean(downside_returns^2))
sortino = (annual_return - risk_free_rate) / annualized_downside_std
```

---

## Module Organization

**Performance vs Risk Split (v1.11.0):**

The metrics package was refactored in v1.11.0 to separate performance and risk concerns:

- **Performance Metrics** (`lib/metrics/performance.py`): Focus on return and reward metrics
  - Sharpe, Sortino, Calmar ratios
  - Annual/total returns
  - Volatility calculations

- **Risk Metrics** (`lib/metrics/risk.py`): Focus on downside and risk measures
  - Drawdown calculations
  - Alpha/beta (benchmark-relative)
  - VaR, CVaR, tail ratios
  - Recovery time and duration

- **Core Orchestrator** (`lib/metrics/core.py`): Coordinates all metric calculations
  - Calls performance and risk modules
  - Handles trade metrics integration
  - Provides unified `calculate_metrics()` interface

**Direct Module Access:**

For advanced use cases, you can import directly from specific modules:

```python
# Direct access to performance metrics
from lib.metrics.performance import calculate_sharpe_ratio, calculate_sortino_ratio

# Direct access to risk metrics
from lib.metrics.risk import calculate_max_drawdown, calculate_alpha_beta

# Direct access to trade metrics
from lib.metrics.trade import calculate_trade_metrics
```

---

## See Also

**Related API Documentation:**
- [Backtest API](backtest.md) - Uses metrics for result analysis
- [Optimize API](optimize.md) - Uses metrics for optimization objectives
- [Data API](data.md) - Data sanitization utilities used by metrics

**Internal Modules:**
- `lib/metrics/core.py` - Main orchestrator
- `lib/metrics/performance.py` - Performance metrics
- `lib/metrics/risk.py` - Risk metrics
- `lib/metrics/trade.py` - Trade-level analysis
- `lib/metrics/rolling.py` - Rolling window metrics
- `lib/metrics/comparison.py` - Strategy comparison
