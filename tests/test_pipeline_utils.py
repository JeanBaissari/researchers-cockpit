"""
Tests for lib.pipeline_utils module.

Tests pipeline setup, validation, and availability checking.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest
import warnings

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.pipeline_utils import (
    setup_pipeline,
    is_pipeline_available,
    validate_pipeline_config
)


class TestPipelineAvailability:
    """Test pipeline availability checking."""
    
    @pytest.mark.unit
    def test_is_pipeline_available(self):
        """Test is_pipeline_available function."""
        # This will depend on whether zipline is installed
        result = is_pipeline_available()
        assert isinstance(result, bool)


class TestSetupPipeline:
    """Test pipeline setup function."""
    
    @pytest.mark.unit
    def test_pipeline_disabled_in_params(self):
        """Test that pipeline is not set up when disabled in params."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': False
            }
        }
        
        result = setup_pipeline(context, params)
        
        assert result is False
        assert context.use_pipeline is False
        assert context.pipeline_data is None
        assert context.pipeline_universe == []
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', False)
    def test_pipeline_not_available_warning(self):
        """Test warning when pipeline API is not available."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': True
            }
        }
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = setup_pipeline(context, params)
            
            assert result is False
            assert context.use_pipeline is False
            assert len(w) > 0
            assert any("not available" in str(warning.message) for warning in w)
    
    @pytest.mark.unit
    def test_pipeline_warning_for_non_equities(self):
        """Test warning when pipeline is used for non-equities asset class."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'crypto'
            }
        }
        
        # Mock pipeline as available
        with patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True):
            with patch('lib.pipeline_utils.attach_pipeline'):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    result = setup_pipeline(context, params, make_pipeline_func=None)
                    
                    # Should warn but not fail
                    assert any("primarily designed for US equities" in str(warning.message) 
                              for warning in w)
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True)
    def test_pipeline_setup_success(self):
        """Test successful pipeline setup."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'equities'
            }
        }
        
        # Mock pipeline creation
        mock_pipeline = Mock()
        def make_pipeline():
            return mock_pipeline
        
        with patch('lib.pipeline_utils.attach_pipeline') as mock_attach:
            result = setup_pipeline(context, params, make_pipeline_func=make_pipeline)
            
            assert result is True
            assert context.use_pipeline is True
            mock_attach.assert_called_once_with(mock_pipeline, 'my_pipeline')
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True)
    def test_pipeline_setup_with_none_pipeline(self):
        """Test pipeline setup when make_pipeline returns None."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'equities'
            }
        }
        
        def make_pipeline():
            return None
        
        result = setup_pipeline(context, params, make_pipeline_func=make_pipeline)
        
        assert result is False
        assert context.use_pipeline is False
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True)
    def test_pipeline_setup_with_exception(self):
        """Test pipeline setup handles exceptions gracefully."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'equities'
            }
        }
        
        def make_pipeline():
            raise ValueError("Pipeline creation failed")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = setup_pipeline(context, params, make_pipeline_func=make_pipeline)
            
            assert result is False
            assert context.use_pipeline is False
            assert any("Failed to create pipeline" in str(warning.message) for warning in w)
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True)
    def test_pipeline_setup_without_make_pipeline_func(self):
        """Test pipeline setup when no make_pipeline function provided."""
        context = Mock()
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'equities'
            }
        }
        
        result = setup_pipeline(context, params, make_pipeline_func=None)
        
        assert result is False
        assert context.use_pipeline is False


class TestValidatePipelineConfig:
    """Test pipeline configuration validation."""
    
    @pytest.mark.unit
    def test_validate_pipeline_disabled(self):
        """Test validation when pipeline is disabled."""
        params = {
            'strategy': {
                'use_pipeline': False
            }
        }
        
        is_valid, warnings_list = validate_pipeline_config(params)
        
        assert is_valid is True
        assert len(warnings_list) == 0
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', False)
    def test_validate_pipeline_not_available(self):
        """Test validation when pipeline API is not available."""
        params = {
            'strategy': {
                'use_pipeline': True
            }
        }
        
        is_valid, warnings_list = validate_pipeline_config(params)
        
        assert is_valid is False
        assert len(warnings_list) > 0
        assert any("not available" in warning for warning in warnings_list)
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True)
    def test_validate_pipeline_non_equities_warning(self):
        """Test validation warning for non-equities asset class."""
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'crypto'
            }
        }
        
        is_valid, warnings_list = validate_pipeline_config(params)
        
        # Should be valid but with warning
        assert is_valid is True
        assert len(warnings_list) > 0
        assert any("primarily designed for US equities" in warning for warning in warnings_list)
    
    @pytest.mark.unit
    @patch('lib.pipeline_utils._PIPELINE_AVAILABLE', True)
    def test_validate_pipeline_equities_no_warning(self):
        """Test validation for equities asset class has no warnings."""
        params = {
            'strategy': {
                'use_pipeline': True,
                'asset_class': 'equities'
            }
        }
        
        is_valid, warnings_list = validate_pipeline_config(params)
        
        assert is_valid is True
        assert len(warnings_list) == 0













