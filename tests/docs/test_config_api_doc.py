"""
Tests for config API documentation (docs/api/config.md).

This doc should clearly explain how lib/config/ maps configuration values
into Zipline-Reloaded's run_algorithm() inputs, which Zipline uses to build
SimulationParameters internally.
"""

from pathlib import Path


def _config_doc_path() -> Path:
    """Return path to docs/api/config.md."""
    return Path(__file__).resolve().parent.parent.parent / "docs" / "api" / "config.md"


def test_config_api_doc_exists():
    """Test that config API document exists."""
    path = _config_doc_path()
    assert path.exists(), "docs/api/config.md should exist"


def test_config_api_doc_has_simulationparameters_section():
    """Test that doc includes section on SimulationParameters integration."""
    content = _config_doc_path().read_text()
    assert "Zipline `SimulationParameters` Integration" in content, (
        "Doc should include section 'Zipline `SimulationParameters` Integration'"
    )


def test_config_api_doc_mentions_zipline_params_module():
    """Test that doc points to the canonical mapping module."""
    content = _config_doc_path().read_text()
    assert "lib/config/zipline_params.py" in content
    assert "extract_zipline_params" in content
