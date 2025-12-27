# Zipline Reloaded Documentation

> Comprehensive API reference for building production-ready algorithmic trading strategies.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Getting Started](00_getting_started/) | Running backtests, algorithm lifecycle |
| [Core API](01_core/) | Context, portfolio, account, recording |
| [Data Access](02_data/) | `BarData`, `current()`, `history()` |
| [Scheduling](03_scheduling/) | `schedule_function()`, date/time rules |
| [Orders](04_orders/) | Order placement, execution styles |
| [Assets](05_assets/) | Asset types, lookups, trading controls |
| [Pipeline](06_pipeline/) | Factor/Filter computations |
| [Finance](07_finance/) | Blotters, commission, slippage models |
| [Data Bundles](08_data_bundles/) | Data ingestion, writers/readers |
| [Metrics](09_metrics/) | Performance metrics, algorithm state |
| [Utilities](10_utilities/) | Caching, helpers |
| [Reference](../11_reference/) | Cheatsheets, strategy examples |

---

## Documentation Index

### Getting Started
- [run_algorithm()](00_getting_started/run_algorithm.md) - Entry point
- [Algorithm Lifecycle](00_getting_started/algorithm_lifecycle.md) - Execution flow

### Core
- [Context Object](01_core/context.md) - State management
- [Portfolio](01_core/portfolio.md) - Portfolio access and positions
- [Account](01_core/account.md) - Account_level metrics and leverage
- [Recording Values](01_core/record.md) - Track custom metrics
- [Environment & External Data](01_core/environment_data.md) - fetch_csv, get_environment

### Data Access
- [BarData Class](02_data/bar_data.md) - The `data` object
- [data.current()](02_data/current.md) - Current prices
- [data.history()](02_data/history.md) - Historical data
- [Tradability Checks](02_data/can_trade.md) - can_trade, is_stale

### Scheduling
- [schedule_function()](03_scheduling/schedule_function.md) - Schedule execution
- [Date Rules](03_scheduling/date_rules.md) - When to run
- [Time Rules](03_scheduling/time_rules.md) - What time to run

### Orders
- [Basic Orders](04_orders/basic_orders.md) - order, order_value, order_percent
- [Target Orders](04_orders/target_orders.md) - order_target variants
- [Execution Styles](04_orders/execution_styles.md) - Market, Limit, Stop
- [Order Management](04_orders/order_management.md) - Get, cancel orders
- [Cancel Policies](04_orders/cancel_policies.md) - EOD, Never cancel

### Assets
- [Asset Types](05_assets/asset_types.md) - Equity, Future classes
- [Asset Lookup](05_assets/asset_lookup.md) - symbol, symbols, sid
- [Asset Finder](05_assets/asset_finder.md) - Advanced asset queries
- [Trading Controls](05_assets/trading_controls.md) - Restrictions and limits

### Pipeline
- [Pipeline Overview](06_pipeline/pipeline_overview.md) - Concepts and usage
- [Factors](06_pipeline/factors.md) - Numerical computations
- [Filters](06_pipeline/filters.md) - Boolean screening
- [Custom Factors](06_pipeline/custom_factors.md) - Build your own
- [Built_in Factors](06_pipeline/builtin_factors.md) - Returns, VWAP, etc.
- [Built_in Filters](06_pipeline/builtin_filters.md) - StaticAssets, universe filters
- [Pipeline Engine](06_pipeline/pipeline_engine.md) - Execution details
- [Data Loaders](06_pipeline/data_loaders.md) - Data sources

### Finance Models
- [Commission Models](07_finance/commission_models.md) - PerShare, PerTrade, PerDollar
- [Slippage Models](07_finance/slippage_models.md) -  Volume, Fixed slippage
- [Blotters](07_finance/blotter.md) - Order execution infrastructure

### Data Bundles
- [Bundles Overview](08_data_bundles/bundles_overview.md) - Understanding bundles
- [Bundles API](08_data_bundles/bundles.md) - Register, ingest, load
- [Asset Metadata](08_data_bundles/asset_metadata.md) - Security information
- [Data Writers](08_data_bundles/data_writers.md) - Write pricing data
- [Data Readers](08_data_bundles/data_readers.md) - Read pricing data

### Metrics
- [Metrics Overview](09_metrics/metrics.md) - Performance tracking
- [Risk Metrics](09_metrics/risk_metrics.md) - Built_in metrics classes
- [Algorithm State](09_metrics/algorithm_state.md) - Portfolio, Account, Ledger

### Utilities
- [Caching](10_utilities/caching.md) - Data caching utilities

### Reference
- [Quick Reference](11_reference/quick_reference.md) - API cheatsheet
- [Strategy Examples](11_reference/strategy_examples.md) - Complete templates

---

## Algorithm Structure

```python
from zipline.api import order, record, symbol
from zipline import run_algorithm

def initialize(context):
    """Called once at start. Set up state here."""
    context.asset = symbol('AAPL')

def handle_data(context, data):
    """Called every bar (minute/daily)."""
    order(context.asset, 10)

def before_trading_start(context, data):
    """Called once per day before market open."""
    pass

def analyze(context, perf):
    """Called once at end with performance DataFrame."""
    pass

results = run_algorithm(
    start=start_date,
    end=end_date,
    initialize=initialize,
    handle_data=handle_data,
    capital_base=100000,
    bundle='quandl'
)
```

___

## Key Concepts

### Data Frequency
_ `'daily'` _ One bar per trading day
_ `'minute'` _ One bar per minute during market hours

### Asset Types
_ **Equity** _ Stocks, partial company ownership
_ **Future** _ Futures contracts

### Pipeline
Pre_compute cross_sectional data before trading starts each day.

___

## File Conventions

Each documentation file:
_ Under 200 lines for easy AI assistant consumption
_ Contains complete, working examples
_ Documents parameters, return types, and exceptions
_ Includes "See Also" cross_references

___

## Source

Based on [Zipline Reloaded](https://zipline.ml4trading.io/) API Reference.
