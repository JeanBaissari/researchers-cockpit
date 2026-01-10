# Create/Update Component Diagram

## Overview

Create/update detailed component diagrams in markdown format with visual-text-based flow diagrams using mermaid syntax.

## Steps

1. **Identify Component** - Determine component/function to document
2. **Analyze Dependencies** - Map component relationships and data flow
3. **Generate Mermaid Diagram** - Create flowchart, sequence, or class diagram
4. **Create Documentation** - Write markdown file with diagram and explanation
5. **Add Component Details** - Document responsibilities, inputs/outputs, dependencies
6. **Link Related Components** - Cross-reference related components and code
7. **Store in docs/architecture/** - Save diagram file in architecture directory

## Checklist

- [ ] Component identified and analyzed
- [ ] Dependencies mapped
- [ ] Mermaid diagram generated
- [ ] Markdown file created in docs/architecture/
- [ ] Overview section written
- [ ] Component diagram included
- [ ] Data flow documented
- [ ] Function call sequence documented
- [ ] Dependencies listed
- [ ] Related components linked

## Component Diagram Template

**File structure:**
```markdown
# Component Name

## Overview
Brief description of component purpose and responsibilities.

## Component Diagram

\`\`\`mermaid
flowchart TD
    A[Component A] --> B[Component B]
    B --> C[Component C]
\`\`\`

## Data Flow
Description of how data flows through the component.

## Function Call Sequence

\`\`\`mermaid
sequenceDiagram
    participant A as Component A
    participant B as Component B
    A->>B: Function Call
    B-->>A: Response
\`\`\`

## Dependencies
- lib/config - Configuration loading
- lib/paths - Path resolution
- lib/logging - Logging utilities

## Related Components
- [Component B](./component_b.md) - Related component
- [Component C](./component_c.md) - Another related component
```

## Diagram Types

**Flowchart:** `flowchart TD` for data flow
**Sequence:** `sequenceDiagram` for function calls
**Class:** `classDiagram` for relationships

## Notes

- Store diagrams in `docs/architecture/` directory
- Use mermaid syntax for diagrams (renders in GitHub, VS Code)
- Keep diagrams focused (one diagram per major flow)
- Update diagrams when components change
- Link to actual code files for reference

## Related Commands

- add-documentation.md - For adding component documentation
- generate-api-docs.md - For API documentation

