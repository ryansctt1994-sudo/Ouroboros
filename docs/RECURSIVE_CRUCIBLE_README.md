# Recursive Crucible Core and Visualization GUI

## Overview

This update introduces two critical components to the Ouroboros repository:

### 1. Recursive Crucible Core (`agent_interface/recursive_crucible.py`)

A self-improving framework for analyzing, testing, and strengthening ECS-based agent code.

**Features:**
- **Multi-strategy weakness detection**
  - Static analysis (AST parsing)
  - Pattern matching (regex-based)
  - Evolutionary memory
  
- **Stress testing via boundary weakening**
  - Boundary injection testing
  - Overload testing
  - Synthetic edge cases
  
- **Automatic code strengthening**
  - Add validation
  - Add error handling
  - Add type checking
  - Optimize performance
  - Add logging
  - Refactoring suggestions
  
- **Validation oracles**
  - Configurable thresholds
  - Success/failure tracking
  - Score-based validation
  
- **Adaptive evolution**
  - Recursive strategy refinement
  - Multi-pass improvement cycles
  - Iteration tracking and history

**Usage:**

```python
from agent_interface.recursive_crucible import RecursiveCrucible

# Initialize crucible
crucible = RecursiveCrucible(max_iterations=5, validation_threshold=0.7)

# Analyze code
code = """
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
"""

# Run recursive improvement
results = crucible.run_recursive(code, "sample.py")

# Get summary
summary = crucible.get_summary()
print(f"Total Weaknesses: {summary['total_weaknesses']}")
print(f"Total Fixes: {summary['total_fixes']}")
print(f"Avg Score: {summary['average_validation_score']:.2f}")
```

### 2. GPU Vector Enhancement (`core/gpu_vector_enhancement.py`)

GPU-accelerated vector operations for ECS components, enabling high-performance computation.

**Features:**
- **Vector operations**
  - Addition, subtraction, multiplication
  - Dot products and cross products
  - Magnitude and normalization
  
- **Batch operations**
  - Process multiple entities simultaneously
  - GPU-accelerated when available
  - CPU fallback mode
  
- **ECS Bridge**
  - Seamless integration with ECS entities
  - Entity vector management
  - Interaction computation
  - Performance tracking

**Usage:**

```python
from core.gpu_vector_enhancement import ECSVectorBridge

# Initialize bridge (with GPU acceleration if available)
bridge = ECSVectorBridge(use_gpu=True)

# Register entities
bridge.register_entity_vector("entity_1", [1.0, 2.0, 3.0])
bridge.register_entity_vector("entity_2", [4.0, 5.0, 6.0])

# Compute interaction
interaction = bridge.compute_entity_interaction("entity_1", "entity_2")

# Batch update entities
entity_ids = ["entity_1", "entity_2"]
deltas = [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2]]
bridge.batch_update_entities(entity_ids, deltas)

# Get statistics
stats = bridge.get_stats()
```

### 3. Crucible Visualization GUI

Windows 8-inspired control panel for real-time monitoring and control.

**Components:**

- **`gui/crucible_tab.py`** - Dedicated visualization layer for recursive crucible monitoring
  - Iteration history tracking
  - Weakness details display
  - Validation progress monitoring
  - Fix logs and status
  
- **`gui/conductor_gui.py`** - Main control panel
  - System overview and metrics
  - Task processing interface
  - Crucible integration
  - Multi-tab interface
  - Logs and diagnostics

**Launch GUI:**

```bash
# Using the launcher script
./run_gui.sh

# Or directly with Python
python3 -m gui.conductor_gui
```

**Note:** The GUI requires tkinter, which should be included with most Python installations.

## Installation

### Basic Installation

```bash
# Clone the repository (if not already done)
git clone https://github.com/AIOSPANDORA/Ouroboros.git
cd Ouroboros

# No additional dependencies required for basic functionality
# The core modules work with pure Python
```

### Optional Dependencies

For enhanced functionality, install the GUI and GPU acceleration dependencies:

```bash
# Install GUI dependencies
pip install -r requirements_gui.txt

# For GPU acceleration (optional)
pip install jax jaxlib

# For improved vector operations
pip install numpy
```

## Testing

Run the comprehensive test suite:

```bash
# Test Recursive Crucible
python3 -m pytest tests/test_recursive_crucible.py -v

# Test GPU Vector Enhancement
python3 -m pytest tests/test_gpu_vector_enhancement.py -v

# Run all new tests
python3 -m pytest tests/test_recursive_crucible.py tests/test_gpu_vector_enhancement.py -v
```

## Examples

See `examples/recursive_crucible_integration.py` for a complete integration example:

```bash
python3 examples/recursive_crucible_integration.py
```

## Architecture

### Recursive Crucible Flow

```
┌──────────────────────────────────────────────────┐
│           Recursive Crucible Core                │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. ANALYZE                                      │
│     ├─ Static Analysis (AST)                     │
│     ├─ Pattern Matching (Regex)                  │
│     └─ Evolutionary Memory                       │
│                                                  │
│  2. TEST                                         │
│     ├─ Boundary Injection                        │
│     ├─ Stress Overload                          │
│     └─ Edge Case Generation                      │
│                                                  │
│  3. STRENGTHEN                                   │
│     ├─ Add Validation                            │
│     ├─ Add Error Handling                        │
│     ├─ Add Type Checking                         │
│     ├─ Optimize Performance                      │
│     └─ Add Logging                               │
│                                                  │
│  4. VALIDATE                                     │
│     ├─ Run Tests                                 │
│     ├─ Check Metrics                             │
│     └─ Score Improvements                        │
│                                                  │
│  5. ITERATE                                      │
│     └─ Repeat until convergence                  │
│                                                  │
└──────────────────────────────────────────────────┘
```

### GPU Vector Enhancement Architecture

```
┌──────────────────────────────────────────────────┐
│         GPU Vector Enhancement                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  ECS Vector Bridge                               │
│  ├─ Entity Vector Registry                       │
│  ├─ Interaction Computation                      │
│  └─ Batch Operations                             │
│                                                  │
│  GPU Vector Processor                            │
│  ├─ JAX Backend (GPU)                            │
│  ├─ NumPy Backend (CPU)                          │
│  └─ Pure Python Fallback                         │
│                                                  │
│  Operations                                      │
│  ├─ Vector Addition                              │
│  ├─ Scalar Multiplication                        │
│  ├─ Dot Product                                  │
│  ├─ Magnitude                                    │
│  ├─ Normalization                                │
│  └─ Batch Processing                             │
│                                                  │
└──────────────────────────────────────────────────┘
```

## Integration with Existing Systems

The Recursive Crucible and GPU Vector Enhancement modules integrate seamlessly with existing Ouroboros components:

- **EDEN ECS**: Analyze and strengthen ECS components and systems
- **Advanced Core**: GPU-accelerated operations for tensor computations
- **Fabric AI Core**: Self-improving agent architectures
- **Diagnostic System**: Enhanced code quality monitoring

## Future Enhancements

Planned improvements:

1. **LLM-Powered Analysis**
   - Deeper weakness detection using language models
   - Intelligent fix generation
   - Context-aware refactoring

2. **Distributed Testing**
   - Multi-node crucible execution
   - Parallel weakness detection
   - Distributed validation

3. **Advanced GPU Operations**
   - Matrix operations
   - Convolution support
   - Custom kernel generation

4. **Enhanced GUI**
   - Real-time code visualization
   - Interactive fix application
   - Performance profiling graphs

## License

See the main repository LICENSE file.

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting pull requests.

## Support

For issues or questions, please open an issue on the GitHub repository.
