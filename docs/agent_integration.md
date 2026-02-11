# Agent Integration Guide (v1.12.0+)

This project is designed to be **AI-agent friendly** while staying **Zipline-Reloaded native** (NO WRAPPERS).


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

## Source of truth (Zipline-Reloaded only)

When implementing or validating Zipline APIs, agents must use **Zipline-Reloaded** as the only reference:

- Canonical repo: `https://github.com/stefan-jansen/zipline-reloaded`

Do not use legacy Quantopian Zipline docs/patterns.

## Where agent instructions live

- **Agent definitions**: `.claude/agents/`
- **Reusable skill/playbooks**: `.claude/skills/`

Agents should follow the current modular architecture (v1.12.0+):

- Use `lib.*` imports (absolute imports from project root)
- Do not add wrapper layers over Zipline APIs
- Keep modules small and focused (SRP + DRY)

## Handoff zones (how to collaborate)

This repo is structured so humans and agents can work in parallel without stepping on each other:

- **Research**: `notebooks/` (prototype ideas, validate Zipline-Reloaded behavior)
- **Implement**: `lib/` (reusable analysis/metrics/plots) and `strategies/` (strategy glue)
- **Backtest**: `scripts/run_backtest.py` and Zipline CLI
- **Analyze**: `lib/metrics/`, `lib/plots/`, `docs/` (document findings)

## File/feature conventions agents must follow

### Logging

Use the centralized logging system:

- Configure at entrypoints using `lib.logging.config.configure_logging`
- Use `lib.logging.config.get_logger` for general logs
- Use specialized loggers from `lib.logging.loggers` where appropriate
- Wrap multi-step operations in `lib.logging.context.LogContext`

Never use the standard library `logging` module directly.

### Paths and configuration

- Do not hardcode paths.
- Resolve project paths with `lib.paths`.
- Load configuration via `lib.config` modules.

### Strategy parameters

Strategies must not hardcode parameters in `strategy.py`.

- Strategy config lives in `strategies/{strategy_name}/parameters.yaml`
- Load strategy parameters via `lib.config.strategy`

### Calendars and bundle registration

- Bundle registration is done in `~/.zipline/extension.py` via `register()`.
- Use `exchange_calendars` built-ins for equities.
- Define custom calendars in `lib/calendars/` for CRYPTO (24/7) and FOREX (24/5 with Sunday open).
- Register custom calendars via `exchange_calendars.register_calendar()` **before** bundle registration.
- Calendar names must match exactly between registration and bundle definitions.

## What agents should (and should not) change

### Safe to change

- `lib/` modules (when adding real value beyond Zipline-Reloaded)
- `strategies/` (new strategies or improvements that respect template rules)
- `docs/` (new focused docs and API docs under `docs/api/`)
- `tests/` (unit tests for new functionality and guardrails)
- `scripts/` (CLI improvements that follow existing conventions)

### Not safe to change without explicit instruction

- `results/`, `reports/`, `logs/`, `data/bundles/` (generated artifacts)
- `.git/` and repository metadata

## Minimal “agent workflow” checklist

- Validate assumptions in `notebooks/` first when unsure about a Zipline behavior.
- Implement reusable logic in `lib/` (small, focused modules).
- Integrate in `strategies/` by loading YAML parameters.
- Add unit tests under `tests/`.
- Run `pytest` and linting before finalizing changes.

---

## Related Documentation

- [Value Add Modules](value_add_modules.md) - Architecture principles (NO WRAPPERS)
- [API Reference](api/README.md) - Complete API documentation
- [Agent Definitions](../.claude/agents/) - Specialized agent instructions
- [Skills](../.claude/skills/) - Reusable agent skills

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
