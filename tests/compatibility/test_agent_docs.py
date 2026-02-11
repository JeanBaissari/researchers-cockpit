"""
Guardrails for AI agent instruction docs.

These tests prevent documentation drift back to deprecated modules/paths that were
removed in the v1.12.0 "NO WRAPPERS" refactor.
"""

# Standard library imports
from pathlib import Path

# Third-party imports
import pytest


@pytest.mark.unit
def test_strategy_developer_agent_doc_has_no_deprecated_references():
    project_root = Path(__file__).parent.parent.parent
    agent_doc = project_root / ".claude" / "agents" / "strategy_developer.md"
    assert agent_doc.exists(), "Expected agent doc at .claude/agents/strategy_developer.md"

    content = agent_doc.read_text(encoding="utf-8")

    # Removed modules (v1.12.0+)
    assert "lib/logging_config.py" not in content
    assert "lib/logging_config" not in content
    assert "lib/backtest.py" not in content

    # Old agent folder reference (this repo standardizes on .claude/agents/)
    assert ".agent/conventions.md" not in content


@pytest.mark.unit
def test_zipline_researcher_agent_doc_targets_zipline_reloaded_only():
    project_root = Path(__file__).parent.parent.parent
    agent_doc = project_root / ".claude" / "agents" / "zipline-researcher.md"
    assert agent_doc.exists(), "Expected agent doc at .claude/agents/zipline-researcher.md"

    content = agent_doc.read_text(encoding="utf-8")

    # Must reference Zipline-Reloaded canonical repo (research source-of-truth)
    assert "https://github.com/stefan-jansen/zipline-reloaded" in content

    # Must not drift to legacy Quantopian Zipline patterns/docs
    assert "quantopian/zipline" not in content
    assert "www.quantopian.com" not in content


@pytest.mark.unit
def test_maintainer_agent_doc_has_no_deprecated_references_and_uses_current_tooling():
    project_root = Path(__file__).parent.parent.parent
    agent_doc = project_root / ".claude" / "agents" / "maintainer.md"
    assert agent_doc.exists(), "Expected agent doc at .claude/agents/maintainer.md"

    content = agent_doc.read_text(encoding="utf-8")

    # Removed modules (v1.12.0+)
    assert "lib/logging_config.py" not in content
    assert "lib/logging_config" not in content
    assert "lib/backtest.py" not in content

    # Current repo conventions
    assert "ruff" in content
    assert "pytest" in content
    assert "conda activate zipline-reloaded" in content


@pytest.mark.unit
def test_agent_integration_doc_exists_is_indexed_and_targets_zipline_reloaded_only():
    project_root = Path(__file__).parent.parent.parent
    doc_path = project_root / "docs" / "AGENT_INTEGRATION.md"
    assert doc_path.exists(), "Expected doc at docs/AGENT_INTEGRATION.md"

    doc_content = doc_path.read_text(encoding="utf-8")

    # Must reference Zipline-Reloaded canonical repo (research source-of-truth)
    assert "https://github.com/stefan-jansen/zipline-reloaded" in doc_content

    # Must not drift to legacy Quantopian Zipline patterns/docs
    assert "quantopian/zipline" not in doc_content
    assert "www.quantopian.com" not in doc_content

    # Must be indexed from docs/README.md per docs standards
    docs_readme = (project_root / "docs" / "README.md").read_text(encoding="utf-8")
    assert "docs/AGENT_INTEGRATION.md" in docs_readme
