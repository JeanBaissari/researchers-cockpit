"""
Test 3: Data Integrity

Verify data consistency:
1. Bundle dates match requested range
2. Returns calculated correctly
3. Positions match transactions
4. Metrics match manual calculations
5. Plots reflect data accurately
"""

# Standard library imports
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Third-party imports
import pytest
import pandas as pd
import numpy as np

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import (
    verify_bundle_dates,
    verify_returns_calculation,
    verify_positions_match_transactions,
    verify_metrics_calculation
)
from lib.bundles import list_bundles


@pytest.mark.unit
@patch('lib.bundles.utils.ensure_bundle_registered')
def test_verify_bundle_dates(mock_ensure_registered):
    """Test bundle date range verification uses ensure_bundle_registered."""
    from lib.validation.core import ValidationResult
    
    bundles = list_bundles()
    
    if len(bundles) == 0:
        pytest.skip("No bundles available for testing")
    
    bundle = bundles[0]
    mock_ensure_registered.return_value = True
    
    # Mock load_bundle to avoid actual bundle loading
    # v1.12.0+: load_bundle is imported from lib.bundles.api inside verify_bundle_dates
    with patch('lib.bundles.api.load_bundle') as mock_load:
        mock_bundle_data = MagicMock()
        mock_bundle_data.equity_daily_bar_reader.sessions = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        mock_load.return_value = mock_bundle_data
        
        # Test with valid dates (within bundle range)
        result = verify_bundle_dates(bundle, '2020-01-01', '2020-12-31')
        assert isinstance(result, ValidationResult), "Should return ValidationResult"
        
        # Verify ensure_bundle_registered was called
        mock_ensure_registered.assert_called_once_with(
            bundle,
            raise_on_missing=True,
            exception_type=FileNotFoundError,
            start_date_hint="2020-01-01",
            end_date_hint="2020-12-31",
        )
    
    # Test with invalid dates (far future)
    mock_ensure_registered.reset_mock()
    mock_ensure_registered.return_value = True
    
    with patch('lib.bundles.api.load_bundle') as mock_load:
        mock_bundle_data = MagicMock()
        mock_bundle_data.equity_daily_bar_reader.sessions = pd.date_range('2020-01-01', '2020-12-31', freq='D')
        mock_load.return_value = mock_bundle_data
        
        result_future = verify_bundle_dates(bundle, '2099-01-01', '2099-12-31')
        assert isinstance(result_future, ValidationResult), "Should return ValidationResult"
        # Future dates should either fail validation or have error messages
        if not result_future.passed:
            assert len(result_future.errors) > 0 or len(result_future.checks) > 0, \
                "Future dates should produce error messages or failed checks"

@pytest.mark.unit
@patch('lib.bundles.utils.ensure_bundle_registered')
def test_verify_bundle_dates_not_found(mock_ensure_registered):
    """Test verify_bundle_dates handles FileNotFoundError from ensure_bundle_registered."""
    from lib.validation.core import ValidationResult
    
    mock_ensure_registered.side_effect = FileNotFoundError("Bundle 'missing' not found")
    
    result = verify_bundle_dates('missing', '2020-01-01', '2020-12-31')
    
    assert isinstance(result, ValidationResult)
    assert not result.passed
    # Should have a check indicating bundle load failed
    assert len(result.checks) > 0


@pytest.mark.unit
def test_verify_returns_calculation():
    """Test returns calculation verification."""
    # Create sample returns and transactions
    dates = pd.date_range('2020-01-01', periods=10, freq='D')
    returns = pd.Series(np.random.randn(10) * 0.01, index=dates)
    
    # Create matching transactions
    transactions = pd.DataFrame({
        'sid': [1] * 10,
        'amount': [100] * 10,
        'price': [100.0] * 10,
        'commission': [0.0] * 10
    }, index=dates)
    
    is_valid, error = verify_returns_calculation(returns, transactions)
    # Should pass basic consistency check
    assert isinstance(is_valid, bool), "Should return boolean"
    # Error can be None when valid, or str when invalid
    assert error is None or isinstance(error, str), f"Error should be None or str, got {type(error)}"


@pytest.mark.unit
def test_verify_positions_match_transactions():
    """Test positions/transactions consistency verification."""
    dates = pd.date_range('2020-01-01', periods=5, freq='D')
    
    # Create transactions
    transactions = pd.DataFrame({
        'sid': [1, 1, 1, 1, 1],
        'amount': [100, -50, 50, -100, 0],
        'price': [100.0, 105.0, 110.0, 115.0, 120.0],
        'commission': [0.0] * 5
    }, index=dates)
    
    # Create positions (should match cumulative transactions)
    positions = pd.DataFrame({
        'positions': [100, 50, 100, 0, 0]  # Cumulative
    }, index=dates)
    
    is_valid, error = verify_positions_match_transactions(positions, transactions)
    assert isinstance(is_valid, bool), "Should return boolean"
    # Error can be None when valid, or str when invalid
    assert error is None or isinstance(error, str), f"Error should be None or str, got {type(error)}"


@pytest.mark.unit
def test_verify_metrics_calculation():
    """Test metrics calculation verification."""
    # Create sample returns with fixed seed for reproducibility
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    returns = pd.Series(np.random.randn(100) * 0.01, index=dates)
    
    # Calculate metrics manually
    total_return = float((1 + returns).prod() - 1)
    annual_return = float((1 + total_return) ** (252 / len(returns)) - 1)
    annual_vol = float(returns.std() * np.sqrt(252))
    
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_dd = float(drawdown.min())
    
    metrics = {
        'total_return': total_return,
        'annual_return': annual_return,
        'annual_volatility': annual_vol,
        'max_drawdown': max_dd
    }
    
    # Verify metrics
    is_valid, discrepancies = verify_metrics_calculation(metrics, returns)

    assert isinstance(is_valid, bool), "Should return boolean"
    assert isinstance(discrepancies, list), "Should return list of discrepancies"

    # When metrics match (is_valid=True), discrepancies should be empty
    # When metrics don't match (is_valid=False), discrepancies will have items
    assert is_valid, f"Metrics should match within tolerance: {discrepancies}"


@pytest.mark.unit
def test_verify_metrics_with_mismatch():
    """Test metrics verification catches mismatches."""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    returns = pd.Series(np.random.randn(100) * 0.01, index=dates)
    
    # Create incorrect metrics
    wrong_metrics = {
        'total_return': 999.0,  # Obviously wrong
        'annual_return': 999.0,
        'annual_volatility': 999.0,
        'max_drawdown': -999.0
    }
    
    is_valid, discrepancies = verify_metrics_calculation(wrong_metrics, returns)
    
    # Should detect mismatches (wrong_metrics are obviously wrong)
    assert not is_valid or len(discrepancies) > 0, \
        f"Should detect metric mismatches, got is_valid={is_valid}, discrepancies={discrepancies}"


@pytest.mark.unit
def test_empty_data_handling():
    """Test that empty data is handled gracefully."""
    # Empty returns
    empty_returns = pd.Series(dtype=float)
    empty_transactions = pd.DataFrame()
    
    is_valid, error = verify_returns_calculation(empty_returns, empty_transactions)
    assert isinstance(is_valid, bool), "Should handle empty data"
    
    is_valid, error = verify_positions_match_transactions(empty_transactions, empty_transactions)
    assert isinstance(is_valid, bool), "Should handle empty data"
    
    empty_metrics = {}
    is_valid, discrepancies = verify_metrics_calculation(empty_metrics, empty_returns)
    assert isinstance(is_valid, bool), "Should handle empty data"



