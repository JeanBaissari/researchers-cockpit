# Generate API Documentation

## Overview

Automatically generate API documentation from docstrings and type hints in lib/ modules, updating docs/api/ files.

## Steps

1. **Parse lib/ Modules** - Scan Python files in lib/ directory
2. **Extract Docstrings** - Parse function signatures, docstrings, examples
3. **Generate Markdown** - Create markdown following docs/api/ patterns
4. **Update API Docs** - Update existing docs/api/ files or create new ones
5. **Cross-Reference** - Link related functions and modules
6. **Validate Format** - Ensure docs follow .cursor/rules/docs-api.mdc standards

## Checklist

- [ ] lib/ modules parsed
- [ ] Docstrings extracted from functions/classes
- [ ] Type hints included in documentation
- [ ] Examples extracted from docstrings
- [ ] Markdown generated following docs/api/ patterns
- [ ] Existing API docs updated or new ones created
- [ ] Cross-references added between related functions
- [ ] Format validated against docs-api.mdc standards

## API Documentation Patterns

**Extract docstrings:**
```python
import ast
from pathlib import Path

def extract_docstrings(file_path: Path):
    """Extract function docstrings from Python file."""
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            functions.append({
                'name': node.name,
                'docstring': docstring,
                'signature': ast.unparse(node)
            })
    return functions
```

**Generate markdown:**
```markdown
# Module Name

## Functions

### function_name
\`\`\`python
def function_name(param1: str, param2: int = 0) -> bool:
    """Function description."""
\`\`\`
**Parameters:** `param1` (str), `param2` (int, optional)
**Returns:** `bool`
```

**Update existing docs:**
```python
from pathlib import Path
doc_path = Path('docs/api') / f"{module_name}.md"
doc_path.write_text(generate_markdown(module_name, functions))
```

## Documentation Standards

**Follow docs-api.mdc patterns:**
- Google-style docstrings (Args, Returns, Raises)
- Include type hints
- Add examples for complex functions
- Cross-reference related functions
- Document public API only

**File structure:**
```
docs/api/
├── backtest.md
├── config.md
├── metrics.md
└── README.md
```

## Notes

- Only document public functions (not _private)
- Extract examples from docstrings
- Maintain cross-references between modules
- Update docs when code changes
- Follow existing docs/api/ file patterns

## Related Commands

- add-documentation.md - For adding docstrings
- create-update-component-diagram.md - For component diagrams

