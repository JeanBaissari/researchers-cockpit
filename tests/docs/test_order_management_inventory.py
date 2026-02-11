"""
Tests to verify Zipline-Reloaded order management APIs documented in inventory.

This test suite verifies that all order management APIs documented in
tasks/ralphy/research/zipline_api_inventory.md are available and function correctly.
"""

import pytest
from zipline.api import (
    order,
    order_target,
    order_target_percent,
    order_target_value,
    order_percent,
    order_value,
    get_open_orders,
    cancel_order,
    get_order,
    set_cancel_policy,
    EODCancel,
    NeverCancel,
    set_max_order_size,
    set_max_position_size,
    set_max_order_count,
    set_max_leverage,
    set_long_only,
    set_do_not_order_list,
)
from zipline.finance.execution import (
    MarketOrder,
    LimitOrder,
    StopOrder,
    StopLimitOrder,
)


class TestOrderAPIImports:
    """Verify all order API functions can be imported."""

    def test_basic_order_functions_importable(self):
        """Test basic order functions are importable."""
        assert callable(order)
        assert callable(order_target)
        assert callable(order_target_percent)
        assert callable(order_target_value)
        assert callable(order_percent)
        assert callable(order_value)

    def test_order_management_functions_importable(self):
        """Test order management functions are importable."""
        assert callable(get_open_orders)
        assert callable(cancel_order)
        assert callable(get_order)

    def test_execution_styles_importable(self):
        """Test execution style classes are importable."""
        assert MarketOrder is not None
        assert LimitOrder is not None
        assert StopOrder is not None
        assert StopLimitOrder is not None

    def test_cancel_policies_importable(self):
        """Test cancellation policy classes are importable."""
        assert callable(set_cancel_policy)
        assert callable(EODCancel)
        assert callable(NeverCancel)

    def test_trading_controls_importable(self):
        """Test trading control functions are importable."""
        assert callable(set_max_order_size)
        assert callable(set_max_position_size)
        assert callable(set_max_order_count)
        assert callable(set_max_leverage)
        assert callable(set_long_only)
        assert callable(set_do_not_order_list)


class TestExecutionStyles:
    """Verify execution style classes work correctly."""

    def test_market_order_creation(self):
        """Test MarketOrder can be instantiated."""
        market_order = MarketOrder()
        assert market_order is not None

    def test_limit_order_creation(self):
        """Test LimitOrder can be instantiated with limit price."""
        limit_order = LimitOrder(limit_price=100.0)
        assert limit_order is not None
        assert limit_order.get_limit_price(is_buy=True) == 100.0

    def test_stop_order_creation(self):
        """Test StopOrder can be instantiated with stop price."""
        stop_order = StopOrder(stop_price=90.0)
        assert stop_order is not None
        assert stop_order.get_stop_price(is_buy=False) == 90.0

    def test_stop_limit_order_creation(self):
        """Test StopLimitOrder can be instantiated with both prices."""
        stop_limit = StopLimitOrder(limit_price=89.0, stop_price=90.0)
        assert stop_limit is not None
        assert stop_limit.get_limit_price(is_buy=True) == 89.0
        assert stop_limit.get_stop_price(is_buy=False) == 90.0


class TestCancelPolicies:
    """Verify cancellation policy classes work correctly."""

    def test_eod_cancel_creation(self):
        """Test EODCancel can be instantiated."""
        policy = EODCancel(warn_on_cancel=True)
        assert policy is not None

    def test_never_cancel_creation(self):
        """Test NeverCancel can be instantiated."""
        policy = NeverCancel()
        assert policy is not None


class TestOrderAPISignatures:
    """Verify order API function signatures match documentation."""

    def test_order_signature(self):
        """Verify order() function exists and is callable."""
        # order(asset, amount, limit_price=None, stop_price=None, style=None)
        assert callable(order)
        # Check it accepts at least 2 positional args
        import inspect

        sig = inspect.signature(order)
        params = list(sig.parameters.keys())
        # Should have at least 'asset' and 'amount' parameters
        assert len(params) >= 2

    def test_order_target_signature(self):
        """Verify order_target() function signature."""
        assert callable(order_target)
        import inspect

        sig = inspect.signature(order_target)
        params = list(sig.parameters.keys())
        assert len(params) >= 2  # asset and target at minimum

    def test_order_target_percent_signature(self):
        """Verify order_target_percent() function signature."""
        assert callable(order_target_percent)
        import inspect

        sig = inspect.signature(order_target_percent)
        params = list(sig.parameters.keys())
        assert len(params) >= 2  # asset and target at minimum

    def test_get_open_orders_signature(self):
        """Verify get_open_orders() function signature."""
        assert callable(get_open_orders)
        import inspect

        sig = inspect.signature(get_open_orders)
        params = list(sig.parameters.keys())
        # Should accept optional asset parameter
        assert "asset" in params or len(params) == 0

    def test_cancel_order_signature(self):
        """Verify cancel_order() function signature."""
        assert callable(cancel_order)
        import inspect

        sig = inspect.signature(cancel_order)
        params = list(sig.parameters.keys())
        assert len(params) >= 1  # Should accept order parameter


class TestTradingControls:
    """Verify trading control functions are available."""

    def test_set_max_order_size_signature(self):
        """Verify set_max_order_size() function signature."""
        assert callable(set_max_order_size)
        import inspect

        sig = inspect.signature(set_max_order_size)
        params = list(sig.parameters.keys())
        # Should have asset, max_shares, max_notional, on_error parameters
        assert len(params) >= 1

    def test_set_max_position_size_signature(self):
        """Verify set_max_position_size() function signature."""
        assert callable(set_max_position_size)

    def test_set_max_order_count_signature(self):
        """Verify set_max_order_count() function signature."""
        assert callable(set_max_order_count)

    def test_set_max_leverage_signature(self):
        """Verify set_max_leverage() function signature."""
        assert callable(set_max_leverage)

    def test_set_long_only_signature(self):
        """Verify set_long_only() function signature."""
        assert callable(set_long_only)

    def test_set_do_not_order_list_signature(self):
        """Verify set_do_not_order_list() function signature."""
        assert callable(set_do_not_order_list)


class TestOrderManagementDocumentation:
    """Verify order management APIs match inventory documentation."""

    def test_all_documented_apis_importable(self):
        """Verify all APIs mentioned in inventory are importable."""
        # This test ensures the inventory documentation is accurate
        documented_apis = [
            "order",
            "order_target",
            "order_target_percent",
            "order_target_value",
            "order_percent",
            "order_value",
            "get_open_orders",
            "cancel_order",
            "get_order",
            "set_cancel_policy",
            "EODCancel",
            "NeverCancel",
            "set_max_order_size",
            "set_max_position_size",
            "set_max_order_count",
            "set_max_leverage",
            "set_long_only",
            "set_do_not_order_list",
        ]

        from zipline.api import __all__ as api_all

        for api_name in documented_apis:
            assert api_name in api_all or api_name in globals(), (
                f"Documented API '{api_name}' is not available"
            )

    def test_all_execution_styles_documented(self):
        """Verify all execution styles are documented and importable."""
        documented_styles = [
            "MarketOrder",
            "LimitOrder",
            "StopOrder",
            "StopLimitOrder",
        ]

        for style_name in documented_styles:
            style_class = globals().get(style_name)
            assert style_class is not None, (
                f"Documented execution style '{style_name}' is not available"
            )
            assert callable(style_class) or hasattr(style_class, "__call__"), (
                f"Execution style '{style_name}' is not callable/instantiable"
            )
