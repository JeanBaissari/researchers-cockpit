"""
Hypothesis lifecycle management for The Researcher's Cockpit.

Provides dataclasses and functions for creating, loading, saving, and managing
trading hypotheses throughout their lifecycle (draft → testing → validated/rejected).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List

from lib.paths import get_project_root
from lib.utils import load_yaml, save_yaml


class HypothesisStatus(Enum):
    """Status of a hypothesis in its lifecycle."""

    DRAFT = "draft"
    TESTING = "testing"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass
class Hypothesis:
    """
    Trading hypothesis with lifecycle tracking.

    Attributes:
        id: Unique identifier (YYYY-MM_slug format)
        created: Creation date (YYYY-MM-DD)
        updated: Last update date (YYYY-MM-DD)
        status: Current lifecycle status
        title: Short hypothesis title
        description: Detailed hypothesis description
        asset_class: Asset class (crypto, forex, equities)
        symbols: List of symbols to test
        timeframe: Timeframe for testing (daily, 1h, etc.)
        why: Rationale for the hypothesis
        prior_evidence: Evidence supporting the hypothesis
        expected_sharpe: Expected Sharpe ratio
        expected_max_drawdown: Expected maximum drawdown
        strategy_name: Associated strategy name
        backtest_ids: List of linked backtest IDs
        parameter_ranges: Parameter ranges for testing
        actual_sharpe: Actual Sharpe ratio from testing
        actual_max_drawdown: Actual maximum drawdown from testing
        conclusion: Final conclusion (validated/rejected with reason)
        learnings: Key learnings from testing
        tags: List of tags for categorization
    """

    id: str
    created: str
    updated: str
    status: HypothesisStatus
    title: str
    description: str
    asset_class: str
    symbols: List[str] = field(default_factory=list)
    timeframe: str = "daily"
    why: str = ""
    prior_evidence: str = ""
    expected_sharpe: Optional[float] = None
    expected_max_drawdown: Optional[float] = None
    strategy_name: Optional[str] = None
    backtest_ids: List[str] = field(default_factory=list)
    parameter_ranges: dict = field(default_factory=dict)
    actual_sharpe: Optional[float] = None
    actual_max_drawdown: Optional[float] = None
    conclusion: Optional[str] = None
    learnings: Optional[str] = None
    tags: List[str] = field(default_factory=list)


def _get_hypotheses_dir() -> Path:
    """Get the hypotheses storage directory."""
    return get_project_root() / "research" / "hypotheses"


def _generate_hypothesis_id(title: str) -> str:
    """Generate a hypothesis ID from title and current date."""
    # Create slug from title (lowercase, replace spaces with hyphens)
    slug = title.lower().replace(" ", "_")[:30]  # Limit to 30 chars
    # Remove special characters
    slug = "".join(c for c in slug if c.isalnum() or c in "-_")
    # Add date prefix
    date_prefix = datetime.now().strftime("%Y-%m")
    return f"{date_prefix}_{slug}"


def create_hypothesis(
    title: str,
    asset_class: str,
    description: str = "",
    symbols: Optional[List[str]] = None,
    timeframe: str = "daily",
    tags: Optional[List[str]] = None,
) -> Hypothesis:
    """
    Create a new hypothesis with DRAFT status.

    Args:
        title: Short hypothesis title
        asset_class: Asset class (crypto, forex, equities)
        description: Detailed hypothesis description
        symbols: List of symbols to test
        timeframe: Timeframe for testing
        tags: List of tags for categorization

    Returns:
        New Hypothesis instance
    """
    today = datetime.now().strftime("%Y-%m-%d")
    hypothesis_id = _generate_hypothesis_id(title)

    return Hypothesis(
        id=hypothesis_id,
        created=today,
        updated=today,
        status=HypothesisStatus.DRAFT,
        title=title,
        description=description,
        asset_class=asset_class,
        symbols=symbols or [],
        timeframe=timeframe,
        tags=tags or [],
    )


def save_hypothesis(hypothesis: Hypothesis) -> Path:
    """
    Save hypothesis to YAML file.

    Args:
        hypothesis: Hypothesis instance to save

    Returns:
        Path to saved YAML file

    Raises:
        OSError: If directory creation or file write fails
    """
    hypotheses_dir = _get_hypotheses_dir()
    hypotheses_dir.mkdir(parents=True, exist_ok=True)

    file_path = hypotheses_dir / f"{hypothesis.id}.yaml"

    # Convert to dict with proper structure
    data = {
        "id": hypothesis.id,
        "created": hypothesis.created,
        "updated": hypothesis.updated,
        "status": hypothesis.status.value,
        "hypothesis": {
            "title": hypothesis.title,
            "description": hypothesis.description,
            "asset_class": hypothesis.asset_class,
            "symbols": hypothesis.symbols,
            "timeframe": hypothesis.timeframe,
        },
        "rationale": {
            "why": hypothesis.why,
            "prior_evidence": hypothesis.prior_evidence,
            "expected_sharpe": hypothesis.expected_sharpe,
            "expected_max_drawdown": hypothesis.expected_max_drawdown,
        },
        "testing": {
            "strategy_name": hypothesis.strategy_name,
            "backtest_ids": hypothesis.backtest_ids,
            "parameter_ranges": hypothesis.parameter_ranges,
        },
        "results": {
            "actual_sharpe": hypothesis.actual_sharpe,
            "actual_max_drawdown": hypothesis.actual_max_drawdown,
            "conclusion": hypothesis.conclusion,
            "learnings": hypothesis.learnings,
        },
        "tags": hypothesis.tags,
    }

    save_yaml(data, file_path)
    return file_path


def load_hypothesis(hypothesis_id: str) -> Hypothesis:
    """
    Load hypothesis from YAML file.

    Args:
        hypothesis_id: Hypothesis identifier

    Returns:
        Loaded Hypothesis instance

    Raises:
        FileNotFoundError: If hypothesis file doesn't exist
        ValueError: If YAML structure is invalid
    """
    file_path = _get_hypotheses_dir() / f"{hypothesis_id}.yaml"
    data = load_yaml(file_path)

    # Extract nested fields
    hyp = data.get("hypothesis", {})
    rat = data.get("rationale", {})
    test = data.get("testing", {})
    res = data.get("results", {})

    return Hypothesis(
        id=data["id"],
        created=data["created"],
        updated=data["updated"],
        status=HypothesisStatus(data["status"]),
        title=hyp.get("title", ""),
        description=hyp.get("description", ""),
        asset_class=hyp.get("asset_class", ""),
        symbols=hyp.get("symbols", []),
        timeframe=hyp.get("timeframe", "daily"),
        why=rat.get("why", ""),
        prior_evidence=rat.get("prior_evidence", ""),
        expected_sharpe=rat.get("expected_sharpe"),
        expected_max_drawdown=rat.get("expected_max_drawdown"),
        strategy_name=test.get("strategy_name"),
        backtest_ids=test.get("backtest_ids", []),
        parameter_ranges=test.get("parameter_ranges", {}),
        actual_sharpe=res.get("actual_sharpe"),
        actual_max_drawdown=res.get("actual_max_drawdown"),
        conclusion=res.get("conclusion"),
        learnings=res.get("learnings"),
        tags=data.get("tags", []),
    )


def list_hypotheses(status: Optional[HypothesisStatus] = None) -> List[Hypothesis]:
    """
    List all hypotheses, optionally filtered by status.

    Args:
        status: Filter by status (None = all)

    Returns:
        List of Hypothesis instances
    """
    hypotheses_dir = _get_hypotheses_dir()
    if not hypotheses_dir.exists():
        return []

    hypotheses = []
    for yaml_file in hypotheses_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):  # Skip template files
            continue
        try:
            hyp = load_hypothesis(yaml_file.stem)
            if status is None or hyp.status == status:
                hypotheses.append(hyp)
        except (FileNotFoundError, ValueError, KeyError):
            # Skip invalid hypothesis files
            continue

    return hypotheses


def link_backtest(hypothesis_id: str, backtest_id: str) -> None:
    """
    Link a backtest to a hypothesis.

    Args:
        hypothesis_id: Hypothesis identifier
        backtest_id: Backtest identifier to link

    Raises:
        FileNotFoundError: If hypothesis doesn't exist
    """
    hyp = load_hypothesis(hypothesis_id)

    # Add backtest ID if not already present
    if backtest_id not in hyp.backtest_ids:
        hyp.backtest_ids.append(backtest_id)

    # Update timestamp
    hyp.updated = datetime.now().strftime("%Y-%m-%d")

    save_hypothesis(hyp)


__all__ = [
    "HypothesisStatus",
    "Hypothesis",
    "create_hypothesis",
    "save_hypothesis",
    "load_hypothesis",
    "list_hypotheses",
    "link_backtest",
]
