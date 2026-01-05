# Metrics API

Comprehensive performance metrics calculation using empyrical-reloaded library.

**Location:** `lib/metrics.py`

---

## calculate_metrics()

Calculate comprehensive performance metrics from returns.

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

| Metric | Description |
|--------|-------------|
| `total_return` | Total cumulative return |
| `annual_return` | Annualized return |
| `annual_volatility` | Annualized volatility |
| `sharpe` | Sharpe ratio (excess return / volatility) |
| `sortino` | Sortino ratio (excess return / downside deviation) |
| `max_drawdown` | Maximum peak-to-trough drawdown |
| `calmar` | Calmar ratio (annual return / max drawdown) |
| `alpha` | Jensen's alpha (requires benchmark) |
| `beta` | Beta to benchmark (requires benchmark) |
| `omega` | Omega ratio |
| `tail_ratio` | Tail ratio |
| `max_drawdown_duration` | Max drawdown duration in days |
| `recovery_time` | Time to recover from max drawdown |

**Trade-Level Metrics (requires transactions):**

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

---

## calculate_rolling_metrics()

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

## compare_strategies()

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

## calculate_trade_metrics()

Calculate trade-level metrics from transactions DataFrame.

**Signature:**
```python
def calculate_trade_metrics(
    transactions: pd.DataFrame
) -> Dict[str, float]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transactions` | pd.DataFrame | required | Transactions with columns: date, sid, amount, price, commission |

**Returns:** `Dict[str, float]` - Trade-level metrics

**Example:**
```python
from lib.metrics import calculate_trade_metrics

trade_metrics = calculate_trade_metrics(transactions_df)
print(f"Total trades: {trade_metrics['trade_count']}")
print(f"Win rate: {trade_metrics['win_rate']:.1%}")
```

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

## See Also

- [Backtest API](backtest.md)
- [Optimize API](optimize.md)
