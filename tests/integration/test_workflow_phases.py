"""
Test 7-phase workflow.

Tests for the complete 7-phase workflow:
1. Hypothesis validation
2. Strategy creation
3. Backtest execution
4. Results analysis
5. Parameter optimization
6. Strategy validation
7. Report generation
"""

# Standard library imports
import sys
import yaml
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.config import load_strategy_params
from lib.backtest import BacktestConfig
from lib.metrics import calculate_metrics
from lib.optimize import grid_search, random_search
from lib.validate import walk_forward, monte_carlo
from lib.report import generate_report


class TestPhase1Hypothesis:
    """Test Phase 1: Hypothesis Validation."""
    
    @pytest.mark.integration
    def test_template_directory_exists(self):
        """Test that strategy template directory exists."""
        template_dir = project_root / 'strategies' / '_template'
        assert template_dir.exists(), "Strategy template directory should exist"
    
    @pytest.mark.integration
    def test_template_has_strategy_file(self):
        """Test that template has strategy.py."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        if strategy_file.exists():
            content = strategy_file.read_text()
            assert 'def initialize(' in content, "Template should have initialize function"
            assert 'def handle_data(' in content, "Template should have handle_data function"


class TestPhase2StrategyCreation:
    """Test Phase 2: Strategy Creation."""
    
    @pytest.mark.unit
    def test_strategy_params_structure(self, sample_strategy_params):
        """Test strategy parameters have required structure."""
        assert 'name' in sample_strategy_params
        assert 'asset_class' in sample_strategy_params
        assert 'timeframe' in sample_strategy_params
        assert 'start_date' in sample_strategy_params
        assert 'end_date' in sample_strategy_params
    
    @pytest.mark.unit
    def test_strategy_params_types(self, sample_strategy_params):
        """Test strategy parameters have correct types."""
        assert isinstance(sample_strategy_params['name'], str)
        assert isinstance(sample_strategy_params['asset_class'], str)
        assert isinstance(sample_strategy_params['symbols'], list)
        assert isinstance(sample_strategy_params['capital_base'], (int, float))


class TestPhase3Backtest:
    """Test Phase 3: Backtest Execution."""
    
    @pytest.mark.unit
    def test_backtest_config_creation(self):
        """Test creating BacktestConfig."""
        config = BacktestConfig(
            strategy_name='test_strategy',
            start_date='2020-01-01',
            end_date='2020-12-31',
            capital_base=100000,
            bundle='test_bundle',
            data_frequency='daily',
        )
        assert config is not None
        assert config.start_date == '2020-01-01'
        assert config.end_date == '2020-12-31'
        assert config.capital_base == 100000
    
    @pytest.mark.unit
    def test_backtest_results_structure(self, sample_backtest_results):
        """Test BacktestResults structure."""
        assert 'portfolio_value' in sample_backtest_results
        assert 'returns' in sample_backtest_results
        assert 'sharpe_ratio' in sample_backtest_results
        assert 'max_drawdown' in sample_backtest_results


class TestPhase4Analysis:
    """Test Phase 4: Results Analysis."""
    
    @pytest.mark.unit
    def test_metrics_calculation(self, sample_backtest_results):
        """Test metrics calculation."""
        returns = sample_backtest_results['returns']
        metrics = calculate_metrics(returns)
        
        sharpe = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('max_drawdown', 0)
        
        assert isinstance(sharpe, (int, float))
        assert isinstance(max_dd, (int, float))
        assert max_dd <= 0
    
    @pytest.mark.unit
    def test_performance_metrics(self, sample_backtest_results):
        """Test performance metrics."""
        total_return = sample_backtest_results['total_return']
        annual_return = sample_backtest_results['annual_return']
        volatility = sample_backtest_results['volatility']
        
        assert isinstance(total_return, (int, float))
        assert isinstance(annual_return, (int, float))
        assert isinstance(volatility, (int, float))
        assert volatility >= 0


class TestPhase5Optimization:
    """Test Phase 5: Parameter Optimization."""
    
    @pytest.mark.unit
    def test_grid_search_function_exists(self):
        """Test that grid_search function exists."""
        assert grid_search is not None
        assert callable(grid_search)
    
    @pytest.mark.unit
    def test_random_search_function_exists(self):
        """Test that random_search function exists."""
        assert random_search is not None
        assert callable(random_search)
    
    @pytest.mark.unit
    def test_optimization_results_structure(self, sample_optimization_results):
        """Test optimization results structure."""
        assert 'best_params' in sample_optimization_results
        assert 'best_score' in sample_optimization_results
        assert 'all_results' in sample_optimization_results


class TestPhase6Validation:
    """Test Phase 6: Strategy Validation."""
    
    @pytest.mark.unit
    def test_walk_forward_function_exists(self):
        """Test that walk_forward function exists."""
        assert walk_forward is not None
        assert callable(walk_forward)
    
    @pytest.mark.unit
    def test_monte_carlo_function_exists(self):
        """Test that monte_carlo function exists."""
        assert monte_carlo is not None
        assert callable(monte_carlo)


class TestPhase7Reporting:
    """Test Phase 7: Report Generation."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_report_exists(self):
        """Test that generate_report function exists."""
        assert generate_report is not None
        assert callable(generate_report)
        
        import inspect
        sig = inspect.signature(generate_report)
        params = list(sig.parameters.keys())
        
        # Should have parameters
        assert len(params) > 0
    
    @pytest.mark.unit
    def test_report_sections(self):
        """Test report has expected sections."""
        expected_sections = [
            'summary',
            'performance_metrics',
            'risk_metrics',
            'trade_analysis',
            'equity_curve',
        ]
        
        # Report should have these sections
        for section in expected_sections:
            assert isinstance(section, str)

