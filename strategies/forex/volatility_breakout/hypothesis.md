# Strategy Hypothesis: Volatility Breakout

> **Strategy Name:** volatility_breakout
> **Asset Class:** Forex
> **Primary Symbol:** EURUSD
> **Secondary Symbol:** NZDJPY
> **Timeframe:** 4-hour (4H)

---

## The Belief

**What specific market behavior are we exploiting?**

Volatility expansion signals regime change and trending moves in forex markets. When price breaks decisively outside Bollinger Bands (closes above the upper band or below the lower band), it indicates that the market has entered a high-momentum state that often persists for multiple bars.

The Bollinger Band breakout captures the transition from low-volatility consolidation to high-volatility trending conditions. This strategy exploits the tendency of forex prices to trend after volatility expansion events, riding the momentum until the market returns to a mean-reverting state (price moves back inside the bands) or a protective stop is triggered.

---

## The Reasoning

**Why does this behavior exist?**

1. **Volatility Clustering**: Financial markets exhibit volatility clustering - periods of high volatility tend to follow high volatility, and low volatility follows low volatility. A breakout beyond 2 standard deviations signals the start of a high-volatility cluster.

2. **Institutional Order Flow**: Large institutional orders often cause sustained directional moves that push prices beyond normal ranges. Once initiated, these flows tend to persist as institutions scale into positions.

3. **Technical Trader Behavior**: Many traders use Bollinger Bands as a reference. Breakouts trigger momentum-following entries from technical traders, creating self-reinforcing price movement.

4. **Stop-Loss Cascades**: Prices breaking key technical levels trigger stop-loss orders from counter-positioned traders, accelerating the move in the breakout direction.

5. **24/5 Forex Market Dynamics**: Unlike equity markets, forex operates continuously during weekdays. This allows momentum moves to develop more cleanly without opening gaps disrupting the signal.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Trending market environments
- During high-impact economic news releases that shift fundamentals
- When central bank policy divergence creates directional bias
- High liquidity sessions (London/NY overlap for EURUSD)
- After periods of consolidation (tight bands) that precede breakouts

**Fails in:**
- Range-bound, choppy markets with frequent false breakouts
- Low liquidity periods (Asian session for major pairs, holiday periods)
- During extreme volatility spikes (flash crashes) where stops may not execute cleanly
- When bands are already wide (price is volatile but directionless)
- During conflicting economic data releases that create whipsaw price action

---

## The Falsification

**What result would prove this hypothesis wrong?**

- If Sharpe Ratio < 0.5 across 3+ years of data, the edge from volatility breakouts is insufficient
- If maximum drawdown > 25%, the risk-adjusted returns are unacceptable for a systematic strategy
- If win rate < 35% with average winner not exceeding 2x average loser, the strategy economics fail
- If performance degrades significantly in recent years (2023-2025), the market dynamics may have changed
- If walk-forward validation shows > 40% degradation from in-sample to out-of-sample, overfitting is likely

---

## Implementation Notes

**How is this hypothesis translated into code?**

**Indicator Calculations:**

1. **Bollinger Bands** (20-period SMA with 2 standard deviation bands):
   - Middle Band = SMA(Close, 20)
   - Upper Band = Middle Band + (2 * StdDev(Close, 20))
   - Lower Band = Middle Band - (2 * StdDev(Close, 20))

2. **ATR (Average True Range)** for stop-loss calculation:
   - True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
   - ATR = SMA(True Range, 14)

**Entry Rules:**
- **Long Entry**: Close > Upper Bollinger Band
- **Short Entry**: Close < Lower Bollinger Band

**Exit Rules:**
- **Signal Exit**: Close returns inside the Bollinger Bands (between upper and lower)
- **Stop Loss**: Entry price +/- (ATR * atr_multiplier) depending on position direction
- **Trailing Stop**: 10% from highest/lowest price since entry (optional)

**Position Sizing:**
- Volatility-scaled targeting 20% annual portfolio volatility
- Formula: position_size = target_vol / realized_vol
- Clamped between min_position_pct (10%) and max_position_pct (95%)

**Module Usage (v1.11.0+):**
- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: `lib.position_sizing.compute_position_size()` for volatility-scaled sizing
- Risk management: Custom ATR-based stops (strategy-specific, not using lib.risk_management)
- Calendar: Uses FOREX calendar (24/5 trading, 260 days/year)
- Data access: Requires 4H data bundle (csv_eurusd_4h)

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| bb_period | High | Shorter periods = more signals, more noise; longer = smoother, fewer opportunities |
| bb_std | High | Lower std dev = more entries, more false signals; higher = fewer, higher quality entries |
| atr_multiplier | Medium | Affects stop distance - too tight = frequent stops, too wide = large losses |
| volatility_target | Medium | Higher target = larger positions, more volatility; lower = smaller, smoother equity curve |
| trailing_stop_pct | Low | Fine-tuning profit protection; moderate sensitivity |
| atr_period | Low | Standard 14-period ATR is robust across most configurations |

**Critical Parameters:**
- bb_period and bb_std together define the breakout threshold
- atr_multiplier is critical for managing downside risk

**Robust Parameters:**
- atr_period (14 is a well-tested default)
- trailing_stop_pct (secondary exit mechanism)

**Optimization Priority:**
1. bb_std (defines signal quality threshold)
2. bb_period (defines lookback for volatility assessment)
3. atr_multiplier (defines stop-loss distance)

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 3+ years for regime diversity (2020-2025 covers COVID volatility and normalization)
- Frequency: 4-hour OHLCV data
- Observations: At least 4,000 4-hour bars (approximately 3 years)

**Warmup Period:**
- Required: 30 days minimum (for 20-period BB and 14-period ATR on 4H data)
- Calculation: max(bb_period, atr_period) * (24/4) / trading_bars_per_day + buffer
- Configure in `parameters.yaml` under `backtest.warmup_days`
- Calculated automatically by `lib.config.get_warmup_days()` (v1.11.0+)

**Data Ingestion (v1.11.0+):**
- Primary bundle: `csv_eurusd_4h`
- Secondary bundle: `csv_nzdjpy_4h` (for multi-asset validation)
- CLI: `python scripts/ingest_data.py --source csv --assets forex --symbols EURUSD --timeframe 4h`
- See `lib/bundles/` package for bundle management utilities

**Data Quality Validation:**
- Pre-ingestion: Use `lib.validation.validate_before_ingest()` to validate source data
- Bundle validation: Use `lib.validation.validate_bundle()` to verify bundle integrity
- CLI: `python scripts/validate_bundles.py csv_eurusd_4h`

**Data Quality:**
- [x] Adjusted prices required? No (forex has no corporate actions)
- [x] Volume data required? No (used for reference only, not in signal generation)
- [x] Missing data tolerance: 5 consecutive bars max (weekends excluded)

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 | FOREX | Continuous trading Mon-Fri, uses `lib.calendars.ForexCalendar` |

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | VIX Equivalent | Expected Behavior | Recommended Action |
|--------|----------------|-------------------|-------------------|
| Low Vol | < 10 (FXVIX) | Few signals, bands tight, breakouts may be significant | Normal position sizing |
| Normal Vol | 10-15 | Regular signal flow, typical performance | Normal operation |
| High Vol | 15-25 | More signals, larger moves, wider stops | Consider reducing position size |
| Crisis | > 25 | Frequent signals but chaotic price action | Reduce to 50% position size |

**Regime Detection:**
- Monitor realized volatility vs. BB width (ATR/price ratio)
- When ATR > 2% of price for forex, consider reducing exposure

**Adaptive Behavior:**
- [x] Should position sizing scale with volatility? Yes (volatility_scaled method)
- [ ] Should parameters adapt to regime? No (fixed parameters for simplicity)
- [ ] Should strategy pause in certain regimes? Optional (crisis regime reduction)

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| USD Index (DXY) | Medium-High | Moderate - directionally exposed to USD |
| Momentum Factor | High | Low - similar alpha source |
| Mean Reversion | Negative | Excellent - opposite market view |
| Carry Trade | Low | Good - different alpha source |
| Volatility | Positive | Poor in isolation - benefits from high vol |

**Portfolio Construction Notes:**
- Best paired with: Mean reversion strategies, carry strategies
- Avoid combining with: Other momentum/breakout strategies on correlated pairs
- Suggested portfolio weight: 15-25% of strategy allocation

**Return Driver Analysis:**
- [x] Long-biased or market-neutral? Can be either - takes both long and short positions
- [ ] Exposed to specific sector risk? No sectors in forex
- [x] Sensitive to interest rate changes? Indirectly through central bank policy impact on volatility

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [ ] Sharpe ratio < 0.3 for 6 consecutive months
- [ ] Maximum drawdown exceeds 30%
- [ ] Win rate drops below 30% over 50+ trades
- [ ] 4 consecutive losing months
- [ ] Annual return < -10% for 1 year

**Qualitative Triggers:**
- [ ] Major structural change in forex market microstructure
- [ ] Regulatory changes affecting retail forex trading
- [ ] Strategy becomes widely published and crowded
- [ ] Data quality issues with 4H data source

**Review Schedule:**
- Weekly: Monitor rolling Sharpe, drawdown, signal frequency
- Monthly: Compare live vs. backtest metrics, review losing trades
- Quarterly: Walk-forward revalidation, parameter sensitivity analysis
- Annually: Full hypothesis reassessment, consider retirement

---

## Optimization Bounds

**Valid parameter ranges for optimization searches:**

| Parameter | Min | Max | Step | Default | Rationale |
|-----------|-----|-----|------|---------|-----------|
| bb_period | 15 | 30 | 5 | 20 | Standard BB period range, balances signal quality vs frequency |
| bb_std | 1.5 | 2.5 | 0.25 | 2.0 | Below 1.5 too noisy, above 2.5 too few signals |
| atr_period | 10 | 20 | 2 | 14 | Standard ATR period range |
| atr_multiplier | 1.5 | 3.0 | 0.25 | 2.0 | Below 1.5 stops too tight, above 3.0 losses too large |
| volatility_target | 0.15 | 0.30 | 0.05 | 0.20 | Risk tolerance range |
| trailing_stop_pct | 0.05 | 0.15 | 0.025 | 0.10 | Secondary exit fine-tuning |

**Parameter Constraints:**
- bb_period should allow sufficient samples for std dev calculation (>= 15)
- atr_multiplier should be <= bb_std * 1.5 to avoid stops beyond breakout threshold

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time (bb_period, bb_std, atr_multiplier)
- Walk-forward window: 252 4H-bar-days train / 63 4H-bar-days test
- Out-of-sample threshold: Must retain 60%+ of in-sample Sharpe
- Number of trials limit: < 100 combinations

**Optimization Strategy:**
- Recommended method: Grid search for initial exploration, random search for refinement
- Cross-validation folds: 5-fold time-series split
- Primary objective: Sharpe ratio (risk-adjusted returns)

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 0.75 (good risk-adjusted returns for systematic forex)
- Maximum Drawdown < 20% (acceptable risk level)
- Win Rate > 40% with Profit Factor > 1.5
- Consistent performance across different volatility regimes
- Walk-forward out-of-sample Sharpe >= 60% of in-sample
- Minimum 100 trades over backtest period for statistical significance

---

## References

**What research, papers, or observations support this hypothesis?**

1. **Bollinger on Bollinger Bands** - John Bollinger's original work on band-based trading
2. **Volatility Clustering in Financial Markets** - Mandelbrot, Engle (ARCH/GARCH literature)
3. **Momentum in FX Markets** - Academic evidence of short-term momentum in currency markets
4. **Trading with Bollinger Bands** - Various practitioner resources on band-based strategies

**Codebase References (v1.11.0+):**
- `lib/bundles/` - Data bundle management and ingestion
- `lib/validation/` - Data quality validation
- `lib/calendars/` - Trading calendar management (ForexCalendar)
- `lib/config/` - Configuration loading and validation
- `lib/backtest/` - Backtest execution and results
- `lib/metrics/` - Performance metrics calculation
- `docs/api/` - Complete API documentation
- `CLAUDE.md` - Project overview and version history

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-20 | Initial hypothesis created for volatility_breakout strategy | Strategy Developer Agent |
