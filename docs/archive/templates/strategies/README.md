# Zipline Strategy Templates

> Production-ready algorithmic trading strategies with configurable parameters.

## Overview

This collection includes **10 strategy templates** organized into two tiers:
- **Basic Templates (01-05)**: Well-engineered foundations for each strategy type
- **Advanced Templates (06-10)**: Sophisticated implementations with regime detection, multi-timeframe analysis, and adaptive parameters

All strategies feature clearly marked `[PLACEHOLDER]` parameters for customization.

---

## Strategy Matrix

| # | Strategy | Type | Complexity | Best For |
|---|----------|------|------------|----------|
| 01 | SMA Cross | Trend Following | Basic | Trending markets, beginners |
| 02 | RSI Mean Reversion | Mean Reversion | Basic | Range-bound markets |
| 03 | Bollinger Bands | Volatility | Basic | Multiple market conditions |
| 04 | MACD Momentum | Momentum | Basic | Trending stocks/ETFs |
| 05 | Breakout Intraday | Intraday | Basic | Liquid instruments |
| 06 | Multi-TF SMA | Trend Following | Advanced | Regime-aware trending |
| 07 | RSI + Correlation | Mean Reversion | Advanced | Multi-asset filtering |
| 08 | BB + Keltner Squeeze | Volatility | Advanced | Volatility breakouts |
| 09 | MACD Impulse System | Momentum | Advanced | Strong trends |
| 10 | Multi-Level Breakout | Intraday | Advanced | S/R level trading |

---

## Basic Strategies (01-05)

### 01 - SMA Cross Strategy
**File**: `01_sma_cross_strategy.py`

Classic dual moving average crossover with trend filter and risk management.

**Key Features**:
- Golden/death cross signals
- Optional 200-day trend filter
- Volatility-scaled position sizing
- Fixed and trailing stops

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `FAST_SMA_PERIOD` | 5-20 | Fast moving average |
| `SLOW_SMA_PERIOD` | 20-100 | Slow moving average |
| `TREND_FILTER_PERIOD` | 100-200 | Long-term trend filter |
| `STOP_LOSS_PCT` | 0.01-0.10 | Stop loss percentage |

---

### 02 - RSI Mean Reversion
**File**: `02_rsi_mean_reversion.py`

Oversold/overbought mean reversion with position scaling.

**Key Features**:
- Dynamic RSI thresholds
- Scale-in on extreme readings
- Holding period limits
- Profit targets and stops

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `RSI_PERIOD` | 7-21 | RSI calculation period |
| `RSI_OVERSOLD` | 20-35 | Entry threshold |
| `SCALE_IN_ENABLED` | bool | Enable pyramiding |
| `MAX_HOLDING_DAYS` | 10-30 | Force exit days |

---

### 03 - Bollinger Bands
**File**: `03_bollinger_bands.py`

Volatility-based strategy with mean reversion or breakout modes.

**Key Features**:
- Dual mode (mean reversion/breakout)
- %B indicator for entries
- Bandwidth filter
- ATR-based stops

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `BB_PERIOD` | 10-30 | Band calculation period |
| `BB_STD_DEV` | 1.5-3.0 | Standard deviations |
| `STRATEGY_MODE` | string | 'mean_reversion' or 'breakout' |
| `MIN_BANDWIDTH` | 0.03-0.10 | Minimum volatility filter |

---

### 04 - MACD Momentum
**File**: `04_macd_momentum.py`

Momentum strategy with signal line crossovers and histogram analysis.

**Key Features**:
- MACD/signal crossovers
- Histogram momentum confirmation
- Zero-line filters
- Trend EMA filter

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `MACD_FAST_PERIOD` | 8-15 | Fast EMA |
| `MACD_SLOW_PERIOD` | 20-30 | Slow EMA |
| `MACD_SIGNAL_PERIOD` | 5-12 | Signal line EMA |
| `USE_TREND_FILTER` | bool | Require trend alignment |

---

### 05 - Breakout Intraday
**File**: `05_breakout_intraday.py`

Intraday opening range breakout with volume confirmation.

**Key Features**:
- Opening range detection
- Volume spike confirmation
- Previous day level integration
- End-of-day flatten

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `OPENING_RANGE_MINUTES` | 15-60 | Range formation period |
| `VOLUME_MULTIPLIER` | 1.2-2.0 | Volume spike requirement |
| `STOP_ATR_MULT` | 1.0-2.5 | ATR-based stop |
| `FLATTEN_EOD` | bool | Close positions at EOD |

---

## Advanced Strategies (06-10)

### 06 - Advanced Multi-Timeframe SMA
**File**: `06_advanced_sma_multitimeframe.py`

Sophisticated trend-following with regime detection and adaptive parameters.

**Key Features**:
- Multi-timeframe alignment (short/medium/long)
- Volatility regime detection (high/normal/low)
- Adaptive SMA periods based on market conditions
- ADX trend strength filter
- Risk parity position sizing
- Drawdown control with hedging option
- Hurst exponent for trend/range detection

**Advanced Concepts**:
```
Regime Detection:
├── Volatility Regime → Adjusts SMA periods
├── Trend Regime → Uses Hurst exponent
└── ADX Filter → Requires trend strength

Position Sizing:
├── Volatility Targeting
├── Signal Strength Weighting
└── Drawdown Reduction
```

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `SHORT/MEDIUM/LONG_FAST/SLOW_SMA` | various | Multi-timeframe SMAs |
| `USE_ADAPTIVE_PERIODS` | bool | Dynamic period adjustment |
| `HIGH_VOL_THRESHOLD` | 0.15-0.30 | Volatility regime threshold |
| `USE_DRAWDOWN_CONTROL` | bool | Reduce risk in drawdowns |
| `TARGET_VOLATILITY` | 0.08-0.20 | Target portfolio volatility |

---

### 07 - Advanced RSI with Correlation Filter
**File**: `07_advanced_rsi_correlation.py`

Sophisticated mean reversion with multi-asset correlation filtering.

**Key Features**:
- Adaptive RSI periods based on volatility
- Dynamic oversold/overbought thresholds
- Multi-asset correlation filter (avoid systemic moves)
- Hurst exponent regime filter
- RSI divergence detection
- Kelly Criterion-inspired position sizing
- Mathematical pyramiding with decay

**Advanced Concepts**:
```
Correlation Filter:
├── Tracks correlated assets (SPY, IWM, DIA)
├── Filters systemic selloffs
└── Seeks idiosyncratic opportunities

Position Sizing (Kelly-inspired):
├── f* = (bp - q) / b
├── Fractional Kelly (25% default)
└── Win rate and payoff ratio estimates
```

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `USE_ADAPTIVE_RSI` | bool | Dynamic RSI period |
| `USE_DYNAMIC_THRESHOLDS` | bool | Vol-adjusted thresholds |
| `USE_CORRELATION_FILTER` | bool | Filter correlated moves |
| `KELLY_FRACTION` | 0.1-0.5 | Kelly criterion fraction |
| `REQUIRE_MEAN_REVERSION_REGIME` | bool | Hurst < 0.5 required |

---

### 08 - Advanced Bollinger Bands with Keltner Squeeze
**File**: `08_advanced_bollinger_squeeze.py`

Volatility strategy combining Bollinger Bands with Keltner Channels.

**Key Features**:
- BB/KC squeeze detection (volatility contraction)
- Adaptive band parameters
- Momentum oscillator for direction
- Adaptive strategy mode (squeeze vs mean reversion)
- Volume profile awareness
- Chandelier exit (ATR-based trailing)
- Partial profit taking

**Advanced Concepts**:
```
Squeeze Detection:
├── BB inside KC = Squeeze forming
├── Momentum determines direction
└── Breakout anticipation mode

Adaptive Mode Selection:
├── ADX > 25 → Squeeze/Breakout mode
└── ADX < 25 → Mean Reversion mode
```

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `KC_ATR_MULT` | 1.0-2.0 | Keltner ATR multiplier |
| `MIN_SQUEEZE_BARS` | 3-8 | Minimum squeeze duration |
| `STRATEGY_MODE` | string | 'squeeze', 'mean_reversion', 'adaptive' |
| `USE_SQUEEZE_ANTICIPATION` | bool | Enter before squeeze fires |
| `USE_CHANDELIER_EXIT` | bool | ATR-based trailing stop |

---

### 09 - Advanced MACD with Impulse System
**File**: `09_advanced_macd_impulse.py`

Elder's Impulse System with multi-timeframe MACD and histogram patterns.

**Key Features**:
- Elder's Impulse System (EMA slope + histogram)
- Multi-timeframe MACD confirmation
- Adaptive MACD parameters by volatility
- Histogram divergence detection
- Momentum ranking for signal strength
- Composite scoring for entries

**Advanced Concepts**:
```
Impulse System:
├── Green: EMA↑ AND Histogram↑ (bullish)
├── Red: EMA↓ AND Histogram↓ (bearish)
└── Blue: Mixed (neutral)

Signal Strength Scoring:
├── MTF Agreement (weight)
├── Histogram Momentum (weight)
├── Impulse Color (weight)
├── ADX Strength (weight)
└── Divergence Bonus (weight)
```

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `USE_IMPULSE_SYSTEM` | bool | Elder's Impulse System |
| `USE_MTF_CONFIRMATION` | bool | Multi-timeframe MACD |
| `MIN_TF_AGREEMENT` | 1-3 | Timeframes required |
| `STRONG_SIGNAL_THRESHOLD` | 0.5-0.9 | Signal strength cutoff |
| `IMPULSE_EXIT_ON_RED` | bool | Exit on red impulse |

---

### 10 - Advanced Multi-Level Intraday Breakout
**File**: `10_advanced_breakout_multilevel.py`

Sophisticated intraday breakout with S/R levels and statistical validation.

**Key Features**:
- Multi-level support/resistance detection
- Statistical breakout validation (z-score)
- Volume profile analysis
- Adaptive range calculation by volatility
- Multi-timeframe trend alignment
- Position scaling on confirmed breakouts
- Failed breakout handling

**Advanced Concepts**:
```
Level Detection:
├── Swing high/low identification
├── Touch count validation
├── Clustering nearby levels
└── Max levels limit

Statistical Validation:
├── Price Z-score > threshold
├── Volume Z-score > threshold
└── Combined validation

Volume Profile:
├── Price bins with volume
├── High Volume Nodes (HVN)
└── Trade near HVN preference
```

**Key Parameters**:
| Parameter | Range | Description |
|-----------|-------|-------------|
| `USE_MULTI_LEVEL` | bool | Multiple S/R levels |
| `USE_STATISTICAL_VALIDATION` | bool | Z-score validation |
| `MIN_BREAKOUT_ZSCORE` | 1.5-3.0 | Price z-score threshold |
| `USE_VOLUME_PROFILE` | bool | Volume at price analysis |
| `USE_MTF_TREND` | bool | Daily trend alignment |

---

## Quick Start

### 1. Select Strategy

Choose based on your trading style and market conditions:

| If you want... | Use... |
|----------------|--------|
| Simple trend following | 01 (basic) or 06 (advanced) |
| Mean reversion in ranges | 02 (basic) or 07 (advanced) |
| Volatility-based trading | 03 (basic) or 08 (advanced) |
| Momentum on strong trends | 04 (basic) or 09 (advanced) |
| Intraday breakouts | 05 (basic) or 10 (advanced) |

### 2. Configure Parameters

Edit the `[PLACEHOLDER]` section at the top of each file:

```python
# ==============================================================================
# [PLACEHOLDERS] - CONFIGURE THESE PARAMETERS
# ==============================================================================

ASSET_SYMBOL = 'SPY'              # Change this
FAST_SMA_PERIOD = 10              # Adjust for your timeframe
# ... etc
```

### 3. Run Backtest

```python
from zipline import run_algorithm
import pandas as pd

# Import your chosen strategy
from strategy_file import initialize, handle_data, analyze

results = run_algorithm(
    start=pd.Timestamp('2020-01-01', tz='UTC'),
    end=pd.Timestamp('2023-12-31', tz='UTC'),
    initialize=initialize,
    handle_data=handle_data,
    analyze=analyze,
    capital_base=100000,
    data_frequency='daily',  # or 'minute' for intraday
    bundle='quandl'
)
```

---

## Common Features

All strategies include:

| Feature | Description |
|---------|-------------|
| Position Sizing | Fixed, volatility-scaled, or risk-based |
| Risk Management | Stop loss, trailing stops, profit targets |
| Cost Modeling | Realistic commission and slippage |
| Recording | Key metrics tracked via `record()` |
| Analysis | `analyze()` function with performance summary |

---

## Parameter Optimization Tips

1. **Start with defaults** - Run baseline before optimizing
2. **Walk-forward testing** - Split data into train/validate/test
3. **Parameter ranges** - Test ranges, not single values
4. **Avoid overfitting** - Fewer parameters is better
5. **Out-of-sample validation** - Always test on unseen data

---

## File Structure

```
strategies/
├── README.md                           # This file
│
├── Basic Templates
│   ├── 01_sma_cross_strategy.py        # SMA crossover
│   ├── 02_rsi_mean_reversion.py        # RSI mean reversion
│   ├── 03_bollinger_bands.py           # Bollinger bands
│   ├── 04_macd_momentum.py             # MACD momentum
│   └── 05_breakout_intraday.py         # Intraday breakout
│
└── Advanced Templates
    ├── 06_advanced_sma_multitimeframe.py   # Multi-TF SMA + regime
    ├── 07_advanced_rsi_correlation.py      # RSI + correlation filter
    ├── 08_advanced_bollinger_squeeze.py    # BB + Keltner squeeze
    ├── 09_advanced_macd_impulse.py         # MACD + impulse system
    └── 10_advanced_breakout_multilevel.py  # Multi-level breakout
```

---

## Risk Disclaimer

These templates are provided for educational purposes. Always:
- Backtest thoroughly before live trading
- Use appropriate position sizing
- Understand the strategy mechanics
- Paper trade before risking capital

**Use at your own risk.**
