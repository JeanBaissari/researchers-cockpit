# Strategy Hypothesis

> **REQUIRED:** Every strategy MUST have a hypothesis.md file. This document articulates what market behavior you're exploiting and why you believe it exists.

---

## The Belief

**What specific market behavior are we exploiting?**

The Breakout Intraday strategy exploits market inefficiencies by capturing momentum continuation when price breaks through previous day high/low levels in trending forex markets. This leverages the psychological significance of daily price boundaries and institutional order flow concentrations, particularly during the London trading session. Phase 11 enhancements (session filtering and ATR-based range detection) further mitigate weaknesses in low-quality or range-bound markets.

---

## The Reasoning

**Why does this behavior exist?**

The strategy is founded on the observation that price movements often accelerate after breaking significant previous day high/low levels due to concentrated institutional order flow and psychological factors. The London trading session provides optimal liquidity and statistically superior trending behavior, leading to higher win rates.

**Market Mechanics:**
- Institutional order flow concentrations at daily price boundaries create momentum continuation
- Psychological significance of previous day high/low levels attracts retail and institutional traders
- London session provides optimal liquidity and trending behavior (07:00-16:00 UTC)
- Breakout momentum persists for several hours after level breaks

**Historical Weaknesses (Phase 11 Enhancements Address):**
- **Session Quality Variation:** Trading all sessions equally led to lower win rates (35-45%) and false breakouts, especially in Asian and New York sessions. London-only mode addresses this by restricting trading to higher-quality sessions.
- **Range-Bound Market Whipsaws:** Consolidating markets frequently triggered both high and low breakouts, resulting in double losses. ATR-based range detection prevents trading during these periods, reducing whipsaw losses by 20-30%.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Trending markets with clear directional bias
- High to medium volatility environments (ATR > 1.5x average)
- London trading session (07:00-16:00 UTC) and London/NY overlap (13:00-16:00 UTC)
- Forex pairs with sufficient liquidity (major and minor pairs)
- Markets with clear previous day high/low levels

**Fails in:**
- Choppy, sideways markets (range-bound consolidation)
- Low volatility environments (ATR < 1.0x average)
- Asian and New York sessions (when London-only mode disabled)
- Low liquidity periods (weekend gaps, holiday periods)
- Markets with frequent false breakouts (addressed by range detection)

**Recommended Timeframes:**
- **15-minute (M15):** Faster signal generation and tighter stops
- **1-hour (H1):** Reduced noise and stronger breakout confirmation
- Both timeframes should be tested to determine optimal performance characteristics

**Session Filter (Phase 11 Enhancement):**
- Restricts trading to London session (07:00-16:00 UTC) and London/NY overlap (13:00-16:00 UTC) when `london_only_mode` is enabled
- Improves win rate by 5-10% compared to trading all sessions

**Range Detection Filter (Phase 11 Enhancement):**
- Prevents trading during range-bound markets
- If `(prev_day_high - prev_low) / ATR(14) < 1.5`, market is consolidating and signals are skipped
- Reduces whipsaw losses by 20-30%

**Daily Trade Limit:**
- Maximum 2 trades per day to prevent overtrading

**Exit Conditions:**
- Trailing Stop Exit: Activates after 10 pips profit, trails by 10 pips
- End-of-Day Exit: Mandatory close at 23:00 UTC
- Optional Opposite Signal Exit

---

## The Falsification

**What result would prove this hypothesis wrong?**

This hypothesis would be proven wrong if, after comprehensive backtesting with Phase 11 enhancements:

- **Sharpe Ratio:** Consistently below 1.0 across multiple market regimes
- **Maximum Drawdown:** Exceeds 8% over any 12-month period
- **Win Rate:** Falls below 45% over 100+ trades
- **Profit Factor:** Consistently below 1.2 (gross profit / gross loss)
- **Correlation:** Strategy fails to maintain low correlation with broader market movements
- **Phase 11 Enhancements:** London-only mode and range detection do not significantly improve win rate (by 5-10%) and reduce whipsaw losses (by 20-30%) compared to baseline

---

## Implementation Notes

**How is this hypothesis translated into code?**

The strategy implements breakout detection by:
- Calculating previous day high/low levels from minute data
- Detecting breakouts when current price exceeds previous day high (long) or falls below previous day low (short)
- Applying session filters to restrict trading to high-quality sessions
- Using ATR-based range detection to avoid consolidating markets
- Managing exits via trailing stops (pips-based activation) and end-of-day exits
- Enforcing daily trade limits to prevent overtrading

**Module Usage (v1.11.0+):**
- **Configuration:** `lib.config.load_strategy_params()` loads parameters from YAML
- **Position sizing:** Custom implementation for minute data volatility scaling (library function uses daily data)
- **Risk management:** `lib.risk_management.check_exit_conditions()` for basic stop losses; custom logic for pips-based trailing stop activation
- **Pipeline setup:** `lib.pipeline_utils.setup_pipeline()` for Pipeline API (disabled for forex)
- **Data access:** `lib.bundles.load_bundle()` to access bundle data
- **Validation:** `lib.validation.validate_bundle()` to verify data quality
- **Warmup calculation:** `lib.config.get_warmup_days()` automatically calculates required warmup period

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference
- `strategies/forex/breakout_intraday/strategy.py` - Full implementation

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| `london_only_mode` | High | Restricting to London session improves win rate by 5-10% |
| `range_detection_threshold` | High | Prevents whipsaw losses in consolidating markets (20-30% reduction) |
| `trailing_stop_pct` | Medium | Affects profit capture vs. premature exits |
| `volatility_target` | Medium | Position sizing sensitivity to volatility regime |
| `atr_period` | Low | ATR calculation period (14 is standard) |
| `eod_exit_hour` | Low | End-of-day exit timing (23:00 UTC standard) |

**Critical Parameters:**
- `london_only_mode`: Most significant impact on win rate
- `range_detection_threshold`: Most significant impact on reducing whipsaw losses
- `trailing_stop_pct`: Affects risk-adjusted returns

**Robust Parameters:**
- `TRAIL_ACTIVATION_PIPS`: 10 pips is standard and robust
- `TRAIL_DISTANCE_PIPS`: 10 pips is standard and robust
- `MAX_DAILY_TRADES`: 2 trades/day is standard for intraday strategies

**Optimization Priority:**
1. `range_detection_threshold` (1.0-2.5 range)
2. `london_only_mode` (boolean, test both settings)
3. `trailing_stop_pct` (0.03-0.20 range)
4. `volatility_target` (0.05-0.30 range)

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: 3+ years for regime diversity (trending, range-bound, high/low volatility)
- Frequency: 1-minute OHLCV data (required for intraday breakout detection)
- Observations: At least 500,000+ minute bars (3+ years of 1-minute data)

**Warmup Period:**
- Required: 30 days (includes 2-day buffer for previous day high/low calculations)
- Must be >= max(all indicator periods) + 2 days
- Configure in `parameters.yaml` under `backtest.warmup_days`
- Calculated automatically by `lib.config.get_warmup_days()` (v1.11.0+)

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source csv --assets forex --timeframe 1m`
- Bundle naming: `{source}_{asset_class}_{timeframe}` (e.g., `csv_forex_1m`)
- Supported sources: csv (local files), yahoo (limited to daily), binance (planned), oanda (planned)
- See `lib/bundles/` package for bundle management utilities

**Data Quality Validation:**
- Pre-ingestion: Use `lib.validation.validate_before_ingest()` to validate source data
- Bundle validation: Use `lib.validation.validate_bundle()` to verify bundle integrity
- CLI: `python scripts/validate_bundles.py {bundle_name}`
- Validation config: `ValidationConfig.strict()` for production, `lenient()` for testing
- See `lib/validation/` package for validation utilities

**Data Quality:**
- [x] Adjusted prices required? No (forex doesn't have splits/dividends)
- [x] Volume data required? Yes (for slippage modeling)
- [x] Missing data tolerance: 5 consecutive minutes max (gaps filled automatically)
- Validation handled by `lib/validation/DataValidator` (v1.11.0+)

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Forex | 260 | 24/5 (Monday-Friday) | FOREX | No weekends, uses `lib.calendars.ForexCalendar` (v1.11.0+) |

**Calendar Management (v1.11.0+):**
- Calendars defined in `lib/calendars/` package
- `ForexCalendar`: 24/5 trading (260 days/year, weekdays only)
- Calendar selection: `lib.calendars.get_calendar_for_asset_class('forex')`
- Session alignment: `lib/calendars/sessions/SessionManager` validates bundle-calendar alignment
- See `lib/calendars/` package for calendar utilities

## Data Ingestion Examples

**Creating Bundles (v1.11.0+):**

```python
from lib.bundles import ingest_bundle, list_bundles

# Ingest 1-minute forex data from CSV
bundle_name = ingest_bundle(
    source='csv',
    assets=['forex'],
    symbols=['EURUSD', 'NZDJPY'],
    timeframe='1m'
)

# List available bundles
bundles = list_bundles()
print(f"Available bundles: {bundles}")
```

**Validating Data Before Backtest:**

```python
from lib.validation import validate_bundle, ValidationConfig

# Validate bundle before backtest
result = validate_bundle('csv_forex_1m', config=ValidationConfig.strict())
if not result.is_valid:
    print(result.summary())
    # Fix issues before proceeding
```

**See Also:**
- `lib/bundles/` - Bundle management package
- `lib/validation/` - Data validation package
- `scripts/ingest_data.py` - CLI for data ingestion
- `scripts/validate_bundles.py` - CLI for bundle validation

---

## Risk Regime

**How does the strategy perform across different volatility environments?**

| Regime | ATR Ratio | Expected Behavior | Recommended Action |
|--------|-----------|-------------------|-------------------|
| Low Vol | < 1.0x | Poor performance, frequent false breakouts | Disable strategy or reduce position size |
| Normal Vol | 1.0-1.5x | Moderate performance, some false breakouts | Normal operation with range detection enabled |
| High Vol | 1.5-2.5x | Strong performance, clear breakouts | Normal operation, optimal conditions |
| Crisis | > 2.5x | High volatility, potential gaps | Reduce position size, tighten stops |

**Regime Detection:**
- How to identify current regime: `(prev_day_high - prev_low) / ATR(14)` ratio
- Indicators to watch: ATR(14), daily range, volatility percentile

**Adaptive Behavior:**
- [x] Should position sizing scale with volatility? Yes (volatility_scaled method)
- [x] Should parameters adapt to regime? Yes (range detection threshold)
- [x] Should strategy pause in certain regimes? Yes (range detection filter)

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (SPY) | Low | Good for portfolio (forex independent) |
| Momentum Factor | Medium | Moderate correlation with momentum |
| Value Factor | Low | Low correlation, good diversification |
| Volatility | Medium | Correlated with volatility regime |
| Other Forex Strategies | Medium-High | Similar market exposure |

**Portfolio Construction Notes:**
- Best paired with: Mean reversion strategies, equity strategies (low correlation)
- Avoid combining with: Other breakout strategies (high correlation)
- Suggested portfolio weight: 10-20% of strategy allocation

**Return Driver Analysis:**
- [x] Long-biased or market-neutral? Directional (long or short based on breakout direction)
- [x] Exposed to specific sector risk? No (forex market-wide)
- [x] Sensitive to interest rate changes? Yes (forex pairs sensitive to rate differentials)

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [x] Sharpe ratio < 0.8 for 6 consecutive months
- [x] Maximum drawdown exceeds 12% over any 12-month period
- [x] Win rate drops below 40% over 200+ trades
- [x] 3 consecutive losing months
- [x] Annual return < 5% for 2+ years

**Qualitative Triggers:**
- [x] Market structure fundamentally changed (e.g., algorithmic trading reduces breakout effectiveness)
- [x] Regulatory changes affect the edge (e.g., forex trading restrictions)
- [x] Strategy becomes too crowded (reduced edge from competition)
- [x] Data source becomes unreliable (CSV data quality issues)

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
| `range_detection_threshold` | 1.0 | 2.5 | 0.1 | 1.5 | Lower = more restrictive, higher = less restrictive |
| `trailing_stop_pct` | 0.03 | 0.20 | 0.01 | 0.08 | Balance between profit capture and premature exits |
| `volatility_target` | 0.05 | 0.30 | 0.05 | 0.15 | Position sizing sensitivity to volatility |
| `atr_period` | 7 | 28 | 7 | 14 | ATR calculation period (14 is standard) |
| `stop_loss_pct` | 0.01 | 0.15 | 0.01 | 0.05 | Fixed stop loss percentage |

**Parameter Constraints:**
- `range_detection_threshold` must be >= 1.0 (prevents division by zero)
- `trailing_stop_pct` should be < `stop_loss_pct` * 2 (prevents conflicting stops)
- `volatility_target` should be within 0.05-0.30 range (realistic volatility targets)

**Overfitting Protection:**
- Maximum parameters to optimize: 3 at a time
- Walk-forward window: 252 days train / 63 days test (4:1 ratio)
- Out-of-sample threshold: Must retain 70%+ of in-sample Sharpe
- Number of trials limit: < 100 combinations per optimization run

**Optimization Strategy:**
- Recommended method: Grid search for discrete parameters, random search for continuous
- Cross-validation folds: 5-fold time-series split
- Primary objective: Sharpe ratio (risk-adjusted return)

---

## Expected Outcomes

**What results would validate this hypothesis?**

- **Sharpe Ratio:** > 1.0 across multiple market regimes
- **Maximum Drawdown:** < 8% over any 12-month period
- **Win Rate:** > 45% over 200+ trades
- **Profit Factor:** > 1.2 (gross profit / gross loss)
- **Consistent Performance:** Stable metrics across trending and range-bound periods
- **Phase 11 Enhancements:** 5-10% improvement in win rate, 20-30% reduction in whipsaw losses

---

## References

**What research, papers, or observations support this hypothesis?**

- Breakout trading strategies are well-documented in technical analysis literature
- London session liquidity and trending behavior observed in forex market microstructure
- ATR-based range detection is a standard technique for avoiding consolidating markets
- Session-based filtering improves win rates in forex trading (empirical observation)

**Codebase References (v1.11.0+):**
- `lib/bundles/` - Data bundle management and ingestion
- `lib/validation/` - Data quality validation
- `lib/calendars/` - Trading calendar management (ForexCalendar)
- `lib/config/` - Configuration loading and validation
- `lib/backtest/` - Backtest execution and results
- `lib/metrics/` - Performance metrics calculation
- `lib/position_sizing/` - Position sizing algorithms
- `lib/risk_management/` - Risk management utilities
- `docs/api/` - Complete API documentation
- `CLAUDE.md` - Project overview and version history

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-19 | Updated to v1.11.0+ template standards, added comprehensive sections | Codebase Architect |
| Previous | Initial hypothesis with Phase 11 enhancements | Strategy Developer |
