# Generate Report

## Overview

Generate comprehensive strategy research report from backtest results, optimization, and validation, saving to reports/ directory.

## Steps

1. **Load Results** - Load metrics, returns, optimization results, validation results
2. **Gather Metrics** - Collect performance metrics, validation scores, parameter history
3. **Create Report** - Generate markdown report with all sections
4. **Save Report** - Save to reports/{strategy}_report_{date}.md
5. **Update Catalog** - Update docs/strategy_catalog.md with strategy status

## Checklist

- [ ] Results loaded from results/{strategy}/latest/
- [ ] Metrics gathered (performance, validation, optimization)
- [ ] Report generated with all sections
- [ ] Report saved to reports/ directory
- [ ] Strategy catalog updated

## Execution Methods

**Script (CLI):**
```bash
python scripts/generate_report.py --strategy btc_sma_cross
python scripts/generate_report.py --strategy btc_sma_cross --output custom_report.md
```

**Library (Programmatic):**
```python
from lib.report import generate_report

report_path = generate_report(
    strategy_name='btc_sma_cross',
    results_dir='results/btc_sma_cross/latest',
    include_validation=True,
    include_optimization=True
)
```

## Report Structure

```markdown
# {Strategy Name} Research Report

## Hypothesis
[From hypothesis.md]

## Performance Summary
| Metric | Value |
|--------|-------|
| Sharpe | 1.23 |
| MaxDD  | -15% |
| Annual Return | 12.5% |
| Win Rate | 58% |

## Validation Results
- Walk-Forward Efficiency: 0.67
- Overfit Probability: 0.28
- Monte Carlo 5th Percentile: 0.05
- Regime Breakdown: [bull/bear/sideways performance]

## Parameters
[From parameters_used.yaml]

## Optimization History
[Best parameters from optimization runs]

## Recommendations
[Agent-generated or human-written]

## Next Steps
[What to do next]
```

## Report Sections

1. **Hypothesis** - Research question and rationale
2. **Performance Summary** - Key metrics table
3. **Equity Curve** - Visual representation
4. **Trade Analysis** - Win rate, profit factor, trade distribution
5. **Regime Breakdown** - Performance by market condition
6. **Validation Results** - Walk-forward, Monte Carlo, overfit scores
7. **Parameters** - Current and historical parameters
8. **Optimization History** - Parameter evolution
9. **Recommendations** - Next steps, position sizing, risk management
10. **Limitations** - Known issues, edge cases, assumptions

## Report Triggers

Reports generated:
1. **Manually** - `python scripts/generate_report.py --strategy {name}`
2. **After validation** - Automatically when walk-forward completes
3. **On demand** - AI agent generates when asked

## Notes

- Reports include all available results (backtest, optimization, validation)
- Use latest results directory by default
- Reports are markdown for easy editing and version control
- Update strategy catalog after generating report
- Include actionable recommendations

## Related Commands

- analyze-results.md - For analyzing results before report
- validate-strategy.md - For validation results in report
- optimize-parameters.md - For optimization history in report
