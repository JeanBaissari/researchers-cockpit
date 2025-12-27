"""
Thin wrapper to re-export calendar utilities from .zipline/extension.py.

This module provides a clean import path for the calendar functions
defined in the .zipline/extension.py configuration file.
"""

import importlib.util
import sys
from pathlib import Path

# Load the extension module from .zipline/extension.py
_project_root = Path(__file__).parent.parent
_extension_path = _project_root / '.zipline' / 'extension.py'

if not _extension_path.exists():
    raise ImportError(f"Extension module not found at {_extension_path}")

_spec = importlib.util.spec_from_file_location("zipline_extension", _extension_path)
_extension_module = importlib.util.module_from_spec(_spec)
sys.modules["zipline_extension"] = _extension_module
_spec.loader.exec_module(_extension_module)

# Re-export public API
register_custom_calendars = _extension_module.register_custom_calendars
get_calendar_for_asset_class = _extension_module.get_calendar_for_asset_class
get_available_calendars = _extension_module.get_available_calendars
get_registered_calendars = _extension_module.get_registered_calendars
register_calendar_type = _extension_module.register_calendar_type
resolve_calendar_name = _extension_module.resolve_calendar_name
CryptoCalendar = _extension_module.CryptoCalendar
ForexCalendar = _extension_module.ForexCalendar

__all__ = [
    'register_custom_calendars',
    'get_calendar_for_asset_class',
    'get_available_calendars',
    'get_registered_calendars',
    'register_calendar_type',
    'resolve_calendar_name',
    'CryptoCalendar',
    'ForexCalendar',
]
