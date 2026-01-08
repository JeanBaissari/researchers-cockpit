"""
Test that no deprecated imports exist in codebase.

This test ensures that all legacy wrapper files have been removed and
no code uses deprecated import paths.
"""

# Standard library imports
import subprocess
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent


class TestDeprecatedFilesRemoved:
    """Test that deprecated wrapper files no longer exist."""
    
    @pytest.mark.unit
    def test_data_loader_removed(self):
        """Test that lib/data_loader.py has been removed."""
        deprecated_file = project_root / 'lib' / 'data_loader.py'
        assert not deprecated_file.exists(), "lib/data_loader.py should be removed"
    
    @pytest.mark.unit
    def test_data_validation_removed(self):
        """Test that lib/data_validation.py has been removed."""
        deprecated_file = project_root / 'lib' / 'data_validation.py'
        assert not deprecated_file.exists(), "lib/data_validation.py should be removed"
    
    @pytest.mark.unit
    def test_data_integrity_removed(self):
        """Test that lib/data_integrity.py has been removed."""
        deprecated_file = project_root / 'lib' / 'data_integrity.py'
        assert not deprecated_file.exists(), "lib/data_integrity.py should be removed"
    
    @pytest.mark.unit
    def test_logging_config_removed(self):
        """Test that lib/logging_config.py has been removed."""
        deprecated_file = project_root / 'lib' / 'logging_config.py'
        assert not deprecated_file.exists(), "lib/logging_config.py should be removed"
    
    @pytest.mark.unit
    def test_optimize_wrapper_removed(self):
        """Test that lib/optimize.py wrapper has been removed."""
        # Note: lib/optimize/ package should exist, but not lib/optimize.py wrapper
        wrapper_file = project_root / 'lib' / 'optimize.py'
        package_dir = project_root / 'lib' / 'optimize'
        assert not wrapper_file.exists(), "lib/optimize.py wrapper should be removed"
        assert package_dir.exists(), "lib/optimize/ package should exist"
    
    @pytest.mark.unit
    def test_validate_wrapper_removed(self):
        """Test that lib/validate.py wrapper has been removed."""
        # Note: lib/validate/ package should exist, but not lib/validate.py wrapper
        wrapper_file = project_root / 'lib' / 'validate.py'
        package_dir = project_root / 'lib' / 'validate'
        assert not wrapper_file.exists(), "lib/validate.py wrapper should be removed"
        assert package_dir.exists(), "lib/validate/ package should exist"
    
    @pytest.mark.unit
    def test_extension_wrapper_removed(self):
        """Test that lib/extension.py has been removed."""
        deprecated_file = project_root / 'lib' / 'extension.py'
        assert not deprecated_file.exists(), "lib/extension.py should be removed"
        
        # lib/calendars/ package should exist
        calendars_package = project_root / 'lib' / 'calendars'
        assert calendars_package.exists(), "lib/calendars/ package should exist"


class TestNoDeprecatedImportsInScripts:
    """Test that scripts don't use deprecated imports."""
    
    @pytest.mark.unit
    def test_no_data_loader_imports_in_scripts(self):
        """Test that scripts don't import from lib.data_loader."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        
        for script in scripts_dir.glob('*.py'):
            content = script.read_text()
            assert 'from lib.data_loader' not in content, \
                f"{script.name} uses deprecated 'from lib.data_loader'"
            assert 'import lib.data_loader' not in content, \
                f"{script.name} uses deprecated 'import lib.data_loader'"
    
    @pytest.mark.unit
    def test_no_data_validation_imports_in_scripts(self):
        """Test that scripts don't import from lib.data_validation."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        
        for script in scripts_dir.glob('*.py'):
            content = script.read_text()
            assert 'from lib.data_validation' not in content, \
                f"{script.name} uses deprecated 'from lib.data_validation'"
            assert 'import lib.data_validation' not in content, \
                f"{script.name} uses deprecated 'import lib.data_validation'"
    
    @pytest.mark.unit
    def test_no_logging_config_imports_in_scripts(self):
        """Test that scripts don't import from lib.logging_config."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        
        for script in scripts_dir.glob('*.py'):
            content = script.read_text()
            assert 'from lib.logging_config' not in content, \
                f"{script.name} uses deprecated 'from lib.logging_config'"
            assert 'import lib.logging_config' not in content, \
                f"{script.name} uses deprecated 'import lib.logging_config'"


class TestNoDeprecatedImportsInLib:
    """Test that lib/ modules don't use deprecated imports."""
    
    @pytest.mark.unit
    def test_lib_init_has_no_fallbacks(self):
        """Test that lib/__init__.py has no backward-compat fallbacks."""
        lib_init = project_root / 'lib' / '__init__.py'
        if not lib_init.exists():
            pytest.skip("lib/__init__.py not found")
        
        content = lib_init.read_text()
        
        # Should not have try/except fallback patterns
        assert 'from .data_loader' not in content, \
            "lib/__init__.py should not import from .data_loader"
        assert 'from .data_validation' not in content, \
            "lib/__init__.py should not import from .data_validation"
        assert 'from .data_integrity' not in content, \
            "lib/__init__.py should not import from .data_integrity"
        assert 'from .logging_config' not in content, \
            "lib/__init__.py should not import from .logging_config"
        assert 'from .extension' not in content, \
            "lib/__init__.py should not import from .extension"

