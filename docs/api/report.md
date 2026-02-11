# Report API

Generate human-readable markdown reports from backtest results.

**Location:** `lib/report/`
**CLI Equivalent:** `scripts/generate_report.py`

---

## generate_report()

Generate a markdown report from strategy results.

**Signature:**
```python
def generate_report(
    strategy_name: str,
    result_type: str = 'backtest',
    output_path: Optional[Path] = None,
    asset_class: Optional[str] = None
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `result_type` | str | `'backtest'` | Type (`'backtest'`, `'optimization'`, `'walkforward'`) |
| `output_path` | Path | None | Output path (auto-generated if None) |
| `asset_class` | str | None | Asset class hint |

**Returns:** `Path` - Path to generated report file

**Raises:**
- `FileNotFoundError`: If results directory or metrics not found

**Example:**
```python
from lib.report import generate_report

# Generate backtest report
report_path = generate_report('spy_sma_cross')
print(f"Report saved to: {report_path}")

# Generate optimization report
report_path = generate_report(
    strategy_name='spy_sma_cross',
    result_type='optimization'
)

# Custom output path
from pathlib import Path
report_path = generate_report(
    strategy_name='spy_sma_cross',
    output_path=Path('reports/custom_report.md')
)
```

**CLI Equivalent:**
```bash
# Generate backtest report
python scripts/generate_report.py --strategy spy_sma_cross

# Generate optimization report
python scripts/generate_report.py --strategy spy_sma_cross --type optimization

# Custom output
python scripts/generate_report.py --strategy spy_sma_cross --output reports/my_report.md
```

**Report Sections:**
1. Hypothesis (from `hypothesis.md`)
2. Performance Summary (Sharpe, Sortino, MaxDD, etc. from `metrics.json`)
3. Zipline Native Metrics (from Performance DataFrame when `performance.pkl` exists)
4. Trade Analysis (if transactions available)
5. Validation Results (if walk-forward data available)
6. Overfit Analysis (if optimization data available)
7. Parameters (from `parameters_used.yaml`)
8. Recommendations (auto-generated)
9. Next Steps (auto-generated)

---

## Performance DataFrame Integration

Report generation loads the **Zipline Performance DataFrame** from the results directory when building Zipline-specific sections. The DataFrame is the same object returned by `zipline.run_algorithm()` and persisted as `performance.pkl` (see [Performance DataFrame Integration](performance_dataframe_integration.md)).

### Data Source

| Source | When Used | Columns Available |
|--------|------------|-------------------|
| `performance.pkl` | Present in results directory | Full Performance DataFrame (38+ columns) |
| `returns.csv` | Fallback when pickle missing | Minimal: `returns` only |

### Performance DataFrame Columns Used by Reports

The following columns from the Performance DataFrame are used by report section builders. All access is defensive (checks `col in perf.columns`); missing columns are skipped.

| Column | Report Section | Usage |
|--------|----------------|-------|
| `alpha` | Benchmark Comparison (Zipline Metrics) | Final value (Jensen's alpha) |
| `beta` | Benchmark Comparison (Zipline Metrics) | Final value (market exposure) |
| `benchmark_period_return` | Benchmark Comparison (Zipline Metrics) | Final value |
| `algorithm_period_return` | Benchmark Comparison (Zipline Metrics) | Final value |
| `gross_leverage` | Leverage Analysis | Max, mean |
| `net_leverage` | Leverage Analysis | Max, mean |
| `sharpe` | Time-Series Metrics (Final); Time-Series Summary | Final value; mean, std, min, max (rolling) |
| `sortino` | Time-Series Metrics (Final); Time-Series Summary | Final value; mean, std, min, max (rolling) |
| `max_drawdown` | Time-Series Metrics (Final); Time-Series Summary | Final value; mean, std, min, max (rolling) |
| `returns` | Fallback DataFrame | When reconstructing from `returns.csv` only |

**Note:** Zipline's `sharpe`, `sortino`, and `max_drawdown` are **rolling** calculations. The Performance Summary section uses **full-period** metrics from `lib/metrics` (saved in `metrics.json`).

### Section Builder Functions

**`load_performance_dataframe(results_dir)`** (`lib/report/sections.py`)

Loads the Performance DataFrame from a results directory.

- Tries `results_dir/performance.pkl` first (full DataFrame).
- Falls back to `results_dir/returns.csv` and builds a minimal DataFrame with `returns` only.
- Returns `None` if neither is available.

**`build_zipline_metrics_section(results_dir)`** (`lib/report/sections.py`)

Builds markdown for Zipline native metrics using the Performance DataFrame:

- **Benchmark comparison:** `alpha`, `beta`, `benchmark_period_return`, `algorithm_period_return`
- **Leverage:** `gross_leverage`, `net_leverage` (max and mean)
- **Time-series (final values):** `sharpe`, `sortino`, `max_drawdown` (final row only; rolling metrics)

**`build_time_series_summary(results_dir)`** (`lib/report/sections.py`)

Builds markdown summarizing rolling time-series metrics from the Performance DataFrame:

- Uses `sharpe`, `sortino`, `max_drawdown` when present.
- Reports mean, std, min, max, and final value for each.

For the full list of Performance DataFrame columns and usage across the project, see [Performance DataFrame Integration](performance_dataframe_integration.md).

---

## update_catalog()

Update strategy catalog with status and metrics.

**Signature:**
```python
def update_catalog(
    strategy_name: str,
    status: str,
    metrics: Dict[str, Any],
    asset_class: Optional[str] = None
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `strategy_name` | str | required | Name of strategy |
| `status` | str | required | Status (`'testing'`, `'validated'`, `'abandoned'`) |
| `metrics` | Dict | required | Metrics dictionary |
| `asset_class` | str | None | Asset class hint |

**Example:**
```python
from lib.report import update_catalog
from lib.metrics import calculate_metrics

# After running backtest
metrics = calculate_metrics(returns)

update_catalog(
    strategy_name='spy_sma_cross',
    status='validated',
    metrics=metrics,
    asset_class='equities'
)
```

**CLI Equivalent:**
```bash
python scripts/generate_report.py --strategy spy_sma_cross \
    --update-catalog \
    --status validated
```

**Catalog Format:**

The strategy catalog is stored at `docs/strategy_catalog.md`:

```markdown
# Strategy Catalog

| Strategy | Asset | Status | Sharpe | Sortino | MaxDD | Last Updated |
|----------|-------|--------|--------|---------|-------|--------------|
| spy_sma_cross | equities | validated | 1.25 | 1.45 | -15.2% | 2024-12-28 |
| btc_momentum | crypto | testing | 0.85 | 0.92 | -22.5% | 2024-12-28 |
```

---

## generate_weekly_summary()

Generate weekly summary report of all strategies.

**Signature:**
```python
def generate_weekly_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | str | None | Optional start date filter |
| `end_date` | str | None | Optional end date filter |

**Returns:** `Path` - Path to generated summary file

**Raises:**
- `FileNotFoundError`: If results directory not found

**Example:**
```python
from lib.report import generate_weekly_summary

summary_path = generate_weekly_summary()
print(f"Summary saved to: {summary_path}")
```

**Output:**
```
reports/weekly_summary_2024W52.md
```

**Summary Contents:**
- Table of all strategies ranked by Sharpe ratio
- Summary statistics (total strategies, average Sharpe, best performer)

---

## Report Templates

### Backtest Report Structure

```markdown
# {Strategy Name} Research Report

Generated: YYYY-MM-DD

## Hypothesis

{Content from hypothesis.md}

## Performance Summary

| Metric | Value |
|--------|-------|
| Total Return | XX.XX% |
| Annual Return | XX.XX% |
| Sharpe Ratio | X.XXX |
| Sortino Ratio | X.XXX |
| Max Drawdown | -XX.XX% |
| Calmar Ratio | X.XXX |
| Annual Volatility | XX.XX% |

## Trade Analysis

| Metric | Value |
|--------|-------|
| Total Trades | XX |
| Win Rate | XX.XX% |
| Profit Factor | X.XXX |
| ...

## Parameters

```yaml
strategy:
  asset_symbol: SPY
  fast_period: 10
  slow_period: 50
...
```

## Recommendations

- Auto-generated based on metrics

## Next Steps

1. Run parameter optimization
2. Perform walk-forward validation
3. Run Monte Carlo simulation

## Files

- Results: `results/{strategy}/latest/`
- Metrics: `results/{strategy}/latest/metrics.json`
```

---

## Auto-Generated Recommendations

The report generator provides contextual recommendations based on metrics:

| Condition | Recommendation |
|-----------|----------------|
| Sharpe < 0.5 | "Sharpe ratio is low. Consider optimizing parameters or revisiting hypothesis." |
| Sharpe > 1.5 | "Strong Sharpe ratio. Consider walk-forward validation to confirm robustness." |
| Sortino < Sharpe * 0.8 | "Sortino ratio significantly lower than Sharpe suggests high downside volatility." |
| MaxDD > 30% | "Maximum drawdown exceeds 30%. Review risk management and position sizing." |
| Win Rate < 40% | "Low win rate. Strategy may benefit from better entry/exit criteria." |

---

## Report Output Locations

| Report Type | Default Location |
|-------------|------------------|
| Backtest | `reports/{strategy}_report_{date}.md` |
| Optimization | `reports/{strategy}_report_{date}.md` |
| Walk-forward | `reports/{strategy}_report_{date}.md` |
| Weekly Summary | `reports/weekly_summary_{week}.md` |
| Strategy Catalog | `docs/strategy_catalog.md` |

---

## See Also

- [Performance DataFrame Integration](performance_dataframe_integration.md) - Full Performance DataFrame column list and project integration
- [Validate API](validate.md) - Walk-forward analysis
- [Optimize API](optimize.md) - Parameter optimization
- [Metrics API](metrics.md) - Performance metrics
