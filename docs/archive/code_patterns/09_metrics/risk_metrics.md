# Risk Metrics

> Track and report algorithm performance metrics.

## Overview

Zipline's metrics system tracks performance throughout a backtest. Metrics update per-bar and per-session, then aggregate into the final performance DataFrame.

---

## Built-in Metrics

### SimpleLedgerField

```python
class zipline.finance.metrics.SimpleLedgerField(ledger_field, packet_field=None)
```

Emit a ledger field value every bar.

| Parameter | Type | Description |
|-----------|------|-------------|
| `ledger_field` | str | Field to read from ledger |
| `packet_field` | str | Output field name (optional) |

### DailyLedgerField

```python
class zipline.finance.metrics.DailyLedgerField(ledger_field, packet_field=None)
```

Like SimpleLedgerField, also adds to cumulative_perf section.

### StartOfPeriodLedgerField

```python
class zipline.finance.metrics.StartOfPeriodLedgerField(ledger_field, packet_field=None)
```

Track value at period start for comparison.

---

## Performance Metrics

### Returns

```python
class zipline.finance.metrics.Returns
```

Tracks daily and cumulative returns.

### BenchmarkReturnsAndVolatility

```python
class zipline.finance.metrics.BenchmarkReturnsAndVolatility
```

Tracks benchmark returns and volatility for comparison.

### AlphaBeta

```python
class zipline.finance.metrics.AlphaBeta
```

End-of-simulation alpha and beta vs benchmark.

### MaxLeverage

```python
class zipline.finance.metrics.MaxLeverage
```

Tracks maximum account leverage reached.

---

## Transaction Metrics

### CashFlow

```python
class zipline.finance.metrics.CashFlow
```

Tracks daily and cumulative cash flow (named 'capital_used' in output).

### Orders

```python
class zipline.finance.metrics.Orders
```

Records all orders placed each day.

### Transactions

```python
class zipline.finance.metrics.Transactions
```

Records all transactions (fills) each day.

### Positions

```python
class zipline.finance.metrics.Positions
```

Tracks positions at end of each day.

---

## ReturnsStatistic

```python
class zipline.finance.metrics.ReturnsStatistic(function, field_name=None)
```

Compute custom statistics from returns series.

| Parameter | Type | Description |
|-----------|------|-------------|
| `function` | callable | Function to apply to returns |
| `field_name` | str | Output field name |

### Example

```python
from zipline.finance.metrics import ReturnsStatistic
import empyrical

sharpe_metric = ReturnsStatistic(
    empyrical.sharpe_ratio,
    field_name='sharpe'
)
```

---

## Metrics Sets

### register()

```python
zipline.finance.metrics.register(name, function=None)
```

Register a custom metrics set.

```python
from zipline.finance.metrics import register, Returns, Positions

@register('my-metrics')
def my_metrics_set():
    return {
        Returns(),
        Positions(),
        # Add custom metrics here
    }
```

### load()

```python
zipline.finance.metrics.load(name)
```

Load a registered metrics set by name.

### unregister()

```python
zipline.finance.metrics.unregister(name)
```

Remove a metrics set registration.

### metrics_sets

```python
zipline.finance.metrics.metrics_sets
```

Immutable mapping of registered metrics sets.

---

## Using Custom Metrics

```python
from zipline import run_algorithm

result = run_algorithm(
    ...,
    metrics_set='my-metrics'
)
```

---

## See Also

- [Algorithm State](algorithm_state.md)
- [run_algorithm()](../00_getting_started/run_algorithm.md)
