"""
Tests for lib.position_sizing module.

Tests position sizing calculations for fixed, volatility-scaled, and Kelly methods.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.position_sizing import compute_position_size


class TestFixedPositionSizing:
    """Test fixed position sizing method."""
    
    @pytest.mark.unit
    def test_fixed_method_returns_max_position(self):
        """Test that fixed method returns max_position_pct."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'fixed',
                'max_position_pct': 0.95
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        assert result == 0.95
    
    @pytest.mark.unit
    def test_fixed_method_with_defaults(self):
        """Test fixed method with default max_position_pct."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'fixed'
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        assert result == 0.95  # Default value
    
    @pytest.mark.unit
    def test_fixed_method_validates_bounds(self):
        """Test that fixed method validates position bounds."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'fixed',
                'max_position_pct': 1.5  # Invalid: > 1.0
            }
        }
        data = Mock()
        
        with pytest.raises(ValueError, match="max_position_pct must be between 0.0 and 1.0"):
            compute_position_size(context, data, context.params)


class TestVolatilityScaledPositionSizing:
    """Test volatility-scaled position sizing method."""
    
    @pytest.mark.unit
    def test_volatility_scaled_with_sufficient_data(self):
        """Test volatility-scaled method with sufficient price history."""
        context = Mock()
        context.asset = Mock()
        context.params = {
            'strategy': {'asset_class': 'equities'},
            'position_sizing': {
                'method': 'volatility_scaled',
                'max_position_pct': 0.95,
                'min_position_pct': 0.10,
                'volatility_lookback': 20,
                'volatility_target': 0.15
            }
        }
        
        # Mock data with sufficient history
        data = Mock()
        data.can_trade.return_value = True
        
        # Create mock price history with known volatility
        prices = pd.Series([100 + i * 0.1 + np.random.randn() for i in range(21)])
        data.history.return_value = prices
        
        result = compute_position_size(context, data, context.params)
        
        # Result should be between min and max
        assert 0.10 <= result <= 0.95
        assert isinstance(result, float)
    
    @pytest.mark.unit
    def test_volatility_scaled_insufficient_data_fallback(self):
        """Test volatility-scaled method falls back to max_position with insufficient data."""
        context = Mock()
        context.asset = Mock()
        context.params = {
            'strategy': {'asset_class': 'equities'},
            'position_sizing': {
                'method': 'volatility_scaled',
                'max_position_pct': 0.95,
                'min_position_pct': 0.10
            }
        }
        
        data = Mock()
        data.can_trade.return_value = True
        data.history.return_value = pd.Series([100, 101])  # Insufficient data
        
        result = compute_position_size(context, data, context.params)
        assert result == 0.95  # Falls back to max_position
    
    @pytest.mark.unit
    def test_volatility_scaled_cannot_trade_fallback(self):
        """Test volatility-scaled method falls back when asset cannot be traded."""
        context = Mock()
        context.asset = Mock()
        context.params = {
            'position_sizing': {
                'method': 'volatility_scaled',
                'max_position_pct': 0.95
            }
        }
        
        data = Mock()
        data.can_trade.return_value = False
        
        result = compute_position_size(context, data, context.params)
        assert result == 0.95
    
    @pytest.mark.unit
    def test_volatility_scaled_different_asset_classes(self):
        """Test volatility-scaled method with different asset classes."""
        context = Mock()
        context.asset = Mock()
        data = Mock()
        data.can_trade.return_value = True
        
        # Create mock price history
        prices = pd.Series([100 + i * 0.1 for i in range(21)])
        data.history.return_value = prices
        
        for asset_class, expected_trading_days in [('equities', 252), ('forex', 260), ('crypto', 365)]:
            context.params = {
                'strategy': {'asset_class': asset_class},
                'position_sizing': {
                    'method': 'volatility_scaled',
                    'max_position_pct': 0.95,
                    'min_position_pct': 0.10,
                    'volatility_lookback': 20,
                    'volatility_target': 0.15
                }
            }
            
            result = compute_position_size(context, data, context.params)
            assert 0.10 <= result <= 0.95


class TestKellyPositionSizing:
    """Test Kelly Criterion position sizing method."""
    
    @pytest.mark.unit
    def test_kelly_method_calculation(self):
        """Test Kelly method calculates position size correctly."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'kelly',
                'max_position_pct': 0.95,
                'min_position_pct': 0.10,
                'kelly': {
                    'win_rate_estimate': 0.55,
                    'avg_win_loss_ratio': 1.5,
                    'kelly_fraction': 0.25
                }
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        
        # Kelly formula: f* = (bp - q) / b
        # b = 1.5, p = 0.55, q = 0.45
        # full_kelly = (1.5 * 0.55 - 0.45) / 1.5 = 0.25
        # fractional_kelly = 0.25 * 0.25 = 0.0625
        # Should be clamped to min_position_pct (0.10)
        assert result >= 0.10
        assert result <= 0.95
    
    @pytest.mark.unit
    def test_kelly_method_with_high_win_rate(self):
        """Test Kelly method with high win rate."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'kelly',
                'max_position_pct': 0.95,
                'min_position_pct': 0.10,
                'kelly': {
                    'win_rate_estimate': 0.70,
                    'avg_win_loss_ratio': 2.0,
                    'kelly_fraction': 0.25
                }
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        assert 0.10 <= result <= 0.95
    
    @pytest.mark.unit
    def test_kelly_method_with_defaults(self):
        """Test Kelly method with default parameters."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'kelly',
                'max_position_pct': 0.95,
                'min_position_pct': 0.10
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        assert 0.10 <= result <= 0.95


class TestPositionSizingEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.unit
    def test_unknown_method_fallback(self):
        """Test that unknown method falls back to fixed."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'unknown_method',
                'max_position_pct': 0.90
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        assert result == 0.90
    
    @pytest.mark.unit
    def test_missing_position_sizing_config(self):
        """Test with missing position_sizing config."""
        context = Mock()
        context.params = {}
        data = Mock()
        
        result = compute_position_size(context, data, context.params)
        assert result == 0.95  # Default fixed method
    
    @pytest.mark.unit
    def test_invalid_min_max_relationship(self):
        """Test validation of min_position > max_position."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'fixed',
                'max_position_pct': 0.50,
                'min_position_pct': 0.60  # Invalid: min > max
            }
        }
        data = Mock()
        
        with pytest.raises(ValueError, match="min_position_pct.*cannot be greater"):
            compute_position_size(context, data, context.params)
    
    @pytest.mark.unit
    def test_uses_context_params_if_params_none(self):
        """Test that function uses context.params if params is None."""
        context = Mock()
        context.params = {
            'position_sizing': {
                'method': 'fixed',
                'max_position_pct': 0.80
            }
        }
        data = Mock()
        
        result = compute_position_size(context, data, None)
        assert result == 0.80

