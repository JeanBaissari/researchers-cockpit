# PRD Template — Researchers Cockpit

> Template for creating Product Requirements Documents (PRDs) for Ralphy

**Usage:**
1. Copy this file: `cp PRD_template.md PRD_[name].md`
2. Fill in tasks
3. Run: `ralphy --cursor --prd PRD_[name].md`

---

## Overview

**Purpose:** [Brief description of what this PRD accomplishes]

**Priority:** [Critical / High / Medium / Low]

**Estimated Duration:** [Time estimate]

**Related Issues:** [GitHub issues, bug numbers, etc.]

---

## Tasks

### Phase 1: [Phase Name]
- [ ] [TASK-001] Task description with specific details
- [ ] [TASK-002] Another task with clear acceptance criteria
- [ ] [TASK-003] Task that depends on TASK-001

### Phase 2: [Phase Name]
- [ ] [TASK-004] Task for second phase
- [ ] [TASK-005] Related task

### Phase 3: [Phase Name]
- [ ] [TASK-006] Final phase task

---

## Acceptance Criteria

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Code follows project architecture rules (150-line limit, SOLID principles)
- [ ] No hardcoded values (use config files)
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or documented if intentional)

---

## Notes

- **Dependencies:** [List any dependencies between tasks]
- **Files to Modify:** [List key files that will be changed]
- **Files to Protect:** [List files that should NOT be modified]
- **Testing Strategy:** [How to verify the changes work]
- **Rollback Plan:** [How to revert if something goes wrong]

---

## Example: Bug Fixes PRD

```markdown
# Bug Fixes - 2026-01-27

## Overview
Fix critical bugs discovered during v1.12.0 testing.

## Tasks

### Critical Bugs
- [ ] [BUG-001] Fix ImportError in lib/bundles/access.py - registry module was deleted in v1.12.0, need to use direct bundles dict access
- [ ] [BUG-002] Fix timezone handling in lib/calendars/forex.py - ensure UTC normalization

### High Priority Bugs
- [ ] [BUG-003] Add missing error handling in lib/bundles/yahoo/fetcher.py for network timeouts
- [ ] [BUG-004] Fix bundle naming in scripts/ingest_data.py to prevent duplicate timeframe suffixes

## Acceptance Criteria
- [ ] All existing tests pass
- [ ] New error handling tested
- [ ] No regressions introduced
```

---

## Example: Feature Development PRD

```markdown
# Feature: CSV Validation in Ingestion Pipeline - 2026-01-27

## Overview
Integrate lib/validation/ into scripts/ingest_data.py to validate CSV files before ingestion.

## Tasks

### Phase 1: Integration
- [ ] [FEAT-001] Import DataValidator from lib.validation in scripts/ingest_data.py
- [ ] [FEAT-002] Add validation step before bundle registration
- [ ] [FEAT-003] Add --skip-validation flag for advanced users

### Phase 2: Testing
- [ ] [FEAT-004] Add unit tests for validation integration
- [ ] [FEAT-005] Test with invalid CSV files (should fail gracefully)
- [ ] [FEAT-006] Test with valid CSV files (should pass)

### Phase 3: Documentation
- [ ] [FEAT-007] Update scripts/ingest_data.py --help text
- [ ] [FEAT-008] Add validation examples to docs/

## Acceptance Criteria
- [ ] CSV validation runs automatically during ingestion
- [ ] Clear error messages when validation fails
- [ ] --skip-validation flag works correctly
- [ ] All tests pass
- [ ] Documentation updated
```

---

## Example: Refactoring PRD

```markdown
# Refactoring: Split lib/metrics/core.py - 2026-01-27

## Overview
Split lib/metrics/core.py (242 lines) into smaller modules following 150-line rule.

## Tasks

### Phase 1: Analysis
- [ ] [REF-001] Analyze lib/metrics/core.py structure and dependencies
- [ ] [REF-002] Identify logical splits (orchestrator vs core functions)

### Phase 2: Implementation
- [ ] [REF-003] Create lib/metrics/orchestrator.py (< 100 lines)
- [ ] [REF-004] Move core functions to lib/metrics/core.py (< 100 lines)
- [ ] [REF-005] Update lib/metrics/__init__.py exports

### Phase 3: Update Dependencies
- [ ] [REF-006] Update imports in lib/backtest/runner.py
- [ ] [REF-007] Update imports in scripts/run_backtest.py
- [ ] [REF-008] Update imports in notebooks/

### Phase 4: Testing
- [ ] [REF-009] Verify all existing tests pass
- [ ] [REF-010] Add tests for new module structure
- [ ] [REF-011] Run full test suite

## Acceptance Criteria
- [ ] No file exceeds 150 lines
- [ ] All existing functionality preserved
- [ ] All tests pass
- [ ] No circular dependencies
- [ ] Documentation updated
```

---

**Tips:**
- Be specific in task descriptions
- Include file paths and line numbers when relevant
- Reference related issues or PRs
- Group related tasks together
- Use parallel groups in YAML format for parallel execution
