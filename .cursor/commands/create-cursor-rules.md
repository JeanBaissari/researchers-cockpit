# Create Cursor Rules

## Overview

Create new cursor rule files following established patterns, ensuring no duplication and proper coverage.

## Steps

1. **Analyze Codebase Area** - Identify codebase area needing rule coverage
2. **Check Existing Rules** - Search `.cursor/rules/` for existing coverage
3. **Validate No Duplication** - Ensure rule doesn't duplicate existing coverage
4. **Generate Rule Template** - Create rule file with proper frontmatter and structure
5. **Add Examples** - Include good/bad pattern examples
6. **Link Related Rules** - Cross-reference related rules in Related Rules section
7. **Validate Structure** - Ensure rule follows established pattern

## Checklist

- [ ] Codebase area analyzed for rule need
- [ ] Existing rules checked for coverage
- [ ] No duplication with existing rules
- [ ] Rule file created with proper frontmatter
- [ ] Description, globs, alwaysApply set correctly
- [ ] Purpose section written
- [ ] Quick Reference table added (if applicable)
- [ ] Patterns section with examples
- [ ] Anti-patterns included
- [ ] Related rules cross-referenced
- [ ] Rule structure validated

## Rule File Structure

**Frontmatter:**
```markdown
---
description: Brief description of rule coverage
globs: **/*.py,lib/**/*.py
alwaysApply: false
---
```

**Rule content:**
```markdown
# Rule Title

## Purpose
Brief explanation of what this rule enforces.

## Quick Reference
[Optional table of key rules]

## Patterns
[Examples and anti-patterns]

## Notes
[Important constraints, best practices]

## Related Rules
- .cursor/rules/architecture.mdc - For foundational patterns
- .cursor/rules/imports.mdc - For import patterns
```

## Rule Creation Patterns

**Check existing rules:**
```bash
# List all rules
ls .cursor/rules/*.mdc

# Search for similar coverage
grep -r "keyword" .cursor/rules/
```

**Rule template:**
```markdown
---
description: Error handling standards - exception types, logging, graceful degradation
globs: **/*.py
alwaysApply: true
---

# Error Handling Standards

## Purpose
Define consistent error handling patterns, exception types, logging
practices, and graceful degradation strategies.

## Patterns

### Custom Exceptions
```python
# ✅ GOOD - Use custom exceptions
from lib.paths import ProjectRootNotFoundError

# ❌ BAD - Generic exceptions
raise Exception("Error occurred")
```

## Related Rules
- .cursor/rules/architecture.mdc - SOLID principles
- .cursor/rules/logging.mdc - Logging patterns
```

## Notes

- Check `.cursor/rules/architecture.mdc` for foundational patterns
- Use `alwaysApply: true` for critical rules (SOLID, imports, logging)
- Use `alwaysApply: false` for specific domain rules
- Include both good and bad examples
- Cross-reference related rules for discoverability

## Related Commands

- update-commands-rules.md - For updating existing rules
- code-review.md - For validating rule compliance

