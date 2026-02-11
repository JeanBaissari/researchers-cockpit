# Strategy Hypothesis: Trend Following Moving Average

> **Strategy Name:** trend_following_ma
> **Asset Class:** Forex
> **Timeframe:** 1-hour
> **Primary Symbol:** EURUSD
> **Secondary Symbol:** NZDJPY

---

## The Belief

**What specific market behavior are we exploiting?**

Forex trends persist over medium-term periods. When a fast moving average (20-period) crosses above a slow moving average (50-period), it signals the beginning of an uptrend. Conversely, when the fast MA crosses below the slow MA, it signals a downtrend. This strategy captures trend continuation by entering positions at these crossover points and holding until the trend reverses.

The moving average crossover is one of the most fundamental trend-following techniques because it:
1. Smooths out price noise to identify underlying direction
2. Provides objective, rule-based entry and exit signals
3. Naturally adapts to changing volatility through price-weighted averaging

---

## The Reasoning

**Why does this behavior exist?**

Forex trend persistence is driven by several market mechanics:

1. **Central Bank Policy Divergence**: Interest rate differentials between countries create sustained capital flows, driving long-term currency trends. When one central bank tightens while another eases, the higher-yielding currency tends to appreciate over extended periods.

2. **Momentum Traders and CTAs**: Commodity Trading Advisors and momentum funds use similar trend-following systems, creating self-reinforcing price movements. When trends begin, these participants pile in, extending the move.

3. **Carry Trade Flows**: Institutional investors borrowing in low-yield currencies to invest in high-yield currencies create persistent directional pressure.

4. **Slow Information Dissemination**: Macroeconomic data and policy changes take time to be fully priced in, allowing trends to develop gradually rather than instantly.

5. **Behavioral Biases**: Retail traders often trade against trends (fading moves), providing liquidity for trend followers. Anchoring bias causes market participants to underreact to new information.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Trending markets with clear directional bias
- Periods of monetary policy divergence between currency pairs
- Moderate to high volatility environments where trends are sustained
- During major economic cycles or geopolitical shifts
- When carry trade conditions favor one currency over another

**Fails in:**
- Choppy, sideways (range-bound) markets with frequent false breakouts
- Low volatility consolidation periods
- Around major news events that cause whipsaw price action
- During risk-off events where correlations spike and moves are erratic
- When both central banks are in similar policy stances

---

## The Falsification

**What result would prove this hypothesis wrong?**

- **Sharpe Ratio < 0.5** across 3+ years of data indicates the edge doesn't exist or is too weak
- **Maximum Drawdown > 25%** suggests unacceptable risk-adjusted returns
- **Win Rate < 35%** combined with average win/loss ratio < 2.0 indicates the strategy is not viable
- **Profit Factor < 1.2** over extended periods suggests no meaningful edge
- If the strategy underperforms buy-and-hold in trending periods, the signal generation is flawed

---

## Implementation Notes

**How is this hypothesis translated into code?**

### Signal Generation
- **Long Entry (Golden Cross)**: SMA(20) crosses above SMA(50)
- **Short Entry (Death Cross)**: SMA(20) crosses below SMA(50)
- **Exit**: Opposite crossover signal or trailing stop triggered

### Position Management
- **Position Size**: Fixed 95% allocation (aggressive for trend capture)
- **Trailing Stop**: 8% from peak to protect profits while allowing room for volatility
- **Fixed Stop Loss**: 5% to limit downside on false signals

### Technical Details
- Uses Simple Moving Average (SMA) rather than EMA for stability
- 1-hour timeframe balances noise reduction with responsiveness
- Crossover detection uses current bar comparison (not look-ahead)

**Module Usage (v1.11.0+):**
- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: Fixed method via `lib.position_sizing.compute_position_size()`
- Risk management: `lib.risk_management.check_exit_conditions()` for trailing stops
- Pipeline setup: Not used (`use_pipeline: false`) - direct price data access
- Data access: 1-hour bundle `csv_eurusd_1h` via `lib.bundles`
- Validation: `lib.validation.validate_bundle()` to verify data quality

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| fast_ma_period | High | Determines responsiveness to trend changes; too short = whipsaws, too long = late entries |
| slow_ma_period | High | Defines trend filter; must be significantly larger than fast period for meaningful signals |
| trailing_stop_pct | Medium | Balances profit protection vs. premature exits; critical for capturing full trend moves |
| stop_loss_pct | Low | Primarily affects worst-case scenarios; modest impact on overall performance |

**Critical Parameters:**
- `fast_ma_period` and `slow_ma_period` ratio (should maintain ~2.5x relationship)
- `trailing_stop_pct` (determines how much profit is captured vs. given back)

**Robust Parameters:**
- `max_position_pct` (within 0.80-1.00 range, impact is proportional)
- `stop_loss_pct` (within 0.03-0.08 range, impact is marginal)

**Optimization Priority:**
1. `slow_ma_period` (defines trend definition)
2. `fast_ma_period` (defines entry timing)
3. `trailing_stop_pct` (exit optimization)

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 3+ years for regime diversity (ideally 5+ years)
- Frequency: 1-hour OHLCV data
- Observations: At least 10,000 hourly bars (~15 months minimum)

**Warmup Period:**
- Required: 50 days (for 50-period slow MA calculation with buffer)
- Must be >= max(slow_ma_period) in hourly bars
- Configure in `parameters.yaml` under `backtest.warmup_days`
- Calculated automatically by `lib.config.get_warmup_days()` (v1.11.0+)

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source csv --assets forex --timeframe 1h`
- Bundle naming: `csv_eurusd_1h` (follows `{source}_{asset_class}_{timeframe}` convention)
- Supported sources: yahoo, csv (CSV preferred for historical forex data)
- See `lib/bundles/` package for bundle management utilities

**Data Quality Validation:**
- Pre-ingestion: Use `lib.validation.validate_before_ingest()` to validate source data
- Bundle validation: Use `lib.validation.validate_bundle()` to verify bundle integrity
- CLI: `python scripts/validate_bundles.py csv_eurusd_1h`
- Validation config: `ValidationConfig.strict()` for production
- See `lib/validation/` package for validation utilities

**Data Quality:**
- [x] Adjusted prices required? No (forex has no splits/dividends)
- [ ] Volume data required? Optional (not used in this strategy)
- [x] Missing data tolerance: 5 consecutive hours max

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 | FOREX | Uses `lib.calendars.ForexCalendar` (v1.11.0+) |

**Calendar Management (v1.11.0+):**
- Calendars defined in `lib/calendars/` package
- `ForexCalendar`: 24/5 trading (260 days/year, weekdays only)
- Calendar selection: `lib.calendars.get_calendar_for_asset_class('forex')`
- Session alignment: `lib/calendars/sessions/SessionManager` validates bundle-calendar alignment
- See `lib/calendars/` package for calendar utilities

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | Vol Proxy | Expected Behavior | Recommended Action |
|--------|-----------|-------------------|-------------------|
| Low Vol | ATR < 30 pips/day | Fewer signals, lower returns | Normal operation |
| Normal Vol | 30-60 pips/day | Optimal performance expected | Normal operation |
| High Vol | 60-100 pips/day | Larger wins/losses, more signals | Consider tighter trailing stop |
| Crisis | > 100 pips/day | Erratic performance, whipsaws | Consider pausing or reducing size |

**Regime Detection:**
- How to identify current regime: 20-day rolling ATR on hourly data
- Indicators to watch: VIX (risk sentiment), currency pair ATR, central bank announcements

**Adaptive Behavior:**
- [x] Should position sizing scale with volatility? Optional (using fixed for simplicity)
- [ ] Should parameters adapt to regime? No (maintain consistency)
- [x] Should strategy pause in certain regimes? Consider pausing during extreme volatility

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (SPY) | Low | Good for portfolio |
| Momentum Factor | Medium-High | Moderate |
| Value Factor | Low | Good for portfolio |
| Volatility | Medium (negative in crisis) | Moderate |
| Other Trend-Following | High | Poor for diversification |

**Portfolio Construction Notes:**
- Best paired with: Mean reversion strategies, carry strategies, or uncorrelated asset classes
- Avoid combining with: Other MA crossover strategies or momentum systems
- Suggested portfolio weight: 10-20% of strategy allocation

**Return Driver Analysis:**
- [x] Long-biased or market-neutral? Can go both long and short
- [x] Exposed to specific sector risk? Currency pair specific
- [ ] Sensitive to interest rate changes? Indirectly through currency valuation

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [x] Sharpe ratio < 0.3 for 12 consecutive months
- [x] Maximum drawdown exceeds 30%
- [x] Win rate drops below 30% over 100+ trades
- [x] 6+ consecutive losing months
- [x] Annual return < -10% for 2+ years

**Qualitative Triggers:**
- [x] Forex market structure fundamentally changes (e.g., fixed exchange rates)
- [x] Regulatory changes affect retail forex trading
- [x] Strategy becomes too crowded (MA crossovers become exploited)
- [x] Data source becomes unreliable or unavailable

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
| fast_ma_period | 10 | 30 | 2 | 20 | Short enough for responsiveness, long enough to filter noise |
| slow_ma_period | 40 | 100 | 5 | 50 | Long enough to define trend, short enough to capture moves |
| trailing_stop_pct | 0.05 | 0.15 | 0.01 | 0.08 | Balance between profit capture and room for volatility |
| stop_loss_pct | 0.03 | 0.08 | 0.01 | 0.05 | Tight enough to limit losses, loose enough to avoid whipsaws |

**Parameter Constraints:**
- `slow_ma_period` must be > `fast_ma_period * 1.5` (minimum separation)
- `trailing_stop_pct` should be > `stop_loss_pct` (trailing should be looser)
- `fast_ma_period` should be >= 10 (avoid noise sensitivity)

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time
- Walk-forward window: 180 days train / 60 days test (for hourly data)
- Out-of-sample threshold: Must retain 70%+ of in-sample Sharpe
- Number of trials limit: < 200 combinations

**Optimization Strategy:**
- Recommended method: Grid search (parameter space is small)
- Cross-validation folds: 5-fold time-series split
- Primary objective: Sharpe ratio (risk-adjusted return)

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 0.7 (conservative target)
- Maximum Drawdown < 20%
- Win Rate > 40% (acceptable for trend-following)
- Profit Factor > 1.5
- Average win > 2x average loss
- Consistent positive returns across different market regimes
- Outperforms buy-and-hold in trending periods

---

## References

**What research, papers, or observations support this hypothesis?**

1. **"Following the Trend" by Andreas Clenow** - Comprehensive guide to trend-following strategies
2. **"Quantitative Trading" by Ernest Chan** - Discusses MA crossover as foundation for systematic trading
3. **AQR Research** - Papers on momentum and trend-following in currencies
4. **CFTC Commitment of Traders** - Shows CTA positioning follows trends

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
| 2026-01-20 | Initial hypothesis creation | Strategy Developer Agent |
