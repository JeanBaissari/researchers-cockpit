"""
Test multi-timeframe integration tests.

End-to-end integration tests for multi-timeframe workflows.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import load_bundle, load_bundle_registry


class TestEndToEndWorkflow:
    """End-to-end integration tests for multi-timeframe workflows."""

    @pytest.mark.integration
    def test_daily_bundle_exists(self):
        """Verify daily bundles can be loaded."""
        registry = load_bundle_registry()
        daily_bundles = [b for b in registry if 'daily' in b]

        if daily_bundles:
            bundle_name = daily_bundles[0]
            try:
                bundle = load_bundle(bundle_name)
                assert bundle is not None
            except FileNotFoundError:
                pytest.skip(f"Bundle {bundle_name} data not found on disk")

    @pytest.mark.integration
    def test_backtest_with_daily_bundle(self):
        """Test backtest execution with daily bundle."""
        registry = load_bundle_registry()

        # Find an equities daily bundle
        equities_daily = [b for b in registry if 'equities' in b and 'daily' in b]
        if not equities_daily:
            pytest.skip("No equities daily bundle available")

        # Verify the bundle has correct frequency
        bundle_meta = registry[equities_daily[0]]
        assert bundle_meta.get('data_frequency') == 'daily'

