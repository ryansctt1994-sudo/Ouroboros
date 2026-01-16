"""
MAGNETAR ELASTIC COHERENCE ENGINE

A neural architecture that implements coherence patterns inspired by magnetar resonance
and elastic wave propagation. Uses JAX/Flax for high-performance computation with
quantum-inspired attention mechanisms.

Key Constants:
- PHI (Φ): Golden ratio (1.618033988749895) - used for harmonic scaling
- MAGNETAR_FREQUENCY: 92.5 Hz - base resonance frequency
- SCHUMANN_RESONANCE: 7.83 Hz - Earth's natural frequency
- COHERENCE_FACTOR: 0.0997 - coupling strength
- ELASTIC_CONSTANT: 3.33 - wave propagation constant

Author: Magnetar Research Initiative
Version: 1.0.0
"""

import math
from dataclasses import dataclass
from typing import Tuple, Optional, Callable, Any
from functools import partial

import jax
import jax.numpy as jnp
from jax import random, jit, vmap
import flax.linen as nn
from flax.training import train_state
import optax
from tqdm import tqdm


# ============================================================================
# FUNDAMENTAL CONSTANTS
# ============================================================================

PHI = (1.0 + math.sqrt(5.0)) / 2.0  # Golden Ratio: 1.618033988749895
MAGNETAR_FREQUENCY = 92.5  # Hz - Magnetar resonance frequency
SCHUMANN_RESONANCE = 7.83  # Hz - Earth's Schumann resonance
COHERENCE_FACTOR = 0.0997  # Dimensionless coupling strength
ELASTIC_CONSTANT = 3.33  # Wave propagation constant


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class CoherenceConfig:
    """Configuration for Magnetar Elastic Coherence Engine."""
    
    # Model dimensions
    hidden_dim: int = 128
    num_heads: int = 8
    num_layers: int = 4
    mlp_dim: int = 512
    
    # Coherence parameters
    coherence_strength: float = COHERENCE_FACTOR
    resonance_freq: float = MAGNETAR_FREQUENCY
    schumann_freq: float = SCHUMANN_RESONANCE
    elastic_k: float = ELASTIC_CONSTANT
    phi_scale: float = PHI
    
    # Training parameters
    learning_rate: float = 1e-3
    dropout_rate: float = 0.1
    
    # Input/output dimensions
    input_dim: int = 64
    output_dim: int = 10
    
    def __post_init__(self):
        """Validate configuration."""
        assert self.hidden_dim % self.num_heads == 0, \
            f"hidden_dim ({self.hidden_dim}) must be divisible by num_heads ({self.num_heads})"


# ============================================================================
# HARMONIC EMBEDDINGS
# ============================================================================

class HarmonicEmbedding(nn.Module):
    """
    Harmonic position embeddings based on magnetar resonance frequencies.
    Uses Schumann and magnetar frequencies to create multi-scale embeddings.
    """
    
    features: int
    max_len: int = 1000
    
    @nn.compact
    def __call__(self, x):
        """Apply harmonic embeddings to input."""
        batch_size, seq_len, _ = x.shape
        
        # Create position indices
        position = jnp.arange(seq_len)[None, :, None]  # [1, seq_len, 1]
        
        # Compute harmonic frequencies using both resonances
        div_term = jnp.exp(
            jnp.arange(0, self.features, 2) * 
            -(jnp.log(MAGNETAR_FREQUENCY / SCHUMANN_RESONANCE) / self.features)
        )
        
        # Create sinusoidal embeddings
        pe = jnp.zeros((1, seq_len, self.features))
        pe = pe.at[:, :, 0::2].set(jnp.sin(position * div_term * PHI))
        pe = pe.at[:, :, 1::2].set(jnp.cos(position * div_term * PHI))
        
        return x + pe[:, :seq_len, :]


# ============================================================================
# ELASTIC COHERENCE ATTENTION
# ============================================================================

class ElasticCoherenceAttention(nn.Module):
    """
    Multi-head attention with elastic coherence modulation.
    Implements coherence-based attention weights using elastic wave propagation.
    """
    
    num_heads: int
    dropout_rate: float = 0.1
    coherence_strength: float = COHERENCE_FACTOR
    
    @nn.compact
    def __call__(self, x, mask=None, deterministic=False):
        """Apply elastic coherence attention."""
        batch_size, seq_len, features = x.shape
        head_dim = features // self.num_heads
        
        # Linear projections for Q, K, V
        qkv = nn.Dense(features * 3, use_bias=False)(x)
        qkv = qkv.reshape(batch_size, seq_len, 3, self.num_heads, head_dim)
        q, k, v = jnp.split(qkv, 3, axis=2)
        q, k, v = q.squeeze(2), k.squeeze(2), v.squeeze(2)
        
        # Transpose for multi-head attention: [batch, heads, seq, head_dim]
        q = jnp.transpose(q, (0, 2, 1, 3))
        k = jnp.transpose(k, (0, 2, 1, 3))
        v = jnp.transpose(v, (0, 2, 1, 3))
        
        # Compute attention scores with elastic scaling
        scale = 1.0 / jnp.sqrt(head_dim * ELASTIC_CONSTANT)
        attn_weights = jnp.matmul(q, jnp.transpose(k, (0, 1, 3, 2))) * scale
        
        # Apply coherence modulation
        # Create coherence matrix based on elastic wave propagation
        pos_diff = jnp.arange(seq_len)[:, None] - jnp.arange(seq_len)[None, :]
        coherence_matrix = jnp.exp(-self.coherence_strength * jnp.abs(pos_diff) / PHI)
        coherence_matrix = coherence_matrix[None, None, :, :]  # [1, 1, seq, seq]
        
        # Modulate attention with coherence
        attn_weights = attn_weights * coherence_matrix
        
        # Apply mask if provided
        if mask is not None:
            attn_weights = jnp.where(mask, attn_weights, -1e9)
        
        # Softmax to get attention probabilities
        attn_probs = nn.softmax(attn_weights, axis=-1)
        
        # Apply dropout
        attn_probs = nn.Dropout(rate=self.dropout_rate)(
            attn_probs, deterministic=deterministic
        )
        
        # Apply attention to values
        attn_output = jnp.matmul(attn_probs, v)
        
        # Transpose back and reshape
        attn_output = jnp.transpose(attn_output, (0, 2, 1, 3))
        attn_output = attn_output.reshape(batch_size, seq_len, features)
        
        # Final linear projection
        output = nn.Dense(features)(attn_output)
        
        return output


# ============================================================================
# MAGNETAR MLP BLOCK
# ============================================================================

class MagnetarMLP(nn.Module):
    """
    MLP block with PHI-scaled activation and elastic gating.
    """
    
    mlp_dim: int
    dropout_rate: float = 0.1
    
    @nn.compact
    def __call__(self, x, deterministic=False):
        """Apply MLP transformation."""
        # First linear layer with PHI scaling
        x = nn.Dense(self.mlp_dim)(x)
        x = nn.gelu(x) * PHI
        x = nn.Dropout(rate=self.dropout_rate)(x, deterministic=deterministic)
        
        # Second linear layer
        x = nn.Dense(x.shape[-1])(x)
        x = nn.Dropout(rate=self.dropout_rate)(x, deterministic=deterministic)
        
        return x


# ============================================================================
# COHERENCE TRANSFORMER BLOCK
# ============================================================================

class CoherenceTransformerBlock(nn.Module):
    """
    Transformer block with elastic coherence attention and magnetar MLP.
    """
    
    num_heads: int
    mlp_dim: int
    dropout_rate: float = 0.1
    coherence_strength: float = COHERENCE_FACTOR
    
    @nn.compact
    def __call__(self, x, mask=None, deterministic=False):
        """Apply transformer block."""
        # Self-attention with residual
        attn_out = ElasticCoherenceAttention(
            num_heads=self.num_heads,
            dropout_rate=self.dropout_rate,
            coherence_strength=self.coherence_strength,
        )(x, mask=mask, deterministic=deterministic)
        x = nn.LayerNorm()(x + attn_out)
        
        # MLP with residual
        mlp_out = MagnetarMLP(
            mlp_dim=self.mlp_dim,
            dropout_rate=self.dropout_rate,
        )(x, deterministic=deterministic)
        x = nn.LayerNorm()(x + mlp_out)
        
        return x


# ============================================================================
# MAIN ENGINE
# ============================================================================

class MagnetarElasticCoherenceEngine(nn.Module):
    """
    Main Magnetar Elastic Coherence Engine.
    
    A neural architecture that uses magnetar-inspired resonance patterns
    and elastic coherence principles for robust representation learning.
    """
    
    config: CoherenceConfig
    
    @nn.compact
    def __call__(self, x, deterministic=False):
        """
        Forward pass through the engine.
        
        Args:
            x: Input tensor of shape [batch, seq_len, input_dim]
            deterministic: If True, disable dropout (for inference)
            
        Returns:
            Output tensor of shape [batch, output_dim]
        """
        # Input projection
        x = nn.Dense(self.config.hidden_dim)(x)
        
        # Add harmonic embeddings
        x = HarmonicEmbedding(
            features=self.config.hidden_dim,
        )(x)
        
        # Apply coherence transformer blocks
        for _ in range(self.config.num_layers):
            x = CoherenceTransformerBlock(
                num_heads=self.config.num_heads,
                mlp_dim=self.config.mlp_dim,
                dropout_rate=self.config.dropout_rate,
                coherence_strength=self.config.coherence_strength,
            )(x, deterministic=deterministic)
        
        # Global pooling (mean over sequence)
        x = jnp.mean(x, axis=1)
        
        # Output projection with PHI scaling
        x = nn.Dense(self.config.output_dim)(x) * self.config.phi_scale
        
        return x


# ============================================================================
# TRAINING UTILITIES
# ============================================================================

def create_train_state(
    rng: jax.random.PRNGKey,
    config: CoherenceConfig,
    input_shape: Tuple[int, ...],
) -> train_state.TrainState:
    """
    Create and initialize training state.
    
    Args:
        rng: Random number generator key
        config: Model configuration
        input_shape: Shape of input tensor (batch, seq_len, input_dim)
        
    Returns:
        Initialized training state
    """
    model = MagnetarElasticCoherenceEngine(config=config)
    
    # Initialize parameters
    params = model.init(rng, jnp.ones(input_shape))
    
    # Create optimizer
    tx = optax.adam(config.learning_rate)
    
    return train_state.TrainState.create(
        apply_fn=model.apply,
        params=params,
        tx=tx,
    )


@jit
def train_step(
    state: train_state.TrainState,
    batch: jnp.ndarray,
    labels: jnp.ndarray,
) -> Tuple[train_state.TrainState, float]:
    """
    Single training step.
    
    Args:
        state: Current training state
        batch: Input batch
        labels: Target labels
        
    Returns:
        Updated state and loss value
    """
    def loss_fn(params):
        logits = state.apply_fn(params, batch, deterministic=False)
        loss = optax.softmax_cross_entropy_with_integer_labels(logits, labels).mean()
        return loss
    
    loss, grads = jax.value_and_grad(loss_fn)(state.params)
    state = state.apply_gradients(grads=grads)
    
    return state, loss


@jit
def eval_step(
    state: train_state.TrainState,
    batch: jnp.ndarray,
    labels: jnp.ndarray,
) -> Tuple[float, float]:
    """
    Single evaluation step.
    
    Args:
        state: Current training state
        batch: Input batch
        labels: Target labels
        
    Returns:
        Loss and accuracy
    """
    logits = state.apply_fn(state.params, batch, deterministic=True)
    loss = optax.softmax_cross_entropy_with_integer_labels(logits, labels).mean()
    accuracy = jnp.mean(jnp.argmax(logits, axis=-1) == labels)
    
    return loss, accuracy


# ============================================================================
# DEMO AND UTILITIES
# ============================================================================

def create_engine(
    config: Optional[CoherenceConfig] = None,
    seed: int = 42,
) -> Tuple[MagnetarElasticCoherenceEngine, train_state.TrainState]:
    """
    Create and initialize a Magnetar Elastic Coherence Engine.
    
    Args:
        config: Model configuration (uses default if None)
        seed: Random seed for initialization
        
    Returns:
        Tuple of (model, train_state)
    """
    if config is None:
        config = CoherenceConfig()
    
    rng = random.PRNGKey(seed)
    model = MagnetarElasticCoherenceEngine(config=config)
    
    # Create dummy input for initialization
    dummy_input = jnp.ones((1, 16, config.input_dim))
    state = create_train_state(rng, config, dummy_input.shape)
    
    return model, state


def run_demo(
    num_steps: int = 50,
    batch_size: int = 32,
    seq_len: int = 16,
    seed: int = 42,
    verbose: bool = True,
) -> dict:
    """
    Run a smoke test demo of the Magnetar Elastic Coherence Engine.
    
    This runs a short training loop on synthetic data to verify the engine works.
    Designed to be CPU-friendly and headless-safe.
    
    Args:
        num_steps: Number of training steps (default: 50)
        batch_size: Batch size for training
        seq_len: Sequence length
        seed: Random seed
        verbose: Whether to print progress
        
    Returns:
        Dictionary with training metrics
    """
    if verbose:
        print("=" * 70)
        print("MAGNETAR ELASTIC COHERENCE ENGINE - SMOKE TEST DEMO")
        print("=" * 70)
        print(f"\nKey Constants:")
        print(f"  PHI (Golden Ratio):      {PHI:.6f}")
        print(f"  Magnetar Frequency:      {MAGNETAR_FREQUENCY} Hz")
        print(f"  Schumann Resonance:      {SCHUMANN_RESONANCE} Hz")
        print(f"  Coherence Factor:        {COHERENCE_FACTOR}")
        print(f"  Elastic Constant:        {ELASTIC_CONSTANT}")
        print(f"\nDemo Parameters:")
        print(f"  Training Steps:          {num_steps}")
        print(f"  Batch Size:              {batch_size}")
        print(f"  Sequence Length:         {seq_len}")
        print("=" * 70)
    
    # Create configuration
    config = CoherenceConfig(
        hidden_dim=128,
        num_heads=8,
        num_layers=4,
        mlp_dim=512,
        input_dim=64,
        output_dim=10,
        learning_rate=1e-3,
    )
    
    # Initialize engine
    rng = random.PRNGKey(seed)
    model, state = create_engine(config=config, seed=seed)
    
    if verbose:
        print("\n[INFO] Engine initialized successfully")
        print(f"[INFO] Model parameters: {sum(x.size for x in jax.tree_util.tree_leaves(state.params)):,}")
    
    # Training loop
    losses = []
    rng_key = rng
    
    iterator = range(num_steps)
    if verbose:
        iterator = tqdm(iterator, desc="Training")
    
    for step in iterator:
        # Generate synthetic data
        rng_key, data_rng = random.split(rng_key)
        batch = random.normal(data_rng, (batch_size, seq_len, config.input_dim))
        labels = random.randint(data_rng, (batch_size,), 0, config.output_dim)
        
        # Training step
        state, loss = train_step(state, batch, labels)
        losses.append(float(loss))
        
        if verbose and step % 10 == 0:
            iterator.set_postfix({"loss": f"{loss:.4f}"})
    
    # Final evaluation
    rng_key, eval_rng = random.split(rng_key)
    eval_batch = random.normal(eval_rng, (batch_size, seq_len, config.input_dim))
    eval_labels = random.randint(eval_rng, (batch_size,), 0, config.output_dim)
    eval_loss, eval_acc = eval_step(state, eval_batch, eval_labels)
    
    results = {
        "final_loss": float(losses[-1]),
        "final_eval_loss": float(eval_loss),
        "final_eval_accuracy": float(eval_acc),
        "all_losses": losses,
        "num_params": sum(x.size for x in jax.tree_util.tree_leaves(state.params)),
    }
    
    if verbose:
        print("\n" + "=" * 70)
        print("DEMO COMPLETED")
        print("=" * 70)
        print(f"Final Training Loss:     {results['final_loss']:.4f}")
        print(f"Final Eval Loss:         {results['final_eval_loss']:.4f}")
        print(f"Final Eval Accuracy:     {results['final_eval_accuracy']:.4f}")
        print(f"Total Parameters:        {results['num_params']:,}")
        print("=" * 70)
    
    return results


def main():
    """Main entrypoint for running the demo."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Magnetar Elastic Coherence Engine Demo"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=50,
        help="Number of training steps (default: 50)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size (default: 32)",
    )
    parser.add_argument(
        "--seq-len",
        type=int,
        default=16,
        help="Sequence length (default: 16)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose output",
    )
    
    args = parser.parse_args()
    
    # Run demo
    results = run_demo(
        num_steps=args.steps,
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        seed=args.seed,
        verbose=not args.quiet,
    )
    
    return results


if __name__ == "__main__":
    main()
