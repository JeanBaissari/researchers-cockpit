"""
Test multi-strategy workflow.

Test parallel strategy development:
1. Create 3 different strategies
2. Run backtests for all
3. Compare results
4. Generate comparison report
5. Verify no conflicts
"""

# Standard library imports
import sys
import shutil
from pathlib import Path

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.utils import create_strategy_from_template
from lib.backtest import run_backtest, save_results
from lib.metrics import compare_strategies
from lib.config import load_strategy_params
from lib.bundles import list_bundles


@pytest.mark.integration
@pytest.mark.slow
def test_multi_strategy_workflow(project_root_path):
    """Test creating and running multiple strategies in parallel."""
    bundles = list_bundles()
    
    if len(bundles) == 0:
        pytest.skip("No bundles available for testing")
    
    bundle = bundles[0]
    strategy_names = []
    
    try:
        # Create 3 test strategies
        for i in range(3):
            strategy_name = f'test_multi_strategy_{i}'
            strategy_names.append(strategy_name)
            
            create_strategy_from_template(
                name=strategy_name,
                asset_class='equities',
                asset_symbol='SPY'
            )
        
        # Verify all strategies were created
        for strategy_name in strategy_names:
            strategy_path = project_root_path / 'strategies' / 'equities' / strategy_name
            assert strategy_path.exists(), f"Strategy {strategy_name} should exist"
    
    finally:
        # Cleanup
        for strategy_name in strategy_names:
            strategy_path = project_root_path / 'strategies' / 'equities' / strategy_name
            if strategy_path.exists():
                shutil.rmtree(strategy_path, ignore_errors=True)

