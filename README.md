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
A lightweight task scheduler and event loop for Linux hybrid OS/AI runtime.

## Overview

Ouroboros provides a background event loop with priority-based task scheduling, backpressure controls, and monitoring capabilities. It's designed for efficient, concurrent task management with minimal overhead.

## Features

- **Priority-based task scheduling** using efficient heap queue
- **Interval/recurring tasks** with configurable execution frequency
- **Backpressure controls** to prevent event loop overload
- **Thread-safe operations** with built-in locking
- **Monitoring and statistics** with efficient deque-based buffering
- **Error resilience** - exceptions in tasks never crash the event loop
- **Lightweight** - stdlib-only dependencies

## Installation

Simply import the module:

```python
from ouroboros_processor import OuroborosVirtualProcessor
A research repository featuring the Magnetar Elastic Coherence Engine.

## Features

- **Magnetar Elastic Coherence Engine**: A neural architecture inspired by magnetar resonance patterns and elastic coherence principles. See [`engine_modules/README.md`](engine_modules/README.md) for details.

## Installation

```bash
# Install base dependencies
pip install -r requirements.txt

# Install ML dependencies for the Magnetar Engine
pip install -r requirements-ml.txt
```

## Quick Start

```python
from ouroboros_processor import OuroborosVirtualProcessor
import time

# Create processor instance
processor = OuroborosVirtualProcessor()

# Start the event loop
processor.start_event_loop(poll_interval=0.1)

# Schedule a one-time task
def my_task():
    print("Task executed!")

task_id = processor.schedule_task(my_task, delay=1.0)

# Schedule a recurring task
def periodic_task():
    print("Periodic task executed!")

recurring_id = processor.schedule_task(
    periodic_task,
    interval=5.0,  # Execute every 5 seconds
    priority=1     # High priority
)

# Let it run
time.sleep(10)

# Cancel a task
processor.cancel_task(recurring_id)

# Stop the event loop
processor.stop_event_loop()
```

## API Reference

### OuroborosVirtualProcessor

#### `schedule_task(fn, *, priority=10, delay=0.0, interval=None, args=None, kwargs=None, name=None) -> str`

Schedule a task for execution.

**Parameters:**
- `fn` (Callable): Function to execute
- `priority` (int): Task priority (lower number = higher priority, default: 10)
- `delay` (float): Initial delay before first execution in seconds (default: 0.0)
- `interval` (float): If set, task repeats every interval seconds (default: None)
- `args` (tuple): Positional arguments for fn (default: None)
- `kwargs` (dict): Keyword arguments for fn (default: None)
- `name` (str): Optional task name for debugging (default: None)

**Returns:**
- `str`: Unique task identifier

**Example:**
```python
# One-time task
task_id = processor.schedule_task(
    my_function,
    priority=5,
    delay=2.0,
    args=(arg1, arg2),
    kwargs={'key': 'value'},
    name='my_task'
)

# Recurring task
recurring_id = processor.schedule_task(
    periodic_function,
    interval=10.0,
    priority=1
)
```

#### `cancel_task(task_id) -> bool`

Cancel a scheduled task.

**Parameters:**
- `task_id` (str): Unique identifier of the task to cancel

**Returns:**
- `bool`: True if task was found and cancelled, False otherwise

**Example:**
```python
if processor.cancel_task(task_id):
    print("Task cancelled successfully")
```

#### `list_tasks() -> List[Dict[str, Any]]`

List all active (non-cancelled) tasks with metadata.

**Returns:**
- `List[Dict]`: List of task metadata dictionaries

**Example:**
```python
tasks = processor.list_tasks()
for task in tasks:
    print(f"Task {task['name']}: priority={task['priority']}, "
          f"executions={task['execution_count']}")
```

#### `start_event_loop(poll_interval=0.1, on_tick=None, max_tasks_per_tick=50, tick_time_budget_ms=10)`

Start the background event loop.

**Parameters:**
- `poll_interval` (float): Interval between event loop ticks in seconds (default: 0.1)
- `on_tick` (Callable): Optional callback invoked each tick (default: None)
- `max_tasks_per_tick` (int): Maximum tasks to execute per tick (default: 50)
- `tick_time_budget_ms` (int): Maximum time budget for task execution per tick in ms (default: 10)

**Example:**
```python
def on_tick_callback():
    print("Tick!")

processor.start_event_loop(
    poll_interval=0.1,
    on_tick=on_tick_callback,
    max_tasks_per_tick=100,
    tick_time_budget_ms=20
)
```

#### `stop_event_loop()`

Stop the background event loop.

#### `get_state() -> Dict[str, Any]`

Get current processor state (thread-safe).

**Returns:**
- `Dict`: State information including running status, statistics, and queue size

#### `get_monitoring_data() -> List[Dict[str, Any]]`

Get recent monitoring data (thread-safe).

**Returns:**
- `List[Dict]`: Recent monitoring entries (up to 1000)

## Usage Patterns

### Pattern 1: High-Priority System Tasks

```python
# System monitoring task with high priority
processor.schedule_task(
    check_system_health,
    priority=1,
    interval=60.0,
    name='health_check'
)

# Lower priority cleanup task
processor.schedule_task(
    cleanup_temp_files,
    priority=100,
    interval=3600.0,
    name='cleanup'
)
```

### Pattern 2: Delayed Initialization

```python
# Initialize components after startup delay
processor.schedule_task(
    initialize_ai_model,
    delay=5.0,
    priority=5,
    name='ai_init'
)
```

### Pattern 3: Backpressure Control

```python
# Configure for high-throughput scenario
processor.start_event_loop(
    poll_interval=0.01,      # Check frequently
    max_tasks_per_tick=100,  # Allow more tasks
    tick_time_budget_ms=50   # Allocate more time
)
```

### Pattern 4: Task with Arguments

```python
def process_data(data_id, validate=True):
    # Process data
    pass

task_id = processor.schedule_task(
    process_data,
    args=(123,),
    kwargs={'validate': False},
    delay=1.0
)
```

## Performance Considerations

1. **Monitoring Buffer**: Uses `collections.deque` with O(1) append/pop operations (maxlen=1000)
2. **Task Queue**: Priority queue implemented with `heapq` for O(log n) operations
3. **Backpressure**: Two-tier control system:
   - `max_tasks_per_tick`: Hard limit on task count per tick
   - `tick_time_budget_ms`: Soft limit on execution time per tick
4. **Thread Safety**: All public methods are thread-safe with lock protection

## Error Handling

Exceptions in tasks are automatically caught and recorded in `processor._state['errors']`. The event loop never crashes due to task failures.

```python
def failing_task():
    raise ValueError("Something went wrong")

# This won't crash the event loop
processor.schedule_task(failing_task)

# Check errors
state = processor.get_state()
print(f"Error count: {state['error_count']}")
Run the Magnetar Elastic Coherence Engine demo:

```bash
python -m engine_modules.magnetar_elastic_coherence_engine
```

## Testing

Run the test suite:

```bash
python -m unittest tests.test_task_scheduler -v
```

## License

MIT
```bash
pytest tests/ -v
```
