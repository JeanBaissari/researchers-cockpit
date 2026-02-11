#!/bin/bash
# Finalize guide documentation to meet compliance standards

set -e

echo "Finalizing guide documentation compliance..."
echo ""

# Fix project_description.md - this is a special case, it's comprehensive but just needs Purpose/Scope/Related
python3 << 'EOF'
filepath = "docs/project_description.md"
with open(filepath, 'r') as f:
    content = f.read()

# Add Purpose + Scope after header, before first section
if "## Purpose" not in content:
    # Find the header block end
    insert_text = """
## Purpose

The Researcher's Cockpit is a research-first algorithmic trading environment built on Zipline-Reloaded. It provides a structured workspace for developing, testing, and validating trading strategies with AI-agent integration and clear separation of concerns.

---

## Scope

**What this covers:**
- Complete project structure and organization
- Directory-by-directory explanations
- File naming conventions and standards
- Integration points (Zipline, Jupyter, AI agents)
- Asset class organization (crypto, forex, equities)

**What this does NOT cover:**
- API implementation details (see `docs/api/`)
- Strategy development specifics (see `.claude/skills/`)
- Troubleshooting guides (see `docs/troubleshooting/`)

---

"""
    # Insert after the badges and philosophy block
    content = content.replace(
        '---\n\n## Project Identity',
        insert_text + '## Project Identity'
    )

# Add Related section before footer
if "## Related Documentation" not in content:
    related = """
## Related Documentation

- [API Reference](docs/api/README.md) - Complete API documentation
- [Documentation Map](docs/doc_map.md) - Visual navigation guide
- [Value Add Modules](docs/value_add_modules.md) - Architecture principles
- [Agent Integration](docs/agent_integration.md) - AI agent integration
- [Strategy Catalog](docs/strategy_catalog.md) - Strategy inventory

---
"""
    # Insert before footer
    content = content.replace(
        "\n**Last Updated:**",
        "\n" + related + "\n**Last Updated:**"
    )

with open(filepath, 'w') as f:
    f.write(content)
print(f"✓ Fixed {filepath}")
EOF

# Fix walkthrough/validation.md - it already has Purpose/Scope from batch script, verify they exist
python3 << 'EOF'
filepath = "docs/walkthrough/validation.md"
with open(filepath, 'r') as f:
    content = f.read()

if "## Purpose" in content and "## Scope" in content:
    print(f"✓ {filepath} already compliant (has Purpose and Scope)")
else:
    print(f"⚠ {filepath} missing Purpose or Scope, but batch script should have added them")
EOF

# Fix value_add_modules.md - add Purpose and Scope
python3 << 'EOF'
filepath = "docs/value_add_modules.md"
with open(filepath, 'r') as f:
    content = f.read()

if "## Purpose" not in content:
    # Insert after header
    insert_text = """
---

## Purpose

This document defines which project modules add value beyond Zipline-Reloaded's core functionality and which areas intentionally use Zipline-Reloaded APIs directly (NO WRAPPERS architecture). It serves as the architectural guide for deciding whether to implement custom code or use framework features.

---

## Scope

**What this covers:**
- Modules that add project-specific value (`lib/config/`, `lib/logging/`, etc.)
- Areas where we use Zipline-Reloaded directly (bundles, calendars, Pipeline)
- Decision criteria for implementing custom vs using framework
- Architecture compliance guidelines

**What this does NOT cover:**
- Detailed API documentation (see `docs/api/`)
- Implementation tutorials (see `.claude/skills/`)
- Zipline-Reloaded API reference (see stefan-jansen/zipline-reloaded)

---

"""
    content = content.replace(
        "## Guiding Principle",
        insert_text + "## Guiding Principle"
    )

with open(filepath, 'w') as f:
    f.write(content)
print(f"✓ Fixed {filepath}")
EOF

# Fix agent_integration.md - add Purpose and Scope
python3 << 'EOF'
filepath = "docs/agent_integration.md"
with open(filepath, 'r') as f:
    content = f.read()

if "## Purpose" not in content:
    # Insert after header
    insert_text = """
---

## Purpose

This guide explains how AI agents should interact with the Researcher's Cockpit codebase, following the NO WRAPPERS architecture and using Zipline-Reloaded APIs directly. It defines conventions, handoff zones, and integration patterns for AI-assisted development.

---

## Scope

**What this covers:**
- Agent instruction locations (`.claude/agents/`, `.claude/skills/`)
- Handoff zones for human-agent collaboration
- File and feature conventions agents must follow
- Logging, paths, and configuration patterns
- Source of truth for Zipline APIs (stefan-jansen/zipline-reloaded only)

**What this does NOT cover:**
- Detailed API documentation (see `docs/api/`)
- Strategy development specifics (see `.claude/skills/`)
- Project architecture details (see `docs/value_add_modules.md`)

---

"""
    content = content.replace(
        "## Source of truth",
        insert_text + "## Source of truth"
    )

with open(filepath, 'w') as f:
    f.write(content)
print(f"✓ Fixed {filepath}")
EOF

# Fix strategy_catalog.md - add Examples section (even if empty, to meet validation)
python3 << 'EOF'
filepath = "docs/strategy_catalog.md"
with open(filepath, 'r') as f:
    content = f.read()

if "## Examples" not in content and "## How to Use" not in content:
    # Add How to Use section before Metrics Reference
    insert_text = """
## How to Use This Catalog

**Adding a new strategy:**
1. Create strategy in `strategies/{asset_class}/{name}/`
2. Run backtest with `python scripts/run_backtest.py --strategy {name}`
3. Update this catalog with performance metrics
4. Run validation (walk-forward, Monte Carlo)
5. Update validation status

**Updating metrics:**
```bash
# After backtest completion
python scripts/generate_report.py --strategy {name}
# Metrics will be in results/{name}/latest/metrics.json
```

**Strategy status workflow:**
```
development → backtested → validated → paper → live
```

---

"""
    content = content.replace(
        "## Metrics Reference",
        insert_text + "## Metrics Reference"
    )

with open(filepath, 'w') as f:
    f.write(content)
print(f"✓ Fixed {filepath}")
EOF

echo ""
echo "✓ All guide docs finalized"
echo "Run: python scripts/enforce_doc_standards.py to verify compliance"
