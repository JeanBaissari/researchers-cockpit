# Strategy Hypothesis: Scalping Momentum

> **Strategy Type:** High-Frequency Momentum Scalping
> **Asset Class:** Forex (EURUSD primary, NZDJPY secondary)
> **Timeframe:** 5-minute bars
> **Expected Hold Time:** 10-30 minutes (2-6 bars)

---

## The Belief

**What specific market behavior are we exploiting?**

Short-term momentum persists for 10-30 minutes in liquid forex pairs. When price makes a strong directional move (indicated by Rate of Change exceeding a threshold), it tends to continue in that direction for several bars before reverting. This high-frequency strategy captures these brief momentum bursts by entering quickly when momentum is detected and exiting within a fixed time window.

The combination of ROC (measuring price velocity) and RSI (measuring relative strength) filters out weak momentum signals and identifies genuine directional moves.

---

## The Reasoning

**Why does this behavior exist?**

1. **Order Flow Cascades**: Large institutional orders create temporary imbalances that take multiple bars to fully execute, causing persistent price movement.

2. **Stop Hunting Dynamics**: When price breaks key levels, stop-loss cascades trigger additional orders in the same direction, extending the move.

3. **Algorithmic Herding**: Many trading algorithms use similar momentum signals, creating self-reinforcing moves in the short term.

4. **Market Maker Adjustment**: After significant moves, market makers adjust their quotes, and the bid-ask spread temporarily widens, creating momentum continuation before mean reversion begins.

5. **Information Propagation**: Economic data and news take time to be fully absorbed by all market participants, creating short-term trending behavior.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Active trading sessions (London Open, NY Open, London/NY Overlap)
- High liquidity periods with tight spreads
- Days with clear directional bias from fundamentals
- Volatile market conditions (higher ROC readings)
- Trending micro-structure environments

**Fails in:**
- Low liquidity periods (Asian session for EUR pairs, rollover times)
- Consolidation/ranging markets with no directional bias
- News blackout periods with minimal volatility
- Weekend gaps and Monday morning open
- Holiday trading sessions with reduced participation
- High-spread environments where transaction costs exceed expected gains

---

## The Falsification

**What result would prove this hypothesis wrong?**

- If Sharpe Ratio < 0.3 across 6+ months of data, the edge is insufficient to overcome costs
- If win rate < 35%, the signal quality is too poor
- If average loss > 2x average win, risk/reward is unacceptable
- If net returns are negative after realistic transaction costs (spread + commission)
- If maximum drawdown > 15%, the strategy is too risky for the expected returns
- If the strategy underperforms buy-and-hold during trending periods

**Critical Warning**: This is a high-frequency strategy with thin margins. Transaction costs are the primary determinant of profitability. Only suitable for:
- Low-spread brokers (< 0.5 pips for EURUSD)
- ECN/STP execution with minimal slippage
- Accounts with competitive commission structures

---

## Implementation Notes

**How is this hypothesis translated into code?**

**Signal Generation:**
1. **ROC (Rate of Change)**: Calculate 5-bar price change percentage
   - Long entry: ROC > 0.3% AND RSI > 55
   - Short entry: ROC < -0.3% AND RSI < 45

2. **RSI Filter**: 7-period RSI confirms momentum direction
   - Long: RSI above neutral (55) indicates buying pressure
   - Short: RSI below neutral (45) indicates selling pressure

3. **Exit Conditions**:
   - Time-based exit: Maximum 6 bars (30 minutes)
   - Signal reversal: Opposite signal generated
   - Stop loss: 1.5% from entry
   - Take profit: 2.5% from entry

**Module Usage (v1.11.0+):**
- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: Fixed 90% allocation (fast entry/exit required)
- Risk management: Custom stop/take-profit with time-based exit
- Data access: `data.history()` for 5-minute bar data
- Validation: `lib.validation.validate_bundle()` to verify data quality

**Key Implementation Details:**
- Uses `handle_data()` for bar-by-bar processing (scalping requires immediate response)
- Tracks bar count since entry for time-based exit
- Supports both long and short positions
- Records detailed metrics for post-analysis

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| roc_threshold | High | Determines signal frequency; too low = many false signals, too high = missed opportunities |
| rsi_long_threshold | High | Filters momentum quality; affects win rate significantly |
| max_hold_bars | Medium | Balances capturing full moves vs. avoiding reversals |
| stop_loss_pct | Medium | Protects against adverse moves; too tight = whipsawed out |
| roc_period | Low | 5 bars is standard for 5m scalping; minor variations |
| rsi_period | Low | 7-14 range all work reasonably well |

**Critical Parameters:**
1. `roc_threshold` - Most affects Sharpe ratio
2. `rsi_long_threshold` / `rsi_short_threshold` - Second most impactful
3. `max_hold_bars` - Third priority

**Robust Parameters:**
- `rsi_period` - Works well across 5-14 range
- `roc_period` - 4-7 bars all perform similarly

**Optimization Priority:**
1. roc_threshold (0.002 - 0.005)
2. RSI thresholds (50-60 long, 40-50 short)
3. max_hold_bars (4-12)

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 6+ months for regime diversity
- Frequency: 5-minute OHLCV bars
- Observations: At least 50,000 bars (approximately 6 months of forex data)

**Warmup Period:**
- Required: 3 days (minimal warmup for fast indicators)
- Must be >= max(roc_period, rsi_period) in bars
- At 5m frequency: 3 days = 3 * 24 * 12 = 864 bars (sufficient for RSI 7)
- Configure in `parameters.yaml` under `backtest.warmup_days`

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source csv --assets forex --timeframe 5m`
- Bundle naming: `csv_eurusd_5m` or `csv_nzdjpy_5m`
- Supported sources: csv (for historical data), yahoo (limited 5m history)

**Data Quality:**
- [x] Adjusted prices required? No (forex has no splits/dividends)
- [x] Volume data required? Optional (forex volume is indicative only)
- [x] Missing data tolerance: 5 consecutive bars max (5m * 5 = 25 minutes)
- Validation handled by `lib/validation/DataValidator` (v1.11.0+)

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 | FOREX | No weekends, uses `lib.calendars.ForexCalendar` (v1.11.0+) |

**5-Minute Data Specifics:**
- 288 bars per trading day (24 hours * 12 bars/hour)
- Approximately 74,880 bars per year
- Gap handling important around weekend close/open

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | ATR Equivalent | Expected Behavior | Recommended Action |
|--------|----------------|-------------------|-------------------|
| Low Vol | ATR < 30 pips | Few signals, lower win rate | Consider pausing |
| Normal Vol | 30-60 pips | Optimal performance | Normal operation |
| High Vol | 60-100 pips | More signals, higher variance | Reduce position size |
| Crisis | > 100 pips | Wide spreads, slippage risk | Strongly consider pausing |

**Regime Detection:**
- How to identify current regime: 20-bar ATR on 5m data, annualized
- Indicators to watch: ATR, realized volatility, bid-ask spread

**Adaptive Behavior:**
- [x] Should position sizing scale with volatility? No - fixed 90% for speed
- [ ] Should parameters adapt to regime? Not in base implementation
- [x] Should strategy pause in certain regimes? Yes, in very low or crisis volatility

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (SPY) | Low | Good - FX uncorrelated to equities |
| Momentum Factor | Medium | Moderate - captures similar dynamics |
| Mean Reversion | Negative | Good - opposite strategy type |
| Carry Trade | Low | Good - different driver |
| Breakout Strategies | Medium | Some overlap in trending periods |

**Portfolio Construction Notes:**
- Best paired with: Mean reversion strategies, longer-term trend followers
- Avoid combining with: Other short-term momentum strategies on same pairs
- Suggested portfolio weight: 5-10% of strategy allocation (high-frequency, high-turnover)

**Return Driver Analysis:**
- [x] Long-biased or market-neutral? Market-neutral (trades both directions)
- [x] Exposed to specific sector risk? No - currency-specific only
- [x] Sensitive to interest rate changes? Minor - primarily technical-driven

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [x] Sharpe ratio < 0.3 for 3 consecutive months
- [x] Maximum drawdown exceeds 15%
- [x] Win rate drops below 35% over 200 trades
- [x] 3 consecutive losing weeks
- [x] Net returns negative after costs for 2+ months

**Qualitative Triggers:**
- [x] Broker significantly increases spreads on traded pairs
- [x] Execution quality degrades (increased slippage)
- [x] Market structure changes (reduced 5m momentum persistence)
- [x] Transaction costs become prohibitive

**Review Schedule:**
- Daily: Monitor P&L, win rate, transaction costs
- Weekly: Review rolling metrics, compare to expectations
- Monthly: Deep dive into strategy health, regime analysis
- Quarterly: Full re-evaluation, consider parameter re-optimization

---

## Optimization Bounds

**Valid parameter ranges for optimization searches:**

| Parameter | Min | Max | Step | Default | Rationale |
|-----------|-----|-----|------|---------|-----------|
| roc_period | 3 | 10 | 1 | 5 | Short lookback for scalping |
| roc_threshold | 0.002 | 0.005 | 0.0005 | 0.003 | 0.2%-0.5% moves are significant for 5m |
| rsi_period | 5 | 14 | 1 | 7 | Standard RSI range |
| rsi_long_threshold | 50 | 60 | 2 | 55 | Above neutral for longs |
| rsi_short_threshold | 40 | 50 | 2 | 45 | Below neutral for shorts |
| max_hold_bars | 4 | 12 | 2 | 6 | 20-60 minutes hold time |
| stop_loss_pct | 0.01 | 0.025 | 0.005 | 0.015 | 1-2.5% stop range |
| take_profit_pct | 0.02 | 0.04 | 0.005 | 0.025 | 2-4% take profit |

**Parameter Constraints:**
- take_profit_pct should be > stop_loss_pct * 1.5 (minimum 1.5:1 reward/risk)
- rsi_long_threshold should be > 50 (above neutral)
- rsi_short_threshold should be < 50 (below neutral)

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time
- Walk-forward window: 30 days train / 7 days test
- Out-of-sample threshold: Must retain 60%+ of in-sample Sharpe
- Number of trials limit: < 50 combinations

**Optimization Strategy:**
- Recommended method: Grid search (small parameter space)
- Cross-validation folds: 5-fold time-series split
- Primary objective: Sharpe ratio after transaction costs

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 0.5 (after transaction costs)
- Win Rate > 40%
- Profit Factor > 1.2
- Maximum Drawdown < 12%
- Average trades per day: 2-5 (not over-trading)
- Average hold time: 15-30 minutes
- Positive expectancy per trade > 0.1% after costs

---

## Transaction Cost Warning

**CRITICAL: This strategy's viability depends heavily on transaction costs.**

| Cost Component | Maximum Acceptable | Impact on Returns |
|----------------|-------------------|-------------------|
| Spread (EURUSD) | 0.5 pips | Major - enters/exits frequently |
| Commission | $3 per round-turn per lot | Moderate |
| Slippage | 0.2 pips per trade | Moderate |
| **Total** | **< 1 pip per round-turn** | **Critical threshold** |

If total transaction costs exceed 1 pip per round-turn, this strategy will likely be unprofitable.

**Recommended Broker Requirements:**
- ECN/STP execution
- Spreads < 0.3 pips during active sessions
- No dealing desk intervention
- Fast execution (< 50ms)

---

## References

**What research, papers, or observations support this hypothesis?**

1. Barberis, Shleifer, Vishny (1998) - "A Model of Investor Sentiment" - momentum persistence
2. Jegadeesh, Titman (1993) - "Returns to Buying Winners and Selling Losers" - momentum returns
3. Practical observation: Market microstructure studies show short-term momentum in liquid markets

**Codebase References (v1.11.0+):**
- `lib/bundles/` - Data bundle management and ingestion
- `lib/validation/` - Data quality validation
- `lib/calendars/` - Trading calendar management (FOREX calendar)
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
