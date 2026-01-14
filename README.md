Ouroboros

A repository for geometry and visualization experiments, featuring the **OuroborosVirtualProcessor** — a virtual processor that emulates ternary cycles and geodesic flows on toroidal manifolds.

## Features

### Core Functionality
- **Ternary cycle simulation**: +1 expansion, 0 reconciliation, -1 collapse on torus
- **Geodesic flow computation**: Parametric horn torus with cusp analysis
- **Delta-check validation**: Ternary Delta-check with torus curvature penalty
- **Event loop integration**: Lightweight overlay for fabric runtimes (e.g., Elpis)

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

## Dependencies

- **Core**: Python 3.7+ (stdlib only for basic functionality)
- **Extended features**: numpy, scipy, networkx
- **Visualization**: matplotlib

## Project Status

**Current Phase:** Round 3 Complete — Equilibrium Sustained  
**Operational Mode:** Presence without Pressure

The SYMCHAOS CRUCIBLE Round 3 has been successfully concluded and sealed. The system is in meditative equilibrium with all objectives achieved. See [SYMCHAOS_CRUCIBLE_ROUND3_SEAL.md](SYMCHAOS_CRUCIBLE_ROUND3_SEAL.md) for the formal completion documentation.

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

