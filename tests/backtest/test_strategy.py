"""
Test backtest strategy.

Tests for strategy execution in backtests.
"""

# Standard library imports
import sys
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest import BacktestConfig


class TestStrategyExecution:
    """Test strategy execution in backtests."""
    
    @pytest.mark.unit
    def test_strategy_file_structure(self, sample_strategy_file):
        """Test strategy file has correct structure."""
        content = sample_strategy_file.read_text()
        
        # Should have imports
        assert 'import' in content or 'from' in content
        
        # Should have initialize function
        assert 'def initialize' in content
        
        # Should have handle_data function
        assert 'def handle_data' in content
    
    @pytest.mark.unit
    def test_strategy_uses_context(self, sample_strategy_file):
        """Test that strategy uses context object."""
        content = sample_strategy_file.read_text()
        
        # Strategy should reference context
        assert 'context' in content

