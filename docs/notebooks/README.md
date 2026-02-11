# Notebooks Documentation

Comprehensive guide to the Jupyter notebooks in the Researcher's Cockpit.

**Architecture**: v1.12.0 NO WRAPPERS - Direct Zipline/pandas APIs

## Overview

The `notebooks/` directory contains 7 interactive Jupyter notebooks that support the complete algorithmic trading research workflow. These notebooks are designed for:

- **Rapid exploration** of data and strategies
- **Interactive analysis** with immediate visual feedback
- **Iterative development** before formalizing strategies
- **Educational purposes** to understand the research pipeline

## Notebook Sequence

The notebooks are numbered to follow a typical research workflow:

| Notebook | Purpose | When to Use |
|----------|---------|-------------|
| **00_data_exploration.ipynb** | Explore available bundles and validate data quality | Before starting any strategy research |
| **01_backtest.ipynb** | Run a single strategy backtest | After creating a strategy or when testing hypothesis |
| **02_optimize.ipynb** | Optimize strategy parameters | After initial backtest shows promise |
| **03_analyze.ipynb** | Deep analysis of backtest results | After backtest to understand performance |
| **04_compare.ipynb** | Compare multiple strategies | When choosing between strategy variants |
| **05_walkforward.ipynb** | Walk-forward validation | Before deploying to production |
| **06_strategy_prototype.ipynb** | Rapid prototyping of new ideas | When exploring new trading hypotheses |

## Quick Start

### Prerequisites

1. **Environment activated**:
   ```bash
   conda activate zipline-reloaded
   ```

2. **Data ingested**:
   ```bash
   python scripts/ingest_data.py --source yahoo --assets equities --timeframe daily
   ```

3. **Jupyter installed** (included in requirements.txt):
   ```bash
   pip install jupyter
   ```

### Launch Notebooks

```bash
# From project root
jupyter notebook notebooks/
```

Then open any notebook from the browser interface.

## Notebook Details

### 00 - Data Exploration

**File**: `00_data_exploration.ipynb`
**Purpose**: Inspect bundles, validate data quality, explore symbols
**Documentation**: [00_data_exploration.md](00_data_exploration.md)

**Key Features**:
- List all available bundles
- Inspect bundle metadata (symbols, date ranges)
- Validate data quality (gaps, outliers, consistency)
- Visualize price and volume data
- Multi-symbol analysis

**When to Use**:
- ✓ Before starting strategy research
- ✓ After ingesting new data
- ✓ When debugging data issues
- ✓ To understand asset characteristics

---

### 01 - Backtest

**File**: `01_backtest.ipynb`
**Purpose**: Execute a single strategy backtest
**Documentation**: [01_backtest.md](01_backtest.md)

**Key Features**:
- Load strategy parameters from YAML
- Run backtest with Zipline's `run_algorithm()`
- Calculate performance metrics
- Generate equity curve visualization
- Save results to standardized directory

**When to Use**:
- ✓ After creating a new strategy
- ✓ To test a hypothesis
- ✓ For quick validation
- ✓ Before optimization

---

### 02 - Optimize

**File**: `02_optimize.ipynb`
**Purpose**: Find optimal strategy parameters
**Documentation**: [02_optimize.md](02_optimize.md)

**Key Features**:
- Grid search or random search
- Train/test split for validation
- Multiple objective metrics (Sharpe, Sortino, Calmar)
- Overfit detection (PBO, efficiency)
- Heatmap visualizations (2D parameter space)

**When to Use**:
- ✓ After initial backtest shows promise
- ✓ To find robust parameters
- ✓ When exploring parameter sensitivity
- ✓ Before walk-forward validation

---

### 03 - Analyze

**File**: `03_analyze.ipynb`
**Purpose**: Deep dive into backtest results
**Documentation**: [03_analyze.md](03_analyze.md)

**Key Features**:
- Comprehensive performance metrics
- Trade analysis (win rate, profit factor)
- Rolling metrics (Sharpe, volatility)
- Return distribution analysis
- Multiple visualizations (equity, drawdown, monthly returns)

**When to Use**:
- ✓ After backtest completion
- ✓ To understand strategy behavior
- ✓ For performance attribution
- ✓ When preparing reports

---

### 04 - Compare

**File**: `04_compare.ipynb`
**Purpose**: Compare multiple strategies
**Documentation**: [04_compare.md](04_compare.md)

**Key Features**:
- Side-by-side metric comparison
- Cumulative return visualization
- Best strategy identification
- Correlation analysis
- Portfolio-level statistics

**When to Use**:
- ✓ When choosing between variants
- ✓ For portfolio construction
- ✓ To validate improvements
- ✓ When reporting to stakeholders

---

### 05 - Walk-Forward

**File**: `05_walkforward.ipynb`
**Purpose**: Validate strategy robustness out-of-sample
**Documentation**: [05_walkforward.md](05_walkforward.md)

**Key Features**:
- Rolling window optimization
- In-sample vs out-of-sample comparison
- Walk-forward efficiency calculation
- Robustness metrics (consistency, degradation)
- Window-by-window visualizations

**When to Use**:
- ✓ Before production deployment
- ✓ To validate optimization results
- ✓ For regulatory compliance
- ✓ When assessing overfitting risk

---

### 06 - Strategy Prototype

**File**: `06_strategy_prototype.ipynb`
**Purpose**: Rapid iteration on new strategy ideas
**Documentation**: [06_strategy_prototype.md](06_strategy_prototype.md)

**Key Features**:
- Inline strategy definition (initialize, handle_data)
- Quick parameter tweaking
- Immediate backtest execution
- Visual feedback (equity, signals)
- Path to formalization

**When to Use**:
- ✓ When exploring new hypotheses
- ✓ For rapid experimentation
- ✓ Before creating formal strategy directory
- ✓ When learning Zipline API

---

## Common Patterns

### 1. Loading Project Modules

All notebooks use this pattern for imports:

```python
# Add project root to path
import sys
from pathlib import Path

project_root = Path().absolute().parent
sys.path.insert(0, str(project_root))

# Now import lib modules
from lib.paths import get_project_root
from lib.bundles import list_bundles
# ... etc
```

### 2. Configuration Cells

Each notebook has a configuration cell at the top:

```python
# Configuration
strategy_name = 'spy_sma_cross'
start_date = '2020-01-01'
end_date = None  # None = today
```

**Always modify these cells** to match your needs before running.

### 3. Direct Zipline APIs (v1.12.0)

Notebooks use direct Zipline APIs following the NO WRAPPERS architecture:

```python
# Direct bundle access
from zipline.data.bundles import bundles, load

# Direct calendar access
from zipline.utils.calendar_utils import get_calendar

# Direct pandas aggregation
daily = minute_df.resample('1d').agg({
    'open': 'first', 'high': 'max', 'low': 'min',
    'close': 'last', 'volume': 'sum'
})
```

### 4. Error Handling

Notebooks include helpful error messages:

```python
try:
    results = run_backtest(strategy_name, ...)
except Exception as e:
    print(f"✗ Backtest failed: {e}")
    print(f"  Check that bundle exists and strategy is valid")
    raise
```

## Best Practices

### Do's ✓

- **Run cells sequentially** - Notebooks are designed to execute top-to-bottom
- **Restart kernel when switching strategies** - Avoids state contamination
- **Save important results** - Notebooks auto-save to `results/` directories
- **Use notebooks for exploration** - Perfect for iterative development
- **Check configuration cells** - Always verify settings before running

### Don'ts ✗

- **Don't skip data exploration** - Always validate data quality first (00_data_exploration)
- **Don't rely on cell execution order** - Re-run from top if uncertain
- **Don't commit notebook outputs** - `.gitignore` excludes them
- **Don't use for production** - Formalize into `strategies/` directory
- **Don't hardcode paths** - Use `lib.paths` functions

## Troubleshooting

### "No bundles found"

**Symptom**: `00_data_exploration.ipynb` shows no bundles
**Cause**: No data ingested
**Fix**: Run `python scripts/ingest_data.py --source yahoo --assets equities --timeframe daily`

### "Strategy not found"

**Symptom**: `01_backtest.ipynb` can't load strategy
**Cause**: Strategy directory doesn't exist or wrong name
**Fix**: Check strategy exists in `strategies/{asset_class}/{strategy_name}/`

### "ImportError: No module named lib"

**Symptom**: Imports fail in first cells
**Cause**: Project root not in Python path
**Fix**: Ensure the setup cell with `sys.path.insert(0, str(project_root))` runs successfully

### "Kernel died" or OOM errors

**Symptom**: Jupyter kernel crashes during execution
**Cause**: Insufficient memory, especially with large bundles
**Fix**: Reduce date range, use smaller bundles, or increase system memory

### "Bundle validation failed"

**Symptom**: Data quality checks fail
**Cause**: Corrupted or incomplete data
**Fix**: Re-ingest bundle with `--force` flag or check source data

## Integration with Scripts

Notebooks complement the command-line scripts:

| Task | Notebook | Script |
|------|----------|--------|
| Data exploration | `00_data_exploration.ipynb` | `scripts/validate_bundles.py` |
| Backtest | `01_backtest.ipynb` | `scripts/run_backtest.py` |
| Optimize | `02_optimize.ipynb` | `scripts/run_optimization.py` |
| Report | `03_analyze.ipynb` | `scripts/generate_report.py` |

**Use notebooks for**: Interactive exploration, debugging, visualization
**Use scripts for**: Automation, batch processing, production workflows

## Customization

### Adding New Notebooks

1. **Copy a template**: Start from `06_strategy_prototype.ipynb`
2. **Follow naming convention**: `NN_descriptive_name.ipynb` (numbered)
3. **Include version header**: Add v1.12.0 NO WRAPPERS note
4. **Document purpose**: Add markdown intro cell explaining use case
5. **Update this README**: Add to notebook sequence table

### Modifying Existing Notebooks

1. **Preserve structure**: Keep setup and configuration cells at top
2. **Add comments**: Explain non-obvious code blocks
3. **Test thoroughly**: Run all cells before committing
4. **Update documentation**: Modify corresponding `.md` file in `docs/notebooks/`

## Architecture Notes

### v1.12.0 NO WRAPPERS

All notebooks follow the NO WRAPPERS architecture:

- **Direct Zipline APIs**: Use `zipline.data.bundles.load()` not wrappers
- **Direct pandas**: Use `df.resample()` not custom aggregation functions
- **Direct calendar access**: Use `get_calendar()` not SessionManager
- **Minimal abstraction**: Only `lib/` modules that add genuine value

### Why This Matters

- **Clarity**: See exactly what Zipline does
- **Maintainability**: No hidden wrapper logic to debug
- **Future-proof**: Compatible with Zipline updates
- **Learning**: Understand framework patterns

## Related Documentation

- **[Workflow Guide](../walkthrough/README.md)** - End-to-end research workflow
- **[Scripts Reference](../scripts_reference.md)** - CLI alternatives to notebooks
- **[API Documentation](../api/README.md)** - `lib/` module reference
- **[Code Patterns](../code_patterns/README.md)** - Common implementation patterns
- **[Troubleshooting](../troubleshooting/README.md)** - Issue resolution guides

## Version History

- **v1.12.0** (2026-01-26): Updated all notebooks to NO WRAPPERS architecture
- **v1.11.0** (2026-01-19): Added `06_strategy_prototype.ipynb`
- **v1.10.0** (2026-01-15): Added `00_data_exploration.ipynb`
- **v1.0.7** (2025-01-17): Initial notebook suite (01-05)

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
**Status**: Production-Ready
