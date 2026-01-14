Ouroboros

A repository for geometry and visualization experiments, featuring the **OuroborosVirtualProcessor** — a virtual processor that emulates ternary cycles and geodesic flows on toroidal manifolds.

## Features

### Core Functionality
- **Ternary cycle simulation**: +1 expansion, 0 reconciliation, -1 collapse on torus
- **Geodesic flow computation**: Parametric horn torus with cusp analysis
- **Delta-check validation**: Ternary Delta-check with torus curvature penalty
- **Event loop integration**: Lightweight overlay for fabric runtimes (e.g., Elpis)

### GGCCD Crucible Framework
The **Global Geometric Construct Compression Dictionary (GGCCD)** framework provides a holistic lexicon system for encoding multi-dimensional states:

- **Immutable True Text Lexicon**: Symbols, glyphs, and their explanations organized into a comprehensive lexicon
- **Composite Statements**: Structured statements combining symbols with context and metadata
- **Lattice Constructs**: Multi-dimensional lattice structures with nodes and relationships
- **Deployment Protocols**: Protocols for deploying and executing GGCCD constructs
- **Ternary State Support**: Native support for ternary states (+1, 0, -1) and transitions
- **Advanced Glyphs**: Δ (Delta), Ø (Empty), Θ (Theta), → (Arrow), ≈ (Approximation), ⊕ (XOR), ⊗ (Tensor), Ω (Omega), Φ (Phi), and more

### Rosetta Translator Prototype (LOL:D → LOL:D.zip)
The **Rosetta Translator** provides complete reversible compression/decompression for LOL:D (Language of Lattice: Dimensional) symbolic-text constructs:

- **Lossless Compression**: Zlib-based compact encoding with lossless text preservation
- **Symbol Mapping**: Extended symbol map supporting GGCCD lattice glyphs and operational chaining
- **Direct Text Encoding**: Plain text embedded directly in compressed stream
- **Relational Integrity**: Maintains traversal relationships in large-scale constructs
- **File Format**: .lold.zip format with versioning, checksums, and metadata
- **Roundtrip Validation**: Built-in validation for compression/decompression integrity

### Extended Features
The processor includes advanced mathematical extensions when `numpy`, `scipy`, and `networkx` are installed:

- **Zeta-seeded ergotropy calculations**: Quantum-inspired extractable work analysis using Riemann zeta function
- **Discretized Möbius kernel (Ω̂ operator)**: Number-theoretic transformations on the torus using the Möbius function
- **Modular symmetry via dr_n mod 9**: Cyclic symmetries mapping to ternary states
- **Ramanujan τ couplings**: Deep number-theoretic coupling via modular discriminant coefficients
- **Symmetry graph construction**: NetworkX-based visualization of modular relationships

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from ouroboros_processor import OuroborosVirtualProcessor

# Create processor instance
processor = OuroborosVirtualProcessor(radius=1.0, lambda_=0.3, threshold=0.4)

# Perform delta check
V_expected = [0.4, 0.2, 0.4]
V_observed = [0.35, 0.25, 0.4]
result = processor.delta_check(V_expected, V_observed)
print(result)  # {'delta': 0.123, 'verdict': 'PASS'}
```

### Extended Features

```python
from ouroboros_processor import create_elpis_processor

# Create processor with zeta seed
processor = create_elpis_processor({"zeta_seed": 0.618, "radius": 1.0})

# Compute zeta-seeded ergotropy
ergotropy = processor.zeta_ergotropy(s=2.0)

# Apply Möbius kernel
kernel = processor.mobius_kernel(n=5, discretization=100)

# Check modular symmetry
mod_class = processor.modular_symmetry(42)  # Returns 42 mod 9 = 6

# Compute Ramanujan tau
tau = processor.ramanujan_tau(7)

# Extended delta check with tau coupling
result = processor.extended_delta_check(V_expected, V_observed, use_tau=True)

# Construct symmetry graph
graph = processor.construct_symmetry_graph(max_nodes=9)
```

### Integration with Elpis Overlay

```python
from overlays.elpis_overlay import register_elpis_overlay

# Register with fabric
overlay = register_elpis_overlay(fabric, name="ouroboros", config={"zeta_seed": 0.5})
overlay.start(poll_interval=1.0)
```

### GGCCD Framework Usage

```python
from ggccd import (
    CompositeStatement, LatticeConstruct, ConstructType,
    create_ternary_lattice, get_symbol
)

# Work with symbols
delta = get_symbol("Δ")
print(delta.true_text.primary)  # "Change operator, difference, delta transformation"

# Create composite statements
statement = CompositeStatement(
    symbols=["Δ", "→", "+1"],
    construct_type=ConstructType.CHAIN,
    context="state_validation"
)
print(statement)  # "Δ → +1 :: state_validation"

# Create ternary lattice
lattice = create_ternary_lattice(
    expansion_positions=[(1.0, 0.0, 0.0)],
    reconciliation_positions=[(0.0, 0.0, 0.0)],
    collapse_positions=[(-1.0, 0.0, 0.0)],
    dimensions=3,
    name="ouroboros_lattice"
)
print(f"Lattice nodes: {len(lattice.nodes)}")
```

### Rosetta Translator Usage

```python
from rosetta import (
    RosettaTranslator, validate_roundtrip,
    save_lold_zip, load_lold_zip
)

# Compress LOL:D constructs
translator = RosettaTranslator(compression_level=6)
lold_construct = "Δ(V_exp, V_obs) → +1 :: validated_state"
compressed = translator.compress(lold_construct)

print(f"Original: {compressed.original_size} bytes")
print(f"Compressed: {compressed.compressed_size} bytes")
print(f"Ratio: {compressed.compression_ratio():.2%}")

# Decompress
decompressed = translator.decompress(compressed)
print(f"Match: {lold_construct == decompressed}")

# Save to file
save_lold_zip(lold_construct, "construct.lold.zip")

# Load from file
loaded = load_lold_zip("construct.lold.zip")

# Validate roundtrip
success, message, ratio = validate_roundtrip(lold_construct)
print(message)
```

See the `examples/` directory for comprehensive usage examples:
- `examples/ggccd_examples.py` - GGCCD framework demonstrations
- `examples/rosetta_examples.py` - Rosetta translator demonstrations

## Dependencies

- **Core**: Python 3.7+ (stdlib only for basic functionality)
- **Extended features**: numpy, scipy, networkx
- **Visualization**: matplotlib

License
-------
This project is licensed under the MIT License — see the LICENSE file for details.

## Data & Empirical Manuscript

The OUROBOROS_MANUSCRIPT_DATA.md file is a data- and provenance-first manuscript documenting the digital artifacts and empirical procedures for the Ouroboros Manifold project. It contains:
- Executive summary
- Parametric geometry and plotting equations (tangential throat condition r = R/2)
- Geodesic integrator ODEs and curvature analysis
- Ternary→binary bridge summary and canonical hashing recipe
- Empirical test plans (deterministic hashing, geodesic convergence, adjudication SLAs)
- Provenance: commit SHAs and artifact inventory

Find the full manuscript here: OUROBOROS_MANUSCRIPT_DATA.md

