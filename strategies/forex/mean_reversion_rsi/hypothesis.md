# Strategy Hypothesis: Mean Reversion RSI

> **Strategy Name:** mean_reversion_rsi
> **Asset Class:** Forex
> **Primary Symbol:** EURUSD
> **Secondary Symbol:** NZDJPY
> **Timeframe:** 15-minute
> **Bundle:** csv_eurusd_15m

---

## The Belief

**What specific market behavior are we exploiting?**

Forex currency pairs exhibit mean-reverting behavior when the Relative Strength Index (RSI) reaches extreme levels. Specifically:

- **Oversold Bounce:** When RSI(14) drops below 30 and then crosses back above 30, the pair is likely to experience a short-term recovery (mean reversion upward).
- **Overbought Reversal:** When RSI(14) rises above 70 and then crosses back below 70, the pair is likely to experience a short-term pullback (mean reversion downward).

This strategy captures the momentum shift that occurs when price has moved too far too fast and reverts toward its recent mean.

---

## The Reasoning

**Why does this behavior exist?**

1. **Market Participant Psychology:**
   - Retail traders tend to chase momentum, creating oversold/overbought conditions.
   - When RSI reaches extreme levels, contrarian traders and algorithms step in, creating counter-pressure.

2. **Institutional Rebalancing:**
   - Large institutional flows often trigger mean reversion when prices deviate significantly from fair value.
   - Portfolio rebalancing at month-end and quarter-end amplifies reversion patterns.

3. **Forex Market Structure:**
   - The forex market operates 24/5 with high liquidity, making extreme moves relatively short-lived.
   - Central bank interventions and macroeconomic releases create temporary dislocations that revert.

4. **Statistical Mean Reversion:**
   - Currency pairs are bounded by fundamental economic relationships (interest rate differentials, trade balances).
   - Extreme deviations from these fundamentals tend to correct over time.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Range-bound or consolidating markets with clear support/resistance levels
- Normal volatility regimes (not during major central bank announcements)
- Markets with established trading ranges
- When RSI extremes coincide with technical support/resistance levels
- During Asian and early European sessions (lower volatility, more mean reversion)

**Fails in:**
- Strong trending markets where RSI can remain overbought/oversold for extended periods
- During major news events (NFP, CPI, FOMC, ECB decisions)
- During geopolitical crises or risk-off events
- Low liquidity periods (holidays, market opens)
- When fundamental shifts change the fair value of the currency pair

---

## The Falsification

**What result would prove this hypothesis wrong?**

The hypothesis should be rejected if:

- **Sharpe Ratio < 0.5** across 2+ years of data (indicates no consistent edge)
- **Maximum Drawdown > 25%** (risk-adjusted returns unacceptable)
- **Win Rate < 40%** (signal quality too low for mean reversion strategy)
- **Profit Factor < 1.2** (insufficient edge to overcome transaction costs)
- **Average Trade < 5 pips net** (transaction costs erode profitability)
- **RSI signals show no predictive power** for next-bar returns (statistical test)

---

## Implementation Notes

**How is this hypothesis translated into code?**

### Entry Logic

1. **Long Entry (Oversold Recovery):**
   - Condition: RSI(14) crosses above 30 (from below)
   - Previous bar RSI < 30, current bar RSI >= 30
   - This captures the momentum shift from oversold to recovery

2. **Short Entry (Overbought Reversal):**
   - Condition: RSI(14) crosses below 70 (from above)
   - Previous bar RSI > 70, current bar RSI <= 70
   - This captures the momentum shift from overbought to pullback

### Exit Logic

1. **Signal Exit:** Close position when opposite signal occurs
2. **Stop Loss:** 3% from entry price (protects against failed reversions)
3. **Take Profit:** 5% from entry price (captures mean reversion target)
4. **Warmup Period:** 21 days minimum for RSI calculation stability

### Position Sizing

- **Method:** Volatility-scaled targeting 15% annual volatility
- **Formula:** position_size = volatility_target / current_volatility
- **Range:** 10% to 95% of portfolio

### Module Usage (v1.11.0+)

- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: `lib.position_sizing.compute_position_size()` for volatility scaling
- Risk management: `lib.risk_management.check_exit_conditions()` for stop losses
- Pipeline setup: Not used (use_pipeline: false for forex)
- Data access: `lib.bundles.load_bundle()` to access bundle data

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| rsi_period | High | Affects signal frequency and quality; shorter periods = more signals but more noise |
| rsi_oversold | Medium | Lower threshold = fewer but higher-quality oversold signals |
| rsi_overbought | Medium | Higher threshold = fewer but higher-quality overbought signals |
| stop_loss_pct | High | Too tight = stopped out before reversion; too loose = large losses on failed trades |
| take_profit_pct | Medium | Should be calibrated to historical mean reversion magnitude |
| volatility_target | Low | Affects position sizing but not signal quality |

**Critical Parameters:**
- `rsi_period`: Determines signal generation frequency and noise level
- `stop_loss_pct`: Must balance between protection and premature exits

**Robust Parameters:**
- `volatility_target`: Small changes don't significantly impact results
- `rsi_oversold`/`rsi_overbought`: Standard 30/70 levels are well-established

**Optimization Priority:**
1. `rsi_period` (range: 7-21)
2. `stop_loss_pct` (range: 0.02-0.05)
3. `take_profit_pct` (range: 0.03-0.08)

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 3+ years for regime diversity (2020-2023 includes COVID volatility, rate hike cycles)
- Frequency: 15-minute OHLCV data
- Observations: At least 50,000 bars (15-minute bars over 3 years)

**Warmup Period:**
- Required: 21 days minimum
- Rationale: RSI(14) needs 14 periods to stabilize; additional buffer for indicator reliability
- Configure in `parameters.yaml` under `backtest.warmup_days`

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source csv --assets forex --timeframe 15m`
- Bundle naming: `csv_eurusd_15m` (primary), `csv_nzdjpy_15m` (secondary)

**Data Quality:**
- [x] Volume data optional (forex volume is dealer-specific)
- [x] Missing data tolerance: 2 consecutive bars max
- [x] Requires gap filling for weekends (FOREX calendar handles this)

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 | FOREX | Uses `lib.calendars.ForexCalendar` (v1.11.0+) |

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | Vol Equivalent | Expected Behavior | Recommended Action |
|--------|----------------|-------------------|-------------------|
| Low Vol | ATR < 0.5% | Fewer signals, higher win rate | Normal position sizing |
| Normal Vol | ATR 0.5-1.0% | Optimal signal generation | Normal operation |
| High Vol | ATR 1.0-2.0% | More signals, lower win rate | Reduce position size |
| Crisis | ATR > 2.0% | RSI extremes persist longer | Consider pausing |

**Regime Detection:**
- How to identify current regime: 20-day ATR as percentage of price
- Indicators to watch: VIX correlation (for risk-off events), ATR, realized volatility

**Adaptive Behavior:**
- [x] Position sizing scales with volatility (volatility_scaled method)
- [ ] Parameters do not adapt to regime (static RSI thresholds)
- [ ] Strategy continues in all regimes (with position sizing adjustment)

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (USD Index) | Low | Good - not directionally biased |
| Momentum Factor | Negative | Good - counter-trend strategy |
| Value Factor | Medium | Moderate - both exploit mean reversion |
| Volatility | Low | Good - uses vol for sizing only |
| Trend Following | Negative | Excellent - natural hedge |

**Portfolio Construction Notes:**
- Best paired with: Trend-following strategies (negative correlation), volatility breakout strategies
- Avoid combining with: Other mean reversion strategies on same pairs
- Suggested portfolio weight: 10-20% of forex allocation

**Return Driver Analysis:**
- [x] Market-neutral (trades both long and short)
- [ ] Not exposed to specific currency bias (trades reversions in both directions)
- [x] Sensitive to interest rate volatility (affects forex pair movements)

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [ ] Sharpe ratio < 0.3 for 6 consecutive months
- [ ] Maximum drawdown exceeds 25%
- [ ] Win rate drops below 35% over 100+ trades
- [ ] 6+ consecutive losing months
- [ ] Profit factor < 1.0 for trailing 12 months

**Qualitative Triggers:**
- [ ] Forex market structure fundamentally changes (reduced liquidity)
- [ ] Central bank policies eliminate mean reversion (permanent trends)
- [ ] RSI indicator becomes widely arbitraged (crowded trade)
- [ ] Transaction costs increase significantly

**Review Schedule:**
- Weekly: Monitor win rate and average trade metrics
- Monthly: Review rolling Sharpe and drawdown
- Quarterly: Full parameter sensitivity analysis
- Annually: Re-evaluate hypothesis validity

---

## Optimization Bounds

**Valid parameter ranges for optimization searches:**

| Parameter | Min | Max | Step | Default | Rationale |
|-----------|-----|-----|------|---------|-----------|
| rsi_period | 7 | 21 | 1 | 14 | Standard RSI periods; too short = noise, too long = lag |
| rsi_oversold | 20 | 35 | 5 | 30 | Classic range for oversold detection |
| rsi_overbought | 65 | 80 | 5 | 70 | Classic range for overbought detection |
| stop_loss_pct | 0.02 | 0.05 | 0.005 | 0.03 | Must protect capital without excessive stops |
| take_profit_pct | 0.03 | 0.08 | 0.01 | 0.05 | Should exceed stop loss for positive expectancy |
| volatility_target | 0.10 | 0.20 | 0.025 | 0.15 | Risk tolerance range |

**Parameter Constraints:**
- `rsi_oversold` must be < 50 (below centerline)
- `rsi_overbought` must be > 50 (above centerline)
- `take_profit_pct` should be >= `stop_loss_pct` for asymmetric reward
- `rsi_overbought` - `rsi_oversold` >= 30 (avoid overlapping zones)

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time
- Walk-forward window: 90 days train / 30 days test
- Out-of-sample threshold: Must retain 60%+ of in-sample Sharpe
- Number of trials limit: < 50 combinations per optimization run

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 0.7 (risk-adjusted returns above market)
- Maximum Drawdown < 20% (controlled risk)
- Win Rate > 45% (better than coin flip)
- Profit Factor > 1.3 (meaningful edge after costs)
- Average Trade Duration: 4-24 hours (intraday to overnight)
- Monthly Trade Count: 20-50 trades (sufficient for statistical significance)

---

## References

**What research, papers, or observations support this hypothesis?**

1. **Academic Literature:**
   - Wilder, J.W. (1978). "New Concepts in Technical Trading Systems" - Original RSI definition
   - Lo, A.W. & MacKinlay, A.C. (1990). "When Are Contrarian Profits Due to Stock Market Overreaction?" - Mean reversion evidence

2. **Market Observations:**
   - RSI is one of the most widely used indicators in forex trading
   - Mean reversion is a well-documented phenomenon in currency markets
   - Institutional traders often use RSI extremes as entry points

**Codebase References (v1.11.0+):**
- `lib/bundles/` - Data bundle management and ingestion
- `lib/validation/` - Data quality validation
- `lib/calendars/` - Trading calendar management (FOREX calendar)
- `lib/config/` - Configuration loading and validation
- `lib/backtest/` - Backtest execution and results
- `lib/metrics/` - Performance metrics calculation
- `docs/api/` - Complete API documentation

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial hypothesis | Strategy Developer Agent |
