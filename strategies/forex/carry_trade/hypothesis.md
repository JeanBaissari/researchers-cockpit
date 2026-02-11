# Strategy Hypothesis: Forex Carry Trade

> **Strategy Name:** carry_trade
> **Asset Class:** forex
> **Primary Symbol:** NZDJPY (high-yield differential)
> **Timeframe:** Daily (1d)
> **Bundle:** csv_nzdjpy_1d

---

## The Belief

**What specific market behavior are we exploiting?**

Currency pairs with positive interest rate differentials tend to appreciate over time as traders are compensated for holding the higher-yielding currency against the lower-yielding one. This phenomenon, known as the "carry trade," exploits the interest rate differential (or "carry") between two currencies.

Specifically, we believe that:
1. High-yield currencies (NZD, AUD) outperform low-yield currencies (JPY, CHF) during periods of positive market sentiment and stable economic conditions.
2. The carry premium is most profitable when combined with a trend-following filter to avoid holding during trend reversals.
3. Volatility spikes signal risk-off periods where carry trades historically underperform, providing a useful exit signal.

---

## The Reasoning

**Why does this behavior exist?**

The carry trade exists due to several fundamental market mechanics:

### 1. Interest Rate Differential (Carry)
- Central banks set interest rates based on economic conditions
- NZD (Reserve Bank of New Zealand) historically offers higher rates than JPY (Bank of Japan)
- Traders holding NZDJPY long earn the interest differential daily (positive swap/rollover)
- This creates a structural bias to hold high-yield currencies

### 2. Uncovered Interest Rate Parity (UIP) Failure
- Economic theory suggests exchange rates should adjust to offset interest rate differentials
- Empirically, UIP fails: high-yield currencies do NOT depreciate as much as theory predicts
- This "forward premium puzzle" creates the carry trade opportunity

### 3. Risk Premium
- Carry trades are exposed to crash risk (sudden unwinding)
- The positive return is compensation for bearing this risk
- Institutional investors and hedge funds systematically harvest this premium

### 4. Market Sentiment Cycles
- During risk-on periods, capital flows to higher-yielding assets
- During risk-off periods (crises), investors flee to safe havens (JPY, USD, CHF)
- Trend filters help distinguish these regimes

### 5. Central Bank Policy Divergence
- BOJ has maintained near-zero rates for decades (yield curve control)
- RBNZ raises rates during economic expansion
- This policy divergence creates persistent carry opportunities

---

## The Conditions

**When should this work? When should it fail?**

### Works well in:
- **Trending markets with positive momentum:** When the 20-day SMA slope is positive, indicating sustained buying pressure
- **Low volatility environments:** When ATR is below the average, signaling stable conditions
- **Risk-on periods:** When global equity markets are rising and VIX is low
- **Policy divergence periods:** When NZ and Japan have different monetary policy directions
- **Commodity uptrends:** NZD is correlated with commodity prices (dairy exports)

### Fails in:
- **Risk-off episodes:** Global crises trigger JPY safe-haven flows
- **Volatility spikes:** ATR > 1.5x average signals potential trend reversal
- **Carry trade unwinding:** Sudden deleveraging causes sharp losses
- **Trend reversals:** When 20-day SMA slope turns negative
- **JPY strength periods:** BOJ policy changes or Japan economic strength
- **Commodity downturns:** Weaker commodity prices hurt NZD

### Historical Risk Events:
- **2008 Global Financial Crisis:** Carry trades collapsed as JPY surged
- **2011 Japan Earthquake/Tsunami:** Initial JPY strength, then unwinding
- **2015 CNY Devaluation:** Risk-off sentiment hurt carry trades
- **2020 COVID Crash:** March 2020 saw massive carry trade unwinding

---

## The Falsification

**What result would prove this hypothesis wrong?**

The hypothesis should be rejected if:

1. **Sharpe Ratio < 0.5** across 3+ years of data
   - A carry trade should provide risk-adjusted returns above this threshold
   - If not, the edge is insufficient to overcome transaction costs

2. **Maximum Drawdown > 30%**
   - Carry trades are known for "up the escalator, down the elevator" profiles
   - If drawdowns exceed 30%, the risk/reward is unacceptable

3. **Win Rate < 40%** over a statistically significant sample
   - Daily rebalancing should produce moderate win rates
   - Very low win rates suggest the trend filter is ineffective

4. **Negative Sharpe during trending periods**
   - If the strategy loses money when the trend filter is positive, the core hypothesis is flawed

5. **ATR spike filter provides no protection**
   - If exits on volatility spikes do not reduce drawdowns, the risk management is ineffective

---

## Implementation Notes

**How is this hypothesis translated into code?**

### Signal Generation
1. **Trend Filter (20-day SMA Slope):**
   - Calculate 20-day Simple Moving Average of close prices
   - Compute slope: `(current_sma - previous_sma) / previous_sma`
   - Signal = 1 (long) if slope > min_trend_slope (0.0001)
   - Signal = 0 (flat) if slope <= min_trend_slope

2. **Volatility Exit (ATR Spike Detection):**
   - Calculate 14-day ATR (Average True Range)
   - Calculate 14-day average ATR
   - If current ATR > 1.5x average ATR, exit position (volatility spike)

3. **Position Management:**
   - Hold 80% position when signal is positive (fixed allocation, lower leverage for carry)
   - Exit to 0% when signal is negative or volatility spike detected
   - Daily rebalancing at market close

4. **Risk Management:**
   - 10% stop loss from entry price
   - Exit on volatility spike regardless of P&L
   - No trailing stop (trend filter handles exits)

### Module Usage (v1.11.0+):
- **Configuration:** `lib.config.load_strategy_params()` loads parameters from YAML
- **Position sizing:** Fixed 80% allocation (parameterized via `max_position_pct`)
- **Risk management:** `lib.risk_management.check_exit_conditions()` for stop losses
- **Data access:** Uses `data.history()` for SMA and ATR calculations

### Entry/Exit Rules Summary:
| Condition | Action |
|-----------|--------|
| Trend slope > 0.0001 AND ATR < 1.5x avg | Enter LONG |
| Trend slope <= 0.0001 | Exit to FLAT |
| ATR >= 1.5x avg | Exit to FLAT |
| Price drops 10% from entry | Exit to FLAT (stop loss) |

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| trend_period | High | Core trend identification; too short = whipsaw, too long = delayed entry |
| atr_spike_multiplier | High | Risk-off detection threshold; too low = early exits, too high = late exits |
| min_trend_slope | Medium | Noise filter for trend direction; affects signal frequency |
| max_position_pct | Low | Fixed allocation; mainly affects leverage/risk scaling |
| stop_loss_pct | Low | Emergency exit only; trend filter should exit before stop in most cases |

### Critical Parameters:
1. **trend_period (10-50):** Most critical for timing entries/exits
2. **atr_spike_multiplier (1.2-2.0):** Controls volatility-based risk management

### Robust Parameters:
- **atr_period (14):** Standard ATR period, little sensitivity
- **max_position_pct (0.80):** Fixed allocation, adjust for risk tolerance

### Optimization Priority:
1. trend_period
2. atr_spike_multiplier
3. min_trend_slope

---

## Data Requirements

**What data is needed for valid backtesting?**

### Minimum History:
- **Duration:** 5+ years for regime diversity (includes risk-on and risk-off periods)
- **Frequency:** Daily OHLCV
- **Observations:** At least 1,000 trading days

### Warmup Period:
- **Required:** 20 days (for 20-day SMA and initial ATR calculations)
- Configure in `parameters.yaml` under `backtest.warmup_days: 20`

### Data Ingestion (v1.11.0+):
```python
from lib.bundles import ingest_bundle

# Ingest daily forex data for NZDJPY
bundle_name = ingest_bundle(
    source='csv',
    assets=['forex'],
    symbols=['NZDJPY'],
    timeframe='daily'
)
```

### Data Quality:
- [x] Adjusted prices required? No (forex has no splits/dividends)
- [ ] Volume data required? No (optional for forex)
- [x] Missing data tolerance: 5 consecutive days max (weekends excluded)

### Asset Class Considerations:
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 | FOREX | Excludes weekends only |

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | VIX Equivalent | Expected Behavior | Recommended Action |
|--------|----------------|-------------------|-------------------|
| Low Vol | < 15 | Strong carry returns, smooth equity curve | Normal operation |
| Normal Vol | 15-25 | Moderate returns with occasional drawdowns | Normal operation |
| High Vol | 25-40 | Reduced returns, ATR filter triggers exits | Reduced exposure via ATR filter |
| Crisis | > 40 | Significant drawdowns if not exited | ATR filter should exit positions |

### Regime Detection:
- Primary: ATR spike detection (14-day ATR > 1.5x average)
- Secondary: 20-day SMA slope turning negative

### Adaptive Behavior:
- [x] Position sizing is fixed (80%) - no volatility scaling
- [x] Parameters do NOT adapt to regime (simple rules-based)
- [x] Strategy exits in high volatility regimes via ATR filter

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (SPY) | Medium-High | Moderate - both are risk-on strategies |
| Momentum Factor | Medium | Moderate - trend filter aligns with momentum |
| Value Factor | Low | Good - different return driver |
| Volatility (VIX) | Negative | Good - exits during vol spikes |
| JPY Index | Negative | Expected - short JPY exposure |
| NZD Index | Positive | Expected - long NZD exposure |

### Portfolio Construction Notes:
- **Best paired with:** Mean reversion strategies, volatility strategies
- **Avoid combining with:** Other carry trades (AUD/JPY, etc.) - high correlation
- **Suggested portfolio weight:** 10-15% of strategy allocation

### Return Driver Analysis:
- [x] Long-biased (positive carry exposure)
- [ ] Not market-neutral
- [x] Sensitive to global risk sentiment
- [x] Sensitive to central bank policy divergence

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

### Quantitative Triggers:
- [x] Sharpe ratio < 0.3 for 12 consecutive months
- [x] Maximum drawdown exceeds 35%
- [x] Win rate drops below 35% over 100+ trades
- [x] 6 consecutive losing months
- [x] Annual return < -10% for 2+ years

### Qualitative Triggers:
- [x] BOJ abandons yield curve control (fundamental policy shift)
- [x] RBNZ cuts rates to near-zero (eliminates carry differential)
- [x] Carry trade becomes too crowded (negative alpha)
- [x] Structural change in NZD/JPY relationship

### Review Schedule:
- **Weekly:** Monitor live performance vs. backtest expectations
- **Monthly:** Review rolling metrics, compare to benchmarks
- **Quarterly:** Deep dive into strategy health, reassess hypothesis
- **Annually:** Full re-evaluation, consider retirement

---

## Optimization Bounds

**Valid parameter ranges for optimization searches:**

| Parameter | Min | Max | Step | Default | Rationale |
|-----------|-----|-----|------|---------|-----------|
| trend_period | 10 | 50 | 5 | 20 | Short enough for responsiveness, long enough for trend persistence |
| atr_period | 10 | 20 | 2 | 14 | Standard ATR range |
| atr_spike_multiplier | 1.2 | 2.0 | 0.1 | 1.5 | Too low = false exits, too high = late exits |
| max_position_pct | 0.60 | 0.90 | 0.10 | 0.80 | Controls leverage |
| stop_loss_pct | 0.05 | 0.15 | 0.025 | 0.10 | Emergency exit threshold |
| min_trend_slope | 0.00005 | 0.0005 | 0.00005 | 0.0001 | Trend direction noise filter |

### Parameter Constraints:
- trend_period must be >= warmup_days - 1 (for sufficient history)
- stop_loss_pct should be > daily volatility to avoid early triggers

### Overfitting Protection:
- **Maximum parameters to optimize:** 3 at a time (trend_period, atr_spike_multiplier, min_trend_slope)
- **Walk-forward window:** 252 days train / 63 days test
- **Out-of-sample threshold:** Must retain 60%+ of in-sample Sharpe
- **Number of trials limit:** < 100 combinations

### Optimization Strategy:
- **Recommended method:** Grid search (small parameter space)
- **Cross-validation folds:** 4-fold time-series split
- **Primary objective:** Sharpe ratio (risk-adjusted returns)

---

## Expected Outcomes

**What results would validate this hypothesis?**

- **Sharpe Ratio:** > 0.7 (acceptable), > 1.0 (good)
- **Maximum Drawdown:** < 25%
- **Win Rate:** > 45%
- **Annual Return:** 5-15% (realistic for daily carry)
- **Consistent performance:** Positive in 3/4 market regimes

---

## References

**What research, papers, or observations support this hypothesis?**

### Academic References:
1. Burnside, C., Eichenbaum, M., & Rebelo, S. (2011). "Carry Trade and Momentum in Currency Markets"
2. Lustig, H., & Verdelhan, A. (2007). "The Cross Section of Foreign Currency Risk Premia and Consumption Growth Risk"
3. Menkhoff, L., Sarno, L., Schmeling, M., & Schrimpf, A. (2012). "Carry Trades and Global Foreign Exchange Volatility"

### Codebase References (v1.11.0+):
- `lib/bundles/` - Data bundle management and ingestion
- `lib/validation/` - Data quality validation
- `lib/calendars/` - Trading calendar management (FOREX 24/5)
- `lib/config/` - Configuration loading and validation
- `lib/backtest/` - Backtest execution and results
- `lib/metrics/` - Performance metrics calculation
- `strategies/_template/` - Strategy template
- `docs/api/` - Complete API documentation
- `CLAUDE.md` - Project overview and version history

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial hypothesis | Strategy Developer Agent |
