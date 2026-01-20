"""
Tests for data sanitization utilities.

Tests for:
- sanitize_value()
- sanitize_series()
- sanitize_for_json()
"""

# Standard library imports
import sys
import json
import math
from pathlib import Path

# Third-party imports
import pytest
import numpy as np
import pandas as pd

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.data.sanitization import (
    sanitize_value,
    sanitize_series,
    sanitize_for_json,
)


class TestSanitizeValue:
    """Tests for sanitize_value() function."""

    @pytest.mark.unit
    def test_sanitize_value_normal(self):
        """Test sanitize_value with normal numeric values."""
        assert sanitize_value(42.0) == 42.0
        assert sanitize_value(0.0) == 0.0
        assert sanitize_value(-100.5) == -100.5
        assert sanitize_value(1e10) == 1e10

    @pytest.mark.unit
    def test_sanitize_value_nan(self):
        """Test sanitize_value replaces NaN with default."""
        result = sanitize_value(float('nan'))
        assert result == 0.0
        assert not math.isnan(result)

    @pytest.mark.unit
    def test_sanitize_value_inf(self):
        """Test sanitize_value replaces Inf with default."""
        result = sanitize_value(float('inf'))
        assert result == 0.0
        assert not math.isinf(result)
        
        result = sanitize_value(float('-inf'))
        assert result == 0.0
        assert not math.isinf(result)

    @pytest.mark.unit
    def test_sanitize_value_none(self):
        """Test sanitize_value replaces None with default."""
        result = sanitize_value(None)
        assert result == 0.0

    @pytest.mark.unit
    def test_sanitize_value_custom_default(self):
        """Test sanitize_value with custom default value."""
        assert sanitize_value(float('nan'), default=999.0) == 999.0
        assert sanitize_value(float('inf'), default=-1.0) == -1.0
        assert sanitize_value(None, default=42.5) == 42.5

    @pytest.mark.unit
    def test_sanitize_value_int_conversion(self):
        """Test sanitize_value converts int to float."""
        result = sanitize_value(42)
        assert isinstance(result, float)
        assert result == 42.0


class TestSanitizeSeries:
    """Tests for sanitize_series() function."""

    @pytest.mark.unit
    def test_sanitize_series_normal(self):
        """Test sanitize_series with normal Series."""
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 5
        assert result.tolist() == [1.0, 2.0, 3.0, 4.0, 5.0]

    @pytest.mark.unit
    def test_sanitize_series_with_nan(self):
        """Test sanitize_series removes NaN values."""
        series = pd.Series([1.0, float('nan'), 3.0, float('nan'), 5.0])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.tolist() == [1.0, 3.0, 5.0]

    @pytest.mark.unit
    def test_sanitize_series_with_inf(self):
        """Test sanitize_series removes Inf values."""
        series = pd.Series([1.0, float('inf'), 3.0, float('-inf'), 5.0])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.tolist() == [1.0, 3.0, 5.0]

    @pytest.mark.unit
    def test_sanitize_series_with_nan_and_inf(self):
        """Test sanitize_series removes both NaN and Inf values."""
        series = pd.Series([1.0, float('nan'), float('inf'), 4.0, float('-inf'), 6.0])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.tolist() == [1.0, 4.0, 6.0]

    @pytest.mark.unit
    def test_sanitize_series_all_nan(self):
        """Test sanitize_series with all NaN values returns empty Series."""
        series = pd.Series([float('nan'), float('nan'), float('nan')])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    @pytest.mark.unit
    def test_sanitize_series_all_inf(self):
        """Test sanitize_series with all Inf values returns empty Series."""
        series = pd.Series([float('inf'), float('-inf'), float('inf')])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    @pytest.mark.unit
    def test_sanitize_series_none_raises(self):
        """Test sanitize_series raises ValueError for None."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_series(None)
        assert 'series cannot be none' in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_sanitize_series_wrong_type_raises(self):
        """Test sanitize_series raises ValueError for non-Series."""
        with pytest.raises(ValueError) as exc_info:
            sanitize_series([1, 2, 3])
        assert 'series must be a pandas series' in str(exc_info.value).lower()
        
        with pytest.raises(ValueError) as exc_info:
            sanitize_series({'a': 1, 'b': 2})
        assert 'series must be a pandas series' in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_sanitize_series_empty(self):
        """Test sanitize_series with empty Series."""
        series = pd.Series([])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 0

    @pytest.mark.unit
    def test_sanitize_series_preserves_index(self):
        """Test sanitize_series preserves index for remaining values."""
        series = pd.Series([1.0, float('nan'), 3.0], index=['a', 'b', 'c'])
        result = sanitize_series(series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 2
        assert 'a' in result.index
        assert 'c' in result.index
        assert 'b' not in result.index


class TestSanitizeForJson:
    """Tests for sanitize_for_json() function."""

    @pytest.mark.unit
    def test_sanitize_for_json_normal_dict(self):
        """Test sanitize_for_json with normal dictionary."""
        data = {'a': 1.0, 'b': 2.0, 'c': 3.0}
        result = sanitize_for_json(data)
        
        assert result == {'a': 1.0, 'b': 2.0, 'c': 3.0}
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_dict_with_nan(self):
        """Test sanitize_for_json replaces NaN in dictionary."""
        data = {'a': 1.0, 'b': float('nan'), 'c': 3.0}
        result = sanitize_for_json(data)
        
        assert result == {'a': 1.0, 'b': 0.0, 'c': 3.0}
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_dict_with_inf(self):
        """Test sanitize_for_json replaces Inf in dictionary."""
        data = {'a': 1.0, 'b': float('inf'), 'c': float('-inf')}
        result = sanitize_for_json(data)
        
        assert result == {'a': 1.0, 'b': 0.0, 'c': 0.0}
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_normal_list(self):
        """Test sanitize_for_json with normal list."""
        data = [1.0, 2.0, 3.0]
        result = sanitize_for_json(data)
        
        assert result == [1.0, 2.0, 3.0]
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_list_with_nan(self):
        """Test sanitize_for_json replaces NaN in list."""
        data = [1.0, float('nan'), 3.0]
        result = sanitize_for_json(data)
        
        assert result == [1.0, 0.0, 3.0]
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_nested_structure(self):
        """Test sanitize_for_json with nested dict/list structure."""
        data = {
            'level1': {
                'a': 1.0,
                'b': float('nan'),
                'nested_list': [2.0, float('inf'), 4.0]
            },
            'level2': [{'x': float('nan')}, {'y': 5.0}]
        }
        result = sanitize_for_json(data)
        
        assert result['level1']['a'] == 1.0
        assert result['level1']['b'] == 0.0
        assert result['level1']['nested_list'] == [2.0, 0.0, 4.0]
        assert result['level2'][0]['x'] == 0.0
        assert result['level2'][1]['y'] == 5.0
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_numpy_types(self):
        """Test sanitize_for_json handles numpy types."""
        data = {
            'float32': np.float32(42.5),
            'float64': np.float64(100.0),
            'int32': np.int32(10),
            'int64': np.int64(20),
            'nan': np.float64('nan'),
            'inf': np.float64('inf'),
        }
        result = sanitize_for_json(data)
        
        assert isinstance(result['float32'], float)
        assert isinstance(result['float64'], float)
        assert isinstance(result['int32'], int)
        assert isinstance(result['int64'], int)
        assert result['nan'] == 0.0
        assert result['inf'] == 0.0
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_preserves_other_types(self):
        """Test sanitize_for_json preserves non-numeric types."""
        data = {
            'string': 'hello',
            'int': 42,
            'bool': True,
            'none': None,
            'list': [1, 2, 3],
        }
        result = sanitize_for_json(data)
        
        assert result == data
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None

    @pytest.mark.unit
    def test_sanitize_for_json_complex_nested(self):
        """Test sanitize_for_json with complex nested structure."""
        data = {
            'metrics': {
                'returns': [1.0, float('nan'), 3.0],
                'sharpe': float('inf'),
                'drawdown': {
                    'max': -10.5,
                    'current': float('nan')
                }
            },
            'trades': [
                {'pnl': 100.0, 'fee': float('inf')},
                {'pnl': float('nan'), 'fee': 5.0}
            ]
        }
        result = sanitize_for_json(data)
        
        assert result['metrics']['returns'] == [1.0, 0.0, 3.0]
        assert result['metrics']['sharpe'] == 0.0
        assert result['metrics']['drawdown']['max'] == -10.5
        assert result['metrics']['drawdown']['current'] == 0.0
        assert result['trades'][0]['pnl'] == 100.0
        assert result['trades'][0]['fee'] == 0.0
        assert result['trades'][1]['pnl'] == 0.0
        assert result['trades'][1]['fee'] == 5.0
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert json_str is not None
