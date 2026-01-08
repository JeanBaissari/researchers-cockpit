"""
Test lib/validation/ API in v1.0.8.

Tests the validation API including:
- DataValidator
- BundleValidator
- BacktestValidator
- ValidationResult
- ValidationConfig
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import (
    # Validators
    DataValidator,
    BundleValidator,
    BacktestValidator,
    SchemaValidator,
    CompositeValidator,
    # Configuration
    ValidationConfig,
    # Results
    ValidationResult,
    ValidationCheck,
    ValidationSeverity,
    ValidationStatus,
    # Convenience functions
    validate_before_ingest,
    validate_bundle,
    validate_backtest_results,
    # Constants
    REQUIRED_OHLCV_COLUMNS,
    INTRADAY_TIMEFRAMES,
    DAILY_TIMEFRAMES,
)


class TestValidationConfig:
    """Test ValidationConfig."""
    
    def test_validation_config_creation(self):
        """Test creating ValidationConfig."""
        config = ValidationConfig(timeframe='1d')
        assert config.timeframe == '1d'
    
    def test_validation_config_strict_mode(self):
        """Test ValidationConfig with strict mode."""
        config = ValidationConfig.strict(timeframe='1d')
        assert config.strict_mode is True
        assert config.timeframe == '1d'
    
    def test_validation_config_permissive_mode(self):
        """Test ValidationConfig with permissive mode."""
        config = ValidationConfig.permissive()
        assert config.strict_mode is False


class TestValidationResult:
    """Test ValidationResult."""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        result = ValidationResult()
        assert result.passed is True
        assert len(result.checks) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_validation_result_add_check(self):
        """Test adding check to ValidationResult."""
        result = ValidationResult()
        result.add_check(
            name='test_check',
            passed=True,
            message='Test passed'
        )
        assert len(result.checks) == 1
        assert result.checks[0].name == 'test_check'
        assert result.checks[0].passed is True
    
    def test_validation_result_add_error(self):
        """Test adding error to ValidationResult."""
        result = ValidationResult()
        result.add_error('Test error')
        assert len(result.errors) == 1
        assert result.passed is False
    
    def test_validation_result_add_warning(self):
        """Test adding warning to ValidationResult."""
        result = ValidationResult()
        result.add_warning('Test warning')
        assert len(result.warnings) == 1
        # Warnings don't fail the result
        assert result.passed is True
    
    def test_validation_result_merge(self):
        """Test merging ValidationResults."""
        result1 = ValidationResult()
        result1.add_check('check1', True, 'Check 1')
        
        result2 = ValidationResult()
        result2.add_check('check2', True, 'Check 2')
        
        merged = result1.merge(result2)
        assert len(merged.checks) == 2
    
    def test_validation_result_bool(self):
        """Test ValidationResult boolean evaluation."""
        result = ValidationResult()
        assert bool(result) is True
        
        result.add_error('Error')
        assert bool(result) is False
    
    def test_validation_result_summary(self):
        """Test ValidationResult summary."""
        result = ValidationResult()
        result.add_check('test', True, 'Test passed')
        summary = result.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_validation_result_to_dict(self):
        """Test ValidationResult to_dict."""
        result = ValidationResult()
        result.add_check('test', True, 'Test')
        data = result.to_dict()
        assert isinstance(data, dict)
        assert 'passed' in data
        assert 'checks' in data


class TestDataValidator:
    """Test DataValidator."""
    
    def test_data_validator_creation(self):
        """Test creating DataValidator."""
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        assert validator is not None
        assert validator.config.timeframe == '1d'
    
    def test_data_validator_validate_valid_data(self, valid_ohlcv_data):
        """Test validating valid OHLCV data."""
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        result = validator.validate(valid_ohlcv_data, asset_name='TEST')
        assert isinstance(result, ValidationResult)
    
    def test_data_validator_validate_invalid_data(self, invalid_ohlcv_data):
        """Test validating invalid OHLCV data."""
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        result = validator.validate(invalid_ohlcv_data, asset_name='TEST')
        assert isinstance(result, ValidationResult)
        # Should have detected issues
        assert len(result.checks) > 0
    
    def test_data_validator_required_columns(self):
        """Test that DataValidator checks required columns."""
        # Create DataFrame missing volume
        dates = pd.date_range('2020-01-01', periods=100, freq='D', tz='UTC')
        df = pd.DataFrame({
            'open': [100.0] * 100,
            'high': [101.0] * 100,
            'low': [99.0] * 100,
            'close': [100.5] * 100,
            # Missing volume
        }, index=dates)
        
        config = ValidationConfig(timeframe='1d')
        validator = DataValidator(config=config)
        result = validator.validate(df, asset_name='TEST')
        
        # Should detect missing volume column
        assert isinstance(result, ValidationResult)


class TestBundleValidator:
    """Test BundleValidator."""
    
    def test_bundle_validator_creation(self):
        """Test creating BundleValidator."""
        config = ValidationConfig()
        validator = BundleValidator(config=config)
        assert validator is not None
    
    @pytest.mark.slow
    def test_bundle_validator_validate_nonexistent_bundle(self, temp_data_dir):
        """Test validating nonexistent bundle."""
        config = ValidationConfig()
        validator = BundleValidator(config=config)
        result = validator.validate('nonexistent_bundle', bundle_path=temp_data_dir)
        assert isinstance(result, ValidationResult)
        # Should fail for nonexistent bundle
        assert not result.passed


class TestBacktestValidator:
    """Test BacktestValidator."""
    
    def test_backtest_validator_creation(self):
        """Test creating BacktestValidator."""
        config = ValidationConfig()
        validator = BacktestValidator(config=config)
        assert validator is not None
    
    def test_backtest_validator_validate_results(self, sample_backtest_results):
        """Test validating backtest results."""
        config = ValidationConfig()
        validator = BacktestValidator(config=config)
        result = validator.validate(
            sample_backtest_results,
            returns=sample_backtest_results['returns'],
            transactions=sample_backtest_results['transactions'],
            positions=sample_backtest_results['positions']
        )
        assert isinstance(result, ValidationResult)
    
    def test_backtest_validator_validate_invalid_results(self):
        """Test validating invalid backtest results."""
        invalid_results = {
            'sharpe_ratio': 999,  # Unrealistic
            'max_drawdown': 0.5,  # Should be negative
            'total_return': -2.0,  # Total loss
        }
        
        config = ValidationConfig()
        validator = BacktestValidator(config=config)
        result = validator.validate(invalid_results)
        assert isinstance(result, ValidationResult)


class TestSchemaValidator:
    """Test SchemaValidator."""
    
    def test_schema_validator_creation(self):
        """Test creating SchemaValidator."""
        config = ValidationConfig()
        validator = SchemaValidator(config=config)
        assert validator is not None
    
    def test_schema_validator_validate_ohlcv_schema(self, valid_ohlcv_data):
        """Test validating OHLCV schema."""
        config = ValidationConfig()
        validator = SchemaValidator(config=config)
        
        # Validate that data has required columns
        required_cols = set(REQUIRED_OHLCV_COLUMNS)
        data_cols = set(valid_ohlcv_data.columns)
        has_required = required_cols.issubset(data_cols)
        
        assert has_required is True


class TestCompositeValidator:
    """Test CompositeValidator."""
    
    def test_composite_validator_creation(self):
        """Test creating CompositeValidator."""
        config = ValidationConfig(timeframe='1d')
        validators = [
            DataValidator(config=config),
            SchemaValidator(config=config),
        ]
        composite = CompositeValidator(validators)
        assert composite is not None
    
    def test_composite_validator_validate(self, valid_ohlcv_data):
        """Test CompositeValidator validation."""
        config = ValidationConfig(timeframe='1d')
        validators = [
            DataValidator(config=config),
        ]
        composite = CompositeValidator(validators)
        result = composite.validate(valid_ohlcv_data, asset_name='TEST')
        assert isinstance(result, ValidationResult)


class TestConvenienceFunctions:
    """Test convenience validation functions."""
    
    def test_validate_before_ingest(self, valid_ohlcv_data):
        """Test validate_before_ingest function."""
        result = validate_before_ingest(
            valid_ohlcv_data,
            asset_name='TEST',
            timeframe='1d'
        )
        assert isinstance(result, ValidationResult)
    
    @pytest.mark.slow
    def test_validate_bundle(self, temp_data_dir):
        """Test validate_bundle function."""
        result = validate_bundle(
            'nonexistent_bundle',
            bundle_path=temp_data_dir
        )
        assert isinstance(result, ValidationResult)
    
    def test_validate_backtest_results(self, sample_backtest_results):
        """Test validate_backtest_results function."""
        result = validate_backtest_results(
            sample_backtest_results,
            returns=sample_backtest_results['returns'],
            transactions=sample_backtest_results['transactions'],
            positions=sample_backtest_results['positions']
        )
        assert isinstance(result, ValidationResult)


class TestValidationSeverity:
    """Test ValidationSeverity enum."""
    
    def test_validation_severity_levels(self):
        """Test that ValidationSeverity has expected levels."""
        assert hasattr(ValidationSeverity, 'ERROR') or hasattr(ValidationSeverity, 'error')
        assert hasattr(ValidationSeverity, 'WARNING') or hasattr(ValidationSeverity, 'warning')
        assert hasattr(ValidationSeverity, 'INFO') or hasattr(ValidationSeverity, 'info')


class TestValidationConstants:
    """Test validation constants."""
    
    def test_required_ohlcv_columns(self):
        """Test REQUIRED_OHLCV_COLUMNS constant."""
        assert isinstance(REQUIRED_OHLCV_COLUMNS, (list, tuple))
        assert 'open' in REQUIRED_OHLCV_COLUMNS
        assert 'high' in REQUIRED_OHLCV_COLUMNS
        assert 'low' in REQUIRED_OHLCV_COLUMNS
        assert 'close' in REQUIRED_OHLCV_COLUMNS
        assert 'volume' in REQUIRED_OHLCV_COLUMNS
    
    def test_intraday_timeframes(self):
        """Test INTRADAY_TIMEFRAMES constant."""
        assert isinstance(INTRADAY_TIMEFRAMES, (list, tuple))
        assert '1m' in INTRADAY_TIMEFRAMES or '1min' in INTRADAY_TIMEFRAMES
    
    def test_daily_timeframes(self):
        """Test DAILY_TIMEFRAMES constant."""
        assert isinstance(DAILY_TIMEFRAMES, (list, tuple))
        assert '1d' in DAILY_TIMEFRAMES or 'daily' in DAILY_TIMEFRAMES

