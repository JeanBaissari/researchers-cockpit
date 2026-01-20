"""
Tests for lib.risk_management module.

Tests exit condition checking for fixed stop loss, trailing stop, and take profit.
"""

import sys
from pathlib import Path
from unittest.mock import Mock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.risk_management import (
    check_exit_conditions,
    get_exit_type_code,
    _check_take_profit,
    _check_trailing_stop,
    _check_fixed_stop
)


class TestTakeProfit:
    """Test take profit exit conditions."""
    
    @pytest.mark.unit
    def test_take_profit_triggered(self):
        """Test take profit is triggered when price exceeds target."""
        current_price = 110.0
        entry_price = 100.0
        risk_params = {
            'use_take_profit': True,
            'take_profit_pct': 0.10
        }
        
        result = _check_take_profit(current_price, entry_price, risk_params)
        assert result == 'take_profit'
    
    @pytest.mark.unit
    def test_take_profit_not_triggered(self):
        """Test take profit is not triggered when price below target."""
        current_price = 105.0
        entry_price = 100.0
        risk_params = {
            'use_take_profit': True,
            'take_profit_pct': 0.10  # Target: 110.0
        }
        
        result = _check_take_profit(current_price, entry_price, risk_params)
        assert result is None
    
    @pytest.mark.unit
    def test_take_profit_with_zero_entry_price(self):
        """Test take profit returns None with zero entry price."""
        current_price = 110.0
        entry_price = 0.0
        risk_params = {
            'use_take_profit': True,
            'take_profit_pct': 0.10
        }
        
        result = _check_take_profit(current_price, entry_price, risk_params)
        assert result is None
    
    @pytest.mark.unit
    def test_take_profit_with_invalid_percentage(self):
        """Test take profit handles invalid percentage gracefully."""
        current_price = 110.0
        entry_price = 100.0
        risk_params = {
            'use_take_profit': True,
            'take_profit_pct': -0.10  # Invalid
        }
        
        # Should use default and still work
        result = _check_take_profit(current_price, entry_price, risk_params)
        # With default 0.10, 110.0 >= 110.0, so should trigger
        assert result == 'take_profit'


class TestTrailingStop:
    """Test trailing stop exit conditions."""
    
    @pytest.mark.unit
    def test_trailing_stop_triggered(self):
        """Test trailing stop is triggered when price drops below stop."""
        current_price = 92.0
        highest_price = 100.0
        risk_params = {
            'use_trailing_stop': True,
            'trailing_stop_pct': 0.08  # Stop at 92.0
        }
        
        result = _check_trailing_stop(current_price, highest_price, risk_params)
        assert result == 'trailing'
    
    @pytest.mark.unit
    def test_trailing_stop_not_triggered(self):
        """Test trailing stop is not triggered when price above stop."""
        current_price = 95.0
        highest_price = 100.0
        risk_params = {
            'use_trailing_stop': True,
            'trailing_stop_pct': 0.08  # Stop at 92.0
        }
        
        result = _check_trailing_stop(current_price, highest_price, risk_params)
        assert result is None
    
    @pytest.mark.unit
    def test_trailing_stop_with_zero_highest_price(self):
        """Test trailing stop returns None with zero highest price."""
        current_price = 90.0
        highest_price = 0.0
        risk_params = {
            'use_trailing_stop': True,
            'trailing_stop_pct': 0.08
        }
        
        result = _check_trailing_stop(current_price, highest_price, risk_params)
        assert result is None


class TestFixedStop:
    """Test fixed stop loss exit conditions."""
    
    @pytest.mark.unit
    def test_fixed_stop_triggered(self):
        """Test fixed stop loss is triggered when price drops below stop."""
        current_price = 95.0
        entry_price = 100.0
        risk_params = {
            'use_stop_loss': True,
            'stop_loss_pct': 0.05  # Stop at 95.0
        }
        
        result = _check_fixed_stop(current_price, entry_price, risk_params)
        assert result == 'fixed'
    
    @pytest.mark.unit
    def test_fixed_stop_not_triggered(self):
        """Test fixed stop loss is not triggered when price above stop."""
        current_price = 96.0
        entry_price = 100.0
        risk_params = {
            'use_stop_loss': True,
            'stop_loss_pct': 0.05  # Stop at 95.0
        }
        
        result = _check_fixed_stop(current_price, entry_price, risk_params)
        assert result is None
    
    @pytest.mark.unit
    def test_fixed_stop_with_zero_entry_price(self):
        """Test fixed stop returns None with zero entry price."""
        current_price = 90.0
        entry_price = 0.0
        risk_params = {
            'use_stop_loss': True,
            'stop_loss_pct': 0.05
        }
        
        result = _check_fixed_stop(current_price, entry_price, risk_params)
        assert result is None


class TestCheckExitConditions:
    """Test main check_exit_conditions function."""
    
    @pytest.mark.unit
    def test_no_exit_when_not_in_position(self):
        """Test that no exit is returned when not in position."""
        context = Mock()
        context.in_position = False
        context.asset = Mock()
        context.entry_price = 100.0
        context.highest_price = 100.0
        
        data = Mock()
        risk_params = {'use_stop_loss': True}
        
        result = check_exit_conditions(context, data, risk_params)
        assert result is None
    
    @pytest.mark.unit
    def test_no_exit_when_cannot_trade(self):
        """Test that no exit is returned when asset cannot be traded."""
        context = Mock()
        context.in_position = True
        context.asset = Mock()
        context.entry_price = 100.0
        context.highest_price = 100.0
        
        data = Mock()
        data.can_trade.return_value = False
        risk_params = {'use_stop_loss': True}
        
        result = check_exit_conditions(context, data, risk_params)
        assert result is None
    
    @pytest.mark.unit
    def test_take_profit_priority(self):
        """Test that take profit has highest priority."""
        context = Mock()
        context.in_position = True
        context.asset = Mock()
        context.entry_price = 100.0
        context.highest_price = 100.0
        
        data = Mock()
        data.can_trade.return_value = True
        data.current.return_value = 110.0  # Triggers take profit
        
        risk_params = {
            'use_take_profit': True,
            'take_profit_pct': 0.10,
            'use_stop_loss': True,
            'stop_loss_pct': 0.05
        }
        
        result = check_exit_conditions(context, data, risk_params)
        assert result == 'take_profit'
    
    @pytest.mark.unit
    def test_trailing_stop_priority_over_fixed(self):
        """Test that trailing stop takes priority over fixed stop."""
        context = Mock()
        context.in_position = True
        context.asset = Mock()
        context.entry_price = 100.0
        context.highest_price = 105.0  # Price went up then down
        
        data = Mock()
        data.can_trade.return_value = True
        data.current.return_value = 96.0  # Below trailing stop (96.6) but above fixed (95.0)
        
        risk_params = {
            'use_trailing_stop': True,
            'trailing_stop_pct': 0.08,  # Stop at 96.6
            'use_stop_loss': True,
            'stop_loss_pct': 0.05  # Stop at 95.0
        }
        
        result = check_exit_conditions(context, data, risk_params)
        assert result == 'trailing'
    
    @pytest.mark.unit
    def test_highest_price_tracking(self):
        """Test that highest_price is updated correctly."""
        context = Mock()
        context.in_position = True
        context.asset = Mock()
        context.entry_price = 100.0
        context.highest_price = 100.0
        
        data = Mock()
        data.can_trade.return_value = True
        data.current.return_value = 105.0  # New high
        
        risk_params = {'use_take_profit': False}
        
        check_exit_conditions(context, data, risk_params)
        
        # highest_price should be updated
        assert context.highest_price == 105.0
    
    @pytest.mark.unit
    def test_highest_price_initialization(self):
        """Test that highest_price is initialized if zero."""
        context = Mock()
        context.in_position = True
        context.asset = Mock()
        context.entry_price = 100.0
        context.highest_price = 0.0  # Not initialized
        
        data = Mock()
        data.can_trade.return_value = True
        data.current.return_value = 102.0
        
        risk_params = {}
        
        check_exit_conditions(context, data, risk_params)
        
        # highest_price should be initialized
        assert context.highest_price == 102.0


class TestExitTypeCode:
    """Test exit type code conversion."""
    
    @pytest.mark.unit
    def test_exit_type_codes(self):
        """Test all exit type codes."""
        assert get_exit_type_code('fixed') == 1
        assert get_exit_type_code('trailing') == 2
        assert get_exit_type_code('take_profit') == 3
        assert get_exit_type_code(None) == 0
        assert get_exit_type_code('unknown') == 0













