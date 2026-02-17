# 🌐 UTe₂ Hybrid AI-Powered Simulation System

## Overview

The **UTe₂ Hybrid System** is a comprehensive, offline-first framework for simulating unconventional superconductivity in uranium ditelluride (UTe₂). It combines advanced physics simulations with AI-powered optimization and supports flexible execution modes from embedded devices to cloud computing.

### Key Features

✨ **Hybrid Execution Engine**
- Multiple execution modes: Offline, Local, Hybrid, and Cloud
- Automatic fallback to local execution when internet is unavailable
- Priority-based task queuing for efficient resource management
- Intelligent workload distribution

🤖 **AI-Powered Optimization**
- Offline-first AI advisor for parameter optimization
- Device-specific recommendations (Raspberry Pi, laptops, HPC clusters)
- Learning from simulation history for improved suggestions
- Pattern recognition for optimal solver strategies

⚡ **Advanced Physics Simulations**
- Bogoliubov-de Gennes (BdG) equation solver for superconductivity
- Spin-triplet pairing calculations for UTe₂
- Reentrant superconductivity modeling at high magnetic fields
- Phase diagram generation (Temperature-Field)
- Superconducting gap structure analysis

💾 **Intelligent Caching**
- Persistent local caching with compression
- Parameter-based hashing for fast lookups
- TTL (time-to-live) management
- Automatic size limit enforcement with LRU eviction

🎨 **Interactive Dashboard**
- Jupyter-based UI with real-time controls
- Interactive parameter sliders (temperature, magnetic field, k-grid)
- Mode selection (Offline/Local/Hybrid/Cloud)
- Live visualization with Plotly
- Connection status indicators
- AI suggestions panel

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   UTe₂ Hybrid System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐         ┌──────────────────┐       │
│  │ Jupyter Dashboard  │────────▶│  Hybrid Engine   │       │
│  │  (Interactive UI)  │         │   (Orchestrator) │       │
│  └────────────────────┘         └──────────────────┘       │
│                                           │                  │
│          ┌────────────────────────────────┼─────────┐       │
│          │                │               │         │       │
│          ▼                ▼               ▼         ▼       │
│  ┌──────────────┐ ┌────────────┐ ┌──────────┐ ┌──────┐    │
│  │ Simulation   │ │    Cache   │ │   AI     │ │Config│    │
│  │   Engine     │ │   System   │ │ Advisor  │ │Files │    │
│  │  (Physics)   │ │  (Storage) │ │ (ML)     │ │      │    │
│  └──────────────┘ └────────────┘ └──────────┘ └──────┘    │
│                                                              │
│  Modes: [Offline] [Local] [Hybrid] [Cloud]                 │
└─────────────────────────────────────────────────────────────┘
```

### Component Overview

1. **Hybrid Execution Engine** (`ute2_hybrid_engine.py`)
   - Central orchestrator for all simulations
   - Manages execution modes and task queuing
   - Coordinates between simulation, caching, and AI components

2. **Simulation Engine** (`ute2_simulation.py`)
   - Implements BdG equation solver
   - Handles UTe₂-specific physics (spin-triplet pairing)
   - Generates phase diagrams and gap structures

3. **Cache System** (`ute2_cache.py`)
   - Persistent storage for simulation results
   - Parameter-based hashing with SHA-256
   - Compression and TTL management

4. **AI Advisor** (`ute2_ai_advisor.py`)
   - Provides optimization recommendations
   - Device-specific parameter suggestions
   - Learning from simulation history

5. **Interactive Dashboard** (`ute2_dashboard.ipynb`)
   - Jupyter notebook with widget controls
   - Real-time visualization
   - AI suggestions interface

6. **Configuration**
   - `hybrid_config.yaml`: System-wide settings
   - `knowledge_base.json`: AI knowledge and device optimizations

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Jupyter Notebook/Lab

### Quick Install

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import yaml, numpy, scipy, plotly; print('✅ All dependencies installed')"
```

### Dependencies

Core requirements:
- `numpy>=1.21.0` - Numerical computing
- `scipy>=1.7.0` - Scientific computing and solvers
- `pyyaml>=6.0` - Configuration file parsing
- `plotly>=5.0.0` - Interactive visualization
- `jupyter>=1.0.0` - Notebook interface
- `ipywidgets>=8.0.0` - Interactive widgets

## Usage

### 1. Quick Start with Dashboard

The easiest way to use the system is through the interactive Jupyter dashboard:

```bash
# Launch Jupyter
jupyter notebook ute2_dashboard.ipynb

# Or use JupyterLab
jupyter lab ute2_dashboard.ipynb
```

Then run all cells to initialize the system and access the interactive controls.

### 2. Python API Usage

#### Basic Simulation

```python
import yaml
from ute2_hybrid_engine import HybridExecutionEngine

# Load configuration
with open('hybrid_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize engine
engine = HybridExecutionEngine(config)

# Set execution mode
engine.set_mode('local')  # offline, local, hybrid, or cloud

# Define simulation parameters
params = {
    'temperature_K': 0.5,
    'magnetic_field_T': 10.0,
    'k_grid_size': 32
}

# Submit and execute task
task_id = engine.submit_task(params, priority=1)
result = engine.execute_next_task()

# Check results
if result.success:
    print(f"✅ Simulation completed in {result.execution_time:.2f}s")
    print(f"Gap statistics: {result.result.gap_function.mean():.6f} eV")
else:
    print(f"❌ Simulation failed: {result.metadata.get('error')}")
```

#### Using AI Advisor

```python
from ute2_ai_advisor import AIAdvisor

# Initialize advisor
advisor = AIAdvisor(config)

# Get device-specific recommendations
recommendations = advisor.get_device_recommendations('laptop')
print(f"Recommended k-grid: {recommendations['recommended_k_grid']}")

# Get parameter suggestions
suggestions = advisor.suggest_parameters(
    temperature=0.5,
    magnetic_field=45.0,  # Reentrant region
    device_type='laptop'
)
print(f"Suggestions: {suggestions}")

# Get troubleshooting advice
solutions = advisor.get_troubleshooting_advice('convergence_failure')
for solution in solutions:
    print(f"  - {solution}")
```

#### Phase Diagram Generation

```python
from ute2_simulation import UTe2SimulationEngine

# Initialize simulation engine
sim_engine = UTe2SimulationEngine(config)

# Generate T-H phase diagram
phase_data = sim_engine.generate_phase_diagram(
    temperature_range=(0.1, 2.5),
    field_range=(0, 80),
    resolution=100
)

# Access phase information
temperatures = phase_data['temperature']
fields = phase_data['magnetic_field']
phases = phase_data['phase']  # 0=Normal, 1=SC, 2=Reentrant SC
```

## Execution Modes

### Offline Mode
**Best for**: Embedded devices, Raspberry Pi, edge computing

- Optimized for minimal resource usage
- Maximum k-grid size: 24 (configurable)
- Uses float32 precision
- No internet required
- Aggressive caching

```python
engine.set_mode('offline')
```

### Local Mode
**Best for**: Laptops, desktops, standard workstations

- Full local execution with standard resources
- Maximum k-grid size: 64 (default)
- Uses float64 precision
- No internet required
- Standard caching

```python
engine.set_mode('local')
```

### Hybrid Mode
**Best for**: Variable workloads, adaptive execution

- Automatically chooses between local and cloud
- Small tasks (k-grid < 100): execute locally
- Large tasks (k-grid ≥ 100): offload to cloud
- Automatic fallback to local if cloud unavailable
- Requires internet for cloud offloading

```python
engine.set_mode('hybrid')
```

### Cloud Mode
**Best for**: Intensive workloads, HPC requirements

- All computations offloaded to cloud
- Unlimited resources (cloud-dependent)
- Requires internet connection
- API key and endpoint configuration needed

```python
engine.set_mode('cloud')
# Note: Requires cloud endpoint configuration in hybrid_config.yaml
```

## Configuration

### System Configuration (`hybrid_config.yaml`)

The main configuration file controls all aspects of the system:

```yaml
execution:
  default_mode: "local"
  modes:
    offline:
      enabled: true
      max_grid_size: 24
    local:
      enabled: true
      max_grid_size: 64
    # ... other modes

ai_advisor:
  enabled: true
  offline_mode: true
  learning:
    enabled: true
    save_frequency: 10

cache:
  enabled: true
  storage_path: "./ute2_cache"
  max_size_mb: 500
  ttl_days: 30

# ... more settings
```

### Knowledge Base (`knowledge_base.json`)

Contains AI-learned patterns and device optimizations:

```json
{
  "device_optimizations": {
    "raspberry_pi": {
      "recommended_k_grid": 24,
      "tips": [
        "Use sparse matrix solvers",
        "Enable aggressive caching"
      ]
    }
  },
  "simulation_regions": {
    "reentrant": {
      "magnetic_field_range_T": [40, 65],
      "optimal_parameters": {
        "k_grid_size": 48,
        "convergence_threshold": 1e-7
      }
    }
  }
}
```

## Physics Background

### UTe₂ Material

Uranium ditelluride (UTe₂) is an unconventional superconductor with unique properties:

- **Critical Temperature**: Tc ≈ 1.6 K
- **Pairing Symmetry**: Spin-triplet (odd-parity)
- **Special Feature**: Reentrant superconductivity at high magnetic fields (40-65 T)
- **Crystal Structure**: Orthorhombic (Immm space group)

### Reentrant Superconductivity

A remarkable feature of UTe₂ is the reemergence of superconductivity at very high magnetic fields:

```
Normal SC │ Normal │ Reentrant SC │ Normal
          │        │              │
H:  0────20T─────40T────────────65T────→
```

The system accurately models this behavior using field-dependent pairing potentials.

### BdG Equations

The simulation solves the Bogoliubov-de Gennes equations self-consistently:

```
┌              ┐ ┌  u  ┐     ┌  u  ┐
│  H    Δ     │ │     │ = E │     │
│  Δ*  -H*    │ └  v  ┘     └  v  ┘
└              ┘
```

Where:
- H: Normal state Hamiltonian
- Δ: Pairing potential (spin-triplet for UTe₂)
- E: Quasiparticle energies

## Performance Tips

### For Raspberry Pi / Limited Devices

```python
# Use offline mode
engine.set_mode('offline')

# Reduce k-grid size
params = {
    'k_grid_size': 16,  # or 24
    'temperature_K': 0.5,
    'magnetic_field_T': 10.0
}

# Get AI recommendations
suggestions = advisor.get_device_recommendations('raspberry_pi')
```

### For Laptops / Desktops

```python
# Use local mode for best performance
engine.set_mode('local')

# Standard k-grid
params = {
    'k_grid_size': 32,  # or 48 for higher accuracy
    'temperature_K': 0.5,
    'magnetic_field_T': 50.0  # Reentrant region
}
```

### For HPC / Cloud

```python
# Use hybrid or cloud mode
engine.set_mode('hybrid')

# Large k-grid for high accuracy
params = {
    'k_grid_size': 128,
    'temperature_K': 0.3,
    'magnetic_field_T': 55.0
}
```

## Troubleshooting

### Common Issues

1. **Simulation doesn't converge**
   ```python
   # Get AI advice
   solutions = advisor.get_troubleshooting_advice('convergence_failure')
   
   # Common solutions:
   # - Reduce k_grid_size
   # - Increase max_iterations in config
   # - Check parameter validity
   ```

2. **Out of memory**
   ```python
   # Get AI advice
   solutions = advisor.get_troubleshooting_advice('memory_overflow')
   
   # Common solutions:
   # - Switch to sparse solver
   # - Reduce k_grid_size
   # - Use lower precision (float32)
   ```

3. **Cache issues**
   ```python
   # Clear cache
   engine.cache.clear()
   
   # Check cache stats
   stats = engine.cache.get_stats()
   print(stats)
   ```

## Testing

Basic tests are integrated into the modules. To run manual verification:

```python
# Test simulation engine
from ute2_simulation import UTe2SimulationEngine
import yaml

with open('hybrid_config.yaml') as f:
    config = yaml.safe_load(f)

engine = UTe2SimulationEngine(config)
result = engine.run_simulation({
    'temperature_K': 0.5,
    'magnetic_field_T': 0.0,
    'k_grid_size': 16
})
assert result.success, "Simulation should succeed"
print("✅ Simulation engine test passed")

# Test cache
from ute2_cache import SimulationCache
cache = SimulationCache(config)
cache.put({'test': 1}, 'test_result')
assert cache.get({'test': 1}) == 'test_result'
print("✅ Cache test passed")

# Test AI advisor
from ute2_ai_advisor import AIAdvisor
advisor = AIAdvisor(config)
suggestions = advisor.suggest_parameters(device_type='laptop')
assert 'k_grid_size' in suggestions
print("✅ AI advisor test passed")
```

## Example Workflows

### Workflow 1: Parameter Exploration

```python
# Explore temperature dependence
temperatures = [0.1, 0.5, 1.0, 1.5, 2.0]
results = []

for T in temperatures:
    task_id = engine.submit_task({
        'temperature_K': T,
        'magnetic_field_T': 10.0,
        'k_grid_size': 32
    })
    result = engine.execute_next_task()
    results.append((T, result))

# Analyze results
for T, res in results:
    if res.success:
        gap_mean = res.result.gap_function.mean()
        print(f"T={T}K: Gap={gap_mean:.6f} eV")
```

### Workflow 2: Reentrant Region Study

```python
# Study reentrant superconductivity
fields = range(0, 80, 5)  # 0 to 80 T in 5 T steps

for H in fields:
    task_id = engine.submit_task({
        'temperature_K': 0.5,
        'magnetic_field_T': float(H),
        'k_grid_size': 48  # Higher resolution for reentrant region
    }, priority=1 if 40 <= H <= 65 else 5)  # Prioritize reentrant region

# Execute all tasks
results = engine.execute_all_tasks()
print(f"Completed {len(results)} simulations")
```

## Contributing

Contributions are welcome! This system is designed to be extensible:

- Add new solver methods in `ute2_simulation.py`
- Enhance AI learning in `ute2_ai_advisor.py`
- Implement cloud backends in `ute2_hybrid_engine.py`
- Improve caching strategies in `ute2_cache.py`

## License

MIT License - See main repository LICENSE file

## Acknowledgments

- Physics model based on UTe₂ superconductivity research
- Hybrid execution framework inspired by edge-cloud computing
- AI advisor using machine learning best practices

## Support

For issues, questions, or contributions:
- Open an issue in the main Ouroboros repository
- Check the knowledge base for common solutions
- Use the AI advisor's troubleshooting feature

---

**Built with ❤️ for the superconductivity research community**

*"Bridging quantum physics and AI, from Raspberry Pi to the cloud"* 🌌
