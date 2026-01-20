# Algorithm Lifecycle

> Understanding the execution flow of a Zipline algorithm.

## Lifecycle Functions

### 1. initialize(context)

Called **once** at the very beginning of the backtest.

```python
def initialize(context):
    """
    Set up algorithm state and configuration.
    
    Parameters
    ----------
    context : object
        Persistent namespace for storing state across function calls.
    """
    context.asset = symbol('AAPL')
    context.lookback = 20
    context.rebalance_frequency = 5
    context.day_count = 0
```

**Use For:**
- Setting up assets to trade
- Configuring algorithm parameters
- Scheduling functions
- Attaching pipelines
- Setting commission/slippage models

### 2. before_trading_start(context, data)

Called **once per trading day**, before market open.

```python
def before_trading_start(context, data):
    """
    Daily preparation before market opens.
    
    Parameters
    ----------
    context : object
        Algorithm state.
    data : BarData
        Data access object (limited - no current prices).
    """
    # Get pipeline results
    context.output = pipeline_output('my_pipeline')
    
    # Select top stocks
    context.longs = context.output.sort_values('factor', ascending=False).head(10)
```

**Use For:**
- Getting pipeline output
- Setting up daily trading lists
- Pre-market analysis
- Daily rebalancing logic

### 3. handle_data(context, data)

Called **every bar** (minute or daily based on `data_frequency`).

```python
def handle_data(context, data):
    """
    Main trading logic executed each bar.
    
    Parameters
    ----------
    context : object
        Algorithm state.
    data : BarData
        Current market data access.
    """
    current_price = data.current(context.asset, 'price')
    
    if data.can_trade(context.asset):
        order_target_percent(context.asset, 0.5)
    
    record(price=current_price)
```

**Use For:**
- Placing orders
- Accessing current prices
- Recording custom metrics
- Real-time signal generation

### 4. analyze(context, perf)

Called **once** at the end of the backtest.

```python
def analyze(context, perf):
    """
    Post-backtest analysis.
    
    Parameters
    ----------
    context : object
        Final algorithm state.
    perf : pd.DataFrame
        Daily performance results.
    """
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    perf['portfolio_value'].plot(ax=axes[0], title='Portfolio Value')
    perf['returns'].cumsum().plot(ax=axes[1], title='Cumulative Returns')
    
    plt.tight_layout()
    plt.savefig('backtest_results.png')
```

**Use For:**
- Generating reports
- Creating visualizations
- Saving results
- Final calculations

## Execution Order

```
┌─────────────────────────────────────────────────────────────┐
│                     BACKTEST START                          │
├─────────────────────────────────────────────────────────────┤
│  initialize(context)                    [ONCE]              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │            FOR EACH TRADING DAY                      │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  before_trading_start(context, data)  [DAILY]       │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │           FOR EACH BAR                       │   │   │
│  │  ├─────────────────────────────────────────────┤   │   │
│  │  │  handle_data(context, data)    [PER BAR]    │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  analyze(context, perf)                 [ONCE]              │
└─────────────────────────────────────────────────────────────┘
```

## Context Object

The `context` object persists across all function calls.

```python
def initialize(context):
    # Store anything you need
    context.asset = symbol('AAPL')
    context.counter = 0
    context.history = []
    context.params = {'threshold': 0.02}

def handle_data(context, data):
    # Access and modify
    context.counter += 1
    context.history.append(data.current(context.asset, 'price'))
```

## See Also

- [run_algorithm()](run_algorithm.md)
- [BarData](../02_data/bar_data.md)
- [schedule_function()](../03_scheduling/schedule_function.md)
