# Recording Values

> Track custom metrics throughout your backtest.

## record()

```python
zipline.api.record(**kwargs)
```

Track and record values each bar. Recorded values appear in performance results.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `**kwargs` | any | Name-value pairs to record |

### Example

```python
def handle_data(context, data):
    price = data.current(context.asset, 'price')
    
    # Record multiple values
    record(
        price=price,
        cash=context.portfolio.cash,
        position_value=context.portfolio.positions_value
    )
```

---

## Accessing Recorded Data

### In analyze()

```python
def analyze(context, perf):
    # Recorded values are columns in perf DataFrame
    print(perf['price'].tail())
    print(perf['cash'].mean())
```

### From run_algorithm()

```python
result = run_algorithm(...)

# Access recorded values
result['price'].plot()
result[['cash', 'position_value']].plot()
```

---

## Common Recording Patterns

### Technical Indicators

```python
def handle_data(context, data):
    prices = data.history(context.asset, 'price', 50, '1d')
    
    sma_20 = prices[-20:].mean()
    sma_50 = prices.mean()
    
    record(
        sma_20=sma_20,
        sma_50=sma_50,
        spread=sma_20 - sma_50
    )
```

### Position Metrics

```python
def handle_data(context, data):
    pos = context.portfolio.positions.get(context.asset)
    
    record(
        shares=pos.amount if pos else 0,
        cost_basis=pos.cost_basis if pos else 0,
        pnl=pos.last_sale_price * pos.amount - pos.cost_basis if pos else 0
    )
```

### Signal Tracking

```python
def handle_data(context, data):
    signal = calculate_signal(data)
    
    record(
        signal=signal,
        signal_strength=abs(signal),
        is_long=1 if signal > 0 else 0
    )
```

---

## Best Practices

1. **Keep names short** - They become DataFrame columns
2. **Record consistently** - Missing values become NaN
3. **Limit quantity** - Too many records slows backtests
4. **Use for debugging** - Great for understanding strategy behavior

---

## See Also

- [analyze() Function](../00_getting_started/algorithm_lifecycle.md)
- [run_algorithm()](../00_getting_started/run_algorithm.md)
