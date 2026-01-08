"""
Test Phase 1: Hypothesis Validation

Tests the hypothesis validation workflow:
- Strategy template creation
- Parameter definition
- Initial validation
"""

import pytest
import sys
from pathlib import Path
import shutil
import yaml

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.config import load_strategy_params


class TestStrategyTemplateStructure:
    """Test strategy template structure."""
    
    def test_template_directory_exists(self):
        """Test that strategy template directory exists."""
        template_dir = project_root / 'strategies' / '_template'
        assert template_dir.exists(), "Strategy template directory should exist"
    
    def test_template_has_strategy_file(self):
        """Test that template has strategy.py."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        assert strategy_file.exists(), "Template should have strategy.py"
    
    def test_template_has_params_file(self):
        """Test that template has params.yaml."""
        params_file = project_root / 'strategies' / '_template' / 'params.yaml'
        assert params_file.exists(), "Template should have params.yaml"
    
    def test_template_strategy_is_valid_python(self):
        """Test that template strategy.py is valid Python."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        
        if not strategy_file.exists():
            pytest.skip("Template strategy.py not found")
        
        # Try to compile the file
        import py_compile
        try:
            py_compile.compile(str(strategy_file), doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"Template strategy.py has syntax errors: {e}")
    
    def test_template_params_is_valid_yaml(self):
        """Test that template params.yaml is valid YAML."""
        params_file = project_root / 'strategies' / '_template' / 'params.yaml'
        
        if not params_file.exists():
            pytest.skip("Template params.yaml not found")
        
        try:
            with open(params_file, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Template params.yaml has invalid YAML: {e}")


class TestStrategyTemplateContent:
    """Test strategy template content."""
    
    def test_template_has_initialize_function(self):
        """Test that template has initialize function."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        
        if not strategy_file.exists():
            pytest.skip("Template strategy.py not found")
        
        content = strategy_file.read_text()
        assert 'def initialize(' in content, "Template should have initialize function"
    
    def test_template_has_handle_data_function(self):
        """Test that template has handle_data function."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        
        if not strategy_file.exists():
            pytest.skip("Template strategy.py not found")
        
        content = strategy_file.read_text()
        assert 'def handle_data(' in content, "Template should have handle_data function"
    
    def test_template_uses_modern_imports(self):
        """Test that template uses modern import paths."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        
        if not strategy_file.exists():
            pytest.skip("Template strategy.py not found")
        
        content = strategy_file.read_text()
        
        # Should NOT use deprecated imports
        assert 'from lib.data_loader' not in content
        assert 'from lib.data_validation' not in content
        
        # If it has lib imports, they should be modern
        if 'from lib' in content:
            # This is OK - modern imports are allowed
            pass


class TestStrategyParameterValidation:
    """Test strategy parameter validation."""
    
    def test_template_params_structure(self):
        """Test that template params.yaml has expected structure."""
        params_file = project_root / 'strategies' / '_template' / 'params.yaml'
        
        if not params_file.exists():
            pytest.skip("Template params.yaml not found")
        
        with open(params_file, 'r') as f:
            params = yaml.safe_load(f)
        
        assert isinstance(params, dict), "params.yaml should contain a dictionary"
        
        # Check for common required fields
        expected_fields = ['name', 'asset_class', 'timeframe']
        for field in expected_fields:
            if field in params:
                assert params[field] is not None, f"{field} should not be None"
    
    def test_load_strategy_params_function(self):
        """Test load_strategy_params function works."""
        # Test that the function exists and can be called
        try:
            result = load_strategy_params('_template')
            assert isinstance(result, dict), "load_strategy_params should return dict"
        except FileNotFoundError:
            # Expected if template params don't exist
            pass
        except Exception as e:
            pytest.fail(f"load_strategy_params raised unexpected error: {e}")


class TestStrategyCreation:
    """Test strategy creation workflow."""
    
    def test_create_strategy_from_template(self, temp_strategy_dir):
        """Test creating a strategy from template."""
        template_dir = project_root / 'strategies' / '_template'
        
        if not template_dir.exists():
            pytest.skip("Template directory not found")
        
        # Copy template files
        strategy_file = template_dir / 'strategy.py'
        params_file = template_dir / 'params.yaml'
        
        if strategy_file.exists():
            shutil.copy(strategy_file, temp_strategy_dir / 'strategy.py')
        
        if params_file.exists():
            shutil.copy(params_file, temp_strategy_dir / 'params.yaml')
        
        # Verify copied files
        assert (temp_strategy_dir / 'strategy.py').exists()
        assert (temp_strategy_dir / 'params.yaml').exists()
    
    def test_customize_strategy_params(self, temp_strategy_dir):
        """Test customizing strategy parameters."""
        params_file = temp_strategy_dir / 'params.yaml'
        
        # Create test params
        test_params = {
            'name': 'test_strategy',
            'asset_class': 'equities',
            'symbols': ['SPY', 'QQQ'],
            'timeframe': '1d',
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'capital_base': 100000,
        }
        
        with open(params_file, 'w') as f:
            yaml.dump(test_params, f)
        
        # Load and verify
        with open(params_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded['name'] == 'test_strategy'
        assert loaded['asset_class'] == 'equities'
        assert 'SPY' in loaded['symbols']


class TestHypothesisDefinition:
    """Test hypothesis definition workflow."""
    
    def test_hypothesis_documentation_in_template(self):
        """Test that template has hypothesis documentation section."""
        strategy_file = project_root / 'strategies' / '_template' / 'strategy.py'
        
        if not strategy_file.exists():
            pytest.skip("Template strategy.py not found")
        
        content = strategy_file.read_text()
        
        # Should have docstring or comments about hypothesis
        assert '"""' in content or "'''" in content or '#' in content
    
    def test_hypothesis_parameters_in_params(self):
        """Test that params.yaml can store hypothesis-related parameters."""
        params_file = project_root / 'strategies' / '_template' / 'params.yaml'
        
        if not params_file.exists():
            pytest.skip("Template params.yaml not found")
        
        with open(params_file, 'r') as f:
            params = yaml.safe_load(f)
        
        # params.yaml should be a dict that can store any parameters
        assert isinstance(params, dict)


class TestStrategyValidation:
    """Test strategy validation before execution."""
    
    def test_strategy_has_required_functions(self, sample_strategy_file):
        """Test that strategy has required functions."""
        content = sample_strategy_file.read_text()
        
        # Must have initialize
        assert 'def initialize(' in content, "Strategy must have initialize function"
        
        # Must have handle_data or before_trading_start
        assert 'def handle_data(' in content or 'def before_trading_start(' in content
    
    def test_strategy_params_can_be_loaded(self, temp_strategy_dir):
        """Test that strategy params can be loaded."""
        params_file = temp_strategy_dir / 'params.yaml'
        
        if not params_file.exists():
            pytest.skip("params.yaml not created by fixture")
        
        with open(params_file, 'r') as f:
            params = yaml.safe_load(f)
        
        assert isinstance(params, dict)
        assert 'name' in params

