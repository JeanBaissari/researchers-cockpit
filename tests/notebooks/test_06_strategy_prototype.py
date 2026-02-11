"""
Tests for 06_strategy_prototype.ipynb

Verifies notebook structure and imports.
"""

import json
import pytest
from pathlib import Path


def test_notebook_exists():
    """Verify notebook file exists."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'
    assert notebook_path.exists(), f"Notebook not found at {notebook_path}"


def test_notebook_structure():
    """Verify notebook has correct structure."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Verify format
    assert nb['nbformat'] == 4, "Notebook should be format 4"
    assert nb['nbformat_minor'] >= 5, "Notebook should be format 4.5+"

    # Verify has cells
    assert len(nb['cells']) >= 10, "Notebook should have at least 10 cells"

    # Verify cell types
    cell_types = [cell['cell_type'] for cell in nb['cells']]
    assert 'markdown' in cell_types, "Notebook should have markdown cells"
    assert 'code' in cell_types, "Notebook should have code cells"


def test_notebook_version_header():
    """Verify notebook has v1.12.0 version header."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find intro cell
    intro_cell = None
    for cell in nb['cells']:
        if cell['cell_type'] == 'markdown' and cell.get('id') == 'intro':
            intro_cell = cell
            break

    assert intro_cell is not None, "Notebook should have intro markdown cell"

    # Verify version mentioned
    content = ''.join(intro_cell['source'])
    assert 'v1.12.0' in content, "Notebook should mention v1.12.0"
    assert 'NO WRAPPERS' in content, "Notebook should mention NO WRAPPERS architecture"


def test_notebook_imports():
    """Verify notebook uses correct imports."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find setup cell
    setup_cell = None
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'setup':
            setup_cell = cell
            break

    assert setup_cell is not None, "Notebook should have setup code cell"

    # Verify imports
    source = ''.join(setup_cell['source'])

    # Check for direct Zipline imports (v1.12.0 NO WRAPPERS)
    assert 'from zipline import run_algorithm' in source, "Should import run_algorithm from zipline"
    assert 'from zipline.api import' in source, "Should import from zipline.api"

    # Check for lib imports
    assert 'from lib.paths import' in source, "Should import from lib.paths"
    assert 'from lib.bundles import' in source, "Should import from lib.bundles"
    assert 'from lib.calendars import' in source, "Should import from lib.calendars"
    assert 'from lib.metrics import' in source, "Should import from lib.metrics"

    # Verify NO wrapper imports (should NOT be present)
    assert 'from lib.data.aggregation import' not in source, "Should NOT import wrapper functions"
    assert 'from lib.calendars.sessions import' not in source, "Should NOT import SessionManager"


def test_notebook_strategy_implementation():
    """Verify notebook has strategy implementation cells."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find strategy logic cell
    strategy_cell = None
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'strategy-logic':
            strategy_cell = cell
            break

    assert strategy_cell is not None, "Notebook should have strategy-logic code cell"

    # Verify has initialize and handle_data functions
    source = ''.join(strategy_cell['source'])
    assert 'def initialize(context):' in source, "Should define initialize() function"
    assert 'def handle_data(context, data):' in source, "Should define handle_data() function"

    # Verify uses direct Zipline APIs
    assert 'data.history(' in source, "Should use data.history() directly"
    assert 'order_target_percent(' in source, "Should use order_target_percent()"
    assert 'record(' in source, "Should use record() for tracking"


def test_notebook_cell_organization():
    """Verify notebook follows proper cell organization."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Expected cell IDs in order
    expected_sections = [
        'intro',           # Markdown header
        'setup',           # Code setup
        'config',          # Code configuration
        'bundle-selection', # Code bundle selection
        'strategy-logic',  # Code strategy implementation
        'run-backtest',    # Code backtest execution
        'calculate-metrics', # Code metrics calculation
        'visualize-equity', # Code visualization
        'analyze-returns',  # Code returns analysis
        'summary',         # Code summary
    ]

    # Get cell IDs
    cell_ids = [cell.get('id') for cell in nb['cells'] if cell['cell_type'] == 'code' or cell.get('id') == 'intro']

    # Verify expected sections are present (order may vary slightly)
    for section_id in expected_sections:
        assert section_id in cell_ids, f"Notebook should have '{section_id}' cell"


def test_notebook_has_visualizations():
    """Verify notebook includes visualization cells."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find visualization cells
    viz_cells = [
        cell for cell in nb['cells']
        if cell['cell_type'] == 'code' and
        ('plt.subplots' in ''.join(cell['source']) or 'plt.plot' in ''.join(cell['source']))
    ]

    assert len(viz_cells) >= 2, "Notebook should have at least 2 visualization cells"


def test_notebook_has_metrics_display():
    """Verify notebook displays performance metrics."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find metrics cell
    metrics_cell = None
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'calculate-metrics':
            metrics_cell = cell
            break

    assert metrics_cell is not None, "Notebook should have calculate-metrics cell"

    source = ''.join(metrics_cell['source'])
    assert 'calculate_metrics' in source, "Should use calculate_metrics() function"
    assert 'total_return' in source, "Should display total return"
    assert 'sharpe' in source, "Should display Sharpe ratio"
    assert 'max_drawdown' in source, "Should display max drawdown"


def test_notebook_parameters_configurable():
    """Verify notebook has configurable parameters."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find config cell
    config_cell = None
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'config':
            config_cell = cell
            break

    assert config_cell is not None, "Notebook should have config code cell"

    source = ''.join(config_cell['source'])

    # Verify key configuration parameters
    assert 'strategy_name' in source, "Should have strategy_name parameter"
    assert 'asset_symbol' in source, "Should have asset_symbol parameter"
    assert 'start_date' in source, "Should have start_date parameter"
    assert 'end_date' in source, "Should have end_date parameter"
    assert 'capital_base' in source, "Should have capital_base parameter"
    assert 'params = {' in source, "Should have params dictionary"


def test_notebook_has_summary():
    """Verify notebook has summary and next steps."""
    notebook_path = Path(__file__).parent.parent.parent / 'notebooks' / '06_strategy_prototype.ipynb'

    with open(notebook_path) as f:
        nb = json.load(f)

    # Find summary cell
    summary_cell = None
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and cell.get('id') == 'summary':
            summary_cell = cell
            break

    assert summary_cell is not None, "Notebook should have summary code cell"

    source = ''.join(summary_cell['source'])
    assert 'Next Steps' in source, "Summary should mention next steps"
    assert 'Hypothesis Validation' in source, "Summary should include hypothesis validation"
