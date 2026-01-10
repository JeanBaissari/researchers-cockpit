# Update Commands/Rules

## Overview

Track and update commands/rules based on project growth, ensuring they stay current and relevant on a 40-day cycle.

## Steps

1. **Check Update Tracking** - Read `.cursor/.update_tracking.yaml` for last update dates
2. **Identify Outdated Items** - Find commands/rules > 40 days since last update
3. **Review Relevance** - Check if command/rule still matches current codebase
4. **Update Examples** - Refresh code examples and patterns
5. **Update Cross-References** - Fix broken links and add new references
6. **Update Metadata** - Record new update date in tracking file
7. **Generate Update Report** - List what was updated and why

## Checklist

- [ ] Update tracking file read
- [ ] Commands/rules > 40 days identified
- [ ] Relevance checked against current codebase
- [ ] Examples updated to match current patterns
- [ ] Cross-references verified and updated
- [ ] Metadata updated with new date
- [ ] Update report generated

## Update Tracking

**Tracking file structure:**
```yaml
# .cursor/.update_tracking.yaml
commands:
  github-commit.md:
    last_updated: 2024-01-15
    update_cycle_days: 40
    status: current
  create-cursor-rules.md:
    last_updated: 2024-01-10
    update_cycle_days: 40
    status: due_soon  # < 10 days remaining
rules:
  architecture.mdc:
    last_updated: 2024-01-01
    update_cycle_days: 40
    status: outdated  # > 40 days
```

**Check update status:**
```python
from datetime import datetime, timedelta
from pathlib import Path
import yaml

def check_updates_needed():
    tracking_file = Path('.cursor/.update_tracking.yaml')
    data = yaml.safe_load(tracking_file.read_text())
    
    today = datetime.now().date()
    outdated = []
    
    for item_type in ['commands', 'rules']:
        for name, info in data.get(item_type, {}).items():
            last_update = datetime.fromisoformat(info['last_updated']).date()
            days_since = (today - last_update).days
            
            if days_since > info['update_cycle_days']:
                outdated.append((item_type, name, days_since))
    
    return outdated
```

## Update Process

**Review command/rule:**
1. Read current command/rule file
2. Check if examples still work with current codebase
3. Verify lib/ module references are correct
4. Check if patterns match current conventions
5. Update outdated examples
6. Fix broken cross-references

**Update tracking:**
```yaml
# After update
commands:
  github-commit.md:
    last_updated: 2024-02-20  # Updated today
    update_cycle_days: 40
    status: current
    update_notes: "Updated examples for new git workflow"
```

## Notes

- Default update cycle: 40 days
- Check both commands and rules
- Update examples to match current lib/ API
- Verify cross-references are valid
- Document update reasons in tracking file

## Related Commands

- create-cursor-rules.md - For creating new rules
- github-commit.md - For committing updates

