# Multi-Timeframe Trend Strategy Hypothesis

> **Strategy Name:** multi_timeframe_trend
> **Asset Class:** FOREX
> **Primary Symbol:** EURUSD
> **Secondary Symbol:** NZDJPY
> **Primary Timeframe:** 1H
> **Higher Timeframe:** 4H (aggregated from 1H data)

---

## The Belief

**What specific market behavior are we exploiting?**

Trend-following strategies exhibit significantly higher success rates when the higher timeframe (4H) trend direction confirms the lower timeframe (1H) trend signals. This multi-timeframe confluence approach reduces false signals and whipsaw losses that commonly plague single-timeframe trend strategies.

The core premise is that when both the 1H moving average crossover (SMA20 crossing SMA50) aligns with the 4H trend direction (SMA10 with positive slope), the resulting trade has institutional backing from longer-term market participants.

**Specific Pattern:**
- **Long Entry:** 1H Golden Cross (SMA20 > SMA50) occurs while 4H SMA(10) has a positive slope (rising trend)
- **Short Entry:** 1H Death Cross (SMA20 < SMA50) occurs while 4H SMA(10) has a negative slope (falling trend)
- **Exit:** Opposite signal on the 1H timeframe OR trailing stop triggered

---

## The Reasoning

**Why does this behavior exist?**

Multi-timeframe confluence exploits the hierarchical nature of market participation:

1. **Institutional Alignment:** Large institutions and funds typically make decisions based on higher timeframes (4H, Daily). When the 4H trend is bullish, institutional order flow supports long positions.

2. **Noise Filtering:** Single-timeframe strategies on 1H data capture many false breakouts and whipsaws during consolidation periods. The 4H filter eliminates trades that go against the broader trend.

3. **Improved Risk-Reward:** By only trading when both timeframes agree, entries are made with the "wind at our back" from larger market participants.

4. **Mean Reversion Avoidance:** The 4H trend filter prevents entering counter-trend positions that would likely face strong resistance from institutional flow.

**Market Mechanics:**
- Retail traders often trade 1H signals in isolation
- Institutions accumulate/distribute on 4H and Daily timeframes
- When 1H signals align with 4H direction, retail and institutional flows combine
- This confluence creates more persistent moves with better follow-through

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Trending markets with clear directional bias
- Markets with good 4H trend persistence (trending for 5+ candles)
- Periods of moderate volatility where trends develop cleanly
- When institutional activity is high (London and NY sessions)
- Markets with clear fundamentals driving direction

**Fails in:**
- Choppy, ranging markets with no clear 4H direction
- High volatility events (NFP, FOMC, central bank decisions)
- Low liquidity periods (holiday weeks, summer months)
- When 4H trend is flat or oscillating (slope near zero)
- News-driven whipsaws that override technical patterns

**Session Considerations:**
- Best performance expected during London (07:00-16:00 UTC) and NY (13:00-22:00 UTC) sessions
- Asian session may produce fewer but cleaner signals
- Overlap period (13:00-16:00 UTC) typically has highest conviction

---

## The Falsification

**What result would prove this hypothesis wrong?**

**Quantitative Rejection Criteria:**
- If Sharpe Ratio < 0.5 across 3+ years of backtested data
- If win rate < 45% (below random chance for trend following)
- If maximum drawdown > 25% (unacceptable risk-adjusted performance)
- If profit factor < 1.2 (edge is too small to be exploitable)
- If adding the 4H filter does not improve Sharpe by at least 0.2 vs. 1H-only strategy

**Qualitative Rejection Criteria:**
- If multi-timeframe confirmation consistently lags too much, causing missed entries
- If the strategy underperforms a simple buy-and-hold during trending periods
- If most profits come from only 1-2 large trades (luck, not edge)

---

## Implementation Notes

**How is this hypothesis translated into code?**

**Multi-Timeframe Data Handling:**
1. Strategy receives 1H OHLCV data from the bundle
2. 1H data is aggregated to 4H using pandas resample('4h')
3. Both timeframes are processed in parallel

**Signal Generation Logic:**
```
4H Analysis:
  - Calculate SMA(10) on 4H close prices
  - Compute slope: current SMA(10) - previous SMA(10)
  - Trend UP: slope > min_4h_slope (0.0001 default)
  - Trend DOWN: slope < -min_4h_slope

1H Analysis:
  - Calculate SMA(20) and SMA(50) on 1H close prices
  - Golden Cross: SMA(20) crosses above SMA(50)
  - Death Cross: SMA(20) crosses below SMA(50)

Entry Conditions:
  - LONG: 1H Golden Cross AND 4H Trend UP
  - SHORT: 1H Death Cross AND 4H Trend DOWN

Exit Conditions:
  - Opposite 1H signal (Golden Cross for shorts, Death Cross for longs)
  - Trailing stop triggered (6% from peak equity)
  - Fixed stop loss (5% from entry)
```

**Module Usage (v1.11.0+):**
- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: `lib.position_sizing.compute_position_size()` for volatility-scaled sizing
- Risk management: Custom trailing stop logic (library doesn't support pip-based trailing)
- Data access: Uses 1H data from bundle, aggregates to 4H internally
- Calendar: FOREX calendar (24/5 trading, 260 days/year)

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| fast_ma_1h | High | Controls entry timing; too short = noise, too long = lag |
| slow_ma_1h | High | Defines trend on 1H; most critical for signal quality |
| trend_ma_4h | Medium | Higher timeframe filter; 10 is standard, 5-20 acceptable |
| min_4h_slope | Medium | Threshold for trend confirmation; too tight = few signals |
| trailing_stop_pct | Medium | Balance between profit protection and premature exits |
| volatility_target | Low | Scales position size; affects risk but not signal quality |

**Critical Parameters:**
- `slow_ma_1h`: Most impact on Sharpe ratio (defines when we're "in trend")
- `fast_ma_1h`: Second most impact (controls entry/exit timing)

**Robust Parameters:**
- `trend_ma_4h`: 10-period is standard; 8-12 range shows similar results
- `volatility_target`: 0.15-0.20 range produces comparable risk-adjusted returns

**Optimization Priority:**
1. `slow_ma_1h` (40-100 range, step 10)
2. `fast_ma_1h` (15-30 range, step 5)
3. `trailing_stop_pct` (0.04-0.08 range, step 0.01)

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 3+ years for regime diversity (2020-2025 ideal, includes COVID volatility)
- Frequency: 1H OHLCV data
- Observations: At least 10,000 1H bars (~417 trading days)

**Warmup Period:**
- Required: 50 days (for 50-period slow MA calculation on 1H data)
- Must be >= max(slow_ma_1h, 4 * trend_ma_4h) to ensure 4H data stability
- Configure in `parameters.yaml` under `backtest.warmup_days`
- Calculated automatically by `lib.config.get_warmup_days()` (v1.11.0+)

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source csv --assets forex --timeframe 1h`
- Bundle naming: `csv_eurusd_1h` (expected primary bundle)
- Supported sources: yahoo, csv
- See `lib/bundles/` package for bundle management utilities

**Data Quality Validation:**
- Pre-ingestion: Use `lib.validation.validate_before_ingest()` to validate source data
- Bundle validation: Use `lib.validation.validate_bundle()` to verify bundle integrity
- CLI: `python scripts/validate_bundles.py csv_eurusd_1h`
- See `lib/validation/` package for validation utilities

**Data Quality:**
- [x] Adjusted prices required? No (FOREX doesn't have splits/dividends)
- [x] Volume data required? No (FOREX volume is indicative only)
- [x] Missing data tolerance: 5 consecutive bars max (weekends excluded)
- Validation handled by `lib/validation/DataValidator` (v1.11.0+)

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 | FOREX | No weekends, uses `lib.calendars.ForexCalendar` (v1.11.0+) |

**Calendar Management (v1.11.0+):**
- Calendars defined in `lib/calendars/` package
- `ForexCalendar`: 24/5 trading (260 days/year, weekdays only)
- Calendar selection: `lib.calendars.get_calendar_for_asset_class('forex')`
- Session alignment: `lib/calendars/sessions/SessionManager` validates bundle-calendar alignment
- See `lib/calendars/` package for calendar utilities

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | VIX Equivalent | Expected Behavior | Recommended Action |
|--------|----------------|-------------------|-------------------|
| Low Vol | < 15 | Fewer signals, tighter ranges | Normal operation, may reduce frequency |
| Normal Vol | 15-25 | Optimal performance expected | Normal operation |
| High Vol | 25-40 | More signals, higher drawdown risk | Reduce position size by 25% |
| Crisis | > 40 | Whipsaws likely, trends may reverse | Consider pausing or 50% position size |

**Regime Detection:**
- How to identify current regime: 20-day rolling volatility of 1H returns
- Indicators to watch: ATR expansion, sudden slope reversals

**Adaptive Behavior:**
- [x] Should position sizing scale with volatility? Yes (volatility_target: 0.18)
- [ ] Should parameters adapt to regime? No (keep consistent for robustness)
- [ ] Should strategy pause in certain regimes? Optional in crisis periods

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| USD Index (DXY) | Medium-High | Depends on pair direction |
| Momentum Factor | High | Strategy is momentum-based |
| Carry Factor | Low | Not yield-driven |
| Volatility | Medium | More signals in volatile periods |

**Portfolio Construction Notes:**
- Best paired with: Mean reversion strategies, non-correlated asset classes (equities, crypto)
- Avoid combining with: Other trend-following forex strategies on same pairs
- Suggested portfolio weight: 15-25% of strategy allocation

**Return Driver Analysis:**
- [x] Long-biased or market-neutral? Market-neutral (can go long or short)
- [ ] Exposed to specific sector risk? No
- [ ] Sensitive to interest rate changes? Indirectly through currency fundamentals

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [ ] Sharpe ratio < 0.3 for 6 consecutive months
- [ ] Maximum drawdown exceeds 30%
- [ ] Win rate drops below 40% over 100+ trades
- [ ] 8 consecutive losing months
- [ ] Annual return < 5% for 2+ years

**Qualitative Triggers:**
- [ ] Fundamental shift in FOREX market structure (e.g., major currency peg changes)
- [ ] Regulatory changes affecting retail FOREX trading
- [ ] Strategy becomes widely published and overcrowded
- [ ] Data source reliability issues

**Review Schedule:**
- Weekly: Monitor live performance vs. backtest expectations
- Monthly: Review rolling metrics, compare to benchmarks
- Quarterly: Deep dive into strategy health, reassess hypothesis
- Annually: Full re-evaluation, consider retirement

---

## Optimization Bounds

**Valid parameter ranges for optimization searches:**

| Parameter | Min | Max | Step | Default | Rationale |
|-----------|-----|-----|------|---------|-----------|
| fast_ma_1h | 15 | 30 | 5 | 20 | Standard short-term MA range |
| slow_ma_1h | 40 | 100 | 10 | 50 | Must be > 2x fast_ma for proper crossover |
| trend_ma_4h | 5 | 20 | 5 | 10 | Higher timeframe smoothing |
| min_4h_slope | 0.00005 | 0.0002 | 0.00005 | 0.0001 | Minimum trend threshold |
| trailing_stop_pct | 0.04 | 0.10 | 0.01 | 0.06 | Balance profit protection vs premature exit |
| volatility_target | 0.12 | 0.22 | 0.02 | 0.18 | Annual volatility target |

**Parameter Constraints:**
- slow_ma_1h must be > fast_ma_1h * 2 (ensures proper crossover spacing)
- stop_loss_pct should be < trailing_stop_pct (fixed stop as last resort)
- warmup_days >= slow_ma_1h (ensures enough data for MA calculation)

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time
- Walk-forward window: 252 days train / 63 days test
- Out-of-sample threshold: Must retain 70%+ of in-sample Sharpe
- Number of trials limit: < 100 combinations

**Optimization Strategy:**
- Recommended method: Grid search (parameters are bounded and discrete)
- Cross-validation folds: 5-fold time-series split
- Primary objective: Sharpe ratio

---

## Expected Outcomes

**What results would validate this hypothesis?**

**Primary Success Criteria:**
- Sharpe Ratio > 0.8 (target: 1.0+)
- Maximum Drawdown < 20%
- Win Rate > 48%
- Profit Factor > 1.3
- Average Trade Duration: 12-72 hours

**Secondary Success Criteria:**
- Out-of-sample Sharpe > 70% of in-sample Sharpe
- Consistent performance across London and NY sessions
- Positive returns in at least 7 of 12 months per year
- 4H filter improves Sharpe by at least 0.2 vs. 1H-only strategy

---

## References

**What research, papers, or observations support this hypothesis?**

- Multiple timeframe analysis is a well-established practice among professional traders
- Elder, Alexander. "Trading for a Living" (Triple Screen Trading System)
- Murphy, John J. "Technical Analysis of the Financial Markets" (Chapter on multiple timeframes)
- Academic research on momentum persistence across timeframes

**Codebase References (v1.11.0+):**
- `lib/bundles/` - Data bundle management and ingestion
- `lib/validation/` - Data quality validation
- `lib/calendars/` - Trading calendar management
- `lib/config/` - Configuration loading and validation
- `lib/backtest/` - Backtest execution and results
- `lib/metrics/` - Performance metrics calculation
- `docs/api/` - Complete API documentation
- `CLAUDE.md` - Project overview and version history

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial hypothesis | Strategy Developer Agent |
