"""
Report templates module.

Contains markdown templates for report generation.
"""

from typing import Dict, Any


def build_performance_summary(metrics: Dict[str, Any]) -> str:
    """Build performance summary table."""
    return f"""| Metric | Value |
|--------|-------|
| Total Return | {metrics.get('total_return', 0):.2%} |
| Annual Return | {metrics.get('annual_return', 0):.2%} |
| Sharpe Ratio | {metrics.get('sharpe', 0):.3f} |
| Sortino Ratio | {metrics.get('sortino', 0):.3f} |
| Max Drawdown | {metrics.get('max_drawdown', 0):.2%} |
| Calmar Ratio | {metrics.get('calmar', 0):.3f} |
| Annual Volatility | {metrics.get('annual_volatility', 0):.2%} |"""


def build_report_header(strategy_name: str, date_str: str, hypothesis: str) -> str:
    """Build report header section."""
    title = strategy_name.replace('_', ' ').title()
    return f"""# {title} Research Report

Generated: {date_str}

## Hypothesis

{hypothesis}

---

## Performance Summary

"""


def build_report_footer(
    strategy_name: str,
    params_yaml: str,
    recommendations: str,
    next_steps: str
) -> str:
    """Build report footer section."""
    return f"""
## Parameters

```yaml
{params_yaml}
```

---

## Recommendations

{recommendations}

---

## Next Steps

{next_steps}

---

## Files

- Results: `results/{strategy_name}/latest/`
- Metrics: `results/{strategy_name}/latest/metrics.json`
- Parameters: `results/{strategy_name}/latest/parameters_used.yaml`
"""





