# Strategy Creator Guide — AI Agent Instructions

> Step-by-step guide for creating new trading strategies in The Researcher's Cockpit.

---

## Overview

When creating a new strategy, you're translating a trading hypothesis into executable Zipline code. This process requires:

1. **Hypothesis documentation** — What are we testing?
2. **Parameter configuration** — What values to use?
3. **Strategy implementation** — How to execute the logic?

---

## Pre-Flight Checklist

Before starting, verify:

- [ ] Strategy name follows conventions (`{asset}_{strategy_type}`)
- [ ] Target asset class exists (`crypto`, `forex`, or `equities`)
- [ ] Template directory exists (`strategies/_template/`)
- [ ] Asset configuration exists (`config/assets/{asset_class}.yaml`)

---

## Step-by-Step Process

### Step 1: Create Strategy Directory

**Action:** Copy the template directory to the target location

```bash
# Determine asset class and strategy name
ASSET_CLASS="crypto"  # or "forex" or "equities"
STRATEGY_NAME="btc_sma_cross"

# Copy template
cp -r strategies/_template strategies/${ASSET_CLASS}/${STRATEGY_NAME}
```

**Verification:**
```bash
ls strategies/${ASSET_CLASS}/${STRATEGY_NAME}/
# Should show: strategy.py, hypothesis.md, parameters.yaml
```

---

### Step 2: Document the Hypothesis

**File:** `strategies/{asset_class}/{strategy_name}/hypothesis.md`

**Required Sections:**

1. **The Belief** — What market behavior are we exploiting?
2. **The Reasoning** — Why does this behavior exist?
3. **The Conditions** — When should this work/fail?
4. **The Falsification** — What would prove this wrong?
5. **Implementation Notes** — How is this coded?
6. **Expected Outcomes** — Success criteria

**Example Structure:**

```markdown
# Strategy Hypothesis

## The Belief
BTC price trends persist for 15-30 days after a moving average crossover.

## The Reasoning
- Retail FOMO creates momentum after breakouts
- Institutional rebalancing creates mean reversion boundaries

## The Conditions
**Works well in:**
- Trending markets
- High volatility environments

**Fails in:**
- Choppy, sideways markets
- Low liquidity periods

## The Falsification
If Sharpe < 0.5 across 3+ years of data, the edge doesn't exist.

## Implementation Notes
- Use fast SMA (10-day) and slow SMA (30-day) crossovers
- Enter on golden cross, exit on death cross
- Apply 200-day trend filter

## Expected Outcomes
- Sharpe Ratio > 1.0
- Maximum Drawdown < 20%
- Win Rate > 50%
```

**Critical:** Every strategy MUST have a hypothesis.md file. This is non-negotiable.

---

### Step 3: Configure Parameters

**File:** `strategies/{asset_class}/{strategy_name}/parameters.yaml`

**Required Sections:**

1. `strategy` — Strategy-specific parameters
2. `position_sizing` — Position sizing rules
3. `risk` — Risk management (stops, limits)
4. `costs` — Commission and slippage (optional, overrides defaults)

**Example:**

```yaml
strategy:
  asset_symbol: BTC-USD
  rebalance_frequency: daily
  minutes_after_open: 30
  
  # Strategy-specific parameters
  fast_period: 10
  slow_period: 30
  trend_filter_period: 200

position_sizing:
  max_position_pct: 0.95
  method: fixed

risk:
  use_stop_loss: true
  stop_loss_pct: 0.05
```

**Rules:**
- NO hardcoded parameters in strategy.py
- All tunable values come from parameters.yaml
- Use asset config defaults when possible (`config/assets/{asset_class}.yaml`)

---

### Step 4: Implement Strategy Logic

**File:** `strategies/{asset_class}/{strategy_name}/strategy.py`

**Required Functions:**

1.  `load_params()` — Load from parameters.yaml
2.  `make_pipeline()` — (Optional) Define and return a Zipline Pipeline object
3.  `initialize(context)` — Set up strategy, including `attach_pipeline()` if using Pipeline API
4.  `before_trading_start(context, data)` — (Optional) Fetch `pipeline_output()` if using Pipeline API
5.  `compute_signals(context, data)` — Calculate trading signals, utilizing pipeline data if available
6.  `rebalance(context, data)` — Execute trades
7.  `handle_data(context, data)` — Optional intra-bar logic
8.  `analyze(context, perf)` — Post-backtest analysis

**Implementation Pattern:**

```python
def initialize(context):
    """Set up the strategy."""
    params = load_params()
    context.params = params
    context.asset = symbol(params['strategy']['asset_symbol'])
    
    # Initialize state
    context.in_position = False
    context.pipeline_data = None # Initialize for pipeline usage

    # Attach Pipeline if defined (assuming make_pipeline() is in strategy.py)
    # If not using Pipeline, the `attach_pipeline` call will safely no-op.
    attach_pipeline(make_pipeline(), 'my_pipeline')

    # Configure costs
    set_commission(...)
    set_slippage(...)
    
    # Schedule functions
    schedule_function(rebalance, ...)

def before_trading_start(context, data):
    """Called once per day before market open (if a Pipeline is attached)."""
    # Fetch pipeline output and store in context.
    # This will populate context.pipeline_data and context.pipeline_universe
    # if a pipeline named 'my_pipeline' was attached in initialize.
    context.pipeline_data = pipeline_output('my_pipeline')
    if context.pipeline_data is not None:
        context.pipeline_universe = context.pipeline_data.index.tolist()
    else:
        context.pipeline_universe = []

def compute_signals(context, data):
    """Compute trading signals, utilizing pipeline data if available."""
    if not data.can_trade(context.asset):
        return 0, {}
    
    # Example: Access pre-computed factors from the pipeline for universe selection or signal generation
    if context.asset in context.pipeline_universe and context.pipeline_data is not None:
        # Access factors by column name, e.g., momentum_10 = context.pipeline_data.loc[context.asset]['momentum_10']
        pass
    
    # Get price history (if not solely relying on pipeline data)
    lookback = context.params['strategy']['slow_period'] + 5
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return 0, {}
    
    # Calculate indicators
    fast_period = context.params['strategy']['fast_period']
    slow_period = context.params['strategy']['slow_period']
    
    fast_sma = prices[-fast_period:].mean()
    slow_sma = prices[-slow_period:].mean()
    
    # Previous values for crossover detection
    fast_sma_prev = prices[-(fast_period + 1):-1].mean()
    slow_sma_prev = prices[-(slow_period + 1):-1].mean()
    
    # Generate signal
    signal = 0
    if fast_sma > slow_sma and fast_sma_prev <= slow_sma_prev:
        signal = 1  # Buy
    elif fast_sma < slow_sma and fast_sma_prev >= slow_sma_prev:
        signal = -1  # Sell
    
    return signal, {'fast_sma': fast_sma, 'slow_sma': slow_sma}

def rebalance(context, data):
    """Main rebalancing function."""
    signal, additional_data = compute_signals(context, data)
    
    if signal is None:
        return
    
    # Record metrics
    record(signal=signal, price=data.current(context.asset, 'price'), **additional_data)
    
    # Execute trades
    max_position = context.params['position_sizing']['max_position_pct']
    
    if signal == 1 and not context.in_position:
        order_target_percent(context.asset, max_position)
        context.in_position = True
    elif signal == -1 and context.in_position:
        order_target_percent(context.asset, 0)
        context.in_position = False
```

**Critical Rules:**
- Load ALL parameters from YAML, never hardcode
- Check `data.can_trade()` before accessing data
- Verify sufficient history before calculations
- Handle edge cases (insufficient data, market closed, etc.)

---

### Step 5: Validate Strategy

**Syntax Check:**

```bash
python -m py_compile strategies/${ASSET_CLASS}/${STRATEGY_NAME}/strategy.py
```

**Import Check:**

```bash
python -c "
import sys
sys.path.insert(0, 'strategies/${ASSET_CLASS}/${STRATEGY_NAME}')
import strategy
print('Imports successful')
"
```

**YAML Validation:**

```bash
python -c "
import yaml
with open('strategies/${ASSET_CLASS}/${STRATEGY_NAME}/parameters.yaml') as f:
    params = yaml.safe_load(f)
    print('YAML valid')
    print(f\"Asset: {params['strategy']['asset_symbol']}\")
"
```

**Required Files Check:**

```bash
# All three files must exist
test -f strategies/${ASSET_CLASS}/${STRATEGY_NAME}/strategy.py || echo "MISSING: strategy.py"
test -f strategies/${ASSET_CLASS}/${STRATEGY_NAME}/hypothesis.md || echo "MISSING: hypothesis.md"
test -f strategies/${ASSET_CLASS}/${STRATEGY_NAME}/parameters.yaml || echo "MISSING: parameters.yaml"
```

---

### Step 6: Create Results Symlink

**Action:** Create symlink from strategy directory to results directory

```bash
# Create results directory if it doesn't exist
mkdir -p results/${STRATEGY_NAME}

# Create symlink
cd strategies/${ASSET_CLASS}/${STRATEGY_NAME}
ln -s ../../../results/${STRATEGY_NAME} results
```

**Note:** This is usually done automatically by the backtest runner, but you can create it manually.

---

## Common Patterns

### Moving Average Crossover

```python
def compute_signals(context, data):
    fast_period = context.params['strategy']['fast_period']
    slow_period = context.params['strategy']['slow_period']
    
    prices = data.history(context.asset, 'price', slow_period + 5, '1d')
    
    fast_sma = prices[-fast_period:].mean()
    slow_sma = prices[-slow_period:].mean()
    fast_sma_prev = prices[-(fast_period + 1):-1].mean()
    slow_sma_prev = prices[-(slow_period + 1):-1].mean()
    
    signal = 0
    if fast_sma > slow_sma and fast_sma_prev <= slow_sma_prev:
        signal = 1
    elif fast_sma < slow_sma and fast_sma_prev >= slow_sma_prev:
        signal = -1
    
    return signal, {'fast_sma': fast_sma, 'slow_sma': slow_sma}
```

### RSI Mean Reversion

```python
def compute_signals(context, data):
    rsi_period = context.params['strategy']['rsi_period']
    oversold = context.params['strategy']['rsi_oversold']
    overbought = context.params['strategy']['rsi_overbought']
    
    prices = data.history(context.asset, 'price', rsi_period + 5, '1d')
    returns = prices.pct_change()
    
    # Calculate RSI
    gains = returns.where(returns > 0, 0)
    losses = -returns.where(returns < 0, 0)
    avg_gain = gains.rolling(rsi_period).mean().iloc[-1]
    avg_loss = losses.rolling(rsi_period).mean().iloc[-1]
    
    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    signal = 0
    if rsi < oversold:
        signal = 1  # Buy oversold
    elif rsi > overbought:
        signal = -1  # Sell overbought
    
    return signal, {'rsi': rsi}
```

### Breakout Strategy

```python
def compute_signals(context, data):
    lookback = context.params['strategy']['lookback_period']
    threshold = context.params['strategy']['breakout_threshold']
    
    prices = data.history(context.asset, 'price', lookback + 5, '1d')
    
    high = prices[-lookback:].max()
    low = prices[-lookback:].min()
    current = prices.iloc[-1]
    
    signal = 0
    if current > high * (1 + threshold):
        signal = 1  # Breakout up
    elif current < low * (1 - threshold):
        signal = -1  # Breakout down
    
    return signal, {'high': high, 'low': low, 'current': current}
```

---

## Error Handling

### Missing Parameters

```python
def load_params():
    params_path = Path(__file__).parent / 'parameters.yaml'
    if not params_path.exists():
        raise FileNotFoundError(
            f"parameters.yaml not found at {params_path}. "
            "Every strategy must have a parameters.yaml file."
        )
    # Load...
```

### Insufficient Data

```python
def compute_signals(context, data):
    lookback = context.params['strategy']['slow_period'] + 5
    prices = data.history(context.asset, 'price', lookback, '1d')
    
    if len(prices) < lookback:
        return 0, {}  # Not enough data yet
    # Proceed...
```

### Market Closed

```python
def compute_signals(context, data):
    if not data.can_trade(context.asset):
        return 0, {}  # Market closed or asset not tradable
    # Proceed...
```

---

## Validation Checklist

Before marking strategy as complete:

- [ ] Strategy directory created in correct location
- [ ] `hypothesis.md` completed with all required sections
- [ ] `parameters.yaml` configured with all parameters
- [ ] `strategy.py` implements all required functions
- [ ] No hardcoded parameters in strategy.py
- [ ] Syntax validation passes
- [ ] Import validation passes
- [ ] YAML validation passes
- [ ] Results symlink created (or will be auto-created)

---

## Next Steps

After creating a strategy:

1. **Run smoke test backtest** — Verify it executes without errors
2. **Review initial results** — Check if logic works as expected
3. **Document any issues** — Note bugs or unexpected behavior
4. **Proceed to optimization** — If initial results are promising

**See:** `.agent/backtest_runner.md` for running backtests

---

## Questions?

- **Naming conventions?** → `.agent/conventions.md`
- **Parameter structure?** → `strategies/_template/parameters.yaml`
- **Code patterns?** → `docs/code_patterns/`
- **Strategy examples?** → `docs/templates/strategies/`

