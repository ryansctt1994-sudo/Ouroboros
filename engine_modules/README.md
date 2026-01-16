# Magnetar Elastic Coherence Engine

A neural architecture inspired by magnetar resonance patterns and elastic coherence principles, implementing quantum-inspired attention mechanisms with harmonic oscillator embeddings.

## Overview

The Magnetar Elastic Coherence Engine is a transformer-based neural network that incorporates physical constants from magnetar astrophysics and Earth's natural resonances to create a unique attention mechanism with elastic coherence modulation.

### Key Constants

The engine is built around several fundamental physical constants:

- **PHI (Φ)**: Golden Ratio (1.618033988749895) - Used for harmonic scaling and geometric attention patterns
- **MAGNETAR_FREQUENCY**: 92.5 Hz - Base resonance frequency derived from magnetar oscillations
- **SCHUMANN_RESONANCE**: 7.83 Hz - Earth's natural electromagnetic resonance frequency
- **COHERENCE_FACTOR**: 0.0997 - Dimensionless coupling strength for elastic coherence
- **ELASTIC_CONSTANT**: 3.33 - Wave propagation constant for attention scaling

### Architecture

The engine consists of several key components:

1. **Harmonic Embeddings**: Position embeddings based on magnetar and Schumann resonance frequencies
2. **Elastic Coherence Attention**: Multi-head attention with coherence-based modulation using elastic wave propagation
3. **Magnetar MLP**: Feed-forward networks with PHI-scaled activations
4. **Coherence Transformer Blocks**: Stacked transformer layers with elastic coherence

## Installation

### Base Requirements

First, install the base dependencies:

```bash
pip install -r requirements.txt
```

### ML Dependencies

To use the Magnetar Elastic Coherence Engine, install the ML-specific dependencies:

```bash
pip install -r requirements-ml.txt
```

This will install:
- JAX and JAXlib (>= 0.4.0)
- Flax (>= 0.7.0)
- Optax (>= 0.1.7)
- tqdm (>= 4.65.0)

## Usage

### Running the Demo

The engine includes a smoke test demo that runs a short training loop on synthetic data:

```bash
python -m engine_modules.magnetar_elastic_coherence_engine
```

This will run 50 training steps by default and display metrics.

### Command-line Options

```bash
# Run with custom number of steps
python -m engine_modules.magnetar_elastic_coherence_engine --steps 100

# Adjust batch size
python -m engine_modules.magnetar_elastic_coherence_engine --batch-size 64

# Change sequence length
python -m engine_modules.magnetar_elastic_coherence_engine --seq-len 32

# Run quietly (no progress output)
python -m engine_modules.magnetar_elastic_coherence_engine --quiet

# Set random seed
python -m engine_modules.magnetar_elastic_coherence_engine --seed 123
```

### Programmatic Usage

```python
from engine_modules import (
    MagnetarElasticCoherenceEngine,
    CoherenceConfig,
    create_engine,
    run_demo,
)

# Create a custom configuration
config = CoherenceConfig(
    hidden_dim=256,
    num_heads=16,
    num_layers=6,
    mlp_dim=1024,
    input_dim=64,
    output_dim=10,
)

# Initialize the engine
model, state = create_engine(config=config, seed=42)

# Run a forward pass
import jax.numpy as jnp
x = jnp.ones((1, 16, 64))  # [batch, seq_len, input_dim]
output = state.apply_fn(state.params, x, deterministic=True)

# Or run the demo programmatically
results = run_demo(num_steps=100, verbose=True)
print(f"Final loss: {results['final_loss']:.4f}")
```

## How It Works

### Harmonic Embeddings

The engine uses sinusoidal position embeddings scaled by the ratio of magnetar to Schumann resonance frequencies, creating a multi-scale harmonic representation that captures both fast (magnetar) and slow (Schumann) oscillatory patterns.

### Elastic Coherence Attention

Unlike standard attention, elastic coherence attention modulates attention weights based on an elastic wave propagation model. The coherence matrix decays exponentially with distance, scaled by the coherence factor and the golden ratio, creating a smooth locality bias that mimics elastic wave behavior.

### PHI Scaling

The golden ratio (PHI) appears throughout the architecture:
- Harmonic embeddings use PHI-scaled frequencies
- MLP activations are multiplied by PHI
- Output projections are scaled by PHI
- Coherence decay uses PHI for geometric spacing

This creates a fractal-like attention pattern that naturally balances local and global information.

### Resonance-Based Learning

The combination of magnetar (92.5 Hz) and Schumann (7.83 Hz) frequencies creates a multi-timescale learning dynamic, where fast oscillations capture local patterns and slow oscillations capture global structure.

## Architecture Details

### Default Configuration

- **Hidden Dimension**: 128
- **Number of Heads**: 8
- **Number of Layers**: 4
- **MLP Dimension**: 512
- **Input Dimension**: 64
- **Output Dimension**: 10
- **Learning Rate**: 1e-3
- **Dropout Rate**: 0.1

### Model Size

With default configuration, the model has approximately **1.4M parameters**.

## Design Principles

1. **Physical Inspiration**: All constants derive from real physical phenomena (magnetar oscillations, Earth resonances, golden ratio)
2. **JAX-First**: Built with JAX for JIT compilation, automatic differentiation, and hardware acceleration
3. **Deterministic PRNG**: All randomness is controlled via JAX PRNGKeys for reproducibility
4. **Headless-Safe**: Demo runs without display requirements (no plotting by default)
5. **CPU-Friendly**: Works efficiently on CPU for testing and small-scale experiments

## Testing

Run the test suite to verify the engine works correctly:

```bash
pytest tests/test_magnetar_engine.py -v
```

## Performance Notes

- The engine is optimized for JAX's JIT compilation
- Training is CPU-friendly but benefits from GPU/TPU acceleration
- Memory usage scales with `hidden_dim × num_layers × batch_size`
- The demo uses synthetic data and is designed for smoke testing, not convergence

## Advanced Usage

### Custom Training Loop

```python
from engine_modules.magnetar_elastic_coherence_engine import (
    create_train_state,
    train_step,
    eval_step,
    CoherenceConfig,
)
import jax
import jax.numpy as jnp
from jax import random

config = CoherenceConfig()
rng = random.PRNGKey(42)
input_shape = (32, 16, 64)  # batch, seq_len, input_dim

# Create training state
state = create_train_state(rng, config, input_shape)

# Training loop
for step in range(100):
    rng, data_rng = random.split(rng)
    batch = random.normal(data_rng, input_shape)
    labels = random.randint(data_rng, (32,), 0, 10)
    
    state, loss = train_step(state, batch, labels)
    
    if step % 10 == 0:
        print(f"Step {step}, Loss: {loss:.4f}")
```

## Citation

If you use the Magnetar Elastic Coherence Engine in your research, please cite:

```
@software{magnetar_engine,
  title = {Magnetar Elastic Coherence Engine},
  author = {Magnetar Research Initiative},
  year = {2026},
  url = {https://github.com/janschulzik-cmyk/Ouroboros}
}
```

## License

See the repository root for license information.

## Contributing

Contributions are welcome! Please ensure:
- Code follows JAX/Flax best practices
- All tests pass
- New features include tests
- Documentation is updated

## Support

For issues or questions:
1. Check existing issues in the repository
2. Run the demo to verify installation
3. Ensure all ML dependencies are installed
4. Check JAX device compatibility (CPU/GPU/TPU)
