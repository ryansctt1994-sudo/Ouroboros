# GGCCD Crucible Framework

## Overview

The **Global Geometric Construct Compression Dictionary (GGCCD)** framework provides a holistic lexicon system for encoding multi-dimensional states using symbols, glyphs, and immutable "True Text" explanations organized into lattice constructs.

## Architecture

The GGCCD framework consists of three main components:

1. **Lexicon** (`ggccd/lexicon.py`) - Symbol and glyph definitions with immutable True Text
2. **Framework** (`ggccd/framework.py`) - Composite statements, lattice constructs, and deployment protocols
3. **Public API** (`ggccd/__init__.py`) - Unified interface for all GGCCD functionality

## Core Concepts

### Symbols and Glyphs

GGCCD defines two types of symbolic elements:

- **Symbols**: Basic elements representing states (e.g., +1, 0, -1)
- **Glyphs**: Advanced operational elements (e.g., Δ, →, ≈)

Each symbol/glyph has immutable **True Text** that defines:
- **Primary meaning**: Core definition
- **Dimensional context**: Role in multi-dimensional space
- **Lattice role**: Function in lattice constructs
- **Operational semantics**: Behavior when executed

### Symbol Categories

1. **STATE** - Ternary state symbols (+1, 0, -1)
2. **GEOMETRIC** - Geometric constructs (Δ, Ø, Θ)
3. **OPERATIONAL** - Operations (→, ≈, ⊕, ⊗)
4. **LATTICE** - Lattice-specific glyphs (Ω, Φ)
5. **SEMANTIC** - Semantic markers (::, |)
6. **COMPOSITE** - Composite constructs (λ, Σ)

## Complete Symbol Reference

### Ternary State Symbols

| Symbol | Name | Encoding | Description |
|--------|------|----------|-------------|
| +1 | Expansion | 1 | Positive expansion state, being, truth assertion |
| 0 | Reconciliation | 0 | Neutral reconciliation, Elpis condition, throat state |
| -1 | Collapse | -1 | Negative collapse state, non-being, contraction |

### Geometric Glyphs

| Symbol | Name | Chainable | Description |
|--------|------|-----------|-------------|
| Δ | Delta | ✓ | Change operator, difference, delta transformation |
| Ø | Empty Set | ✗ | Null state, empty construct, void reference |
| Θ | Theta | ✓ | Angular parameter, rotation, cyclic phase |

### Operational Glyphs

| Symbol | Name | Chainable | Description |
|--------|------|-----------|-------------|
| → | Arrow/Implication | ✓ | Directional flow, implication, state transition |
| ≈ | Approximation | ✓ | Approximate equality, fuzzy match |
| ⊕ | XOR/Direct Sum | ✓ | Exclusive OR, direct sum, symmetric difference |
| ⊗ | Tensor Product | ✓ | Tensor product, cross product, outer product |

### Lattice-Specific Glyphs

| Symbol | Name | Description |
|--------|------|-------------|
| Ω | Omega/Omega-Hat | Möbius kernel operator, sacred constant (717) |
| Φ | Phi/Golden Ratio | Golden ratio (1.618...), geometric proportion |

### Semantic Markers

| Symbol | Name | Chainable | Description |
|--------|------|-----------|-------------|
| :: | Scope Separator | ✓ | Scope separator, namespace delimiter |
| \| | Pipe/Separator | ✓ | Separator for hash chains, logical OR |

### Composite Constructs

| Symbol | Name | Description |
|--------|------|-------------|
| λ | Lambda | Tuning parameter, lambda function, eigenvalue |
| Σ | Sigma | Summation operator, ternary state space |

## Usage Examples

### Working with Symbols

```python
from ggccd import get_symbol, get_glyph, list_all_symbols

# Get a symbol by character
delta = get_symbol("Δ")
print(delta.name)  # "Delta"
print(delta.true_text.primary)  # "Change operator, difference, delta transformation"

# Get a symbol by name
arrow = get_glyph("Arrow/Implication")
print(arrow.symbol)  # "→"
print(arrow.chainable)  # True

# List all available symbols
all_symbols = list_all_symbols()
for glyph, name in all_symbols.items():
    print(f"{glyph}: {name}")
```

### Creating Composite Statements

```python
from ggccd import CompositeStatement, ConstructType, encode_construct

# Simple statement
statement = CompositeStatement(
    symbols=["Δ", "→", "+1"],
    construct_type=ConstructType.CHAIN,
    context="state_validation"
)
print(statement)  # "Δ → +1 :: state_validation"

# Validate chainability
is_valid = statement.validate_chainability()  # True

# Encode to string
encoded = encode_construct(statement)
```

### Building Lattice Constructs

```python
from ggccd import LatticeConstruct, LatticeNode

# Create a lattice
lattice = LatticeConstruct(dimensions=3, name="test_lattice")

# Add nodes
node1 = LatticeNode(symbol="+1", position=(0.0, 0.0, 0.0), state_value=1)
node2 = LatticeNode(symbol="0", position=(1.0, 0.0, 0.0), state_value=0)
node3 = LatticeNode(symbol="-1", position=(0.0, 1.0, 0.0), state_value=-1)

lattice.add_node(node1)
lattice.add_node(node2)
lattice.add_node(node3)

# Connect nodes
lattice.connect_nodes(node1.node_id, node2.node_id)
lattice.connect_nodes(node2.node_id, node3.node_id)

# Query nodes
expansion_nodes = lattice.get_nodes_by_symbol("+1")
print(f"Expansion nodes: {len(expansion_nodes)}")
```

### Ternary State Lattices

```python
from ggccd import create_ternary_lattice

# Create a ternary lattice (optimized for Ouroboros)
lattice = create_ternary_lattice(
    expansion_positions=[(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
    reconciliation_positions=[(0.5, 0.5, 0.0)],
    collapse_positions=[(-1.0, 0.0, 0.0), (0.0, -1.0, 0.0)],
    dimensions=3,
    name="ouroboros_ternary_lattice"
)

print(f"Total nodes: {len(lattice.nodes)}")
print(f"Expansion nodes: {len(lattice.get_nodes_by_symbol('+1'))}")
print(f"Reconciliation nodes: {len(lattice.get_nodes_by_symbol('0'))}")
print(f"Collapse nodes: {len(lattice.get_nodes_by_symbol('-1'))}")
```

### Operation Chaining

```python
from ggccd import apply_operation_chain

# Start with a base statement
base = CompositeStatement(
    symbols=["Δ"],
    construct_type=ConstructType.SIMPLE,
    context="delta_operation"
)

# Chain operations (only chainable symbols allowed)
operations = ["→", "≈", "Θ"]
chained = apply_operation_chain(base, operations)

print(chained)  # "Δ → ≈ Θ :: delta_operation"
```

### Deployment Protocols

```python
from ggccd import DeploymentProtocol, create_ternary_lattice

# Create a lattice
lattice = create_ternary_lattice(
    expansion_positions=[(1.0, 0.0, 0.0)],
    reconciliation_positions=[(0.0, 0.0, 0.0)],
    collapse_positions=[(-1.0, 0.0, 0.0)],
    dimensions=3,
    name="protocol_lattice"
)

# Create deployment protocol
protocol = DeploymentProtocol(
    construct=lattice,
    execution_order=[node.node_id for node in lattice.nodes],
    validation_rules=["validate_ternary_states", "check_connectivity"],
    deployment_context={"mode": "production", "timeout": 717}
)

# Validate protocol
is_valid, errors = protocol.validate()
print(f"Protocol valid: {is_valid}")

# Execute steps
for i in range(len(protocol.execution_order)):
    step = protocol.execute_step(i)
    print(f"Step {i}: {step}")
```

### Extending Lattices

```python
from ggccd import extend_lattice, create_ternary_lattice

# Create base lattice
base = create_ternary_lattice(
    expansion_positions=[(1.0, 0.0, 0.0)],
    reconciliation_positions=[(0.0, 0.0, 0.0)],
    collapse_positions=[(-1.0, 0.0, 0.0)],
    dimensions=3,
    name="base"
)

# Create extension
extension = create_ternary_lattice(
    expansion_positions=[(0.0, 1.0, 0.0)],
    reconciliation_positions=[(0.0, 0.5, 0.0)],
    collapse_positions=[(0.0, -1.0, 0.0)],
    dimensions=3,
    name="extension"
)

# Extend lattice (merge strategies: "append", "merge", "overlay")
extended = extend_lattice(base, extension, merge_strategy="append")
print(f"Extended lattice has {len(extended.nodes)} nodes")
```

## Integration with Ouroboros

GGCCD integrates seamlessly with the Ouroboros processor:

```python
from ouroboros_processor import OuroborosVirtualProcessor
from ggccd import create_ternary_lattice, CompositeStatement, ConstructType

# Create processor
processor = OuroborosVirtualProcessor(radius=1.0, lambda_=0.3, threshold=0.4)

# Perform delta check
V_expected = [0.4, 0.2, 0.4]
V_observed = [0.35, 0.25, 0.4]
result = processor.delta_check(V_expected, V_observed)

# Create GGCCD statement representing the result
statement = CompositeStatement(
    symbols=["Δ", "→", "+1" if result["verdict"] == "PASS" else "-1"],
    construct_type=ConstructType.CHAIN,
    context=f"delta_check_result_{result['verdict'].lower()}"
)

print(statement)  # "Δ → +1 :: delta_check_result_pass"

# Create lattice representing ternary processor state
lattice = create_ternary_lattice(
    expansion_positions=[(processor.R, 0.0, 0.0)],
    reconciliation_positions=[(processor.R / 2, 0.0, 0.0)],
    collapse_positions=[(-processor.R, 0.0, 0.0)],
    dimensions=3,
    name="processor_state_lattice"
)
```

## Advanced Topics

### Custom Symbol Categories

You can filter symbols by category:

```python
from ggccd import get_symbols_by_category, SymbolCategory

# Get all operational glyphs
operational = get_symbols_by_category(SymbolCategory.OPERATIONAL)
for symbol in operational:
    print(f"{symbol.symbol}: {symbol.name}")
```

### Encoding and Decoding

```python
from ggccd import encode_construct, decode_construct, ConstructType
import json

# Encode composite statement
statement = CompositeStatement(symbols=["Δ", "→", "+1"], 
                              construct_type=ConstructType.CHAIN,
                              context="test")
encoded = encode_construct(statement)

# Decode back
decoded = decode_construct(encoded, ConstructType.CHAIN)
print(decoded)

# Encode lattice (produces JSON)
lattice = create_ternary_lattice(...)
encoded_json = encode_construct(lattice)
lattice_dict = json.loads(encoded_json)

# Decode lattice
decoded_lattice = decode_construct(encoded_json, ConstructType.LATTICE)
```

## Best Practices

1. **Use True Text**: Always consult symbol True Text for accurate operational semantics
2. **Validate Chainability**: Check `validate_chainability()` before executing chain constructs
3. **Dimension Matching**: Ensure lattice node positions match lattice dimensions
4. **Context Annotation**: Always provide meaningful context for composite statements
5. **Ternary States**: Use `create_ternary_lattice()` for Ouroboros-compatible lattices
6. **Protocol Validation**: Always validate deployment protocols before execution

## See Also

- `examples/ggccd_examples.py` - Comprehensive usage examples
- `rosetta/README.md` - Rosetta Translator for LOL:D compression
- `MASTERSTACK_KERNEL_v2.0.kernel` - Kernel specification with ternary semantics
- `specs/MASTER_EPISTEMIC_SPEC_v1.0.md` - Epistemic framework specification
