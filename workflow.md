# Workflow Guide — Hybrid A: The Researcher's Cockpit

> This document describes how work flows through the system, from initial hypothesis to validated strategy.

---

## The Core Loop

Every piece of research follows this cycle:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│    HYPOTHESIS  →  STRATEGY  →  BACKTEST  →  ANALYZE  →  OPTIMIZE   │
│         ↑                                                    │      │
│         │                                                    │      │
│         └────────────────────────────────────────────────────┘      │
│                         (iterate until satisfied)                   │
│                                                                     │
│    Then: VALIDATE  →  DOCUMENT  →  ARCHIVE or DEPLOY                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Hypothesis Formation

### What Happens
You have an idea about market behavior. Before writing any code, you articulate what you believe and why.

### Where It Lives
`strategies/{asset_class}/{strategy_name}/hypothesis.md`

### Required Content

Every hypothesis file must answer:

1. **The Belief**
   - What specific market behavior are we exploiting?
   - Example: "BTC price trends persist for 15-30 days after a moving average crossover"

2. **The Reasoning**
   - Why does this behavior exist?
   - What market participants or mechanics create this opportunity?
   - Example: "Retail FOMO creates momentum. Institutional rebalancing creates mean reversion boundaries."

3. **The Conditions**
   - When should this work? When should it fail?
   - Example: "Works in trending markets. Fails in choppy, sideways conditions."

4. **The Falsification**
   - What result would prove this hypothesis wrong?
   - Example: "If Sharpe < 0.5 across 3+ years of data, the edge doesn't exist."

### AI Agent Behavior
When an agent receives a hypothesis (plain English description), it:
1. Creates the strategy directory
2. Writes `hypothesis.md` with structured answers
3. Generates initial `parameters.yaml` based on the hypothesis
4. Creates `strategy.py` skeleton

---

## Phase 2: Strategy Creation

### What Happens
The hypothesis is translated into executable Zipline code.

### Where It Lives
`strategies/{asset_class}/{strategy_name}/strategy.py`

### The Template Pattern

Every strategy starts by copying `strategies/_template/`:

```
strategies/_template/
├── strategy.py           # Canonical structure
├── hypothesis.md         # Empty template
└── parameters.yaml       # Default params
```

The template provides:
- Standard imports
- `initialize()` skeleton with parameter loading
- `handle_data()` with common patterns
- `analyze()` with standard metrics calculation
- Logging hooks

### Parameter Externalization

**Critical Rule:** No hardcoded parameters in `strategy.py`.

All tunable values live in `parameters.yaml`:

```yaml
# parameters.yaml
strategy:
  fast_period: 10
  slow_period: 50
  
position_sizing:
  max_position_pct: 0.95
  
risk:
  stop_loss_pct: 0.02
  take_profit_pct: 0.05
```

The strategy loads these at initialization:

```python
def initialize(context):
    params = load_params()  # From lib/
    context.fast = params['strategy']['fast_period']
    context.slow = params['strategy']['slow_period']
```

This separation enables:
- Optimization without code changes
- Version control of parameter history
- Clear audit trail

### AI Agent Behavior
When creating a strategy, the agent:
1. Reads `hypothesis.md` to understand intent
2. Reads `.agent/strategy_creator.md` for conventions
3. Implements `strategy.py` following the template
4. Validates syntax and imports
5. Runs a quick smoke test (1 month of data)

---

## Phase 3: Backtest Execution

### What Happens
The strategy runs against historical data to produce returns, positions, and transactions.

### Where It Lives
- **Input:** `strategies/{name}/` (strategy + params)
- **Output:** `results/{name}/backtest_{timestamp}/`

### Execution Methods

**Method A: Notebook (Interactive)**
```
Open: notebooks/01_backtest.ipynb
Set:  strategy_name = "btc_sma_cross"
Run:  All cells
```

**Method B: Script (Automated)**
```bash
python scripts/run_backtest.py --strategy btc_sma_cross
```

**Method C: Library (Programmatic)**
```python
from lib.backtest import run_backtest
results = run_backtest("btc_sma_cross")
```

### Output Structure

Every backtest produces:

```
results/{strategy}/backtest_{timestamp}/
├── returns.csv           # Time series of returns
├── positions.csv         # Position sizes over time
├── transactions.csv      # Every trade with prices, costs
├── metrics.json          # Calculated performance metrics
├── parameters_used.yaml  # Exact params (for reproducibility)
└── equity_curve.png      # Visual representation
```

### Metrics Calculated

Standard metrics (via Empyrical):
- Sharpe Ratio (annualized)
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Annual Return
- Annual Volatility
- Win Rate
- Profit Factor

Custom metrics:
- Average Trade Duration
- Trades Per Month
- Max Consecutive Losses
- Recovery Time from Max DD

### AI Agent Behavior
When running a backtest, the agent:
1. Reads `.agent/backtest_runner.md`
2. Validates strategy file exists and is syntactically correct
3. Checks data bundle availability
4. Executes backtest with appropriate date range
5. Saves all outputs to timestamped directory
6. Updates `latest` symlink
7. Reports summary metrics

---

## Phase 4: Analysis

### What Happens
You examine backtest results to understand what the strategy actually did, not just the headline numbers.

### Where It Lives
- **Input:** `results/{name}/backtest_{timestamp}/`
- **Output:** Understanding (notes in hypothesis.md) + visualizations

### Analysis Checklist

1. **Equity Curve Shape**
   - Is it smooth or jagged?
   - Are there long flat periods?
   - When did drawdowns occur?

2. **Trade Distribution**
   - Are wins and losses balanced?
   - Any outlier trades driving results?
   - Consistent behavior across time?

3. **Regime Analysis**
   - Performance in bull markets?
   - Performance in bear markets?
   - Performance in sideways markets?

4. **Parameter Sensitivity**
   - Would slight parameter changes destroy results?
   - Is the edge robust or fragile?

### Key Questions to Answer

After analysis, you should know:
- **Is the hypothesis supported?** (Yes/No/Partially)
- **What's the realistic Sharpe?** (Be conservative)
- **What's the maximum drawdown I should expect?** (Usually worse than backtest)
- **Should I optimize or abandon?**

### AI Agent Behavior
When analyzing results, the agent:
1. Reads `.agent/analyst.md`
2. Loads metrics and returns from results directory
3. Generates standard visualizations
4. Identifies anomalies or concerns
5. Summarizes findings in structured format
6. Suggests next steps (optimize, modify, abandon)

---

## Phase 5: Optimization

### What Happens
You search for better parameters while guarding against overfitting.

### Where It Lives
- **Input:** `strategies/{name}/` + parameter ranges
- **Output:** `results/{name}/optimization_{timestamp}/`

### Optimization Methods

**Grid Search**
- Exhaustive search over parameter grid
- Best for ≤3 parameters with small ranges
- Produces heatmaps showing parameter sensitivity

**Random Search**
- Random sampling from parameter space
- Better for many parameters or large ranges
- More efficient than grid for high dimensions

**Bayesian Optimization** (advanced)
- Sequential model-based optimization
- Best for expensive-to-evaluate strategies
- Finds good params with fewer iterations

### Anti-Overfit Protocols

**CRITICAL:** Optimization without validation is curve-fitting.

Every optimization must include:

1. **In-Sample / Out-of-Sample Split**
   - Optimize on 70% of data
   - Validate on held-out 30%
   - Compare IS vs OOS performance

2. **Walk-Forward Analysis**
   - Rolling optimization windows
   - Test on subsequent periods
   - More realistic than single split

3. **Overfit Probability Score**
   - Calculate probability that results are due to chance
   - Score > 0.5 = likely overfit, proceed with caution

### Output Structure

```
results/{strategy}/optimization_{timestamp}/
├── grid_results.csv      # All parameter combinations tested
├── best_params.yaml      # Winning parameters
├── heatmap_sharpe.png    # Parameter sensitivity visualization
├── in_sample_metrics.json
├── out_sample_metrics.json
└── overfit_score.json    # {"pbo": 0.23, "verdict": "acceptable"}
```

### Decision Framework

After optimization:

| OOS Sharpe | Overfit Score | Decision |
|------------|---------------|----------|
| > 1.0      | < 0.3         | Proceed to validation |
| > 0.5      | < 0.5         | Proceed with caution |
| > 0.5      | > 0.5         | Re-examine hypothesis |
| < 0.5      | Any           | Abandon or fundamentally rethink |

### AI Agent Behavior
When optimizing, the agent:
1. Reads `.agent/optimizer.md`
2. Loads strategy and current parameters
3. Requests parameter ranges (or uses defaults from hypothesis)
4. Runs optimization with specified method
5. Automatically runs validation checks
6. Saves all outputs
7. Updates `parameters.yaml` only if validation passes
8. Reports summary with recommendation

---

## Phase 6: Validation

### What Happens
Rigorous testing to ensure the strategy isn't just a statistical artifact.

### Where It Lives
- **Input:** Optimized strategy
- **Output:** `results/{name}/walkforward_{timestamp}/` or `montecarlo_{timestamp}/`

### Validation Methods

**Walk-Forward Analysis**
- Split data into multiple train/test periods
- Optimize on each training period
- Test on subsequent period
- Aggregate results across all folds

**Monte Carlo Simulation**
- Shuffle trade returns
- Generate thousands of equity paths
- Calculate confidence intervals
- Understand range of possible outcomes

**Regime Robustness**
- Identify market regimes (bull/bear/sideways)
- Test performance in each regime
- Strategy should be profitable (or at least not disastrous) in all regimes

### Validation Thresholds

To proceed from research to production consideration:

| Metric | Minimum Threshold |
|--------|-------------------|
| Walk-Forward Efficiency | > 0.5 (OOS performance / IS performance) |
| Monte Carlo 5th percentile | > 0 (shouldn't lose money in worst scenarios) |
| Overfit Probability | < 0.4 |
| Regime Consistency | Positive in 2/3 regimes minimum |

### AI Agent Behavior
When validating, the agent:
1. Runs full validation suite
2. Generates confidence intervals
3. Produces regime breakdown
4. Makes explicit pass/fail determination
5. Documents reasoning for determination

---

## Phase 7: Documentation & Archival

### What Happens
Successful strategies are documented for future reference. Failed strategies are documented for learning.

### Where It Lives
- **Reports:** `reports/{strategy_name}_report_{date}.md`
- **Catalog:** `docs/strategy_catalog.md`

### Report Contents

Every strategy report includes:
1. Hypothesis summary
2. Final parameters
3. Performance metrics
4. Validation results
5. Risk characteristics
6. Recommended position sizing
7. Known limitations
8. Next steps (if any)

### Strategy Catalog

The catalog (`docs/strategy_catalog.md`) tracks all strategies:

```markdown
| Strategy | Asset | Status | Sharpe | Last Updated |
|----------|-------|--------|--------|--------------|
| btc_sma_cross | Crypto | Validated | 1.23 | 2024-12-18 |
| eth_mean_rev | Crypto | Testing | 0.87 | 2024-12-20 |
| eurusd_breakout | Forex | Abandoned | -0.12 | 2024-12-15 |
```

---

## Workflow Shortcuts

### "Quick Test" — 30 Minutes
1. Hypothesis → Strategy (use template, minimal customization)
2. Backtest (1 year of data)
3. Quick metrics review
4. Decision: pursue or abandon

### "Full Research" — 4-8 Hours
1. Hypothesis (thorough documentation)
2. Strategy (careful implementation)
3. Backtest (full available history)
4. Analysis (all visualizations)
5. Optimization (grid search)
6. Walk-forward validation
7. Documentation

### "Production Validation" — 1-2 Days
1. Everything in Full Research
2. Monte Carlo simulation
3. Regime robustness testing
4. Stress testing (historical crisis periods)
5. Parameter sensitivity analysis
6. Final report generation

---

## Data Flow Summary

```
config/settings.yaml
        ↓
config/data_sources.yaml → lib/data_loader.py → data/bundles/
        ↓
strategies/{name}/hypothesis.md
        ↓
strategies/{name}/strategy.py ← strategies/_template/
        ↓
strategies/{name}/parameters.yaml
        ↓
lib/backtest.py (Zipline execution)
        ↓
results/{name}/backtest_{timestamp}/
        ↓
lib/metrics.py + lib/plots.py
        ↓
results/{name}/optimization_{timestamp}/ (if optimizing)
        ↓
lib/validate.py
        ↓
results/{name}/walkforward_{timestamp}/ (validation)
        ↓
lib/report.py
        ↓
reports/{name}_report_{date}.md
        ↓
docs/strategy_catalog.md (updated)
```

---

## Handoff Protocols

### Human → AI Agent

When handing a task to an AI agent:

1. **Specify the strategy name**
   - Agent locates `strategies/{asset}/{name}/`

2. **Specify the action**
   - `create`, `backtest`, `optimize`, `analyze`, `validate`, `report`

3. **Specify any overrides**
   - Date range, parameter ranges, validation method

Example: "Run walk-forward validation on btc_sma_cross using 2021-2024 data with 6-month windows"

### AI Agent → Human

Agent responses always include:

1. **Action taken**
2. **Output location**
3. **Summary metrics**
4. **Recommendation** (proceed, modify, abandon)
5. **Next suggested action**

Example: "Walk-forward complete. Results in results/btc_sma_cross/walkforward_20241220_143000/. WF Efficiency: 0.67. Overfit score: 0.28. Recommendation: Proceed to Monte Carlo validation."

---

## Error Handling

### Missing Data
- Agent checks bundle existence before backtest
- If missing, suggests: `python scripts/ingest_data.py --source {source} --assets {asset}`

### Strategy Errors
- Syntax errors caught before execution
- Runtime errors logged with full traceback
- Results directory still created with error log

### Optimization Failures
- If no parameters improve on default, report this
- If all parameters produce negative Sharpe, recommend abandoning hypothesis

### Validation Failures
- Clear pass/fail with reasoning
- Failed validation doesn't delete results — learning opportunity
