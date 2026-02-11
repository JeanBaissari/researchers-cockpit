# AI Agent Integration Guide

This document describes how AI agents integrate with the Researcher's Cockpit codebase, following the NO WRAPPERS architecture principles and targeting Zipline-Reloaded exclusively.

## Overview

The Researcher's Cockpit is designed as an AI-agent-optimized research environment. Every component, folder structure, and convention is built to facilitate seamless handoffs between human researchers and AI agents.

## Targeted Framework: Zipline-Reloaded

**We exclusively target Zipline-Reloaded**, the actively maintained fork:

- **Package**: `zipline-reloaded` (installed via `pip install zipline-reloaded`)
- **Import**: `import zipline` (same import, different package)
- **Canonical Repository**: https://github.com/stefan-jansen/zipline-reloaded
- **Documentation**: https://zipline.ml4trading.io/

### Why Zipline-Reloaded?

Zipline-Reloaded is the modern, maintained successor to the legacy Quantopian Zipline:
- Python 3.8+ support
- Updated pandas compatibility
- Active maintenance and bug fixes
- Enhanced bundle management
- Improved calendar support via `exchange_calendars`

**Important**: Do NOT consult or reference legacy Quantopian Zipline documentation or patterns. Always use Zipline-Reloaded as the source of truth.

## NO WRAPPERS Architecture (v1.12.0+)

The project follows the **NO WRAPPERS** directive (AD-001):

### What This Means

- **Direct API Usage**: Use Zipline-Reloaded APIs directly without abstraction layers
- **No Wrapper Functions**: Don't create functions that simply call Zipline APIs
- **Framework Expertise**: Agents should understand Zipline-Reloaded patterns

### Examples

**✅ Correct - Direct Usage:**
```python
from zipline.data.bundles.csvdir import csvdir_equities
from zipline.data.bundles import register
from zipline.utils.calendar_utils import get_calendar

# Direct bundle registration
register('eurusd_1m', csvdir_equities(...), calendar_name='FOREX')

# Direct calendar access
calendar = get_calendar('FOREX')

# Direct pandas aggregation
daily = minute_df.resample('1d').agg({
    'open': 'first', 'high': 'max', 'low': 'min',
    'close': 'last', 'volume': 'sum'
})
```

**❌ Incorrect - Wrapper Functions:**
```python
# DON'T create wrappers
def register_bundle(name, path):
    """Wraps Zipline's register function"""
    register(name, csvdir_equities(path))

# DON'T abstract Zipline APIs
def get_trading_calendar(name):
    """Wraps get_calendar"""
    return get_calendar(name)
```

## Agent Capabilities

Specialized agents are defined in `.claude/agents/`:

### Core Research Agents

- **zipline-researcher**: Investigates Zipline-Reloaded capabilities to prevent duplication
- **codebase-architect**: Enforces SOLID/DRY principles and architectural standards
- **strategy-developer**: Creates trading strategies following project conventions
- **backtest-runner**: Executes backtests and manages results
- **validator**: Performs data quality validation
- **optimizer**: Runs parameter optimization
- **analyst**: Analyzes backtest results and generates reports

### Agent Conventions

All agents follow these conventions (see `.claude/agents/{agent_name}.md`):

1. **Read Agent Instructions First**: Each agent has detailed instructions in `.claude/agents/`
2. **Follow Project Standards**: Adhere to CLAUDE.md conventions
3. **Use Correct Import Paths**: Always use `lib.*` imports (modular architecture)
4. **Save to Correct Locations**: Respect directory structure
5. **Update Documentation**: Keep docs in sync with code changes

## Directory Structure

The project structure is optimized for AI agent workflows:

```
researchers_cockpit/
├── .claude/
│   ├── agents/          # Agent instruction files
│   └── skills/          # Reusable skill modules (20+ Zipline-Reloaded patterns)
├── lib/                 # Core library (modular packages)
│   ├── bundles/         # Data bundle management
│   ├── backtest/        # Backtest execution
│   ├── validation/      # Data quality validation
│   ├── metrics/         # Performance metrics
│   ├── calendars/       # Custom trading calendars (FOREX, CRYPTO)
│   └── ...
├── strategies/          # Trading strategy implementations
├── data/                # Raw and processed data
├── results/             # Backtest results (timestamped)
├── scripts/             # CLI tools for common tasks
├── notebooks/           # Jupyter analysis notebooks
├── tests/               # Comprehensive test suite (1200+ tests)
└── docs/                # Documentation (this file)
```

## AI Agent Workflows

### 1. Creating a New Strategy

```bash
# Agent reads template
strategies/_template/

# Agent creates new strategy
strategies/forex/my_strategy/
├── strategy.py           # Main strategy logic
├── parameters.yaml       # Strategy parameters
└── README.md            # Strategy documentation
```

### 2. Running Backtests

```bash
# Agent executes via CLI
python scripts/run_backtest.py --strategy forex/my_strategy

# Results saved automatically
results/forex_my_strategy/backtest_20260210_143022/
├── performance.csv
├── recorded_vars.pkl
├── config.yaml
└── logs/
```

### 3. Optimization Workflow

```bash
# Agent defines parameter grid in parameters.yaml
# Agent runs optimization
python scripts/run_optimization.py --strategy forex/my_strategy

# Results analyzed
results/forex_my_strategy/optimize_20260210_150000/
├── optimization_results.csv
├── best_params.yaml
└── plots/
```

## Integration with Zipline-Reloaded

### Bundle Management

Agents use Zipline's native bundle system directly:

```python
# In ~/.zipline/extension.py
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

register(
    'eurusd_1m',
    csvdir_equities(
        ['daily'],
        '/path/to/csvdir/eurusd/'
    ),
    calendar_name='FOREX'
)
```

### Custom Calendars

Custom calendars for 24/7 (CRYPTO) and 24/5 (FOREX) markets:

```python
from lib.calendars import CryptoCalendar, ForexCalendar
from exchange_calendars import register_calendar

# Register before bundle ingestion
register_calendar('CRYPTO', CryptoCalendar())
register_calendar('FOREX', ForexCalendar())
```

### Strategy Implementation

Strategies use Zipline's native API directly:

```python
def initialize(context):
    """Initialize strategy (called once)"""
    context.asset = symbol('EURUSD')
    schedule_function(rebalance, date_rules.every_day())

def handle_data(context, data):
    """Handle each bar (called every bar)"""
    price = data.current(context.asset, 'price')
    # Trading logic...
```

## Testing Requirements

All agent-generated code must include tests:

- **Unit Tests**: Test individual functions/modules
- **Integration Tests**: Test component interactions
- **Compliance Tests**: Verify NO WRAPPERS compliance

Run tests before committing:

```bash
pytest tests/ -v
```

## Documentation Standards

Agents must maintain documentation:

1. **API Documentation**: Update `docs/api/` for new modules
2. **Code Patterns**: Document new patterns in `docs/code_patterns/`
3. **Strategy Catalog**: Update `docs/strategy_catalog.md` for new strategies
4. **CLAUDE.md**: Update project overview for major features

## Linting and Code Quality

All code must pass linting:

```bash
ruff check lib/ strategies/ scripts/
ruff format lib/ strategies/ scripts/
```

## Version Control

Agents follow conventional commit standards:

```bash
git commit -m "feat(strategies): add forex momentum strategy"
git commit -m "fix(bundles): handle missing data gracefully"
git commit -m "docs(api): update validation module docs"
```

## Success Criteria

An AI agent successfully integrates when:

1. ✅ It reads and follows agent instructions in `.claude/agents/`
2. ✅ It uses Zipline-Reloaded APIs directly (NO WRAPPERS)
3. ✅ It respects project structure and conventions
4. ✅ It generates code that passes all tests
5. ✅ It updates documentation appropriately
6. ✅ It commits changes with descriptive messages
7. ✅ All code references Zipline-Reloaded (not legacy Zipline)

## Common Pitfalls

Avoid these common mistakes:

- ❌ Creating wrapper functions around Zipline APIs
- ❌ Using relative imports instead of `lib.*` imports
- ❌ Hardcoding paths instead of using `lib.paths.get_project_root()`
- ❌ Skipping tests for new functionality
- ❌ Not updating documentation
- ❌ Referencing legacy Quantopian Zipline patterns
- ❌ Using deprecated pandas/numpy APIs

## Additional Resources

- **Agent Instructions**: `.claude/agents/` directory
- **Skills Library**: `.claude/skills/` (20+ Zipline-Reloaded patterns)
- **Code Patterns**: `docs/code_patterns/`
- **Workflow Guide**: `workflow.md`
- **Pipeline Guide**: `pipeline.md`
- **Zipline-Reloaded Docs**: https://zipline.ml4trading.io/
- **Zipline-Reloaded Repo**: https://github.com/stefan-jansen/zipline-reloaded

---

**Last Updated**: 2026-02-10
**Architecture Version**: v1.12.0 (NO WRAPPERS)
