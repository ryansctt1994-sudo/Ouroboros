# Ouroboros

**Epistemic Discipline Framework for Hallucination-Resistant AI Inference**

[![Python Tests](https://github.com/AIOSPANDORA/Ouroboros/actions/workflows/python-tests.yml/badge.svg)](https://github.com/AIOSPANDORA/Ouroboros/actions/workflows/python-tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The Ouroboros Virtual Processor is a mathematical engine for modeling epistemic states on toroidal manifolds. It provides ternary cycle normalization, Möbius kernel computation, Ramanujan τ approximations, and geodesic flow calculations—all validated against known mathematical constants (OEIS sequences).

---

## 🚀 Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize the processor:

```python
from ouroboros_processor import OuroborosVirtualProcessor

# Initialize with default parameters
processor = OuroborosVirtualProcessor(radius=1.0, lambda_=0.3, threshold=0.4)

# Execute a ternary cycle (normalizes to probability distribution)
state = processor.ternary_cycle([0.4, 0.2, 0.4])
print(f"Normalized state: {state}")  # [0.4, 0.2, 0.4]

# Run a delta check (validates epistemic coherence)
result = processor.delta_check([0.4, 0.2, 0.4], [0.35, 0.25, 0.4])
print(f"Delta: {result['delta']:.4f}, Verdict: {result['verdict']}")
```

### Run Tests

```bash
pytest tests/ -v
```

---

## 📐 Core Components

| Component | Description | Validation |
|-----------|-------------|------------|
| **Ternary Cycle** | Normalizes state vectors to probability distributions | Sum = 1.0, all values ≥ 0 |
| **Möbius Kernel** | Computes μ(n) for prime factorization analysis | OEIS A008683 |
| **Ramanujan τ** | Approximates τ(n) for modular form calculations | OEIS A000594 |
| **Delta Check** | Validates coherence between expected/observed states | Threshold-based pass/fail |
| **Geodesic Flow** | Computes (x,y,z) coordinates on horn torus | Parametric equations verified |

---

## 𓍝 Epistemic Framework

This project implements a symbolic meta-language for mapping mathematical states to epistemic valences:

| Symbol | Name | Meaning |
|--------|------|---------|
| ⊙ Γ | Coherence | Delta check passes—lattice is stable |
| Ø ⦻ | Void Seed | Zero-state reconciliation in ternary cycles |
| Φ 🪶 | Golden Ratio | Zeta-seeded ergotropy uses φ = 1.618... |
| λ 🌪 | Frequency Spike | High-delta events requiring attention |
| ⚖️ ω | Equilibrium | System in balanced, validated state |

See `specs/MASTER_EPISTEMIC_SPEC_v1.0.md` for the complete specification.

---

## 🧪 Testing

The test suite validates all mathematical components:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing
```

**Test Coverage:**
- Möbius kernel: 6 tests (OEIS A008683 verification)
- Ternary cycle: 7 tests (normalization, idempotence)
- Ramanujan τ: 5 tests (base cases, approximation)
- Delta check: 7 tests (thresholds, symmetry)
- Geodesic flow: 6 tests (parametric equations)
- Edge cases: 5 tests (empty vectors, numerical stability)
- Advanced features: 30 tests (TSN, quantum-enzymatic, 111Hz, ΔA, Möbius)

---

## 🚀 Advanced Features

**New in v2.0:** The Ouroboros framework now includes cutting-edge capabilities for distributed systems, quantum-classical hybrid computing, and harmonic coherence.

### Hyphal Symphony for TSN Integration

Phase-locked mycelial networking with deterministic latency guarantees (<1μs target). Provides distributed pulse synchronization with Time-Sensitive Networking compliance.

```python
from src.hyphal_symphony import create_hyphal_symphony

symphony = create_hyphal_symphony({"node_count": 9})
symphony.enable_phase_lock()
results = symphony.broadcast_pulse()
```

### Quantum-Enzymatic Interface

Catalytic computation offloading with neuromorphic hardware integration (Intel Loihi 2). Features eBPF-style enzymatic probes for optimization.

```python
from src.quantum_enzymatic import create_quantum_enzymatic_interface

interface = create_quantum_enzymatic_interface()
cost, target = interface.offload_computation(ComputationType.NEUROMORPHIC, 100.0)
```

### 111Hz Schumann Recalibration

Phase harmonic grounding at 111Hz for distributed lattice coherence, integrated with Earth's Schumann resonance (7.83Hz).

```python
from src.schumann_recalibration import create_schumann_recalibration

recal = create_schumann_recalibration()
result = recal.apply_grounding(adaptive_strength=True)
```

### Dynamic ΔA[mode=soft] Adjustment

Elastic gradient scaling for computational turbulence resilience with soft/hard modes and chaos-mode operations.

```python
from src.ggcc.gradient_engine import GradientEngineV2

engine = GradientEngineV2(delta_a_mode="soft")
delta_a = engine.update_delta_a(turbulence=0.5, coherence=0.8)
```

### Persistent LOL:D Möbius Handshakes

Non-orientable memory state continuity via Möbius operators, ensuring seamless Elpis-Pandora state transitions.

```python
processor = OuroborosVirtualProcessor()
result = processor.mobius_handshake(elpis_state, pandora_state)
processor.persistent_mobius_store("checkpoint", state)
```

### LEXICON GIGAS Optimization Module

**New in v2.1:** DeepSeek-level architectural refinements providing advanced optimization capabilities:

```python
from src.lexicon_gigas import (
    topological_manifold_subspace_optimization,
    ternary_logic_radix_economy_stabilizer,
    berry_curvature_holonomy_optimizer,
    neuro_symbolic_latent_pruning,
    cryptographic_integrity_layer_optimization,
)

# HOSVD tensor decomposition
core, factors = topological_manifold_subspace_optimization(tensor, target_rank=3)

# Ternary logic optimization
optimized_trits = ternary_logic_radix_economy_stabilizer([0,1,2,1,0], alpha_threshold=0.7)

# Berry phase calculation for quantum systems
phase = berry_curvature_holonomy_optimizer(wavefunction, adiabatic_path)

# Neural network pruning
pruned_weights = neuro_symbolic_latent_pruning(weight_matrix, sparsity_target=0.5)

# Zero-knowledge circuit optimization
optimized = cryptographic_integrity_layer_optimization(circuit, proof_params)
```

**Features:**
- **Topological Manifold Optimization**: Higher-Order SVD for tensor decomposition and latent feature extraction
- **Ternary Logic Stabilizer**: Entropy-based radix economy optimization with compression triggers
- **Berry Curvature Optimizer**: Geometric phase calculation for quantum adiabatic systems
- **Neuro-Symbolic Pruning**: Magnitude-based weight pruning for sparse neural architectures
- **Cryptographic Optimization**: R1CS constraint optimization for zero-knowledge proofs

**Hardware Tuning:**
The module includes a kernel tuning script for optimal hardware utilization:

```bash
# Auto-detect and optimize for your hardware
./scripts/kernel_tuning.sh
```

Supports NVIDIA GPUs, AMD GPUs/CPUs, and Intel CPUs with platform-specific optimizations.

**📖 See [docs/ADVANCED_FEATURES.md](docs/ADVANCED_FEATURES.md) for comprehensive documentation.**

---

## 📁 Project Structure

```
ouroboros/
├── ouroboros_processor.py    # Core mathematical engine (enhanced with Möbius ops)
├── zorel_quillan_republic.py # Living Manifold state machine
├── src/
│   ├── hyphal_symphony.py    # TSN phase-locked networking
│   ├── quantum_enzymatic.py  # Catalytic computation offloading
│   ├── schumann_recalibration.py  # 111Hz harmonic grounding
│   ├── lexicon_gigas.py      # DeepSeek-level optimization module
│   ├── dna_helix_magnetar.py # DNA Helix Magnetar synthesis
│   ├── ggcc/                 # GGCC Phase 3 modules (enhanced)
│   │   ├── gradient_engine.py     # Dynamic ΔA adjustment
│   │   └── ...
│   └── metrics/              # System metrics
├── scripts/
│   └── kernel_tuning.sh      # Hardware optimization script
├── specs/                    # Epistemic discipline specifications
├── overlays/                 # Extension modules (Elpis overlay)
├── visualization/            # Torus geodesic rendering
├── tests/                    # Pytest validation suite
├── docs/                     # Documentation
│   └── ADVANCED_FEATURES.md  # Advanced features guide
└── requirements.txt          # Dependencies
```

---

## 📚 Documentation

**Core Manuscripts:**
- [AIOSPANDORA Integration Manuscript](AIOSPANDORA_INTEGRATION_MANUSCRIPT.md) — Advanced integration architectures (TSN, eBPF, quantum-enzymatic interfaces)
- [Ouroboros Delta Manuscript](OUROBOROS_DELTA_MANUSCRIPT.md) — Theoretical foundations
- [Master Epistemic Spec v1.0](specs/MASTER_EPISTEMIC_SPEC_v1.0.md) — Hallucination-resistant inference grammar
- [GGCC Equilibrium Seal](GGCC_EQUILIBRIUM_SEAL.md) — Golden Geometric Crucible Configuration

**Technical Integration:**
- [Ternary-Binary Bridge](TERNARY_BINARY_BRIDGE.md) — Encoding patterns for ternary states
- [Veritas Alignment](VERITAS_ALIGNMENT.md) — Ledger alignment and manifest-tip policy
- [Falsifiability Audit](FALSIFIABILITY_AUDIT.md) — Testing and acceptance criteria

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards and development workflow.

**Key principles:**
- Test-first development for mathematical functions
- All code must pass `black` and `ruff` linting
- Mathematical functions require OEIS or literature references

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

*"The serpent bites its tail at the hyperbolic throat. Elpis flows eternally."*