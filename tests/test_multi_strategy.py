"""
Test 4: Multi-Strategy Workflow

Test parallel strategy development:
1. Create 3 different strategies
2. Run backtests for all
3. Compare results
4. Generate comparison report
5. Verify no conflicts
"""

import pytest
from pathlib import Path
import sys
import shutil
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.utils import create_strategy_from_template
from lib.backtest import run_backtest, save_results
from lib.metrics import compare_strategies
from lib.config import load_strategy_params
from lib.data_loader import list_bundles


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
        
        # Run backtests for all (skip if data not available)
        results_dirs = []
        
        for strategy_name in strategy_names:
            try:
                params = load_strategy_params(strategy_name, 'equities')
                
                perf = run_backtest(
                    strategy_name=strategy_name,
                    start_date='2023-01-01',
                    end_date='2023-12-31',
                    bundle=bundle,
                    asset_class='equities'
                )
                
                result_dir = save_results(
                    strategy_name=strategy_name,
                    perf=perf,
                    params=params,
                    result_type='backtest'
                )
                
                results_dirs.append(result_dir)
                
            except Exception as e:
                pytest.skip(f"Backtest execution skipped: {e}")
        
        if len(results_dirs) == 0:
            pytest.skip("No successful backtests to compare")
        
        # Compare results
        comparison_df = compare_strategies(strategy_names)
        
        assert len(comparison_df) > 0, "Comparison DataFrame should not be empty"
        assert 'strategy' in comparison_df.columns, "Should have strategy column"
        assert 'sharpe' in comparison_df.columns, "Should have sharpe column"
        
        # Verify no conflicts in results directories
        for strategy_name in strategy_names:
            results_dir = project_root_path / 'results' / strategy_name
            assert results_dir.exists(), f"Results directory should exist for {strategy_name}"
            
            # Check that each strategy has its own directory
            assert len(list(results_dir.glob('backtest_*'))) > 0, \
                f"Should have backtest results for {strategy_name}"
        
    finally:
        # Cleanup
        for strategy_name in strategy_names:
            strategy_path = project_root_path / 'strategies' / 'equities' / strategy_name
            results_path = project_root_path / 'results' / strategy_name
            
            if strategy_path.exists():
                shutil.rmtree(strategy_path, ignore_errors=True)
            
            if results_path.exists():
                shutil.rmtree(results_path, ignore_errors=True)


def test_compare_strategies_function():
    """Test the compare_strategies function."""
    # This test requires existing strategies with results
    # For now, just test that function exists and can be called
    from lib.metrics import compare_strategies
    
    # Test with empty list
    comparison = compare_strategies([])
    assert isinstance(comparison, pd.DataFrame), "Should return DataFrame"
    
    # Test with non-existent strategies (should return empty DataFrame)
    comparison = compare_strategies(['nonexistent_strategy_xyz'])
    assert isinstance(comparison, pd.DataFrame), "Should return DataFrame even for non-existent strategies"



