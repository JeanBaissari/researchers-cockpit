"""
Unit tests for ValidationResult property mappings.

Tests verify correct behavior of:
- passed property
- error_checks property
- warning_checks property
"""

# Standard library imports
import sys
from pathlib import Path
from datetime import datetime

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.validation import (
    ValidationResult,
    ValidationCheck,
    ValidationSeverity
)


class TestValidationResultPassedProperty:
    """Test the 'passed' property of ValidationResult."""
    
    @pytest.mark.unit
    def test_passed_defaults_to_true(self):
        """Test that ValidationResult defaults to passed=True."""
        result = ValidationResult()
        assert result.passed is True, "ValidationResult should default to passed=True"
    
    @pytest.mark.unit
    def test_passed_remains_true_with_passed_checks(self):
        """Test that passed remains True when only passing checks are added."""
        result = ValidationResult()
        result.add_check('check1', True, 'All good')
        result.add_check('check2', True, 'Still good')
        assert result.passed is True, "Should remain True with only passing checks"
    
    @pytest.mark.unit
    def test_passed_becomes_false_with_error_check(self):
        """Test that passed becomes False when an error check fails."""
        result = ValidationResult()
        result.add_check('check1', True, 'All good')
        result.add_check('check2', False, 'Error occurred', severity=ValidationSeverity.ERROR)
        assert result.passed is False, "Should become False when error check fails"
    
    @pytest.mark.unit
    def test_passed_remains_true_with_warning_check(self):
        """Test that passed remains True when only warning checks fail."""
        result = ValidationResult()
        result.add_check('check1', True, 'All good')
        result.add_check('check2', False, 'Warning occurred', severity=ValidationSeverity.WARNING)
        assert result.passed is True, "Should remain True when only warning checks fail"
    
    @pytest.mark.unit
    def test_passed_remains_true_with_info_check(self):
        """Test that passed remains True when only info checks fail."""
        result = ValidationResult()
        result.add_check('check1', True, 'All good')
        result.add_check('check2', False, 'Info message', severity=ValidationSeverity.INFO)
        assert result.passed is True, "Should remain True when only info checks fail"
    
    @pytest.mark.unit
    def test_passed_with_add_error(self):
        """Test that add_error() sets passed to False."""
        result = ValidationResult()
        result.add_error('Something went wrong')
        assert result.passed is False, "add_error() should set passed to False"
    
    @pytest.mark.unit
    def test_passed_with_add_warning(self):
        """Test that add_warning() does not affect passed."""
        result = ValidationResult()
        result.add_warning('Minor issue')
        assert result.passed is True, "add_warning() should not affect passed"
    
    @pytest.mark.unit
    def test_passed_with_mixed_checks(self):
        """Test passed property with mixed check results."""
        result = ValidationResult()
        result.add_check('check1', True, 'Passed')
        result.add_check('check2', False, 'Warning', severity=ValidationSeverity.WARNING)
        result.add_check('check3', False, 'Error', severity=ValidationSeverity.ERROR)
        assert result.passed is False, "Should be False when any error check fails"
    
    @pytest.mark.unit
    def test_passed_after_merge(self):
        """Test that passed property is correctly updated after merge."""
        result1 = ValidationResult()
        result1.add_check('check1', True, 'Passed')
        
        result2 = ValidationResult()
        result2.add_check('check2', False, 'Error', severity=ValidationSeverity.ERROR)
        
        result1.merge(result2)
        assert result1.passed is False, "Merged result should be False if any merged result has errors"


class TestValidationResultErrorChecksProperty:
    """Test the 'error_checks' property of ValidationResult."""
    
    @pytest.mark.unit
    def test_error_checks_empty_by_default(self):
        """Test that error_checks is empty for new ValidationResult."""
        result = ValidationResult()
        assert len(result.error_checks) == 0, "error_checks should be empty by default"
    
    @pytest.mark.unit
    def test_error_checks_includes_failed_error_severity(self):
        """Test that error_checks includes failed checks with ERROR severity."""
        result = ValidationResult()
        result.add_check('error_check', False, 'Error message', severity=ValidationSeverity.ERROR)
        assert len(result.error_checks) == 1, "Should have one error check"
        assert result.error_checks[0].name == 'error_check', "Error check should have correct name"
        assert result.error_checks[0].severity == ValidationSeverity.ERROR, "Should have ERROR severity"
        assert result.error_checks[0].passed is False, "Should be a failed check"
    
    @pytest.mark.unit
    def test_error_checks_excludes_passed_checks(self):
        """Test that error_checks excludes passed checks even with ERROR severity."""
        result = ValidationResult()
        result.add_check('passed_check', True, 'Passed', severity=ValidationSeverity.ERROR)
        assert len(result.error_checks) == 0, "Should not include passed checks"
    
    @pytest.mark.unit
    def test_error_checks_excludes_warning_checks(self):
        """Test that error_checks excludes failed checks with WARNING severity."""
        result = ValidationResult()
        result.add_check('warning_check', False, 'Warning', severity=ValidationSeverity.WARNING)
        assert len(result.error_checks) == 0, "Should not include warning checks"
    
    @pytest.mark.unit
    def test_error_checks_excludes_info_checks(self):
        """Test that error_checks excludes failed checks with INFO severity."""
        result = ValidationResult()
        result.add_check('info_check', False, 'Info', severity=ValidationSeverity.INFO)
        assert len(result.error_checks) == 0, "Should not include info checks"
    
    @pytest.mark.unit
    def test_error_checks_multiple_errors(self):
        """Test error_checks with multiple error checks."""
        result = ValidationResult()
        result.add_check('error1', False, 'Error 1', severity=ValidationSeverity.ERROR)
        result.add_check('error2', False, 'Error 2', severity=ValidationSeverity.ERROR)
        result.add_check('error3', False, 'Error 3', severity=ValidationSeverity.ERROR)
        assert len(result.error_checks) == 3, "Should include all error checks"
        assert all(c.severity == ValidationSeverity.ERROR for c in result.error_checks), \
            "All checks should have ERROR severity"
        assert all(not c.passed for c in result.error_checks), \
            "All checks should be failed"
    
    @pytest.mark.unit
    def test_error_checks_mixed_severities(self):
        """Test error_checks with mixed check severities."""
        result = ValidationResult()
        result.add_check('error1', False, 'Error', severity=ValidationSeverity.ERROR)
        result.add_check('warning1', False, 'Warning', severity=ValidationSeverity.WARNING)
        result.add_check('info1', False, 'Info', severity=ValidationSeverity.INFO)
        result.add_check('passed1', True, 'Passed', severity=ValidationSeverity.ERROR)
        assert len(result.error_checks) == 1, "Should only include failed ERROR checks"
        assert result.error_checks[0].name == 'error1', "Should be the error check"
    
    @pytest.mark.unit
    def test_error_checks_after_merge(self):
        """Test error_checks property after merging results."""
        result1 = ValidationResult()
        result1.add_check('error1', False, 'Error 1', severity=ValidationSeverity.ERROR)
        
        result2 = ValidationResult()
        result2.add_check('error2', False, 'Error 2', severity=ValidationSeverity.ERROR)
        result2.add_check('warning1', False, 'Warning', severity=ValidationSeverity.WARNING)
        
        result1.merge(result2)
        assert len(result1.error_checks) == 2, "Should include error checks from both results"
        error_names = {c.name for c in result1.error_checks}
        assert error_names == {'error1', 'error2'}, "Should have both error checks"


class TestValidationResultWarningChecksProperty:
    """Test the 'warning_checks' property of ValidationResult."""
    
    @pytest.mark.unit
    def test_warning_checks_empty_by_default(self):
        """Test that warning_checks is empty for new ValidationResult."""
        result = ValidationResult()
        assert len(result.warning_checks) == 0, "warning_checks should be empty by default"
    
    @pytest.mark.unit
    def test_warning_checks_includes_failed_warning_severity(self):
        """Test that warning_checks includes failed checks with WARNING severity."""
        result = ValidationResult()
        result.add_check('warning_check', False, 'Warning message', severity=ValidationSeverity.WARNING)
        assert len(result.warning_checks) == 1, "Should have one warning check"
        assert result.warning_checks[0].name == 'warning_check', "Warning check should have correct name"
        assert result.warning_checks[0].severity == ValidationSeverity.WARNING, "Should have WARNING severity"
        assert result.warning_checks[0].passed is False, "Should be a failed check"
    
    @pytest.mark.unit
    def test_warning_checks_excludes_passed_checks(self):
        """Test that warning_checks excludes passed checks even with WARNING severity."""
        result = ValidationResult()
        result.add_check('passed_check', True, 'Passed', severity=ValidationSeverity.WARNING)
        assert len(result.warning_checks) == 0, "Should not include passed checks"
    
    @pytest.mark.unit
    def test_warning_checks_excludes_error_checks(self):
        """Test that warning_checks excludes failed checks with ERROR severity."""
        result = ValidationResult()
        result.add_check('error_check', False, 'Error', severity=ValidationSeverity.ERROR)
        assert len(result.warning_checks) == 0, "Should not include error checks"
    
    @pytest.mark.unit
    def test_warning_checks_excludes_info_checks(self):
        """Test that warning_checks excludes failed checks with INFO severity."""
        result = ValidationResult()
        result.add_check('info_check', False, 'Info', severity=ValidationSeverity.INFO)
        assert len(result.warning_checks) == 0, "Should not include info checks"
    
    @pytest.mark.unit
    def test_warning_checks_multiple_warnings(self):
        """Test warning_checks with multiple warning checks."""
        result = ValidationResult()
        result.add_check('warning1', False, 'Warning 1', severity=ValidationSeverity.WARNING)
        result.add_check('warning2', False, 'Warning 2', severity=ValidationSeverity.WARNING)
        result.add_check('warning3', False, 'Warning 3', severity=ValidationSeverity.WARNING)
        assert len(result.warning_checks) == 3, "Should include all warning checks"
        assert all(c.severity == ValidationSeverity.WARNING for c in result.warning_checks), \
            "All checks should have WARNING severity"
        assert all(not c.passed for c in result.warning_checks), \
            "All checks should be failed"
    
    @pytest.mark.unit
    def test_warning_checks_mixed_severities(self):
        """Test warning_checks with mixed check severities."""
        result = ValidationResult()
        result.add_check('error1', False, 'Error', severity=ValidationSeverity.ERROR)
        result.add_check('warning1', False, 'Warning', severity=ValidationSeverity.WARNING)
        result.add_check('info1', False, 'Info', severity=ValidationSeverity.INFO)
        result.add_check('passed1', True, 'Passed', severity=ValidationSeverity.WARNING)
        assert len(result.warning_checks) == 1, "Should only include failed WARNING checks"
        assert result.warning_checks[0].name == 'warning1', "Should be the warning check"
    
    @pytest.mark.unit
    def test_warning_checks_after_merge(self):
        """Test warning_checks property after merging results."""
        result1 = ValidationResult()
        result1.add_check('warning1', False, 'Warning 1', severity=ValidationSeverity.WARNING)
        
        result2 = ValidationResult()
        result2.add_check('warning2', False, 'Warning 2', severity=ValidationSeverity.WARNING)
        result2.add_check('error1', False, 'Error', severity=ValidationSeverity.ERROR)
        
        result1.merge(result2)
        assert len(result1.warning_checks) == 2, "Should include warning checks from both results"
        warning_names = {c.name for c in result1.warning_checks}
        assert warning_names == {'warning1', 'warning2'}, "Should have both warning checks"


class TestValidationResultPropertyInteractions:
    """Test interactions between different properties."""
    
    @pytest.mark.unit
    def test_properties_with_all_check_types(self):
        """Test all properties with various check types."""
        result = ValidationResult()
        
        # Add different types of checks
        result.add_check('passed_error', True, 'Passed error', severity=ValidationSeverity.ERROR)
        result.add_check('failed_error', False, 'Failed error', severity=ValidationSeverity.ERROR)
        result.add_check('passed_warning', True, 'Passed warning', severity=ValidationSeverity.WARNING)
        result.add_check('failed_warning', False, 'Failed warning', severity=ValidationSeverity.WARNING)
        result.add_check('passed_info', True, 'Passed info', severity=ValidationSeverity.INFO)
        result.add_check('failed_info', False, 'Failed info', severity=ValidationSeverity.INFO)
        
        # Test passed property
        assert result.passed is False, "Should be False due to failed error check"
        
        # Test error_checks property
        assert len(result.error_checks) == 1, "Should have one error check"
        assert result.error_checks[0].name == 'failed_error', "Should be the failed error check"
        
        # Test warning_checks property
        assert len(result.warning_checks) == 1, "Should have one warning check"
        assert result.warning_checks[0].name == 'failed_warning', "Should be the failed warning check"
        
        # Test total checks
        assert len(result.checks) == 6, "Should have all 6 checks"
        assert len(result.passed_checks) == 3, "Should have 3 passed checks"
        assert len(result.failed_checks) == 3, "Should have 3 failed checks"
    
    @pytest.mark.unit
    def test_properties_with_only_warnings(self):
        """Test properties when only warnings are present (should still pass)."""
        result = ValidationResult()
        result.add_check('warning1', False, 'Warning 1', severity=ValidationSeverity.WARNING)
        result.add_check('warning2', False, 'Warning 2', severity=ValidationSeverity.WARNING)
        
        assert result.passed is True, "Should pass when only warnings are present"
        assert len(result.error_checks) == 0, "Should have no error checks"
        assert len(result.warning_checks) == 2, "Should have 2 warning checks"
    
    @pytest.mark.unit
    def test_properties_with_only_errors(self):
        """Test properties when only errors are present."""
        result = ValidationResult()
        result.add_check('error1', False, 'Error 1', severity=ValidationSeverity.ERROR)
        result.add_check('error2', False, 'Error 2', severity=ValidationSeverity.ERROR)
        
        assert result.passed is False, "Should fail when errors are present"
        assert len(result.error_checks) == 2, "Should have 2 error checks"
        assert len(result.warning_checks) == 0, "Should have no warning checks"
    
    @pytest.mark.unit
    def test_properties_empty_result(self):
        """Test properties with empty ValidationResult."""
        result = ValidationResult()
        
        assert result.passed is True, "Empty result should pass"
        assert len(result.error_checks) == 0, "Should have no error checks"
        assert len(result.warning_checks) == 0, "Should have no warning checks"
        assert len(result.checks) == 0, "Should have no checks"
    
    @pytest.mark.unit
    def test_properties_consistency(self):
        """Test that properties are consistent with each other."""
        result = ValidationResult()
        result.add_check('error1', False, 'Error', severity=ValidationSeverity.ERROR)
        result.add_check('warning1', False, 'Warning', severity=ValidationSeverity.WARNING)
        result.add_check('passed1', True, 'Passed', severity=ValidationSeverity.ERROR)
        
        # error_checks should only include failed ERROR checks
        error_check_names = {c.name for c in result.error_checks}
        assert error_check_names == {'error1'}, "error_checks should only have failed errors"
        
        # warning_checks should only include failed WARNING checks
        warning_check_names = {c.name for c in result.warning_checks}
        assert warning_check_names == {'warning1'}, "warning_checks should only have failed warnings"
        
        # All error_checks should be in failed_checks
        failed_check_names = {c.name for c in result.failed_checks}
        assert 'error1' in failed_check_names, "error_checks should be in failed_checks"
        assert 'warning1' in failed_check_names, "warning_checks should be in failed_checks"
        assert 'passed1' not in failed_check_names, "Passed checks should not be in failed_checks"

