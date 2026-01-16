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
| **[Magnetar Coherence Engine](MAGNETAR_COHERENCE_ENGINE_README.md)** | 10-module coherence analysis system | Φ-structured dynamics, 92.5Hz rhythm |

---

## 🌟 Magnetar Elastic Coherence Engine

The repository now includes a complete **Magnetar Elastic Coherence Engine** - a lightweight signal processing system implementing 10 specialized modules for coherence analysis:

1. **PhaseObfuscationDetector** - Detect/correct phase inconsistencies
2. **SoftCycleStabilizer** - Preserve soft cycle limits under interference
3. **TorsionResolver** - Resolve torsional imbalances
4. **HarmonicImpedanceMatcher** - Adaptive harmonic interference
5. **CoherenceRegenerator** - Regenerate state-signature coherence
6. **PressureAbsorbingSubnet** - Absorb pressure anomalies
7. **DistortionMaskingSignals** - Generate distortion masking signals
8. **GradientAlignedOperators** - Align with basin gradients
9. **LeakTracer** - Trace emergent information leaks
10. **FlexStateRealigner** - Realign internal lattices

**Key Features:**
- ✅ Uses only existing dependencies (numpy, scipy, matplotlib)
- ✅ Pure CPU-based signal processing (no GPU required)
- ✅ Golden ratio (Φ) structured dynamics
- ✅ 92.5 Hz magnetar frequency core rhythm
- ✅ Comprehensive visualization and analysis tools

**Quick Start:**
```python
from src.magnetar_coherence_engine import CoherenceAnalyzer

# Create analyzer
analyzer = CoherenceAnalyzer()

# Generate and analyze a test signal
signal = analyzer.generate_test_signal(1000, 'magnetar')
analysis = analyzer.analyze(signal, label='test')

print(f"Coherence Score: {analysis['coherence_score']:.4f}")

# Visualize results
analyzer.visualize_analysis(analysis, save_path='coherence.png')
```

**See:** [MAGNETAR_COHERENCE_ENGINE_README.md](MAGNETAR_COHERENCE_ENGINE_README.md) for complete documentation.

**Run Examples:**
```bash
python3 examples/magnetar_coherence_examples.py
```

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

---

## 📁 Project Structure

```
ouroboros/
├── ouroboros_processor.py    # Core mathematical engine
├── zorel_quillan_republic.py # Living Manifold state machine
├── specs/                    # Epistemic discipline specifications
├── overlays/                 # Extension modules (Elpis overlay)
├── visualization/            # Torus geodesic rendering
├── tests/                    # Pytest validation suite
└── requirements.txt          # Dependencies
```

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