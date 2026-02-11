# Strategy Hypothesis: Forex Range Trading

> **Market Behavior:** Forex pairs spend 60-70% of time in range-bound consolidation between support and resistance levels. This strategy exploits mean reversion within identifiable ranges.

---

## The Belief

**What specific market behavior are we exploiting?**

Currency pairs oscillate between support and resistance levels during consolidation phases. When price approaches established range boundaries, there is a statistically higher probability of reversion to the mean rather than breakout. This strategy uses Bollinger Bands to dynamically identify these range boundaries and RSI to confirm oversold/overbought conditions before entering mean-reversion trades.

The core insight: Markets trend only 30-40% of the time. The remaining 60-70% is spent in consolidation where range-trading strategies can capture multiple smaller profitable moves while trend-following strategies get whipsawed.

---

## The Reasoning

**Why does this behavior exist?**

1. **Market Microstructure:** Large institutional orders are often executed within ranges to minimize market impact. Banks and hedge funds accumulate/distribute positions at key levels, creating support/resistance.

2. **Profit-Taking Behavior:** After directional moves, traders take profits creating natural reversal points. This profit-taking clusters at round numbers and technical levels.

3. **Option Market Dynamics:** FX option expirations and hedging activity around strike prices create "gravity" that keeps price within ranges, especially during low-volatility periods.

4. **Liquidity Clustering:** Market makers provide liquidity at known levels, making it harder for price to escape ranges without significant fundamental catalysts.

5. **Mean-Reversion Tendency:** Exchange rates have fundamental equilibrium levels based on purchasing power parity, interest rate differentials, and trade flows. Deviations from these levels tend to correct over time.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Low to moderate volatility environments (normal market conditions)
- During consolidation phases after trending moves
- News-quiet periods (no major economic announcements)
- Stable interest rate differential environments
- Overlapping trading sessions with high liquidity (London-NY overlap)

**Fails in:**
- Trending markets with strong momentum (band expansion filter required)
- High-impact news events (NFP, central bank decisions)
- Volatile market regimes (VIX equivalent > 20)
- Breakout scenarios with follow-through
- Low liquidity periods (Asian session for EUR/USD)

---

## The Falsification

**What result would prove this hypothesis wrong?**

- If Sharpe < 0.3 across 3+ years of data, the range-trading edge does not exist for the tested pairs
- If maximum drawdown > 25%, risk-adjusted returns are unacceptable
- If win rate < 45%, the mean-reversion hypothesis is invalid
- If average winner/loser ratio < 0.8, losses exceed recoverable gains
- If > 40% of trades are stopped out at loss, the range identification is faulty

---

## Implementation Notes

**How is this hypothesis translated into code?**

**Entry Logic:**
1. **Long Entry:** Price touches lower Bollinger Band (20-period, 2 std dev) AND RSI(14) < 40
   - Rationale: Price at statistical lower bound + momentum confirms oversold
2. **Short Entry:** Price touches upper Bollinger Band AND RSI(14) > 60
   - Rationale: Price at statistical upper bound + momentum confirms overbought

**Exit Logic:**
1. **Mean Reversion Exit:** Price reaches middle Bollinger Band (20-period SMA)
   - Rationale: Target is the statistical mean, capturing the reversion move
2. **Opposite Signal Exit:** Exit if opposite entry conditions are met
   - Rationale: Prevents holding through new signal in opposite direction
3. **Stop Loss:** 4% fixed stop beyond the touched band
   - Rationale: Protects against breakouts that invalidate the range assumption
4. **Band Expansion Exit:** Exit if Bollinger Band width > 1.2x average width
   - Rationale: Band expansion signals potential breakout/trend, invalidating range assumption

**Position Sizing:**
- Volatility-scaled targeting 12% annualized volatility
- Conservative sizing appropriate for mean-reversion (lower per-trade conviction than trend-following)

**Module Usage (v1.11.0+):**
- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: `lib.position_sizing.compute_position_size()` for volatility-scaled sizing
- Risk management: `lib.risk_management.check_exit_conditions()` for stop losses
- Pipeline setup: Not used (use_pipeline: false for forex)
- Data access: `lib.bundles.load_bundle()` to access bundle data
- Validation: `lib.validation.validate_bundle()` to verify data quality

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| bb_period | High | Defines the range identification window; too short = noisy ranges, too long = slow adaptation |
| bb_std | High | Controls band width; narrower bands = more signals but higher whipsaw risk |
| rsi_lower/upper | Medium | Entry confirmation; too strict = missed opportunities, too loose = false signals |
| band_expansion_threshold | Medium | Trend filter sensitivity; affects ability to avoid breakouts |
| stop_loss_pct | Low | Risk management safety net; affects max loss per trade |

**Critical Parameters:**
- bb_period (20): Core range identification - most impact on Sharpe ratio
- bb_std (2.0): Trade frequency vs. quality tradeoff

**Robust Parameters:**
- rsi_period (14): Industry standard, small changes minimal impact
- volatility_target (0.12): Conservative setting, can be adjusted based on risk appetite

**Optimization Priority:**
1. bb_period (15-30) - Most impactful
2. bb_std (1.5-2.5) - Second most impactful
3. rsi_lower/rsi_upper (30-45 / 55-70) - Entry refinement

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 3+ years for regime diversity (capturing both range-bound and trending periods)
- Frequency: 30-minute OHLCV (strategy timeframe)
- Observations: At least 25,000 bars (3 years of 30m data = ~62,000 bars)

**Warmup Period:**
- Required: 20 days minimum (for Bollinger Band calculation)
- Must be >= bb_period (20 bars at 30m = ~40 hours for full BB, but using daily bars for BB calculation)
- Configure in `parameters.yaml` under `backtest.warmup_days`
- Calculated automatically by `lib.config.get_warmup_days()` (v1.11.0+)

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source csv --assets forex --timeframe 30m`
- Bundle naming: `csv_eurusd_30m` (recommended naming convention)
- Supported sources: yahoo, csv

**Data Quality:**
- [x] Adjusted prices required? No (forex has no splits/dividends)
- [x] Volume data required? No (forex volume data is unreliable/unavailable)
- [x] Missing data tolerance: 5 consecutive bars max (will gap-fill)
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

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | FX Volatility | Expected Behavior | Recommended Action |
|--------|---------------|-------------------|-------------------|
| Low Vol | < 8% ann. | Strong performance, clear ranges | Normal operation, potentially increase position sizes |
| Normal Vol | 8-15% ann. | Good performance, ranges may widen | Normal operation |
| High Vol | 15-25% ann. | Reduced performance, ranges unstable | Reduce position sizes, tighten band expansion filter |
| Crisis | > 25% ann. | Poor performance, breakouts dominate | Consider pausing or significantly reducing exposure |

**Regime Detection:**
- How to identify current regime: 20-day rolling volatility of daily returns
- Indicators to watch: Bollinger Band width, ATR expansion, consecutive band touches

**Adaptive Behavior:**
- [x] Should position sizing scale with volatility? Yes - volatility-scaled sizing is core
- [x] Should parameters adapt to regime? Consider widening bands in high volatility
- [x] Should strategy pause in certain regimes? Yes - band expansion filter provides automatic pause

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (S&P 500) | Low | Good - FX ranges often independent of equity trends |
| Momentum Factor | Negative | Excellent - mean-reversion is opposite of momentum |
| Carry Trade | Low-Medium | Moderate - some correlation via interest rate sensitivity |
| Volatility (VIX) | Negative | Good - performs better when volatility is low |

**Portfolio Construction Notes:**
- Best paired with: Trend-following strategies, momentum strategies
- Avoid combining with: Other mean-reversion strategies on same pairs
- Suggested portfolio weight: 15-25% of strategy allocation

**Return Driver Analysis:**
- [x] Long-biased or market-neutral? Market-neutral (takes both long and short positions)
- [x] Exposed to specific sector risk? Interest rate differential risk
- [x] Sensitive to interest rate changes? Yes, but primarily through volatility impact

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [x] Sharpe ratio < 0.3 for 6 consecutive months
- [x] Maximum drawdown exceeds 30%
- [x] Win rate drops below 40% over 100 trades
- [x] 4 consecutive losing months
- [x] Annual return < -5% for 2+ years

**Qualitative Triggers:**
- [x] Central bank policy divergence creates sustained trends
- [x] Geopolitical events create persistent directional bias
- [x] Market structure changes (algorithm proliferation reduces range-bound behavior)
- [x] Data source quality degrades

**Review Schedule:**
- Weekly: Monitor live performance vs. backtest expectations, check band expansion frequency
- Monthly: Review rolling metrics, compare to benchmarks, assess regime
- Quarterly: Deep dive into strategy health, reassess hypothesis
- Annually: Full re-evaluation, parameter optimization refresh

---

## Optimization Bounds

**Valid parameter ranges for optimization searches:**

| Parameter | Min | Max | Step | Default | Rationale |
|-----------|-----|-----|------|---------|-----------|
| bb_period | 15 | 30 | 1 | 20 | Shorter periods react faster, longer smoother |
| bb_std | 1.5 | 2.5 | 0.1 | 2.0 | Industry standard is 2.0, allow exploration |
| rsi_period | 10 | 20 | 2 | 14 | Standard RSI period range |
| rsi_lower | 30 | 45 | 5 | 40 | Oversold threshold range |
| rsi_upper | 55 | 70 | 5 | 60 | Overbought threshold range |
| band_expansion_threshold | 1.0 | 1.5 | 0.1 | 1.2 | Trend detection sensitivity |
| stop_loss_pct | 0.02 | 0.06 | 0.01 | 0.04 | Risk tolerance range |

**Parameter Constraints:**
- rsi_upper must be > rsi_lower + 10 (avoid overlapping thresholds)
- stop_loss_pct should be < expected profit target
- bb_period should be >= 15 for statistical significance

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time
- Walk-forward window: 252 days train / 63 days test
- Out-of-sample threshold: Must retain 70%+ of in-sample Sharpe
- Number of trials limit: < 200 combinations

**Optimization Strategy:**
- Recommended method: Grid search for bb_period/bb_std first, then random search for RSI thresholds
- Cross-validation folds: 5-fold time-series split
- Primary objective: Sharpe ratio

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 0.5 (conservative target for mean-reversion)
- Maximum Drawdown < 20%
- Win Rate > 50%
- Average profit/loss ratio > 0.8
- Band expansion filter activates < 30% of potential signals
- Consistent performance across different volatility regimes (Sharpe within 0.3 of average)

---

## References

**What research, papers, or observations support this hypothesis?**

1. **Empirical Studies:** Academic research on mean-reversion in FX markets (e.g., Clarida, Taylor studies on exchange rate behavior)
2. **Market Microstructure:** Literature on institutional order flow and price discovery in FX
3. **Technical Analysis:** Bollinger's original work on bands and volatility normalization
4. **Quantitative Finance:** Studies on the 60/40 range/trend split in financial markets

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
