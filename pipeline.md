# Pipeline Guide — Hybrid A: The Researcher's Cockpit

> Hybrid A uses implicit pipelines rather than explicit pipeline configurations. This document explains how workflows chain together.

---

## Pipeline Philosophy

In Hybrid A, pipelines are **workflow patterns**, not separate configuration files. The system is designed for interactive research where you (or an AI agent) execute steps sequentially, making decisions between each step.

Think of it like cooking without a recipe card: you know the general sequence (prep → cook → plate), but you adjust based on what you see at each stage.

---

## Standard Workflow Patterns

### Pattern 1: Quick Validation

**Purpose:** Rapidly test if a hypothesis has any merit before investing time.

**Duration:** 15-30 minutes

**Sequence:**
```
1. Create hypothesis.md (5 min)
2. Generate strategy from template (5 min)
3. Backtest on 1 year of data (5 min execution)
4. Review Sharpe, MaxDD, trade count (5 min)
5. Decision: pursue or abandon
```

**When to Use:**
- Testing a new idea
- Screening multiple hypotheses
- First look at a new asset class

**Success Criteria:**
- Sharpe > 0.3 (low bar, just checking for signal)
- Reasonable trade count (not 2 trades in a year)
- No catastrophic drawdown (>50%)

---

### Pattern 2: Full Research Cycle

**Purpose:** Thoroughly develop and validate a single strategy.

**Duration:** 4-8 hours

**Sequence:**
```
1. Document hypothesis thoroughly (30 min)
2. Implement strategy with care (1-2 hours)
3. Backtest on full history (30 min)
4. Deep analysis of results (1 hour)
   - Equity curve examination
   - Trade distribution
   - Regime breakdown
5. Optimization with anti-overfit (1-2 hours)
   - Grid search on key parameters
   - Walk-forward validation
6. Final documentation (30 min)
7. Update strategy catalog
```

**When to Use:**
- Strategy passed Quick Validation
- Allocating serious research time
- Preparing for potential production

**Success Criteria:**
- OOS Sharpe > 0.7
- Walk-forward efficiency > 0.5
- Overfit probability < 0.4
- Consistent across 2+ regimes

---

### Pattern 3: Production Preparation

**Purpose:** Ensure strategy is robust enough for real capital.

**Duration:** 1-2 days

**Sequence:**
```
1. Complete Full Research Cycle (if not done)
2. Monte Carlo simulation (2 hours)
   - 1000+ equity path simulations
   - Calculate confidence intervals
3. Stress testing (2 hours)
   - Test on specific crisis periods
   - COVID crash, 2022 bear market, etc.
4. Parameter sensitivity analysis (2 hours)
   - Vary each parameter ±20%
   - Ensure no cliff edges
5. Out-of-sample hold-out (1 hour)
   - Reserve most recent 3-6 months
   - Final validation on unseen data
6. Comprehensive report generation
7. Position sizing recommendations
```

**When to Use:**
- Strategy passed Full Research
- Considering real capital allocation
- Need institutional-grade documentation

**Success Criteria:**
- Monte Carlo 5th percentile > 0
- Survives all historical stress periods
- No parameter cliff edges
- Fresh OOS confirms previous results

---

### Pattern 4: Multi-Asset Scan

**Purpose:** Test the same strategy logic across multiple assets.

**Duration:** 2-4 hours

**Sequence:**
```
1. Define strategy template with placeholder asset
2. Define asset list (e.g., all crypto majors)
3. For each asset:
   - Configure data bundle
   - Run backtest
   - Collect metrics
4. Aggregate into comparison matrix
5. Rank by risk-adjusted return
6. Identify best candidates for deeper research
```

**When to Use:**
- Strategy logic is asset-agnostic
- Seeking diversification
- Building a portfolio of strategies

**Output:**
- Comparison matrix (CSV)
- Ranking by Sharpe, MaxDD, etc.
- Candidates for Pattern 2 (Full Research)

---

### Pattern 5: Parameter Re-optimization

**Purpose:** Refresh parameters on existing strategy with new data.

**Duration:** 1-2 hours

**Sequence:**
```
1. Load existing strategy
2. Extend data bundle with recent data
3. Run optimization on rolling window
   - Example: Most recent 2 years
4. Compare new params vs old params
5. If improvement: update parameters.yaml
6. Run quick validation on new params
7. Document parameter change rationale
```

**When to Use:**
- Scheduled maintenance (monthly/quarterly)
- Market regime appears to have shifted
- Strategy performance degrading

**Caution:**
- Don't over-optimize
- Maintain hypothesis alignment
- Document every parameter change

---

## Pipeline Execution

### Manual Execution

Most research in Hybrid A is manual, executed step-by-step:

```bash
# Step 1: Create strategy
cp -r strategies/_template strategies/crypto/btc_new_idea
# Edit hypothesis.md and strategy.py

# Step 2: Backtest
python scripts/run_backtest.py --strategy btc_new_idea

# Step 3: Review results
cat results/btc_new_idea/latest/metrics.json

# Step 4: Optimize (if promising)
python scripts/run_optimization.py --strategy btc_new_idea --method grid

# Step 5: Validate
# Use notebooks/05_walkforward.ipynb
```

### Notebook-Driven Execution

For interactive work, notebooks provide a guided experience:

```
notebooks/01_backtest.ipynb    # Set strategy_name, run all cells
notebooks/02_optimize.ipynb    # Set param ranges, run optimization
notebooks/03_analyze.ipynb     # Load results, generate visualizations
```

### AI Agent Execution

AI agents execute pipelines by following `.agent/` instructions:

**Human Input:**
"Run full research on btc_momentum hypothesis: BTC trends following 20-day breakouts."

**Agent Execution:**
1. Read `.agent/strategy_creator.md`
2. Create strategy directory and files
3. Read `.agent/backtest_runner.md`
4. Execute backtest
5. Read `.agent/analyst.md`
6. Analyze results
7. If Sharpe > 0.3, proceed to optimization
8. Read `.agent/optimizer.md`
9. Run optimization with walk-forward
10. Generate report
11. Update strategy catalog

The agent chains these steps automatically but can pause for human input at decision points.

---

## Data Pipeline

### Ingestion Flow

```
External Data Source
        ↓
API Client (Yahoo, Binance, OANDA)
        ↓
Raw Data (DataFrame)
        ↓
Zipline Bundle Ingestion
        ↓
data/bundles/{bundle_name}/
        ↓
Available for backtesting
```

### Ingestion Commands

```bash
# Ingest crypto data from Yahoo
python scripts/ingest_data.py --source yahoo --assets crypto

# Ingest forex data from OANDA
python scripts/ingest_data.py --source oanda --assets forex

# Ingest specific symbol
python scripts/ingest_data.py --source binance --symbol BTC-USDT --timeframe 1h
```

### Bundle Naming Convention

```
{source}_{asset_class}_{timeframe}
```

Examples:
- `yahoo_crypto_daily`
- `binance_btc_1h`
- `oanda_forex_1h`
- `yahoo_equities_daily`

### Cache Management

API responses are cached to avoid redundant calls:

```
data/cache/
├── yahoo_2024_12_18.parquet    # Cached for 24 hours
├── binance_2024_12_20.parquet
└── ...
```

Cache is automatically invalidated after 24 hours. Force refresh with:

```bash
python scripts/ingest_data.py --source yahoo --assets crypto --force
```

---

## Results Pipeline

### Result Creation Flow

Every execution creates a timestamped result directory:

```
Backtest Execution
        ↓
results/{strategy}/backtest_{YYYYMMDD}_{HHMMSS}/
├── returns.csv
├── positions.csv
├── transactions.csv
├── metrics.json
├── parameters_used.yaml
└── equity_curve.png
        ↓
Update results/{strategy}/latest symlink
```

### Result Types

| Type | Directory Pattern | Contents |
|------|-------------------|----------|
| Backtest | `backtest_{timestamp}` | returns, positions, transactions, metrics |
| Optimization | `optimization_{timestamp}` | grid_results, best_params, heatmaps |
| Walk-Forward | `walkforward_{timestamp}` | in/out sample results, robustness score |
| Monte Carlo | `montecarlo_{timestamp}` | simulation paths, confidence intervals |

### Result Retention

- **All results are retained** — Storage is cheap, reproducibility is valuable
- **`latest` symlink** always points to most recent run of any type
- **Manual cleanup** via: `rm -rf results/{strategy}/backtest_2024*` (if needed)

---

## Report Pipeline

### Report Generation Flow

```
results/{strategy}/latest/
        ↓
lib/report.py (template rendering)
        ↓
reports/{strategy}_report_{date}.md
```

### Report Triggers

Reports are generated:
1. **Manually:** `python scripts/generate_report.py --strategy {name}`
2. **After validation:** Automatically when walk-forward completes
3. **On demand:** AI agent generates when asked

### Report Contents

```markdown
# {Strategy Name} Research Report

## Hypothesis
[From hypothesis.md]

## Performance Summary
| Metric | Value |
| Sharpe | 1.23  |
| MaxDD  | -15%  |
...

## Validation Results
- Walk-Forward Efficiency: 0.67
- Overfit Probability: 0.28
- Regime Breakdown: ...

## Parameters
[From parameters_used.yaml]

## Recommendations
[Agent-generated or human-written]

## Next Steps
[What to do next]
```

---

## Linking Strategies to Results

### The Symlink Pattern

Each strategy folder contains a symlink to its results:

```
strategies/crypto/btc_sma_cross/
├── strategy.py
├── hypothesis.md
├── parameters.yaml
└── results -> ../../../results/btc_sma_cross/
```

This means:
```bash
# From strategy folder, access results directly
cat strategies/crypto/btc_sma_cross/results/latest/metrics.json

# Or from results folder
cat results/btc_sma_cross/latest/metrics.json
```

Both paths reach the same data.

### Creating the Symlink

When creating a new strategy:

```bash
cd strategies/crypto/btc_new_strategy
ln -s ../../../results/btc_new_strategy results
```

Or let the backtest script create it automatically on first run.

---

## Parallel Execution

### What Can Run in Parallel

- **Multiple backtests** on different strategies
- **Grid search cells** within an optimization
- **Monte Carlo simulations** (embarrassingly parallel)

### What Must Be Sequential

- **Optimization → Validation** (validation uses optimized params)
- **Backtest → Analysis** (analysis needs backtest results)
- **Data ingestion** (API rate limits)

### Practical Parallelism

For most solo researchers, parallel execution isn't necessary. The bottleneck is thinking, not computation.

If needed, run multiple strategies in separate terminal sessions:

```bash
# Terminal 1
python scripts/run_backtest.py --strategy btc_sma_cross

# Terminal 2  
python scripts/run_backtest.py --strategy eth_mean_reversion

# Terminal 3
python scripts/run_backtest.py --strategy eurusd_breakout
```

Results go to separate directories. No conflicts.

---

## Pipeline Customization

### Adding a New Workflow Pattern

1. Document the pattern in this file
2. Create corresponding notebook (if interactive)
3. Create corresponding script (if automated)
4. Add to `.agent/` instructions

### Modifying Existing Patterns

1. Update this document
2. Update any affected notebooks/scripts
3. Update `.agent/` instructions
4. Test with a sample strategy

### Pattern Selection Guide

| Situation | Recommended Pattern |
|-----------|---------------------|
| New idea, uncertain merit | Quick Validation |
| Promising idea, serious research | Full Research |
| Strategy for real capital | Production Preparation |
| Testing across markets | Multi-Asset Scan |
| Existing strategy maintenance | Parameter Re-optimization |
