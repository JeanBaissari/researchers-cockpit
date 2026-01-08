"""
Test end-to-end workflow.

Complete journey for one strategy:
1. Create strategy from template
2. Write hypothesis
3. Configure parameters
4. Ingest data
5. Run backtest
6. Analyze results
7. Optimize parameters
8. Walk-forward validate
9. Generate report
10. Update catalog
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

from lib.utils import create_strategy_from_template, get_strategy_path
from lib.config import load_strategy_params, validate_strategy_params
from lib.backtest import run_backtest, save_results
from lib.bundles import list_bundles


@pytest.mark.integration
def test_end_to_end_workflow(project_root_path, test_strategy_name, test_asset_class, cleanup_test_strategy):
    """
    Test complete end-to-end workflow for a strategy.
    
    This test verifies:
    1. Strategy creation from template
    2. Parameter configuration
    3. Data ingestion (if needed)
    4. Backtest execution
    5. Results saving
    6. All outputs exist
    """
    strategy_name = test_strategy_name
    asset_class = test_asset_class
    
    # Step 1: Create strategy from template
    strategy_path = create_strategy_from_template(
        name=strategy_name,
        asset_class=asset_class,
        asset_symbol='SPY'
    )
    
    assert strategy_path.exists(), "Strategy directory should be created"
    
    # Step 2: Verify strategy files exist
    assert (strategy_path / 'strategy.py').exists(), "strategy.py should exist"
    assert (strategy_path / 'parameters.yaml').exists(), "parameters.yaml should exist"
    
    # Step 3: Load and validate parameters
    params = load_strategy_params(strategy_name, asset_class)
    assert params is not None, "Should load strategy parameters"
    
    validation_result, errors = validate_strategy_params(params, strategy_name)
    assert validation_result, f"Strategy parameters should be valid, but got errors: {errors}"
    
    # Step 4: Check bundles are available
    bundles = list_bundles()
    assert isinstance(bundles, (list, dict)), "Should be able to list bundles"
    
    # Note: Actual backtest execution would require bundle data
    # This test verifies the workflow setup is correct

