#!/bin/bash
# Batch fix all non-compliant documentation files

set -e

PROJ_ROOT="/home/jeanbaissari/Documents/Programming/python-projects/algorithmic_trading/v1_researchers_cockpit"

echo "Applying batch fixes to documentation..."
echo ""

# Fix project_description.md - add metadata footer only (already has good structure)
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/jeanbaissari/Documents/Programming/python-projects/algorithmic_trading/v1_researchers_cockpit')

filepath = "docs/project_description.md"
with open(filepath, 'r') as f:
    content = f.read()

footer = """
---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture"""

if "**Last Updated:**" not in content:
    content = content.rstrip() + "\n" + footer + "\n"
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")
else:
    print(f"⚠ {filepath} already has footer")
EOF

# Fix value_add_modules.md
python3 << 'EOF'
filepath = "docs/value_add_modules.md"
with open(filepath, 'r') as f:
    content = f.read()

# Add Related section before final line
related = """
---

## Related Documentation

- [Agent Integration](agent_integration.md) - How AI agents work in this repo
- [API Reference](api/README.md) - Complete API documentation
- [Project Description](project_description.md) - Project overview
- [Verification Reports](verification/) - Compliance verification proofs

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture"""

if "## Related Documentation" not in content and "**Last Updated:**" not in content:
    content = content.rstrip() + "\n" + related + "\n"
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")
else:
    print(f"⚠ {filepath} already has footer/related")
EOF

# Fix agent_integration.md
python3 << 'EOF'
filepath = "docs/agent_integration.md"
with open(filepath, 'r') as f:
    content = f.read()

footer = """
---

## Related Documentation

- [Value Add Modules](value_add_modules.md) - Architecture principles (NO WRAPPERS)
- [API Reference](api/README.md) - Complete API documentation
- [Agent Definitions](../.claude/agents/) - Specialized agent instructions
- [Skills](../.claude/skills/) - Reusable agent skills

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture"""

if "**Last Updated:**" not in content:
    content = content.rstrip() + "\n" + footer + "\n"
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")
else:
    print(f"⚠ {filepath} already has footer")
EOF

# Fix walkthrough/validation.md
python3 << 'EOF'
filepath = "docs/walkthrough/validation.md"
with open(filepath, 'r') as f:
    content = f.read()

# Add Purpose section after header
if "## Purpose" not in content:
    content = content.replace(
        "## Prerequisites",
        """## Purpose

This walkthrough guides you through the complete validation workflow in the Researcher's Cockpit, from data quality checks through bundle verification to post-backtest result validation.

---

## Scope

**What this covers:**
- Pre-ingestion CSV data validation
- Bundle integrity verification
- Post-backtest result validation
- Common validation errors and fixes

**What this does NOT cover:**
- Strategy validation (walk-forward, Monte Carlo) - see `lib/strategy_validation/`
- Data ingestion process - see [Bundles API](../api/bundles.md)

---

## Prerequisites"""
    )

# Add Related and footer
if "## Related" not in content and "**Last Updated:**" not in content:
    footer = """
---

## Related Documentation

- [Validation API](../api/validation.md) - Data validation reference
- [Bundles API](../api/bundles.md) - Bundle management
- [Troubleshooting: Data Validation](../troubleshooting/data_validation.md)
- [Validation Architecture](../validation/validation_architecture.md)

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture"""
    content = content.rstrip() + "\n" + footer + "\n"

with open(filepath, 'w') as f:
    f.write(content)
print(f"✓ Fixed {filepath}")
EOF

echo ""
echo "✓ All batch fixes applied"
echo "Run: python scripts/enforce_doc_standards.py to verify compliance"
