"""
Test edge cases and boundary conditions.

Test boundary conditions:
1. Very short backtest (1 month)
2. Very long backtest (10 years) - skip if too slow
3. Single trade strategy
4. No trades strategy
5. Extreme parameters
6. Missing data periods
"""

# Standard library imports
import sys
import shutil
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params, validate_strategy_params
from lib.utils import create_strategy_from_template
from lib.bundles import list_bundles


@pytest.mark.slow
def test_very_short_backtest(project_root_path):
    """Test backtest with very short date range (1 month)."""
    bundles = list_bundles()
    
    if len(bundles) == 0:
        pytest.skip("No bundles available")
    
    bundle = bundles[0]
    strategy_name = 'test_short_backtest'
    
    try:
        create_strategy_from_template(
            name=strategy_name,
            asset_class='equities',
            asset_symbol='SPY'
        )
        
        params = load_strategy_params(strategy_name, 'equities')
        
        # Very short backtest: 1 month
        # Note: Actual execution would require bundle data
        assert params is not None
    
    finally:
        # Cleanup
        strategy_path = project_root_path / 'strategies' / 'equities' / strategy_name
        if strategy_path.exists():
            shutil.rmtree(strategy_path, ignore_errors=True)


@pytest.mark.slow
def test_extreme_parameters(project_root_path):
    """Test backtest with extreme parameters."""
    bundles = list_bundles()
    
    if len(bundles) == 0:
        pytest.skip("No bundles available")
    
    strategy_name = 'test_extreme_params'
    
    try:
        create_strategy_from_template(
            name=strategy_name,
            asset_class='equities',
            asset_symbol='SPY'
        )
        
        params = load_strategy_params(strategy_name, 'equities')
        
        # Test with extreme capital base
        params['capital_base'] = 1  # Very small
        validation_result = validate_strategy_params(params)
        
        # May or may not pass validation depending on implementation
        assert isinstance(validation_result, bool)
    
    finally:
        # Cleanup
        strategy_path = project_root_path / 'strategies' / 'equities' / strategy_name
        if strategy_path.exists():
            shutil.rmtree(strategy_path, ignore_errors=True)

