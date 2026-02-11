"""
Research utilities for The Researcher's Cockpit.

This package provides hypothesis lifecycle management for tracking trading ideas
from conception through validation or rejection.

Public API:
    - HypothesisStatus: Enum for hypothesis lifecycle states
    - Hypothesis: Dataclass for hypothesis data
    - create_hypothesis: Create a new hypothesis
    - save_hypothesis: Save hypothesis to YAML
    - load_hypothesis: Load hypothesis from YAML
    - list_hypotheses: List hypotheses with optional status filter
    - link_backtest: Link a backtest to a hypothesis
"""

from __future__ import annotations

from .hypothesis import (
    HypothesisStatus,
    Hypothesis,
    create_hypothesis,
    save_hypothesis,
    load_hypothesis,
    list_hypotheses,
    link_backtest,
)

__all__ = [
    "HypothesisStatus",
    "Hypothesis",
    "create_hypothesis",
    "save_hypothesis",
    "load_hypothesis",
    "list_hypotheses",
    "link_backtest",
]
