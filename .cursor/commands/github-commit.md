# GitHub Commit

## Overview

Create professional git commits following conventional commit format with automatic type detection, line length limits, and pre-commit validation.

## Steps

1. **Analyze Staged Changes** - Check git status and staged files to detect change type
2. **Detect Commit Type** - Analyze file patterns to suggest commit type (feat, fix, docs, refactor, test, chore)
3. **Validate Excluded Files** - Check for excluded files (results/, data/bundles/, *.pyc, etc.)
4. **Enforce Line Limits** - Validate subject (50 chars) and body (72 chars) line lengths
5. **Pre-commit Checks** - Verify no large files, no secrets, proper formatting
6. **Generate Commit Message** - Create conventional commit message with type, scope, subject, and body
7. **Validate Commit Size** - Warn if commit changes > 200 lines (recommended limit)

## Checklist

- [ ] Staged files analyzed for change type
- [ ] Commit type detected (feat/fix/docs/refactor/test/chore)
- [ ] Excluded files checked (results/, data/bundles/, etc.)
- [ ] Subject line ≤ 50 characters
- [ ] Body lines ≤ 72 characters
- [ ] No large files (> 1MB) in commit
- [ ] No secrets or sensitive data detected
- [ ] Commit size < 200 lines changed (or justified)
- [ ] Commit message follows conventional format

## Commit Message Format

**Conventional commit structure:**
```
{type}({scope}): {subject}

{body}

{footer}
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(backtest): add walk-forward validation support

Add walk-forward analysis to backtest runner with configurable
window sizes and step sizes. Supports both anchored and
unanchored walk-forward methods.

Closes #123
```

```
fix(config): resolve path resolution for nested strategies

Fix get_strategy_path() to correctly resolve paths for
strategies in nested asset class directories.

Fixes #456
```

**Line length validation:**
```bash
# Subject: 50 chars max
feat(backtest): add validation  # ✅ 35 chars

feat(backtest): add comprehensive walk-forward validation support  # ❌ 67 chars
```

## Pre-commit Validation

**Check excluded files:**
```bash
# Files to exclude from commits
results/
data/bundles/
*.pyc
__pycache__/
*.log
.env
```

**Check for secrets:**
```bash
# Patterns to flag
API_KEY=
SECRET=
PASSWORD=
PRIVATE_KEY=
```

**Check commit size:**
```bash
git diff --cached --stat
# Warn if > 200 lines changed
```

## Notes

- Subject line: 50 characters max (hard limit)
- Body lines: 72 characters max (soft limit, wrap at 72)
- Recommended commit size: < 200 lines changed per commit
- Use `git commit --amend` to fix commit messages
- Use `git commit --no-verify` only when necessary (bypasses hooks)

## Related Commands

- code-review.md - For reviewing commit changes
- check-code-quality.md - For pre-commit quality checks











