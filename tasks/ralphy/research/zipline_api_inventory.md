# Zipline-Reloaded Data Access API Inventory

**Project:** v1_researchers_cockpit  
**Date:** 2026-01-27  
**Purpose:** Comprehensive inventory of Zipline-Reloaded data access APIs for direct usage (v1.12.0+ NO WRAPPERS architecture)

---

## Table of Contents

1. [Core Data Access APIs](#core-data-access-apis)
2. [Asset Management APIs](#asset-management-apis)
3. [Portfolio & Account APIs](#portfolio--account-apis)
4. [Order Management APIs](#order-management-apis)
5. [Pipeline APIs](#pipeline-apis)
6. [Calendar & Scheduling APIs](#calendar--scheduling-apis)
7. [Bundle Management APIs](#bundle-management-apis)
8. [Commission & Slippage APIs](#commission--slippage-apis)
9. [Recording & Metrics APIs](#recording--metrics-apis)
10. [Utility APIs](#utility-apis)
11. [Best Practices](#best-practices)
12. [Common Patterns](#common-patterns)

---

## Core Data Access APIs

### `data.history()`

**Purpose:** Retrieve historical price/volume data for one or more assets.

**Signature:**
```python
data.history(
    assets,           # Asset or list of assets
    fields,           # 'price', 'close', 'open', 'high', 'low', 'volume', or list
    bar_count,       # Number of bars to retrieve
    frequency,       # '1d', '1m', '1h', etc.
    data_frequency=None  # Override data frequency
) -> pd.DataFrame
```

**Examples:**
```python
# Single asset, single field
prices = data.history(context.asset, 'close', 100, '1d')

# Single asset, multiple fields
ohlcv = data.history(context.asset, ['open', 'high', 'low', 'close', 'volume'], 50, '1m')

# Multiple assets
prices = data.history([asset1, asset2], 'price', 30, '1d')

# Minute data aggregation (use pandas directly)
minute_data = data.history(context.asset, ['open', 'high', 'low', 'close'], 1440, '1m')
hourly_data = minute_data.resample('1h').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
})
```

**Return Type:** `pd.Series` or `pd.DataFrame` depending on inputs:
- Single asset + single field → `pd.Series` with DatetimeIndex
- Single asset + multiple fields → `pd.DataFrame` with DatetimeIndex index and field columns
- Multiple assets + single field → `pd.DataFrame` with DatetimeIndex index and asset columns
- Multiple assets + multiple fields → `pd.DataFrame` with MultiIndex (date, asset) and field columns

**Notes:**
- Returns pandas DataFrame/Series for seamless integration
- Index is DatetimeIndex aligned to trading calendar
- Data is automatically adjusted for splits, dividends, and mergers as of current simulation time
- Frequency must match bundle frequency or be aggregatable (e.g., '1m' → '1h' via pandas)
- Missing data semantics: NaN for dates/assets with no data
- For minute data, if current simulation time is not a valid market time, uses last market close

**Common Use Cases:**
- Technical indicator calculations (SMA, RSI, MACD)
- Multi-timeframe analysis
- Price pattern detection
- Volume analysis

---

### `data.current()`

**Purpose:** Get current (most recent) price or field value for an asset.

**Signature:**
```python
data.current(
    asset,      # Asset object
    field,      # 'price', 'close', 'open', 'high', 'low', 'volume'
    field_name=None  # Alternative field name
) -> float
```

**Examples:**
```python
# Current price
current_price = data.current(context.asset, 'price')

# Current close
close = data.current(context.asset, 'close')

# Current volume
volume = data.current(context.asset, 'volume')
```

**Return Type:** Scalar, `pd.Series`, or `pd.DataFrame` depending on inputs:
- Single asset + single field → scalar (float or `pd.Timestamp` for 'last_traded')
- Single asset + multiple fields → `pd.Series` with field names as index
- Multiple assets + single field → `pd.Series` with assets as index
- Multiple assets + multiple fields → `pd.DataFrame` with assets as index and fields as columns

**Field Semantics:**
- **'price'**: Last known close price, forward-filled from earlier minute if no trade this minute. Adjusted for splits/dividends. Returns NaN if asset never traded or delisted.
- **'open', 'high', 'low', 'close'**: Values for current minute/day. Returns NaN if no trades occurred.
- **'volume'**: Trade volume for current minute/day. Returns 0 if no trades occurred.
- **'last_traded'**: Datetime of last minute in which asset traded. Returns `pd.NaT` if no known value.

**Notes:**
- Returns the most recent available value
- For minute data, returns value for current minute
- For daily data, returns value for current day
- If current simulation time is not a valid market time for asset, uses most recent market close
- Values are adjusted for corporate actions (splits, dividends) as of current simulation time

---

### `data.can_trade()`

**Purpose:** Check if an asset can be traded (has data available).

**Signature:**
```python
data.can_trade(asset) -> bool
```

**Examples:**
```python
# Check before trading
if data.can_trade(context.asset):
    order_target_percent(context.asset, 1.0)

# Multi-asset check
tradeable_assets = [asset for asset in universe if data.can_trade(asset)]
```

**Return Type:** `bool`

**Notes:**
- Returns `True` if asset has data and can be traded
- Returns `False` if asset is delisted, missing data, or outside trading hours
- Always check before placing orders to avoid errors

---

### `data.is_stale()`

**Purpose:** Check if asset data is stale (not updated recently).

**Signature:**
```python
data.is_stale(asset) -> bool
```

**Examples:**
```python
# Check for stale data
if data.is_stale(context.asset):
    logger.warning(f"Stale data for {context.asset}")
    return  # Skip trading logic
```

**Return Type:** `bool`

**Notes:**
- Useful for detecting data feed issues
- Returns `True` if data hasn't been updated recently
- Typically used in live trading scenarios

---

### `data.get_spot_value()`

**Purpose:** Get spot value for a field at a specific time (advanced usage).

**Signature:**
```python
data.get_spot_value(
    asset,
    field,       # 'price', 'close', 'open', 'high', 'low', 'volume', 'last_traded'
    dt,          # Specific datetime (pd.Timestamp)
    data_frequency  # 'daily' or 'minute'
) -> float, int, or pd.Timestamp
```

**Examples:**
```python
# Get price at specific time
price_at_open = data.get_spot_value(
    context.asset,
    'open',
    data.current_dt.replace(hour=9, minute=30),
    '1d'
)

# Get close price at end of previous day
prev_day_close = data.get_spot_value(
    context.asset,
    'close',
    data.current_dt - pd.Timedelta(days=1),
    'daily'
)
```

**Return Type:** `float` (for price fields), `int` (for volume), or `pd.Timestamp` (for 'last_traded')

**Notes:**
- Advanced API for specific timestamp queries
- Less commonly used than `data.current()` or `data.history()`
- Useful for intraday analysis at specific times
- Returns unadjusted spot value at the specified datetime
- Part of the internal DataPortal API, exposed through BarData protocol

---

### `data.get_last_traded_dt()`

**Purpose:** Get the last trading datetime for an asset.

**Signature:**
```python
data.get_last_traded_dt(asset) -> pd.Timestamp
```

**Examples:**
```python
# Check last trade time
last_trade = data.get_last_traded_dt(context.asset)
if (data.current_dt - last_trade).days > 1:
    logger.warning(f"No recent trades for {context.asset}")
```

**Return Type:** `pd.Timestamp`

**Notes:**
- Returns the most recent trading datetime
- Useful for detecting inactive assets
- Can be used to filter out delisted assets

---

## Asset Management APIs

### `symbol()`

**Purpose:** Create an asset object from a symbol string.

**Signature:**
```python
symbol(sid_or_symbol) -> Asset
```

**Examples:**
```python
# Equities
aapl = symbol('AAPL')
spy = symbol('SPY')

# Crypto (Yahoo Finance format)
btc = symbol('BTC-USD')
eth = symbol('ETH-USD')

# Forex (Yahoo Finance format)
eurusd = symbol('EURUSD=X')
gbpusd = symbol('GBPUSD=X')

# In initialize()
context.asset = symbol('AAPL')
```

**Return Type:** `Asset` object

**Notes:**
- Symbol format depends on data source
- Yahoo Finance uses `SYMBOL-USD` for crypto, `SYMBOL=X` for forex
- Asset object is used in all data access and order APIs
- Asset objects are cached by Zipline

---

### Asset Lookup (via AssetFinder)

**Purpose:** Look up assets by various criteria.

**Examples:**
```python
# Get asset finder from context (advanced)
from zipline.assets import AssetFinder
finder = context.asset_finder

# Lookup by SID (internal ID)
asset = finder.retrieve_asset(sid)

# Lookup by symbol
asset = finder.lookup_symbol(symbol, as_of_date)

# Get all assets
all_assets = finder.retrieve_all([sid1, sid2, ...])
```

**Notes:**
- Advanced API, typically not needed for simple strategies
- Useful for multi-asset strategies with dynamic universe
- AssetFinder is available via context in some Zipline versions

---

## Portfolio & Account APIs

### `context.portfolio`

**Purpose:** Access portfolio state and positions.

**Attributes:**
```python
context.portfolio.positions          # Dict of positions by asset
context.portfolio.positions[asset]  # Position object for asset
context.portfolio.cash               # Available cash
context.portfolio.portfolio_value   # Total portfolio value
context.portfolio.starting_cash      # Initial capital
context.portfolio.positions_value    # Total value of positions
```

**Examples:**
```python
# Check cash available
if context.portfolio.cash > 10000:
    order_target_percent(context.asset, 0.5)

# Get position for asset
position = context.portfolio.positions[context.asset]
if position:
    shares = position.amount
    cost_basis = position.cost_basis
    last_sale_price = position.last_sale_price

# Calculate portfolio metrics
total_value = context.portfolio.portfolio_value
cash_pct = context.portfolio.cash / total_value
```

**Position Object Attributes:**
```python
position.amount          # Number of shares (negative for short)
position.cost_basis      # Total cost of position
position.last_sale_price # Last sale price
position.asset           # Asset object
```

---

### `context.account`

**Purpose:** Access account-level information (brokerage account).

**Attributes:**
```python
context.account.buying_power    # Available buying power
context.account.total_position_value  # Total position value
context.account.regt_requirement # Regulatory requirement
context.account.equity_with_loan # Equity including loan
context.account.available_funds # Available funds
```

**Examples:**
```python
# Check buying power
if context.account.buying_power > 5000:
    # Can place order
    pass

# Calculate leverage
leverage = context.account.total_position_value / context.account.equity_with_loan
```

**Notes:**
- Account APIs are more relevant for live trading
- In backtesting, portfolio APIs are typically sufficient
- Account APIs provide margin/leverage information

---

## Order Management APIs

### `order()`

**Purpose:** Place a market order for a specific number of shares.

**Signature:**
```python
order(asset, amount) -> Order
```

**Examples:**
```python
# Buy 100 shares
order(context.asset, 100)

# Sell 50 shares (negative amount)
order(context.asset, -50)

# Close position
current_position = context.portfolio.positions[context.asset]
if current_position:
    order(context.asset, -current_position.amount)
```

**Return Type:** `Order` object

**Notes:**
- Positive amount = buy, negative = sell
- Market order (executes immediately at current price)
- Order object can be used to track/cancel

---

### `order_target()`

**Purpose:** Place order to achieve target number of shares.

**Signature:**
```python
order_target(asset, target) -> Order
```

**Examples:**
```python
# Target 100 shares
order_target(context.asset, 100)

# Close position (target 0)
order_target(context.asset, 0)

# Increase position to 200 shares
order_target(context.asset, 200)
```

**Return Type:** `Order` object

**Notes:**
- Calculates difference between current and target
- Places order for the difference
- More convenient than `order()` for target-based strategies

---

### `order_target_percent()`

**Purpose:** Place order to achieve target portfolio percentage.

**Signature:**
```python
order_target_percent(asset, target) -> Order
```

**Examples:**
```python
# Target 50% of portfolio
order_target_percent(context.asset, 0.5)

# Close position
order_target_percent(context.asset, 0.0)

# Full position (100%)
order_target_percent(context.asset, 1.0)
```

**Return Type:** `Order` object

**Notes:**
- Target is decimal (0.5 = 50%)
- Automatically calculates shares based on portfolio value
- Most common order API for percentage-based strategies

---

### `order_target_value()`

**Purpose:** Place order to achieve target dollar value.

**Signature:**
```python
order_target_value(asset, target) -> Order
```

**Examples:**
```python
# Target $10,000 position
order_target_value(context.asset, 10000)

# Close position
order_target_value(context.asset, 0)
```

**Return Type:** `Order` object

**Notes:**
- Target is dollar amount
- Useful for fixed-dollar strategies
- Less common than `order_target_percent()`

---

### `order_percent()`

**Purpose:** Place order for percentage of portfolio (additive).

**Signature:**
```python
order_percent(asset, percent) -> Order
```

**Examples:**
```python
# Add 10% to position
order_percent(context.asset, 0.1)

# Reduce position by 25%
order_percent(context.asset, -0.25)
```

**Return Type:** `Order` object

**Notes:**
- Additive (adds to current position)
- Percent is decimal (0.1 = 10%)
- Less common than `order_target_percent()`

---

### `order_value()`

**Purpose:** Place order for dollar value (additive).

**Signature:**
```python
order_value(asset, value) -> Order
```

**Examples:**
```python
# Buy $5,000 worth
order_value(context.asset, 5000)

# Sell $2,000 worth
order_value(context.asset, -2000)
```

**Return Type:** `Order` object

**Notes:**
- Additive (adds to current position)
- Value is dollar amount
- Less common than `order_target_value()`

---

### `get_open_orders()`

**Purpose:** Get list of open orders for an asset (or all assets).

**Signature:**
```python
get_open_orders(asset=None) -> list[Order]
```

**Examples:**
```python
# Get open orders for specific asset
open_orders = get_open_orders(context.asset)
for order in open_orders:
    cancel_order(order)

# Get all open orders
all_orders = get_open_orders()
```

**Return Type:** `list[Order]`

**Notes:**
- Returns list of Order objects
- Empty list if no open orders
- Useful for order management and cancellation

---

### `cancel_order()`

**Purpose:** Cancel an open order.

**Signature:**
```python
cancel_order(order) -> None
```

**Examples:**
```python
# Cancel specific order
order = order_target_percent(context.asset, 0.5)
cancel_order(order)

# Cancel all open orders for asset
for order in get_open_orders(context.asset):
    cancel_order(order)
```

**Return Type:** `None`

**Notes:**
- Cancels the order if still open
- No effect if order already filled or cancelled
- Common pattern: cancel before placing new order

---

### `get_order()`

**Purpose:** Get order by ID (advanced usage).

**Signature:**
```python
get_order(order_id) -> Order
```

**Examples:**
```python
# Store order ID
order = order_target_percent(context.asset, 0.5)
order_id = order.id

# Retrieve later
order = get_order(order_id)
if order.open:
    cancel_order(order)
```

**Return Type:** `Order` object

**Notes:**
- Advanced API for order tracking
- Typically not needed for simple strategies
- Useful for complex order management systems

---

## Execution Styles

Zipline-Reloaded supports multiple order execution styles beyond simple market orders. Execution styles control how and when orders are filled.

### `MarketOrder`

**Purpose:** Execute order immediately at current market price (default).

**Signature:**
```python
from zipline.finance.execution import MarketOrder

order(asset, amount, style=MarketOrder())
# Or simply (MarketOrder is default):
order(asset, amount)
```

**Examples:**
```python
from zipline.finance.execution import MarketOrder

# Explicit market order
order(context.asset, 100, style=MarketOrder())

# Market order is default, so this is equivalent:
order(context.asset, 100)

# With target functions
order_target_percent(context.asset, 0.5, style=MarketOrder())
```

**Notes:**
- Default execution style for all order functions
- Executes immediately at current price
- No price protection
- Most common for backtesting

---

### `LimitOrder`

**Purpose:** Execute order only at specified limit price or better.

**Signature:**
```python
from zipline.finance.execution import LimitOrder

order(asset, amount, style=LimitOrder(limit_price))
# Or use limit_price parameter:
order(asset, amount, limit_price=price)
```

**Examples:**
```python
from zipline.finance.execution import LimitOrder

# Buy at $100 or lower
current_price = data.current(context.asset, 'price')
limit_price = current_price * 0.98  # 2% below current
order(context.asset, 100, style=LimitOrder(limit_price))

# Sell at $110 or higher
order(context.asset, -50, limit_price=110)

# Using limit_price parameter (shorthand)
order_target_percent(context.asset, 0.5, limit_price=100)

# Limit order with target functions
order_target(context.asset, 200, limit_price=95)
```

**Notes:**
- For buys: executes at limit_price or lower
- For sells: executes at limit_price or higher
- Order may not fill if price never reaches limit
- Useful for price improvement and slippage reduction

---

### `StopOrder`

**Purpose:** Place market order when price reaches stop threshold.

**Signature:**
```python
from zipline.finance.execution import StopOrder

order(asset, amount, style=StopOrder(stop_price))
# Or use stop_price parameter:
order(asset, amount, stop_price=price)
```

**Examples:**
```python
from zipline.finance.execution import StopOrder

# Stop-loss: sell if price drops to $90
current_price = data.current(context.asset, 'price')
stop_loss = current_price * 0.90  # 10% stop loss
order(context.asset, -100, style=StopOrder(stop_loss))

# Stop-entry: buy if price breaks above $105
order(context.asset, 100, stop_price=105)

# Using stop_price parameter (shorthand)
order_target_percent(context.asset, 0.0, stop_price=90)  # Stop-loss exit
```

**Notes:**
- For sells: triggers when price falls to or below stop_price
- For buys: triggers when price rises to or above stop_price
- Converts to market order when triggered
- Common for stop-loss and breakout strategies

---

### `StopLimitOrder`

**Purpose:** Place limit order when price reaches stop threshold.

**Signature:**
```python
from zipline.finance.execution import StopLimitOrder

order(asset, amount, style=StopLimitOrder(limit_price, stop_price))
# Or use both parameters:
order(asset, amount, limit_price=limit, stop_price=stop)
```

**Examples:**
```python
from zipline.finance.execution import StopLimitOrder

# Stop-limit sell: if price drops to $90, sell at $89 or better
order(context.asset, -100, style=StopLimitOrder(limit_price=89, stop_price=90))

# Stop-limit buy: if price breaks $105, buy at $106 or better
order(context.asset, 100, limit_price=106, stop_price=105)

# Combined with target functions
order_target(context.asset, 0, limit_price=89, stop_price=90)
```

**Notes:**
- Combines stop trigger with limit price protection
- More control than StopOrder but may not fill
- Useful for precise entry/exit with price protection

---

## Order Cancellation Policies

Zipline-Reloaded provides policies to automatically cancel open orders at specific times.

### `set_cancel_policy()`

**Purpose:** Set automatic order cancellation policy.

**Signature:**
```python
from zipline.api import set_cancel_policy, EODCancel, NeverCancel

set_cancel_policy(cancel_policy)
```

**Examples:**
```python
from zipline.api import set_cancel_policy, EODCancel, NeverCancel

def initialize(context):
    # Cancel all orders at end of day (default for minute simulations)
    set_cancel_policy(EODCancel(warn_on_cancel=True))
    
    # Never automatically cancel orders
    set_cancel_policy(NeverCancel())
```

**Notes:**
- Set in `initialize()` function
- Applies to all orders placed during simulation
- Only affects minutely simulations (daily simulations don't need this)

---

### `EODCancel`

**Purpose:** Cancel all open orders at end of trading day.

**Signature:**
```python
from zipline.api import EODCancel

EODCancel(warn_on_cancel=True)
```

**Examples:**
```python
from zipline.api import set_cancel_policy, EODCancel

def initialize(context):
    # Cancel orders at end of day with warnings
    set_cancel_policy(EODCancel(warn_on_cancel=True))
    
    # Cancel silently
    set_cancel_policy(EODCancel(warn_on_cancel=False))
```

**Notes:**
- Default behavior for minutely simulations
- Prevents orders from carrying over to next day
- `warn_on_cancel=True` logs warnings when orders are cancelled

---

### `NeverCancel`

**Purpose:** Never automatically cancel orders (orders persist until filled or manually cancelled).

**Signature:**
```python
from zipline.api import NeverCancel

NeverCancel()
```

**Examples:**
```python
from zipline.api import set_cancel_policy, NeverCancel

def initialize(context):
    # Orders persist across days until filled
    set_cancel_policy(NeverCancel())
```

**Notes:**
- Orders remain open until filled or manually cancelled
- Useful for limit orders that should persist
- May cause unexpected behavior if not managed carefully

---

## Trading Controls

Zipline-Reloaded provides trading controls to enforce risk management and prevent unintended behavior.

### `set_max_order_size()`

**Purpose:** Set maximum shares or dollar value for individual orders.

**Signature:**
```python
set_max_order_size(
    asset=None,           # Asset-specific or all assets
    max_shares=None,     # Maximum shares per order
    max_notional=None,   # Maximum dollar value per order
    on_error='fail'      # 'fail' or 'warn'
)
```

**Examples:**
```python
def initialize(context):
    # Limit all orders to 1000 shares max
    set_max_order_size(max_shares=1000)
    
    # Limit all orders to $50,000 max value
    set_max_order_size(max_notional=50000)
    
    # Asset-specific limit
    set_max_order_size(
        asset=context.asset,
        max_shares=500,
        max_notional=25000
    )
    
    # Warn instead of fail
    set_max_order_size(max_shares=1000, on_error='warn')
```

**Notes:**
- Enforced at order placement time
- Prevents oversized orders
- `on_error='fail'` raises exception, `'warn'` logs warning

---

### `set_max_position_size()`

**Purpose:** Set maximum shares or dollar value for positions (not individual orders).

**Signature:**
```python
set_max_position_size(
    asset=None,           # Asset-specific or all assets
    max_shares=None,     # Maximum shares in position
    max_notional=None,   # Maximum dollar value in position
    on_error='fail'      # 'fail' or 'warn'
)
```

**Examples:**
```python
def initialize(context):
    # Limit position size to 5000 shares
    set_max_position_size(max_shares=5000)
    
    # Limit position value to $100,000
    set_max_position_size(max_notional=100000)
    
    # Asset-specific position limit
    set_max_position_size(
        asset=context.asset,
        max_shares=2000,
        max_notional=50000
    )
```

**Notes:**
- Enforced when order would increase position beyond limit
- Position can exceed limit due to splits/dividends (not prevented)
- Different from `set_max_order_size()` (which limits individual orders)

---

### `set_max_order_count()`

**Purpose:** Set maximum number of orders per day.

**Signature:**
```python
set_max_order_count(max_count, on_error='fail')
```

**Examples:**
```python
def initialize(context):
    # Maximum 10 orders per day
    set_max_order_count(10)
    
    # Warn instead of fail
    set_max_order_count(20, on_error='warn')
```

**Notes:**
- Prevents excessive trading
- Useful for controlling transaction costs
- Counts all orders placed in a single day

---

### `set_max_leverage()`

**Purpose:** Set maximum portfolio leverage.

**Signature:**
```python
set_max_leverage(max_leverage)
```

**Examples:**
```python
def initialize(context):
    # Maximum 2x leverage
    set_max_leverage(2.0)
    
    # No leverage limit (default)
    set_max_leverage(None)
```

**Notes:**
- Leverage = total_position_value / portfolio_value
- Prevents over-leveraged positions
- Useful for risk management

---

### `set_long_only()`

**Purpose:** Restrict algorithm to long positions only (no shorting).

**Signature:**
```python
set_long_only(on_error='fail')
```

**Examples:**
```python
def initialize(context):
    # Long-only strategy
    set_long_only()
    
    # Warn on short attempts instead of failing
    set_long_only(on_error='warn')
```

**Notes:**
- Prevents short positions
- Sell orders that would create shorts are rejected
- Useful for compliance or strategy constraints

---

### `set_do_not_order_list()`

**Purpose:** Restrict trading on specific assets (restricted list).

**Signature:**
```python
set_do_not_order_list(restricted_list, on_error='fail')
```

**Examples:**
```python
def initialize(context):
    # Restrict trading on specific assets
    restricted = [symbol('AAPL'), symbol('MSFT')]
    set_do_not_order_list(restricted)
    
    # Use SecurityList for dynamic restrictions
    from zipline.finance.asset_restrictions import SecurityList
    restricted_list = SecurityList(...)
    set_do_not_order_list(restricted_list)
```

**Notes:**
- Prevents orders on restricted assets
- Useful for compliance (insider trading restrictions, etc.)
- Can use SecurityList for dynamic restrictions

---

## Order Object

Order objects returned by order functions provide information about order status and properties.

### Order Attributes

```python
order.id              # Unique order identifier (str)
order.asset           # Asset object for this order
order.amount          # Number of shares ordered (int)
order.filled          # Number of shares filled (int)
order.status          # Order status (OPEN, FILLED, CANCELLED, etc.)
order.open            # Boolean: True if order is still open
order.stop_price      # Stop price if applicable (float or None)
order.limit_price     # Limit price if applicable (float or None)
order.created         # Timestamp when order was created
order.dt              # Datetime when order was placed
```

**Examples:**
```python
# Place order and check status
order = order_target_percent(context.asset, 0.5)

# Check if order is open
if order.open:
    print(f"Order {order.id} is still open")
    print(f"Filled: {order.filled} of {order.amount} shares")

# Access order properties
print(f"Asset: {order.asset.symbol}")
print(f"Created: {order.created}")
print(f"Limit price: {order.limit_price}")
```

**Notes:**
- Order objects are returned immediately after placing order
- Status updates as order is filled or cancelled
- Use `order.open` to check if order is still active

---

## Order Management Best Practices

### 1. Cancel Orders Before Placing New Ones

```python
# ✅ GOOD - Cancel existing orders first
for order in get_open_orders(context.asset):
    cancel_order(order)
order_target_percent(context.asset, 0.5)

# ❌ BAD - May have conflicting orders
order_target_percent(context.asset, 0.5)
order_target_percent(context.asset, 0.7)  # Multiple orders
```

### 2. Check Order Status Before Cancelling

```python
# ✅ GOOD - Check if order exists and is open
order = order_target_percent(context.asset, 0.5)
if order and order.open:
    cancel_order(order)

# ❌ BAD - May cancel already-filled order
order = order_target_percent(context.asset, 0.5)
cancel_order(order)  # Order may already be filled
```

### 3. Use Appropriate Execution Styles

```python
# ✅ GOOD - Limit order for price improvement
current_price = data.current(context.asset, 'price')
limit_price = current_price * 0.99  # 1% better
order(context.asset, 100, limit_price=limit_price)

# ✅ GOOD - Stop order for risk management
stop_loss = entry_price * 0.95  # 5% stop loss
order(context.asset, -position.amount, stop_price=stop_loss)

# ❌ BAD - Market order when limit would work
order(context.asset, 100)  # May get worse price
```

### 4. Handle Order Fills Gracefully

```python
# ✅ GOOD - Check fill status
order = order_target_percent(context.asset, 0.5)
if order.filled < order.amount:
    # Order partially filled, handle accordingly
    remaining = order.amount - order.filled
    logger.info(f"Order partially filled: {order.filled}/{order.amount}")

# ❌ BAD - Assume order filled immediately
order = order_target_percent(context.asset, 0.5)
# Order may not be filled yet!
```

### 5. Use Trading Controls for Risk Management

```python
# ✅ GOOD - Set position limits
def initialize(context):
    set_max_position_size(max_notional=100000)  # $100k max position
    set_max_order_size(max_shares=1000)         # 1000 shares max per order
    set_max_leverage(2.0)                        # 2x max leverage

# ❌ BAD - No risk controls
def initialize(context):
    # No limits - dangerous!
    pass
```

### 6. Manage Order Cancellation Policy

```python
# ✅ GOOD - Set appropriate cancellation policy
def initialize(context):
    # For intraday strategies, cancel at end of day
    set_cancel_policy(EODCancel(warn_on_cancel=True))
    
    # For limit orders that should persist
    # set_cancel_policy(NeverCancel())

# ❌ BAD - Default behavior may not match strategy
def initialize(context):
    # May have unexpected order behavior
    pass
```

---

## Order Management Patterns

### Pattern 1: Cancel and Replace

```python
def rebalance(context, data):
    # Cancel existing orders
    for order in get_open_orders(context.asset):
        cancel_order(order)
    
    # Place new order
    order_target_percent(context.asset, 0.5)
```

### Pattern 2: Stop-Loss Management

```python
def manage_stop_loss(context, data):
    position = context.portfolio.positions[context.asset]
    if position and position.amount > 0:
        current_price = data.current(context.asset, 'price')
        entry_price = position.cost_basis / position.amount
        stop_loss = entry_price * 0.95  # 5% stop loss
        
        # Cancel existing stop orders
        for order in get_open_orders(context.asset):
            if order.stop_price:
                cancel_order(order)
        
        # Place new stop-loss order
        order(context.asset, -position.amount, stop_price=stop_loss)
```

### Pattern 3: Limit Order Entry

```python
def limit_order_entry(context, data):
    if not data.can_trade(context.asset):
        return
    
    current_price = data.current(context.asset, 'price')
    
    # Only place limit order if no existing orders
    if not get_open_orders(context.asset):
        # Buy at 2% below current price
        limit_price = current_price * 0.98
        order(context.asset, 100, limit_price=limit_price)
```

### Pattern 4: Order Status Tracking

```python
def track_orders(context, data):
    # Store order IDs for tracking
    if not hasattr(context, 'pending_orders'):
        context.pending_orders = {}
    
    # Check status of pending orders
    for order_id, order_info in list(context.pending_orders.items()):
        order = get_order(order_id)
        if not order.open:
            # Order filled or cancelled
            del context.pending_orders[order_id]
            if order.status == 'FILLED':
                logger.info(f"Order {order_id} filled: {order.filled} shares")
```

---

## Pipeline APIs

### `attach_pipeline()`

**Purpose:** Attach a Pipeline to the algorithm.

**Signature:**
```python
attach_pipeline(pipeline, name, chunksize=None) -> None
```

**Examples:**
```python
from zipline.api import attach_pipeline
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    return Pipeline(columns={'sma_30': sma})

def initialize(context):
    pipeline = make_pipeline()
    attach_pipeline(pipeline, 'my_pipeline')
```

**Return Type:** `None`

**Notes:**
- Pipeline must be attached in `initialize()`
- Name is used to retrieve output later
- Pipeline runs before `before_trading_start()`
- Primarily designed for US equities

---

### `pipeline_output()`

**Purpose:** Get Pipeline output data.

**Signature:**
```python
pipeline_output(name) -> pd.DataFrame
```

**Examples:**
```python
def before_trading_start(context, data):
    # Get pipeline output
    pipeline_data = pipeline_output('my_pipeline')
    
    # Access factor values
    for asset in pipeline_data.index:
        sma_value = pipeline_data.loc[asset, 'sma_30']
        if sma_value > threshold:
            order_target_percent(asset, 0.1)
```

**Return Type:** `pd.DataFrame` with assets as index and factors as columns

**Notes:**
- Must be called in `before_trading_start()` or later
- Returns DataFrame with factor values for all assets
- Index contains Asset objects
- Columns are factor names from Pipeline

---

### Pipeline Factors

**Common Built-in Factors:**
```python
from zipline.pipeline.factors import (
    SimpleMovingAverage,
    ExponentialMovingAverage,
    AverageDollarVolume,
    Returns,
    RSI,
    MACD,
    BollingerBands,
    # ... many more
)
```

**Examples:**
```python
from zipline.pipeline.factors import SimpleMovingAverage, AverageDollarVolume
from zipline.pipeline.data import EquityPricing

# Simple moving average
sma_50 = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=50)

# Average dollar volume (liquidity filter)
avg_dollar_volume = AverageDollarVolume(window_length=30)

# Combine in pipeline
universe = avg_dollar_volume.top(500)  # Top 500 by liquidity
pipeline = Pipeline(columns={'sma_50': sma_50}, screen=universe)
```

**Notes:**
- Factors compute values for all assets in universe
- Window length is in bars (days for daily data)
- Factors can be combined and used in screens
- Custom factors can be created via `CustomFactor`

---

### Pipeline Filters

**Purpose:** Filter assets in Pipeline universe.

**Examples:**
```python
from zipline.pipeline.filters import StaticAssets, StaticSids

# Static asset list
universe = StaticAssets([asset1, asset2, asset3])

# By SID
universe = StaticSids([1, 2, 3])

# Combined with factors
liquid_stocks = AverageDollarVolume(window_length=30).top(500)
pipeline = Pipeline(screen=liquid_stocks)
```

**Notes:**
- Filters determine which assets appear in pipeline output
- Can be combined with boolean operators (`&`, `|`, `~`)
- Screens are applied after factor computation

---

## Calendar & Scheduling APIs

### `schedule_function()`

**Purpose:** Schedule a function to run at specific times.

**Signature:**
```python
schedule_function(
    func,
    date_rule,
    time_rule,
    half_days=True
) -> None
```

**Examples:**
```python
from zipline.api import schedule_function, date_rules, time_rules

# Daily at market open + 30 minutes
schedule_function(
    rebalance,
    date_rule=date_rules.every_day(),
    time_rule=time_rules.market_open(minutes=30)
)

# Weekly on Monday
schedule_function(
    weekly_rebalance,
    date_rule=date_rules.week_start(days_offset=0),
    time_rule=time_rules.market_open()
)

# Monthly on first trading day
schedule_function(
    monthly_rebalance,
    date_rule=date_rules.month_start(days_offset=0),
    time_rule=time_rules.market_open()
)

# End of day
schedule_function(
    end_of_day_cleanup,
    date_rule=date_rules.every_day(),
    time_rule=time_rules.market_close()
)
```

**Date Rules:**
```python
date_rules.every_day()
date_rules.week_start(days_offset=0)
date_rules.week_end(days_offset=0)
date_rules.month_start(days_offset=0)
date_rules.month_end(days_offset=0)
date_rules.every_week(weekday=0)  # 0=Monday
```

**Time Rules:**
```python
time_rules.market_open(minutes=0)
time_rules.market_close(minutes=0)
time_rules.every_minute()
```

**Notes:**
- Functions are called automatically at scheduled times
- More efficient than checking time in `handle_data()`
- Multiple functions can be scheduled
- Time rules respect trading calendar

---

### `get_calendar()`

**Purpose:** Get trading calendar by name.

**Signature:**
```python
from zipline.utils.calendar_utils import get_calendar

calendar = get_calendar(calendar_name)
```

**Examples:**
```python
from zipline.utils.calendar_utils import get_calendar

# Get custom calendars
forex_calendar = get_calendar('FOREX')
crypto_calendar = get_calendar('CRYPTO')

# Get exchange calendars
nyse_calendar = get_calendar('NYSE')
nasdaq_calendar = get_calendar('NASDAQ')

# Use calendar methods
sessions = forex_calendar.sessions_in_range(start_date, end_date)
is_open = forex_calendar.is_open_on_session(session_date)
```

**Calendar Methods:**
```python
calendar.sessions_in_range(start, end)  # Get all sessions
calendar.is_open_on_session(date)       # Check if date is trading day
calendar.previous_session(date)          # Previous trading day
calendar.next_session(date)              # Next trading day
calendar.minute_to_session_label(minute) # Convert minute to session
```

**Notes:**
- Custom calendars (FOREX, CRYPTO) must be registered in extension.py
- Exchange calendars (NYSE, NASDAQ) are built-in
- Calendar determines trading sessions and market hours

---

## Bundle Management APIs

### Direct Bundle Access

**Purpose:** Access bundles dictionary directly (v1.12.0+ NO WRAPPERS).

**Examples:**
```python
from zipline.data.bundles import bundles

# List all bundles
bundle_names = list(bundles.keys())
print(f"Available bundles: {bundle_names}")

# Access bundle data
bundle_data = bundles['eurusd_1m']

# Check bundle metadata
if hasattr(bundle_data, 'equity_daily_bar_reader'):
    reader = bundle_data.equity_daily_bar_reader
    start = reader.first_trading_day
    end = reader.last_available_dt
```

**Notes:**
- Direct access to Zipline's bundles dictionary
- No wrapper functions needed (v1.12.0+)
- Bundle registration done in `~/.zipline/extension.py`
- Bundle data structure varies by source

---

### Bundle Registration (in extension.py)

**Purpose:** Register bundles in `~/.zipline/extension.py`.

**Examples:**
```python
# CSV bundle registration
from zipline.data.bundles.csvdir import csvdir_equities
from zipline.data.bundles import register
from zipline.utils.calendar_utils import get_calendar

# Register CSV bundle
register(
    'eurusd_1m',
    csvdir_equities(
        ['EURUSD'],
        '/path/to/data/csvdir',
    ),
    calendar_name='FOREX'
)

# Register Yahoo bundle
from zipline.data.bundles import yahoo_equities
register(
    'yahoo_btc_daily',
    yahoo_equities(['BTC-USD'], start_date='2020-01-01'),
    calendar_name='CRYPTO'
)
```

**Notes:**
- All bundle registration in extension.py (v1.12.0+)
- No wrapper functions for registration
- Calendar must match asset class
- Bundle names should be `{symbol}_{timeframe}` format

---

## Commission & Slippage APIs

### `set_commission()`

**Purpose:** Set commission model for trades.

**Signature:**
```python
from zipline.api import set_commission
from zipline.finance import commission

set_commission(
    us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0),
    # ... other asset types
)
```

**Examples:**
```python
from zipline.api import set_commission
from zipline.finance import commission

# Per-share commission
set_commission(
    us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0)
)

# Percentage commission (for forex/crypto)
set_commission(
    us_equities=commission.PerTrade(cost=5.0)  # $5 per trade
)

# Custom commission
set_commission(
    us_equities=commission.PerDollar(cost=0.0015)  # 0.15% per dollar
)
```

**Commission Types:**
```python
commission.PerShare(cost, min_trade_cost)  # Per share + minimum
commission.PerTrade(cost)                  # Fixed per trade
commission.PerDollar(cost)                 # Percentage of trade value
```

**Notes:**
- Set in `initialize()` function
- Different models for different asset types
- Affects backtest realism
- Default is PerShare(cost=0.005, min_trade_cost=1.0)

---

### `set_slippage()`

**Purpose:** Set slippage model for trades.

**Signature:**
```python
from zipline.api import set_slippage
from zipline.finance import slippage

set_slippage(
    us_equities=slippage.VolumeShareSlippage(volume_limit=0.025, price_impact=0.1),
    # ... other asset types
)
```

**Examples:**
```python
from zipline.api import set_slippage
from zipline.finance import slippage

# Volume-based slippage
set_slippage(
    us_equities=slippage.VolumeShareSlippage(
        volume_limit=0.025,    # Max 2.5% of daily volume
        price_impact=0.1      # 10% price impact
    )
)

# Fixed slippage (for forex/crypto)
set_slippage(
    us_equities=slippage.FixedSlippage(spread=0.0001)  # 1 pip for forex
)
```

**Slippage Types:**
```python
slippage.VolumeShareSlippage(volume_limit, price_impact)
slippage.FixedSlippage(spread)
slippage.VolatilityVolumeShare(volume_limit)
```

**Notes:**
- Set in `initialize()` function
- Models market impact of large orders
- VolumeShareSlippage is most realistic for equities
- FixedSlippage is common for forex/crypto (spread-based)

---

## Recording & Metrics APIs

### `record()`

**Purpose:** Record custom metrics for later analysis.

**Signature:**
```python
record(**kwargs) -> None
```

**Examples:**
```python
from zipline.api import record

# Record single values
record(price=data.current(context.asset, 'price'))
record(signal=1, sma_50=100.5, rsi=45.2)

# Record in rebalance function
def rebalance(context, data):
    signal, indicators = compute_signals(context, data)
    record(
        signal=signal,
        price=data.current(context.asset, 'price'),
        sma_short=indicators['sma_short'],
        sma_long=indicators['sma_long'],
        rsi=indicators['rsi']
    )
```

**Return Type:** `None`

**Notes:**
- Values are stored in performance DataFrame
- Accessible in `analyze()` function via `perf` DataFrame
- Useful for debugging and analysis
- Can record any numeric values

---

### `set_benchmark()`

**Purpose:** Set benchmark asset for performance comparison.

**Signature:**
```python
set_benchmark(asset) -> None
```

**Examples:**
```python
from zipline.api import set_benchmark, symbol

def initialize(context):
    context.asset = symbol('AAPL')
    set_benchmark(context.asset)  # Compare to AAPL
    
    # Or use different benchmark
    spy = symbol('SPY')
    set_benchmark(spy)  # Compare to S&P 500
```

**Return Type:** `None`

**Notes:**
- Set in `initialize()` function
- Used for alpha/beta calculations
- Default is S&P 500 (SPY)
- Benchmark returns included in performance DataFrame

---

## Utility APIs

### `context.current_dt`

**Purpose:** Get current algorithm datetime.

**Examples:**
```python
# Current datetime
current_time = context.current_dt

# Check time of day
if current_time.hour == 9 and current_time.minute == 30:
    # Market open logic
    pass

# Check day of week
if current_time.weekday() == 0:  # Monday
    # Weekly logic
    pass
```

**Return Type:** `pd.Timestamp`

**Notes:**
- Timezone-naive (UTC in v1.0.3+)
- Updates each bar
- Useful for time-based logic

---

### `data.current_dt`

**Purpose:** Get current data datetime (same as context.current_dt).

**Examples:**
```python
# Current datetime from data object
current_time = data.current_dt

# Use in data queries
prev_day = current_time - pd.Timedelta(days=1)
```

**Return Type:** `pd.Timestamp`

**Notes:**
- Alias for `context.current_dt`
- Same value, different access point
- Use whichever is more convenient

---

## Best Practices

### 1. Always Check `data.can_trade()`

```python
# ✅ GOOD
if data.can_trade(context.asset):
    order_target_percent(context.asset, 0.5)

# ❌ BAD
order_target_percent(context.asset, 0.5)  # May fail if asset not tradeable
```

### 2. Handle Insufficient Data

```python
# ✅ GOOD
try:
    prices = data.history(context.asset, 'close', 100, '1d')
    if len(prices) < 100:
        return  # Not enough data
    sma = prices.mean()
except (KeyError, ValueError):
    return  # Data unavailable

# ❌ BAD
prices = data.history(context.asset, 'close', 100, '1d')
sma = prices.mean()  # May fail if insufficient data
```

### 3. Use Appropriate Frequency

```python
# ✅ GOOD - Match bundle frequency
# Bundle is daily
prices = data.history(context.asset, 'close', 30, '1d')

# Bundle is minute, aggregate to hourly
minute_data = data.history(context.asset, 'close', 1440, '1m')
hourly_data = minute_data.resample('1h').last()  # Direct pandas

# ❌ BAD - Requesting unavailable frequency
prices = data.history(context.asset, 'close', 30, '1h')  # If bundle is daily
```

### 4. Cancel Orders Before New Ones

```python
# ✅ GOOD
# Cancel existing orders
for order in get_open_orders(context.asset):
    cancel_order(order)

# Place new order
order_target_percent(context.asset, 0.5)

# ❌ BAD
order_target_percent(context.asset, 0.5)  # May have conflicting orders
order_target_percent(context.asset, 0.7)  # Multiple orders
```

### 5. Use `schedule_function()` Instead of Time Checks

```python
# ✅ GOOD
def initialize(context):
    schedule_function(
        rebalance,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.market_open(minutes=30)
    )

# ❌ BAD
def handle_data(context, data):
    if data.current_dt.hour == 9 and data.current_dt.minute == 30:
        rebalance(context, data)  # Less efficient
```

### 6. Direct Pandas for Aggregation (v1.12.0+)

```python
# ✅ GOOD - Direct pandas (v1.12.0+)
minute_data = data.history(context.asset, ['open', 'high', 'low', 'close'], 1440, '1m')
hourly_data = minute_data.resample('1h').agg({
    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
})

# ❌ BAD - Wrapper function (removed in v1.12.0)
# hourly_data = aggregate_ohlcv(minute_data, '1h')  # NO WRAPPERS
```

---

## Common Patterns

### Pattern 1: Simple Moving Average Crossover

```python
def compute_signals(context, data):
    if not data.can_trade(context.asset):
        return 0, {}
    
    # Get prices
    prices = data.history(context.asset, 'close', 50, '1d')
    
    if len(prices) < 50:
        return 0, {}
    
    # Calculate SMAs
    sma_short = prices.tail(20).mean()
    sma_long = prices.mean()
    
    # Generate signal
    signal = 1 if sma_short > sma_long else -1
    
    return signal, {'sma_short': sma_short, 'sma_long': sma_long}
```

### Pattern 2: Multi-Timeframe Analysis

```python
def analyze_multi_timeframe(context, data):
    # Get minute data
    minute_data = data.history(
        context.asset,
        ['open', 'high', 'low', 'close'],
        1440,  # 24 hours
        '1m'
    )
    
    # Aggregate to different timeframes
    hourly = minute_data.resample('1h').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
    })
    
    daily = minute_data.resample('1d').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
    })
    
    # Analyze trends
    hourly_trend = hourly['close'].iloc[-1] > hourly['close'].mean()
    daily_trend = daily['close'].iloc[-1] > daily['close'].mean()
    
    # Signal only when both align
    return 1 if (hourly_trend and daily_trend) else 0
```

### Pattern 3: Pipeline-Based Multi-Asset Strategy

```python
def make_pipeline():
    from zipline.pipeline import Pipeline
    from zipline.pipeline.factors import SimpleMovingAverage, AverageDollarVolume
    from zipline.pipeline.data import EquityPricing
    
    # Factors
    sma_50 = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=50)
    avg_volume = AverageDollarVolume(window_length=30)
    
    # Screen: Top 500 by liquidity
    universe = avg_volume.top(500)
    
    return Pipeline(
        columns={'sma_50': sma_50, 'avg_volume': avg_volume},
        screen=universe
    )

def before_trading_start(context, data):
    pipeline_data = pipeline_output('my_pipeline')
    context.pipeline_universe = pipeline_data.index.tolist()

def rebalance(context, data):
    # Trade top 10 by SMA
    pipeline_data = pipeline_output('my_pipeline')
    top_10 = pipeline_data.nlargest(10, 'sma_50')
    
    for asset in top_10.index:
        order_target_percent(asset, 0.1)  # 10% each
```

### Pattern 4: Position Sizing with Risk Management

```python
def rebalance(context, data):
    if not data.can_trade(context.asset):
        return
    
    # Calculate position size based on volatility
    prices = data.history(context.asset, 'close', 30, '1d')
    volatility = prices.pct_change().std()
    
    # Risk-based position sizing (2% risk per trade)
    risk_per_trade = 0.02
    position_size = risk_per_trade / volatility if volatility > 0 else 0
    
    # Cap at 50% of portfolio
    position_size = min(position_size, 0.5)
    
    order_target_percent(context.asset, position_size)
```

### Pattern 5: Session-Based Trading (Forex)

```python
def initialize(context):
    schedule_function(
        check_sessions,
        date_rule=date_rules.every_day(),
        time_rule=time_rules.every_minute()
    )

def check_sessions(context, data):
    current_time = data.current_dt
    hour = current_time.hour
    
    # Only trade during London/NY overlap
    if 13 <= hour < 16:  # UTC overlap hours
        if data.can_trade(context.asset):
            # Trading logic
            pass
```

---

## API Summary Table

| API | Module | Purpose | Return Type |
|-----|--------|---------|-------------|
| `data.history()` | `zipline.api` | Historical price data | `pd.DataFrame` |
| `data.current()` | `zipline.api` | Current price | `float` |
| `data.can_trade()` | `zipline.api` | Check tradeability | `bool` |
| `data.is_stale()` | `zipline.api` | Check data freshness | `bool` |
| `symbol()` | `zipline.api` | Create asset | `Asset` |
| `order()` | `zipline.api` | Place order | `Order` |
| `order_target()` | `zipline.api` | Target shares | `Order` |
| `order_target_percent()` | `zipline.api` | Target percentage | `Order` |
| `get_open_orders()` | `zipline.api` | List open orders | `list[Order]` |
| `cancel_order()` | `zipline.api` | Cancel order | `None` |
| `schedule_function()` | `zipline.api` | Schedule function | `None` |
| `attach_pipeline()` | `zipline.api` | Attach pipeline | `None` |
| `pipeline_output()` | `zipline.api` | Get pipeline data | `pd.DataFrame` |
| `record()` | `zipline.api` | Record metrics | `None` |
| `set_commission()` | `zipline.api` | Set commission | `None` |
| `set_slippage()` | `zipline.api` | Set slippage | `None` |
| `set_benchmark()` | `zipline.api` | Set benchmark | `None` |
| `get_calendar()` | `zipline.utils.calendar_utils` | Get calendar | `TradingCalendar` |

---

## Additional Data Access Notes

### Data Adjustment Behavior

All data returned by `data.history()`, `data.current()`, and `data.get_spot_value()` is automatically adjusted for:
- **Stock Splits**: Price fields are multiplied by split ratio, volume is divided
- **Dividends**: Price fields are adjusted to reflect dividend impact
- **Mergers**: Price fields are adjusted by merger ratio
- **Stock Dividends**: Position adjustments handled automatically

Adjustments are applied as of the current simulation time, ensuring no look-ahead bias.

### Data Frequency Considerations

- **Daily Data**: Use `frequency='1d'` for daily bars. Bundle must contain daily data or be aggregatable from minute data.
- **Minute Data**: Use `frequency='1m'` for minute bars. Bundle must contain minute data.
- **Aggregation**: For multi-timeframe analysis, use direct pandas operations:
  ```python
  minute_data = data.history(asset, 'close', 1440, '1m')
  hourly_data = minute_data.resample('1h').last()
  daily_data = minute_data.resample('1d').last()
  ```

### Missing Data Handling

- **NaN Values**: Returned for dates/assets with no available data
- **Forward Filling**: The 'price' field is forward-filled from earlier minutes if no trade occurred
- **Volume**: Returns 0 (not NaN) if no trades occurred in the current bar
- **Last Traded**: Returns `pd.NaT` if asset has never traded

### Performance Considerations

- **Caching**: Zipline caches recent data for performance
- **Batch Queries**: Requesting multiple assets/fields in one call is more efficient than multiple single calls
- **Window Size**: Larger `bar_count` values require more memory but enable longer lookback periods

## References

- **GitHub Repository:** https://github.com/stefan-jansen/zipline-reloaded
- **Project Architecture:** See `CLAUDE.md` for v1.12.0 NO WRAPPERS directive
- **Strategy Template:** `strategies/_template/strategy.py` for usage examples

---

**Last Updated:** 2026-01-27  
**Version:** v1.12.0+ (NO WRAPPERS Architecture)  
**Zipline-Reloaded Version:** 3.1.1 (verified)  
**Status:** Comprehensive inventory of Zipline-Reloaded data access APIs  
**Source:** Official API Reference (https://zipline.ml4trading.io/api-reference.html)
