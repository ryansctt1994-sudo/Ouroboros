# Manuscript Validation Guide

## Overview

The **Manuscript Validation System** ensures that documentation (manuscripts) stays synchronized with live code. It validates cross-references, verifies code examples, and integrates with the master manuscript catalog.

## What is Manuscript Validation?

Manuscript validation is the process of:
1. **Code Verification**: Ensuring code references in documentation exist and are current
2. **Cross-Reference Checking**: Validating links between documents
3. **Integration Validation**: Confirming catalog synchronization
4. **Section Marking**: Adding validation markers to document sections

## Architecture

```
┌────────────────────────────────────────┐
│      Manuscript Validator              │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────┐  ┌──────────────┐   │
│  │   Vector     │  │  Manuscript  │   │
│  │   Manifest   │  │  Catalog     │   │
│  └───────┬──────┘  └──────┬───────┘   │
│          │                 │           │
│          └────────┬────────┘           │
│                   │                    │
│         ┌─────────▼─────────┐          │
│         │  Code Reference   │          │
│         │  Validator        │          │
│         └─────────┬─────────┘          │
│                   │                    │
│         ┌─────────▼─────────┐          │
│         │  Cross-Reference  │          │
│         │  Checker          │          │
│         └─────────┬─────────┘          │
│                   │                    │
│         ┌─────────▼─────────┐          │
│         │  Validation       │          │
│         │  Report           │          │
│         └───────────────────┘          │
│                                        │
└────────────────────────────────────────┘
```

## Usage

### Basic Validation

Validate all manuscripts in repository:

```bash
python tools/manuscript_validator.py
```

### Specific Manuscript

Validate a single manuscript:

```bash
python tools/manuscript_validator.py --manuscript ARCHITECTURE.md
```

### Generate Report

Save validation report to JSON:

```bash
python tools/manuscript_validator.py --output manuscript_report.json
```

## Validation Process

### 1. **Manuscript Discovery**

The validator discovers manuscripts matching patterns:
- `*MANUSCRIPT*.md` - Files with "MANUSCRIPT" in name
- `*_DATA.md` - Data catalogs
- `docs/*.md` - All documentation files

### 2. **Section Parsing**

Each manuscript is parsed into logical sections:

```markdown
# Main Title

## Section 1
Content for section 1...

## Section 2
Content for section 2...

### Subsection 2.1
Subsection content...
```

Becomes:
```python
[
    {"title": "# Main Title", "content": "...", "level": 1},
    {"title": "## Section 1", "content": "...", "level": 2},
    {"title": "## Section 2", "content": "...", "level": 2},
    {"title": "### Subsection 2.1", "content": "...", "level": 3}
]
```

### 3. **Code Reference Extraction**

Extract code references from markdown:

#### Code Blocks
````markdown
```python
def quantum_update(entity):
    quantum = entity.get_component(QuantumResonance)
```
````

Extracts: `quantum_update`, `QuantumResonance`

#### Inline Code
```markdown
The `QuantumSystem` uses `QuantumResonance` components.
```

Extracts: `QuantumSystem`, `QuantumResonance`

#### File Paths
```markdown
See `python-bridge/eden_ecs/systems.py` for implementation.
```

Extracts: `python-bridge/eden_ecs/systems.py`

### 4. **Reference Verification**

Each reference is verified against:

**Vector Manifest:**
```python
if reference in vectors:
    return True, f"Found in vectors: {reference}"
```

**Partial Match:**
```python
for vector_id, vector_data in vectors.items():
    if vector_data.get("name") == reference:
        return True, f"Found vector: {vector_id}"
```

**File System:**
```python
file_path = repo_root / reference
if file_path.exists():
    return True, f"File exists: {reference}"
```

### 5. **Cross-Reference Checking**

Validate markdown links:

```markdown
See [Architecture Guide](../docs/ARCHITECTURE.md) for details.
```

Validation:
```python
cross_ref_pattern = r'\[([^\]]+)\]\(([^\)]+\.md)\)'
cross_refs = re.findall(cross_ref_pattern, content)

for ref_text, ref_file in cross_refs:
    ref_path = repo_root / ref_file
    if not ref_path.exists():
        errors.append(f"Broken cross-reference: {ref_file}")
```

### 6. **Integration Validation**

Check integration with `OUROBOROS_MANUSCRIPT_DATA.md`:

```python
manuscript_data_path = repo_root / "OUROBOROS_MANUSCRIPT_DATA.md"
with open(manuscript_data_path, 'r') as f:
    master_content = f.read()

if manuscript_path.name not in master_content:
    warnings.append(f"{manuscript_path.name} not referenced in master catalog")
```

## Validation Markers

Each section receives a validation marker:

```python
@dataclass
class ValidationMarker:
    section: str             # Section title
    status: str              # "validated", "outdated", "missing_reference", "error"
    timestamp: float         # When validated
    details: str             # Status details
    references: List[str]    # Code references in section
```

**Status Types:**
- `validated` - All references valid, section up-to-date
- `outdated` - Code references changed since last update
- `missing_reference` - References not found in codebase
- `error` - Critical validation error

## Report Structure

```json
{
  "timestamp": 1708185600.0,
  "manuscript": "ARCHITECTURE.md",
  "total_sections": 12,
  "validated_sections": 10,
  "warnings": [
    "Section 'Advanced Features' has invalid references: ['FutureSystem']"
  ],
  "errors": [],
  "markers": [
    {
      "section": "Overview",
      "status": "validated",
      "timestamp": 1708185600.0,
      "details": "All 5 references validated",
      "references": ["QuantumSystem", "World", "Entity", ...]
    }
  ],
  "cross_references_valid": true,
  "integration_status": "synced"
}
```

## Integration Status

Three possible statuses:

### `synced`
- All references valid
- Cross-references work
- Listed in master catalog
- **Action:** None needed

### `needs_update`
- Some warnings present
- Minor reference issues
- May need catalog update
- **Action:** Review warnings, update if needed

### `broken`
- Critical errors found
- Broken cross-references
- Not in master catalog
- **Action:** Fix immediately

## Self-Updating Manuscripts

Manuscripts can include validation markers in comments:

```markdown
<!-- VALIDATION: validated @ 2024-02-17 16:40:00 -->
<!-- REFERENCES: 12 verified -->

## Quantum System

The `QuantumSystem` manages quantum resonance...

<!-- VALIDATION_END -->
```

Auto-update with:

```python
def add_validation_markers(manuscript_path, marker):
    """Add validation markers to manuscript."""
    with open(manuscript_path, 'r') as f:
        content = f.read()
    
    # Add marker comment
    marker_text = f"<!-- VALIDATION: {marker.status} @ {timestamp} -->"
    marker_text += f"\n<!-- REFERENCES: {len(marker.references)} verified -->\n"
    
    # Insert after section heading
    # ... implementation
```

## Best Practices

### 1. **Keep References Current**

Update documentation when code changes:

```bash
# After refactoring
python tools/manuscript_validator.py --manuscript ARCHITECTURE.md

# Fix any broken references
# Re-validate
python tools/manuscript_validator.py --manuscript ARCHITECTURE.md
```

### 2. **Use Inline Code for References**

Instead of:
```markdown
The quantum system uses quantum resonance.
```

Use:
```markdown
The `QuantumSystem` uses `QuantumResonance` components.
```

### 3. **Verify Cross-References**

Before adding links:
```bash
# Check if target exists
ls -la docs/ARCHITECTURE.md

# Add link
[Architecture Guide](../docs/ARCHITECTURE.md)

# Validate
python tools/manuscript_validator.py
```

### 4. **Maintain Master Catalog**

Keep `OUROBOROS_MANUSCRIPT_DATA.md` updated:

```markdown
## Digital Artifacts Inventory

Files:
- README.md
- ARCHITECTURE.md  <!-- Add new manuscripts here -->
- IMPLEMENTATION.md
- docs/ecs_vectorization.md
...
```

### 5. **CI/CD Integration**

Add to CI pipeline:

```yaml
- name: Validate manuscripts
  run: python tools/manuscript_validator.py
  
- name: Check for errors
  run: |
    python tools/manuscript_validator.py --output report.json
    if grep -q '"errors": \[\]' report.json; then
      echo "No errors found"
    else
      echo "Validation errors detected"
      exit 1
    fi
```

## Advanced Features

### Custom Reference Patterns

Add custom patterns for domain-specific references:

```python
# System names with underscores
system_refs = re.findall(r'\b([A-Z][a-zA-Z]*System)\b', content)

# Component names
component_refs = re.findall(r'\b([A-Z][a-zA-Z]*Component)\b', content)

# Adapter names
adapter_refs = re.findall(r'\b([A-Z][a-zA-Z]*Adapter)\b', content)
```

### Semantic Validation

Validate code examples execute correctly:

```python
def validate_code_block(code, language):
    """Validate code block executes without errors."""
    if language == "python":
        try:
            compile(code, '<manuscript>', 'exec')
            return True, "Code compiles"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
    return True, "Skipped validation"
```

### Documentation Coverage

Track documentation coverage:

```python
# Find undocumented systems
all_systems = [v for v in vectors if v['type'] == 'class' and 'System' in v['name']]
documented_systems = extract_systems_from_manuscripts(manuscripts)

undocumented = set(all_systems) - set(documented_systems)
print(f"Undocumented systems: {len(undocumented)}")
```

## Troubleshooting

### Issue: False positives on valid references

**Cause:** Reference pattern too strict  
**Solution:** Extend reference extraction patterns

### Issue: Broken cross-references after repo restructure

**Cause:** File paths changed  
**Solution:** Update all cross-reference paths

### Issue: Manuscript not in catalog

**Cause:** Missing from OUROBOROS_MANUSCRIPT_DATA.md  
**Solution:** Add to Digital Artifacts Inventory section

## Examples

### Example 1: Validate Architecture Docs

```bash
$ python tools/manuscript_validator.py --manuscript docs/ARCHITECTURE.md

Validating manuscript: ARCHITECTURE.md

======================================================================
MANUSCRIPT VALIDATION: ARCHITECTURE.md
======================================================================
Status: VALIDATED
Sections: 12/12 validated
Cross-references: ✓ Valid
Warnings: 0
Errors: 0
----------------------------------------------------------------------

✓ Manuscript fully validated!
======================================================================
```

### Example 2: Fix Broken References

```bash
$ python tools/manuscript_validator.py --manuscript IMPLEMENTATION.md

WARNINGS:
  ⚠ Section 'Future Systems' has invalid references: ['FutureSystem']

# Update IMPLEMENTATION.md - remove or fix 'FutureSystem' reference

$ python tools/manuscript_validator.py --manuscript IMPLEMENTATION.md

✓ Manuscript fully validated!
```

### Example 3: Integration Report

```bash
$ python tools/manuscript_validator.py --output report.json

✓ Validation reports saved to: report.json

$ cat report.json
{
  "ARCHITECTURE.md": {
    "status": "synced",
    "validated_sections": 12,
    ...
  },
  ...
}
```

## Future Enhancements

- **Live Preview**: Real-time validation in editors
- **Auto-Fix**: Automatically update broken references
- **Version Tracking**: Track documentation versions
- **Diff Analysis**: Show what changed in code vs docs
- **AI Suggestions**: Suggest documentation improvements

---

**Documentation that stays synchronized with code, validated automatically.**
