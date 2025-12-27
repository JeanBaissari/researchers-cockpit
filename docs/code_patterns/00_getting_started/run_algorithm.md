# run_algorithm()

> Entry point for executing a backtest simulation.

## Function Signature

```python
zipline.run_algorithm(
    start,
    end,
    initialize,
    capital_base,
    handle_data=None,
    before_trading_start=None,
    analyze=None,
    data_frequency='daily',
    bundle='quandl',
    bundle_timestamp=None,
    trading_calendar=None,
    metrics_set='default',
    benchmark_returns=None,
    default_extension=True,
    extensions=(),
    strict_extensions=True,
    environ=os.environ,
    blotter='default'
)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start` | datetime | Backtest start date |
| `end` | datetime | Backtest end date |
| `initialize` | callable | `initialize(context)` - Called once at start |
| `capital_base` | float | Starting capital |
| `handle_data` | callable | `handle_data(context, data)` - Called every bar |
| `before_trading_start` | callable | `before_trading_start(context, data)` - Daily, before market |
| `analyze` | callable | `analyze(context, perf)` - Called at end |
| `data_frequency` | str | `'daily'` or `'minute'` |
| `bundle` | str | Data bundle name (default: `'quandl'`) |
| `bundle_timestamp` | datetime | Bundle data lookup timestamp |
| `trading_calendar` | TradingCalendar | Calendar for trading days |
| `metrics_set` | iterable/str | Metrics to compute |
| `benchmark_returns` | pd.Series | Benchmark return series |
| `default_extension` | bool | Load `$ZIPLINE_ROOT/extension.py` |
| `extensions` | iterable | Additional extension modules |
| `strict_extensions` | bool | Fail on extension load errors |
| `environ` | mapping | Environment variables |
| `blotter` | str/Blotter | Order management blotter |

## Returns

| Type | Description |
|------|-------------|
| pd.DataFrame | Daily performance metrics |

## Example

### Daily Frequency Example

```python
from zipline import run_algorithm
from zipline.api import order_target_percent, symbol
import pandas as pd

def initialize(context):
    context.asset = symbol('AAPL')
    context.target_pct = 0.5

def handle_data(context, data):
    order_target_percent(context.asset, context.target_pct)

start = pd.Timestamp('2020-01-01', tz='utc')
end = pd.Timestamp('2020-12-31', tz='utc')

results = run_algorithm(
    start=start,
    end=end,
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    data_frequency='daily',
    bundle='quandl' # Or your custom bundle like 'yahoo_equities_daily'
)

# Results DataFrame contains daily performance
print(results.columns)
# ['period_open', 'period_close', 'starting_value', 'ending_value',
#  'starting_cash', 'ending_cash', 'portfolio_value', 'pnl', 
#  'returns', 'cash_flow', 'benchmark_returns', ...]
```

### Minute Frequency Example

To run a backtest at minute frequency, you need to:

1.  Ensure your data bundle contains minute-level data (e.g., `yahoo_equities_minute`). You may need to ingest this data first using `scripts/ingest_data.py --timeframe minute`.
2.  Set `data_frequency='minute'` in `run_algorithm()`.
3.  Adjust your strategy's `schedule_function` calls or `handle_data` logic to operate on minute bars.

```python
from zipline import run_algorithm
from zipline.api import order_target_percent, symbol, schedule_function, date_rules, time_rules
import pandas as pd

def initialize(context):
    context.asset = symbol('AAPL')
    context.target_pct = 0.5
    # Schedule handle_data to run every minute
    schedule_function(
        rebalance_minute,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.every_minute()
    )

def rebalance_minute(context, data):
    # Access minute data
    current_price = data.current(context.asset, 'price')
    # Example: Simple order logic
    if current_price is not None and data.can_trade(context.asset):
        order_target_percent(context.asset, context.target_pct)

# Note: handle_data is often passed as None for minute frequency when using schedule_function
# as scheduled functions often encapsulate the main logic.
def handle_data(context, data):
    pass

start = pd.Timestamp('2020-01-01 09:30', tz='America/New_York').astimezone(pd.Timestamp.utcnow().tz)
end = pd.Timestamp('2020-01-02 16:00', tz='America/New_York').astimezone(pd.Timestamp.utcnow().tz)

results_minute = run_algorithm(
    start=start,
    end=end,
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    data_frequency='minute',
    bundle='yahoo_equities_minute' # Ensure this bundle is ingested with minute data
)

print("\nMinute Frequency Results:")
print(results_minute.head())
```

## Performance DataFrame Columns

Key columns in returned DataFrame:
- `portfolio_value` - Total portfolio value
- `pnl` - Profit and loss
- `returns` - Daily returns
- `starting_cash`, `ending_cash` - Cash positions
- `starting_value`, `ending_value` - Portfolio values
- `benchmark_returns` - Benchmark comparison
- `orders` - Orders placed
- `transactions` - Executed trades
- `positions` - Current holdings

## See Also

- [Algorithm Lifecycle](algorithm_lifecycle.md)
- [Data Bundles](../08_data_bundles/bundles_overview.md)
- [Metrics](../09_metrics/metrics.md)
