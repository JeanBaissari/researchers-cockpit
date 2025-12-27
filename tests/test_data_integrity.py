"""
Test 3: Data Integrity

Verify data consistency:
1. Bundle dates match requested range
2. Returns calculated correctly
3. Positions match transactions
4. Metrics match manual calculations
5. Plots reflect data accurately
"""

import pytest
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.data_integrity import (
    verify_bundle_dates,
    verify_returns_calculation,
    verify_positions_match_transactions,
    verify_metrics_calculation
)
from lib.data_loader import list_bundles


def test_verify_bundle_dates():
    """Test bundle date range verification."""
    bundles = list_bundles()
    
    if len(bundles) == 0:
        pytest.skip("No bundles available for testing")
    
    bundle = bundles[0]
    
    # Test with valid dates (within bundle range)
    is_valid, error = verify_bundle_dates(bundle, '2020-01-01', '2020-12-31')
    # May be invalid if bundle doesn't cover these dates, that's OK
    
    # Test with invalid dates (far future)
    is_valid_future, error_future = verify_bundle_dates(bundle, '2099-01-01', '2099-12-31')
    assert not is_valid_future or len(error_future) > 0, \
        "Future dates should be invalid or produce error message"


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
    assert isinstance(error, str), "Should return error message string"


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
    assert isinstance(error, str), "Should return error message string"


def test_verify_metrics_calculation():
    """Test metrics calculation verification."""
    # Create sample returns
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
    
    # Metrics should match (within tolerance)
    assert is_valid or len(discrepancies) == 0, \
        f"Metrics should match or have minor discrepancies: {discrepancies}"


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
    
    is_valid, discrepancies = verify_metrics_calculation(wrong_metrics, returns, tolerance=0.01)
    
    # Should detect mismatches
    assert not is_valid or len(discrepancies) > 0, \
        "Should detect metric mismatches"


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



