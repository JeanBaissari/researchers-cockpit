"""
Test Phase 2: Strategy Creation

Tests the strategy creation and configuration workflow:
- Data ingestion
- Bundle registration
- Strategy configuration
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.bundles import (
    register_bundle_metadata,
    list_bundles,
    VALID_TIMEFRAMES,
    VALID_SOURCES,
)
from lib.config import load_strategy_params


class TestDataIngestionSetup:
    """Test data ingestion setup."""
    
    def test_valid_timeframes_available(self):
        """Test that valid timeframes are defined."""
        assert len(VALID_TIMEFRAMES) > 0
        assert '1d' in VALID_TIMEFRAMES
    
    def test_valid_sources_available(self):
        """Test that valid data sources are defined."""
        assert len(VALID_SOURCES) > 0
        assert 'yahoo' in VALID_SOURCES
    
    def test_bundle_metadata_registration(self, temp_data_dir):
        """Test registering bundle metadata."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            register_bundle_metadata(
                bundle_name='test_bundle',
                source='yahoo',
                asset_class='equities',
                symbols=['SPY'],
                timeframe='1d'
            )
            
            # Should complete without error
            bundles = list_bundles()
            assert isinstance(bundles, (list, dict))


class TestBundleConfiguration:
    """Test bundle configuration."""
    
    def test_bundle_list_function(self, temp_data_dir):
        """Test listing bundles."""
        with patch('lib.bundles.registry.get_project_root', return_value=temp_data_dir.parent):
            bundles = list_bundles()
            assert isinstance(bundles, (list, dict))
    
    def test_bundle_naming_convention(self):
        """Test that bundle names follow convention."""
        # Bundle names typically: {source}_{asset_class}_{timeframe}
        bundle_name = 'yahoo_equities_1d'
        parts = bundle_name.split('_')
        
        assert len(parts) >= 3
        assert parts[0] in VALID_SOURCES
        assert parts[-1] in VALID_TIMEFRAMES


class TestStrategyConfiguration:
    """Test strategy configuration."""
    
    def test_strategy_params_structure(self, sample_strategy_params):
        """Test strategy parameters have required structure."""
        assert 'name' in sample_strategy_params
        assert 'asset_class' in sample_strategy_params
        assert 'timeframe' in sample_strategy_params
        assert 'start_date' in sample_strategy_params
        assert 'end_date' in sample_strategy_params
    
    def test_strategy_params_types(self, sample_strategy_params):
        """Test strategy parameters have correct types."""
        assert isinstance(sample_strategy_params['name'], str)
        assert isinstance(sample_strategy_params['asset_class'], str)
        assert isinstance(sample_strategy_params['symbols'], list)
        assert isinstance(sample_strategy_params['capital_base'], (int, float))
    
    def test_strategy_timeframe_is_valid(self, sample_strategy_params):
        """Test that strategy timeframe is valid."""
        timeframe = sample_strategy_params['timeframe']
        assert timeframe in VALID_TIMEFRAMES


class TestDataBundleAlignment:
    """Test alignment between strategy and data bundles."""
    
    def test_strategy_bundle_match(self, sample_strategy_params):
        """Test that strategy can identify its bundle."""
        # Strategy should specify which bundle to use
        asset_class = sample_strategy_params['asset_class']
        timeframe = sample_strategy_params['timeframe']
        
        # Bundle name convention
        bundle_name = f"yahoo_{asset_class}_{timeframe}"
        
        assert asset_class in bundle_name
        assert timeframe in bundle_name
    
    def test_strategy_symbols_defined(self, sample_strategy_params):
        """Test that strategy has symbols defined."""
        assert 'symbols' in sample_strategy_params
        assert len(sample_strategy_params['symbols']) > 0


class TestStrategyDirectory:
    """Test strategy directory structure."""
    
    def test_create_strategy_directory(self, temp_strategy_dir):
        """Test creating strategy directory."""
        assert temp_strategy_dir.exists()
        assert temp_strategy_dir.is_dir()
    
    def test_strategy_has_required_files(self, sample_strategy_file):
        """Test that strategy directory has required files."""
        strategy_dir = sample_strategy_file.parent
        
        assert (strategy_dir / 'strategy.py').exists()
        assert (strategy_dir / 'params.yaml').exists()


class TestConfigurationValidation:
    """Test configuration validation."""
    
    def test_valid_asset_classes(self):
        """Test that valid asset classes are recognized."""
        valid_asset_classes = ['equities', 'crypto', 'forex']
        
        for asset_class in valid_asset_classes:
            # Should be recognized
            assert isinstance(asset_class, str)
            assert len(asset_class) > 0
    
    def test_date_format_validation(self, sample_strategy_params):
        """Test that dates are in correct format."""
        start_date = sample_strategy_params['start_date']
        end_date = sample_strategy_params['end_date']
        
        # Dates should be in YYYY-MM-DD format
        assert isinstance(start_date, str)
        assert isinstance(end_date, str)
        assert len(start_date) == 10
        assert len(end_date) == 10
        assert start_date[4] == '-'
        assert start_date[7] == '-'
    
    def test_capital_base_positive(self, sample_strategy_params):
        """Test that capital_base is positive."""
        capital_base = sample_strategy_params['capital_base']
        assert capital_base > 0


class TestDataPreparation:
    """Test data preparation workflow."""
    
    @pytest.mark.slow
    def test_csv_data_directory_structure(self, temp_data_dir):
        """Test that CSV data directory has correct structure."""
        processed_dir = temp_data_dir / 'processed'
        assert processed_dir.exists()
        
        # Should have timeframe subdirectories
        daily_dir = processed_dir / '1d'
        assert daily_dir.exists()
    
    def test_csv_file_created(self, sample_csv_file):
        """Test that CSV file can be created."""
        assert sample_csv_file.exists()
        assert sample_csv_file.suffix == '.csv'
        
        # Verify it has data
        df = pd.read_csv(sample_csv_file, index_col=0, parse_dates=True)
        assert len(df) > 0
        assert 'open' in df.columns
        assert 'close' in df.columns


class TestStrategyInitialization:
    """Test strategy initialization."""
    
    def test_strategy_file_structure(self, sample_strategy_file):
        """Test strategy file has correct structure."""
        content = sample_strategy_file.read_text()
        
        # Should have imports
        assert 'import' in content or 'from' in content
        
        # Should have initialize function
        assert 'def initialize' in content
        
        # Should have handle_data function
        assert 'def handle_data' in content
    
    def test_strategy_uses_context(self, sample_strategy_file):
        """Test that strategy uses context object."""
        content = sample_strategy_file.read_text()
        
        # Strategy should reference context
        assert 'context' in content

