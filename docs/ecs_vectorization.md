# ECS Vectorization Guide

## Overview

The **ECS Vectorization System** transforms the Ouroboros codebase into a machine-readable, searchable knowledge base. Every function, class, method, and system becomes a **vector** - a structured metadata envelope that captures its essence, dependencies, and relationships.

## What is a Vector?

A vector is a comprehensive metadata structure that describes a code unit:

```json
{
  "vector_id": "eden_ecs.systems.QuantumSystem",
  "type": "class",
  "name": "QuantumSystem",
  "parent": null,
  "module": "eden_ecs.systems",
  "file_path": "python-bridge/eden_ecs/systems.py",
  "language": "python",
  "line_start": 82,
  "line_end": 116,
  "signature": "class QuantumSystem(System)",
  "docstring": "Updates 750 THz UV quantum resonance...",
  "domain": "quantum",
  "purity": "impure",
  "dependencies": ["System", "World", "Entity", "QuantumResonance"],
  "internal_refs": [],
  "constants": {},
  "hash": "a8f3c92d4e7b1f65",
  "decorators": [],
  "attributes": ["resonance_threshold"],
  "visibility": "public",
  "base_classes": ["System"]
}
```

## Vector Components

### Core Metadata

| Field | Type | Description |
|-------|------|-------------|
| `vector_id` | string | Unique identifier (module.path.name) |
| `type` | string | Code unit type (function, class, method, etc.) |
| `name` | string | Name of the code unit |
| `parent` | string | Parent class/module (if applicable) |
| `module` | string | Python module path |

### Source Information

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | string | Relative path to source file |
| `language` | string | Programming language (python, rust) |
| `line_start` | int | Starting line number |
| `line_end` | int | Ending line number |

### Code Structure

| Field | Type | Description |
|-------|------|-------------|
| `signature` | string | Function/class signature |
| `docstring` | string | Documentation string |
| `decorators` | array | List of decorators |
| `base_classes` | array | Parent classes (for classes) |
| `attributes` | array | Class attributes/fields |

### Analysis

| Field | Type | Description |
|-------|------|-------------|
| `domain` | string | Semantic domain (quantum, sync, etc.) |
| `purity` | string | Pure/impure function classification |
| `dependencies` | array | External dependencies |
| `internal_refs` | array | Internal cross-references |
| `constants` | object | Named constants used |
| `hash` | string | Cryptographic hash of content |
| `visibility` | string | Public/private visibility |

## Vectorization Process

### 1. **Code Scanning**

The vectorizer (`tools/vectorize.py`) scans the repository:

```bash
python tools/vectorize.py --root . --output vectors.json
```

**Process:**
1. Walk repository directory tree
2. Skip build artifacts, caches, virtual environments
3. Parse Python files with AST
4. Parse Rust files with regex patterns
5. Extract metadata for each code unit

### 2. **Metadata Extraction**

For each code unit:
- Parse syntax tree to extract structure
- Compute cryptographic hash for integrity
- Identify dependencies and references
- Extract docstrings and signatures
- Classify purity and visibility

### 3. **Vector Generation**

Create structured vector with:
- Unique ID based on module path
- Complete metadata envelope
- Hash for change detection
- Relationships to other vectors

### 4. **Manifest Creation**

Output JSON manifest:

```json
{
  "metadata": {
    "version": "1.0.0",
    "timestamp": 1708185600.0,
    "total_vectors": 2075
  },
  "vectors": [
    { /* vector 1 */ },
    { /* vector 2 */ },
    ...
  ]
}
```

## Runtime Vector Validation

The **Runtime Vector Validator** (`tools/runtime_validator.py`) validates runtime ECS state against static vectors.

### Validation Process

```python
from runtime_validator import RuntimeVectorValidator

# Initialize validator
validator = RuntimeVectorValidator("vectors.json")

# Get runtime state (from live ECS)
runtime_vectors = get_ecs_runtime_state(world)

# Validate
report = validator.validate_runtime_state(runtime_vectors)

# Check results
if report.drift_count > 0:
    print(f"Drift detected: {report.drift_count} events")
    recommendations = validator.get_self_healing_recommendations(report)
```

### Drift Detection

The validator detects several drift types:

#### 1. **Missing Vectors**
- Vector exists in static manifest but not in runtime
- **Severity:** Critical
- **Cause:** Code was deleted or not loaded
- **Action:** Restore from backup or regenerate

#### 2. **Added Vectors**
- Vector exists in runtime but not in static manifest
- **Severity:** Medium
- **Cause:** New code not yet vectorized
- **Action:** Run vectorization tool to update manifest

#### 3. **Signature Changed**
- Function/class signature differs from manifest
- **Severity:** High
- **Cause:** Code was modified
- **Action:** Re-vectorize changed file

#### 4. **Modified Vectors**
- Other changes (docstring, dependencies, location)
- **Severity:** Medium/Low
- **Cause:** Documentation or refactoring changes
- **Action:** Update vectors if intentional

### Cryptographic Verification

Each vector has a cryptographic hash:

```python
def _compute_vector_hash(self, vector_data: Dict[str, Any]) -> str:
    """Compute hash for a vector (excluding the hash field itself)."""
    data = {k: v for k, v in vector_data.items() if k != "hash"}
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()
```

This enables:
- Change detection
- Integrity verification
- Tamper detection
- Version tracking

### Self-Healing

The validator provides recommendations:

```python
recommendations = validator.get_self_healing_recommendations(report)

for rec in recommendations:
    print(f"{rec['priority']}: {rec['description']}")
    print(f"Action: {rec['action']}")
    for step in rec['steps']:
        print(f"  - {step}")
```

**Example recommendations:**
- **Missing vector:** Check git history, restore from backup
- **Signature changed:** Re-vectorize file, update manifest
- **Added vector:** Run vectorization, validate new code

## Integration with ECS

### Vector-Based Queries

Use vectors to query ECS state:

```python
# Find all quantum-related systems
quantum_vectors = [
    v for v in vectors
    if "quantum" in v.get("domain", "").lower()
    or "quantum" in v.get("name", "").lower()
]

# Find all systems with specific dependency
sync_systems = [
    v for v in vectors
    if "MycelialSyncSystem" in v.get("dependencies", [])
]

# Find high-priority systems
priority_systems = [
    v for v in vectors
    if v.get("type") == "class"
    and any("priority" in attr.lower() for attr in v.get("attributes", []))
]
```

### Runtime State Extraction

Extract runtime vectors from live ECS:

```python
from eden_ecs import World
from eden_ecs.adapters import QuantumSystemAdapter

# Create world and adapter
world = World()
quantum_system = QuantumSystem()
adapter = QuantumSystemAdapter(quantum_system)

# Extract runtime vectors
runtime_vectors = adapter.get_runtime_vectors(world)

# Each runtime vector captures live state
for vector in runtime_vectors:
    print(f"Entity: {vector['entity_id']}")
    print(f"Quantum Phase: {vector['quantum_phase']}")
    print(f"Coherence: {vector['coherence']}")
```

## Best Practices

### 1. **Regular Vectorization**

Re-vectorize after significant changes:

```bash
# After adding new files
python tools/vectorize.py

# After refactoring
python tools/vectorize.py

# Before major releases
python tools/vectorize.py --output vectors_v2.json
```

### 2. **Validation in CI/CD**

Add to CI pipeline:

```yaml
- name: Validate vectors
  run: python tools/runtime_validator.py
```

### 3. **Version Control**

Commit `vectors.json` to track changes:

```bash
git add vectors.json
git commit -m "Update vectors after refactoring"
```

### 4. **Documentation Sync**

Keep vectors synchronized with documentation:

```bash
python tools/manuscript_validator.py
```

## Use Cases

### 1. **Code Search**

Find code units by metadata:
- Search by domain: "quantum", "sync", "teleport"
- Search by dependency: "QuantumResonance"
- Search by type: "class", "function", "method"

### 2. **Impact Analysis**

Understand change impact:
- Find all dependents of a function
- Track internal references
- Identify affected systems

### 3. **Documentation Generation**

Auto-generate documentation from vectors:
- API references from signatures
- Dependency graphs from relationships
- Module overviews from metadata

### 4. **Quality Metrics**

Track code quality:
- Function purity distribution
- Dependency complexity
- Documentation coverage

### 5. **Refactoring Support**

Safe refactoring with validation:
- Detect signature changes
- Verify dependency updates
- Validate cross-references

## Advanced Features

### Custom Vector Types

Extend vectorization for domain-specific needs:

```python
class CustomVectorizer(CodebaseVectorizer):
    def extract_quantum_metadata(self, node):
        """Extract quantum-specific metadata."""
        metadata = {}
        # Custom extraction logic
        return metadata
```

### Vector Analytics

Analyze vector relationships:

```python
import networkx as nx

# Build dependency graph
G = nx.DiGraph()
for vector in vectors:
    for dep in vector.get("dependencies", []):
        G.add_edge(vector["vector_id"], dep)

# Find central components
centrality = nx.betweenness_centrality(G)
important = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
```

### Live Monitoring

Monitor runtime state continuously:

```python
# Periodic validation
import time

validator = RuntimeVectorValidator("vectors.json")

while True:
    runtime_vectors = get_ecs_runtime_state(world)
    report = validator.validate_runtime_state(runtime_vectors)
    
    if report.drift_count > 0:
        alert_team(report)
    
    time.sleep(60)  # Check every minute
```

## Troubleshooting

### Issue: Hash mismatches on every run

**Cause:** Non-deterministic code (timestamps, random values)  
**Solution:** Exclude non-deterministic fields from hash

### Issue: Too many false positives

**Cause:** Overly sensitive drift detection  
**Solution:** Adjust severity thresholds or filter by drift type

### Issue: Slow vectorization

**Cause:** Large codebase or complex parsing  
**Solution:** Parallelize parsing or cache results

## Future Enhancements

- **Machine Learning**: Predict optimal refactorings
- **Semantic Search**: Natural language queries
- **Auto-Documentation**: Generate docs from vectors
- **Quantum Integration**: Quantum-ready vector encoding
- **Blockchain**: Immutable vector history

---

**The codebase is now searchable, validatable, and self-aware.**
