# Generate Weekly Summary

## Overview

Generate weekly summary report aggregating all strategy results, tracking progress over time, and summarizing performance trends.

## Steps

1. **Collect Strategy Metrics** - Gather metrics from all strategies with latest results
2. **Aggregate Performance** - Calculate aggregate statistics across strategies
3. **Track Progress** - Compare current week to previous weeks
4. **Summarize Trends** - Identify performance trends and patterns
5. **Generate Report** - Create markdown report with summary
6. **Save to Reports** - Save report to reports/ directory

## Checklist

- [ ] Strategy metrics collected from all strategies
- [ ] Aggregate performance calculated
- [ ] Progress tracked (week-over-week)
- [ ] Trends summarized
- [ ] Weekly report generated
- [ ] Report saved to reports/ directory

## Summary Generation Patterns

**Generate weekly summary:**
```python
from lib.report.weekly import generate_weekly_summary
from pathlib import Path

# Generate summary for current week
summary_path = generate_weekly_summary()
print(f"Weekly summary saved to: {summary_path}")
```

**Generate summary for date range:**
```python
from lib.report.weekly import generate_weekly_summary

# Generate summary for specific date range
summary_path = generate_weekly_summary(
    start_date='2024-12-01',
    end_date='2024-12-31'
)
print(f"Summary saved to: {summary_path}")
```

**View weekly summary:**
```python
from lib.utils import get_project_root
from pathlib import Path
from datetime import datetime

root = get_project_root()
reports_dir = root / 'reports'

# Find latest weekly summary
week_str = datetime.now().strftime('%YW%U')
summary_file = reports_dir / f'weekly_summary_{week_str}.md'

if summary_file.exists():
    print(summary_file.read_text())
else:
    print(f"Weekly summary not found: {summary_file}")
```

**Generate summary programmatically:**
```python
from lib.report.weekly import generate_weekly_summary

summary_path = generate_weekly_summary()
print(f"Generated summary: {summary_path}")
```

## Summary Contents

- **Strategy Count** - Number of strategies with results
- **Performance Summary** - Aggregate metrics (avg Sharpe, best/worst performers)
- **Status Breakdown** - Count of testing/validated/abandoned strategies
- **Top Performers** - Best strategies by Sharpe, Sortino, Calmar
- **Progress Tracking** - Week-over-week changes
- **Trends** - Performance trends and patterns

## Report Format

Weekly summaries are saved as markdown files in `reports/` directory with naming:
- `weekly_summary_YYYYWww.md` (e.g., `weekly_summary_2024W51.md`)

## Notes

- Use `lib/report/weekly.py:generate_weekly_summary()` (don't duplicate summary logic)
- Use existing report generation patterns
- Reference `lib/report/` modules for consistency
- Generate summaries weekly for tracking progress
- Summaries help track strategy portfolio health over time

## Related Commands

- update-catalog.md - For updating strategy catalog (often run together)
- analyze-results.md - For detailed analysis of individual strategies
- compare-strategies.md - For comparing specific strategies

