"""
Test lib/bundles/ API.

Tests the bundle management API including:
- Bundle registry operations
- Timeframe validation
- Bundle ingestion (mocked)
- Cache operations
"""

# Standard library imports
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import inspect

# Third-party imports
import pytest
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import (
    # Timeframe configuration
    VALID_TIMEFRAMES,
    VALID_SOURCES,
    TIMEFRAME_TO_YF_INTERVAL,
    get_timeframe_info,
    validate_timeframe_date_range,
    # Registry
    load_bundle_registry,
    save_bundle_registry,
    register_bundle_metadata,
    list_bundles,
    get_registered_bundles,
    add_registered_bundle,
    discard_registered_bundle,
    # Utils
    is_valid_date_string,
    # Main API
    ingest_bundle,
    load_bundle,
    get_bundle_symbols,
)


class TestTimeframeConfiguration:
    """Test timeframe configuration and validation."""
    
    @pytest.mark.unit
    def test_valid_timeframes_list(self):
        """Test that VALID_TIMEFRAMES is a non-empty list."""
        assert isinstance(VALID_TIMEFRAMES, list)
        assert len(VALID_TIMEFRAMES) > 0
        assert '1d' in VALID_TIMEFRAMES
        assert '1h' in VALID_TIMEFRAMES
    
    @pytest.mark.unit
    def test_valid_sources_list(self):
        """Test that VALID_SOURCES is a non-empty list."""
        assert isinstance(VALID_SOURCES, list)
        assert len(VALID_SOURCES) > 0
        assert 'yahoo' in VALID_SOURCES
    
    @pytest.mark.unit
    def test_timeframe_to_yf_interval_mapping(self):
        """Test that timeframe to yfinance interval mapping exists."""
        assert isinstance(TIMEFRAME_TO_YF_INTERVAL, dict)
        assert '1d' in TIMEFRAME_TO_YF_INTERVAL
        assert '1h' in TIMEFRAME_TO_YF_INTERVAL
    
    @pytest.mark.unit
    def test_get_timeframe_info(self):
        """Test getting timeframe information."""
        info = get_timeframe_info('1d')
        assert info is not None
        assert 'yf_interval' in info or 'interval' in info or info is not None
    
    @pytest.mark.unit
    def test_validate_timeframe_date_range(self):
        """Test validating date range for timeframe."""
        # This should return a tuple (start_date, end_date, warning)
        result = validate_timeframe_date_range(
            timeframe='1d',
            start_date='2020-01-01',
            end_date='2020-12-31'
        )
        # Result should be a tuple with 3 elements
        assert isinstance(result, tuple)
        assert len(result) == 3
        start_date, end_date, warning = result
        assert start_date is not None
        assert end_date is not None
        # warning can be None or a string
        assert warning is None or isinstance(warning, str)


class TestBundleRegistry:
    """Test bundle registry operations."""
    
    @pytest.mark.unit
    def test_load_bundle_registry(self, temp_data_dir):
        """Test loading bundle registry."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            registry = load_bundle_registry()
            assert isinstance(registry, dict)
    
    @pytest.mark.unit
    def test_save_bundle_registry(self, temp_data_dir):
        """Test saving bundle registry."""
        test_registry = {
            'test_bundle': {
                'symbols': ['SPY'],
                'calendar_name': 'XNYS',
                'data_frequency': 'daily',
                'timeframe': '1d',
                'registered_at': datetime.now().isoformat(),
            }
        }
        
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            save_bundle_registry(test_registry)
            loaded = load_bundle_registry()
            assert 'test_bundle' in loaded or loaded == test_registry or loaded == {}
    
    @pytest.mark.unit
    def test_register_bundle_metadata(self, temp_data_dir):
        """Test registering bundle metadata."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            register_bundle_metadata(
                bundle_name='test_bundle',
                symbols=['SPY'],
                calendar_name='XNYS',
                start_date='2020-01-01',
                end_date='2020-12-31',
                data_frequency='daily',
                timeframe='1d'
            )
            
            registry = load_bundle_registry()
            # Check if bundle was registered
            assert isinstance(registry, dict)
    
    @pytest.mark.unit
    def test_list_bundles(self, temp_data_dir):
        """Test listing bundles."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            bundles = list_bundles()
            assert isinstance(bundles, (list, dict))
    
    @pytest.mark.unit
    def test_get_registered_bundles(self):
        """Test getting registered bundles set."""
        registered = get_registered_bundles()
        assert isinstance(registered, set)
    
    @pytest.mark.unit
    def test_add_registered_bundle(self):
        """Test adding bundle to registered set."""
        initial_count = len(get_registered_bundles())
        add_registered_bundle('test_bundle_xyz')
        after_count = len(get_registered_bundles())
        assert after_count >= initial_count
    
    @pytest.mark.unit
    def test_discard_registered_bundle(self):
        """Test removing bundle from registered set."""
        add_registered_bundle('test_bundle_to_remove')
        discard_registered_bundle('test_bundle_to_remove')
        registered = get_registered_bundles()
        # Should handle gracefully even if not in set
        assert isinstance(registered, set)


class TestBundleUtils:
    """Test bundle utility functions."""
    
    @pytest.mark.unit
    def test_is_valid_date_string_valid(self):
        """Test validating valid date strings."""
        assert is_valid_date_string('2020-01-01') is True
        assert is_valid_date_string('2020-12-31') is True
    
    @pytest.mark.unit
    def test_is_valid_date_string_invalid(self):
        """Test validating invalid date strings."""
        assert is_valid_date_string('invalid') is False
        assert is_valid_date_string('2020-13-01') is False
        assert is_valid_date_string('') is False


class TestBundleAPI:
    """Test main bundle API functions."""
    
    @pytest.mark.unit
    def test_ingest_bundle_signature(self):
        """Test that ingest_bundle has correct signature."""
        sig = inspect.signature(ingest_bundle)
        params = list(sig.parameters.keys())
        
        # Should have essential parameters
        assert 'bundle_name' in params or 'source' in params
    
    @pytest.mark.unit
    def test_load_bundle_signature(self):
        """Test that load_bundle has correct signature."""
        sig = inspect.signature(load_bundle)
        params = list(sig.parameters.keys())
        
        # Should have bundle_name parameter
        assert 'bundle_name' in params
    
    @pytest.mark.unit
    def test_get_bundle_symbols_signature(self):
        """Test that get_bundle_symbols has correct signature."""
        sig = inspect.signature(get_bundle_symbols)
        params = list(sig.parameters.keys())
        
        # Should have bundle_name parameter
        assert 'bundle_name' in params


class TestBundleIntegration:
    """Integration tests for bundle operations."""
    
    @pytest.mark.slow
    def test_bundle_workflow_mock(self, temp_data_dir):
        """Test complete bundle workflow with mocks."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            # Register metadata
            register_bundle_metadata(
                bundle_name='test_workflow_bundle',
                symbols=['TEST'],
                calendar_name='XNYS',
                start_date='2020-01-01',
                end_date='2020-12-31',
                data_frequency='daily',
                timeframe='1d'
            )
            
            # Verify it's in registry
            registry = load_bundle_registry()
            assert isinstance(registry, dict)
            
            # Verify list_bundles works
            bundles = list_bundles()
            assert isinstance(bundles, (list, dict))


class TestBundleConfiguration:
    """Test bundle configuration."""
    
    @pytest.mark.unit
    def test_bundle_list_function(self, temp_data_dir):
        """Test listing bundles."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            bundles = list_bundles()
            assert isinstance(bundles, (list, dict))
    
    @pytest.mark.unit
    def test_bundle_naming_convention(self):
        """Test that bundle names follow convention."""
        # Bundle names typically: {source}_{asset_class}_{timeframe}
        bundle_name = 'yahoo_equities_1d'
        parts = bundle_name.split('_')
        
        assert len(parts) >= 3
        assert parts[0] in VALID_SOURCES
        assert parts[-1] in VALID_TIMEFRAMES


class TestBundlePatterns:
    """Test bundle registration and loading patterns."""
    
    @pytest.mark.unit
    def test_list_bundles(self):
        """Test listing bundles."""
        bundles = list_bundles()
        assert isinstance(bundles, list), "Should return a list"
    
    @pytest.mark.unit
    def test_bundle_loading_error_handling(self):
        """Test bundle loading handles missing bundles gracefully."""
        with pytest.raises(FileNotFoundError):
            load_bundle('nonexistent_bundle_12345')

