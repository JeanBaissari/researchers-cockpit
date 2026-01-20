# Strategy Hypothesis

> **REQUIRED:** Every strategy MUST have a hypothesis.md file. This document articulates what market behavior you're exploiting and why you believe it exists.

---

## The Belief

**What specific market behavior are we exploiting?**

[Describe the market inefficiency, pattern, or edge you're testing. Be specific.]

Example: "BTC price trends persist for 15-30 days after a moving average crossover. The momentum created by retail FOMO and institutional rebalancing creates predictable directional moves."

---

## The Reasoning

**Why does this behavior exist?**

[Explain the market mechanics, participant behavior, or structural factors that create this opportunity.]

Example:
- Retail FOMO creates momentum after breakouts
- Institutional rebalancing creates mean reversion boundaries
- Market microstructure creates predictable patterns

---

## The Conditions

**When should this work? When should it fail?**

[Describe market conditions, regimes, or environments where this strategy should perform well or poorly.]

**Works well in:**
- Trending markets
- High volatility environments
- [Add specific conditions]

**Fails in:**
- Choppy, sideways markets
- Low liquidity periods
- [Add specific conditions]

---

## The Falsification

**What result would prove this hypothesis wrong?**

[Define clear criteria for rejecting the hypothesis.]

Example:
- If Sharpe < 0.5 across 3+ years of data, the edge doesn't exist
- If maximum drawdown > 30%, risk-adjusted returns are unacceptable
- If win rate < 40%, the strategy is not viable

---

## Implementation Notes

**How is this hypothesis translated into code?**

[Brief description of the strategy implementation approach.]

Example:
- Use fast SMA (10-day) and slow SMA (30-day) crossovers
- Enter on golden cross, exit on death cross
- Apply 200-day trend filter to avoid trading in bear markets

**Module Usage (v1.11.0+):**
- Configuration: `lib.config.load_strategy_params()` loads parameters from YAML
- Position sizing: `lib.position_sizing.compute_position_size()` for dynamic sizing
- Risk management: `lib.risk_management.check_exit_conditions()` for stop losses
- Pipeline setup: `lib.pipeline_utils.setup_pipeline()` for Pipeline API strategies
- Data access: `lib.bundles.load_bundle()` to access bundle data
- Validation: `lib.validation.validate_bundle()` to verify data quality

**See Also:**
- `strategies/_template/strategy.py` - Strategy implementation template
- `lib/_exports.py` - Complete public API reference

---

## Parameter Sensitivity

**Which parameters have the most impact on performance?**

[Identify the 2-3 most important parameters and their sensitivity.]

| Parameter | Sensitivity | Impact Description |
|-----------|-------------|-------------------|
| [param1] | High | [Why this parameter matters most] |
| [param2] | Medium | [Moderate impact on results] |
| [param3] | Low | [Less critical, can use default] |

**Critical Parameters:**
- [List 2-3 parameters that most affect Sharpe ratio]

**Robust Parameters:**
- [List parameters where small changes don't significantly impact results]

**Optimization Priority:**
1. [Highest priority parameter]
2. [Second priority]
3. [Lower priority]

---

## Data Requirements

**What data is needed for valid backtesting?**

**Minimum History:**
- Duration: [e.g., "5+ years for regime diversity"]
- Frequency: [e.g., "Daily OHLCV"]
- Observations: [e.g., "At least 1000 trading days"]

**Warmup Period:**
- Required: [e.g., "200 days for longest indicator"]
- Must be >= max(all indicator periods)
- Configure in `parameters.yaml` under `backtest.warmup_days`
- Calculated automatically by `lib.config.get_warmup_days()` (v1.11.0+)

**Data Ingestion (v1.11.0+):**
- Use `lib.bundles.ingest_bundle()` to create data bundles
- CLI: `python scripts/ingest_data.py --source yahoo --assets equities --timeframe daily`
- Bundle naming: `{source}_{asset_class}_{timeframe}` (e.g., `yahoo_equities_daily`)
- Supported sources: yahoo, csv, binance (planned), oanda (planned)
- See `lib/bundles/` package for bundle management utilities

**Data Quality Validation:**
- Pre-ingestion: Use `lib.validation.validate_before_ingest()` to validate source data
- Bundle validation: Use `lib.validation.validate_bundle()` to verify bundle integrity
- CLI: `python scripts/validate_bundles.py {bundle_name}`
- Validation config: `ValidationConfig.strict()` for production, `lenient()` for testing
- See `lib/validation/` package for validation utilities

**Data Quality:**
- [ ] Adjusted prices required? (for equities with splits/dividends)
- [ ] Volume data required?
- [ ] Missing data tolerance: [X] consecutive days max
- Validation handled by `lib/validation/DataValidator` (v1.11.0+)

**Asset Class Considerations:**
| Asset Class | Trading Days/Year | Session Hours | Calendar | Notes |
|-------------|-------------------|---------------|----------|-------|
| Equities | 252 | 9:30-16:00 ET | XNYS | Standard US market, uses `lib.calendars` for custom calendars |
| Forex | 260 | 24/5 | FOREX | No weekends, uses `lib.calendars.ForexCalendar` (v1.11.0+) |
| Crypto | 365 | 24/7 | CRYPTO | No market close, uses `lib.calendars.CryptoCalendar` (v1.11.0+) |

**Calendar Management (v1.11.0+):**
- Calendars defined in `lib/calendars/` package
- `CryptoCalendar`: 24/7 trading (365 days/year)
- `ForexCalendar`: 24/5 trading (260 days/year, weekdays only)
- Calendar selection: `lib.calendars.get_calendar_for_asset_class(asset_class)`
- Session alignment: `lib/calendars/sessions/SessionManager` validates bundle-calendar alignment
- See `lib/calendars/` package for calendar utilities

## Data Ingestion Examples

**Creating Bundles (v1.11.0+):**

```python
from lib.bundles import ingest_bundle, list_bundles

# Ingest daily equities data
bundle_name = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY', 'AAPL'],
    timeframe='daily'
)

# List available bundles
bundles = list_bundles()
print(f"Available bundles: {bundles}")
```

**Validating Data Before Backtest:**

```python
from lib.validation import validate_bundle, ValidationConfig

# Validate bundle before backtest
result = validate_bundle('yahoo_equities_daily', config=ValidationConfig.strict())
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

| Regime | VIX Equivalent | Expected Behavior | Recommended Action |
|--------|----------------|-------------------|-------------------|
| Low Vol | < 15 | [Expected performance] | [Position sizing adjustment] |
| Normal Vol | 15-25 | [Expected performance] | [Normal operation] |
| High Vol | 25-40 | [Expected performance] | [Reduce exposure?] |
| Crisis | > 40 | [Expected performance] | [Consider pausing] |

**Regime Detection:**
- How to identify current regime: [e.g., "20-day rolling volatility"]
- Indicators to watch: [e.g., "VIX, ATR, realized vol"]

**Adaptive Behavior:**
- [ ] Should position sizing scale with volatility?
- [ ] Should parameters adapt to regime?
- [ ] Should strategy pause in certain regimes?

---

## Correlation Analysis

**What is this strategy correlated with?**

| Factor/Strategy | Expected Correlation | Diversification Value |
|-----------------|---------------------|----------------------|
| Market (SPY) | [High/Medium/Low] | [Good/Poor for portfolio] |
| Momentum Factor | [High/Medium/Low] | [Notes] |
| Value Factor | [High/Medium/Low] | [Notes] |
| Volatility | [High/Medium/Low] | [Notes] |

**Portfolio Construction Notes:**
- Best paired with: [Strategies that would complement this one]
- Avoid combining with: [Highly correlated strategies]
- Suggested portfolio weight: [e.g., "10-20% of strategy allocation"]

**Return Driver Analysis:**
- [ ] Long-biased or market-neutral?
- [ ] Exposed to specific sector risk?
- [ ] Sensitive to interest rate changes?

---

## Exit Criteria

**When should this strategy be abandoned entirely?**

**Quantitative Triggers:**
- [ ] Sharpe ratio < [X] for [Y] consecutive months
- [ ] Maximum drawdown exceeds [X]%
- [ ] Win rate drops below [X]% over [Y] trades
- [ ] [X] consecutive losing months
- [ ] Annual return < [X]% for 2+ years

**Qualitative Triggers:**
- [ ] Market structure fundamentally changed
- [ ] Regulatory changes affect the edge
- [ ] Strategy becomes too crowded
- [ ] Data source becomes unreliable

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
| [param1] | [X] | [X] | [X] | [X] | [Why these bounds] |
| [param2] | [X] | [X] | [X] | [X] | [Why these bounds] |
| [param3] | [X] | [X] | [X] | [X] | [Why these bounds] |

**Parameter Constraints:**
- [Constraint 1, e.g., "slow_period must be > fast_period * 2"]
- [Constraint 2, e.g., "stop_loss_pct should be < take_profit_pct"]
- [Constraint 3]

**Overfitting Protection:**
- Maximum parameters to optimize: [e.g., "3 at a time"]
- Walk-forward window: [e.g., "252 days train / 63 days test"]
- Out-of-sample threshold: [e.g., "Must retain 70%+ of in-sample Sharpe"]
- Number of trials limit: [e.g., "< 100 combinations"]

**Optimization Strategy:**
- Recommended method: [Grid search / Random search / Bayesian]
- Cross-validation folds: [e.g., "5-fold time-series split"]
- Primary objective: [e.g., "Sharpe ratio" or "Risk-adjusted return"]

---

## Expected Outcomes

**What results would validate this hypothesis?**

[Define success criteria.]

- Sharpe Ratio > 1.0
- Maximum Drawdown < 20%
- Win Rate > 50%
- Consistent performance across different market regimes

---

## References

**What research, papers, or observations support this hypothesis?**

[Optional: List any relevant sources or prior research.]

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
| YYYY-MM-DD | Initial hypothesis | [Your name] |
