"""
Tests for Magnetar Elastic Coherence Engine

Minimal test suite to verify the engine works correctly with small tensor shapes.
"""

import pytest

# Only run these tests if ML dependencies are available
try:
    import jax
    import jax.numpy as jnp
    from jax import random
    import flax.linen as nn
    import optax
    
    ML_DEPS_AVAILABLE = True
except ImportError:
    ML_DEPS_AVAILABLE = False

# Skip all tests if ML dependencies not installed
pytestmark = pytest.mark.skipif(
    not ML_DEPS_AVAILABLE,
    reason="ML dependencies (JAX/Flax/Optax) not installed"
)


if ML_DEPS_AVAILABLE:
    from engine_modules import (
        MagnetarElasticCoherenceEngine,
        CoherenceConfig,
        create_engine,
        run_demo,
    )
    from engine_modules.magnetar_elastic_coherence_engine import (
        HarmonicEmbedding,
        ElasticCoherenceAttention,
        MagnetarMLP,
        CoherenceTransformerBlock,
        create_train_state,
        train_step,
        eval_step,
        PHI,
        MAGNETAR_FREQUENCY,
        SCHUMANN_RESONANCE,
        COHERENCE_FACTOR,
        ELASTIC_CONSTANT,
    )


class TestConstants:
    """Test that fundamental constants are defined correctly."""
    
    def test_phi_value(self):
        """Test golden ratio constant."""
        assert abs(PHI - 1.618033988749895) < 1e-10
    
    def test_magnetar_frequency(self):
        """Test magnetar frequency constant."""
        assert MAGNETAR_FREQUENCY == 92.5
    
    def test_schumann_resonance(self):
        """Test Schumann resonance constant."""
        assert SCHUMANN_RESONANCE == 7.83
    
    def test_coherence_factor(self):
        """Test coherence factor constant."""
        assert COHERENCE_FACTOR == 0.0997
    
    def test_elastic_constant(self):
        """Test elastic constant."""
        assert ELASTIC_CONSTANT == 3.33


class TestConfiguration:
    """Test configuration dataclass."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CoherenceConfig()
        assert config.hidden_dim == 128
        assert config.num_heads == 8
        assert config.num_layers == 4
        assert config.mlp_dim == 512
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CoherenceConfig(
            hidden_dim=256,
            num_heads=16,
            num_layers=6,
        )
        assert config.hidden_dim == 256
        assert config.num_heads == 16
        assert config.num_layers == 6
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid: hidden_dim divisible by num_heads
        config = CoherenceConfig(hidden_dim=128, num_heads=8)
        assert config.hidden_dim % config.num_heads == 0
        
        # Invalid: hidden_dim not divisible by num_heads
        with pytest.raises(AssertionError):
            CoherenceConfig(hidden_dim=100, num_heads=8)


class TestHarmonicEmbedding:
    """Test harmonic embedding module."""
    
    def test_forward_pass(self):
        """Test forward pass with small tensor."""
        module = HarmonicEmbedding(features=64)
        rng = random.PRNGKey(0)
        
        # Small input: [batch=2, seq_len=8, features=64]
        x = random.normal(rng, (2, 8, 64))
        params = module.init(rng, x)
        output = module.apply(params, x)
        
        # Output shape should match input
        assert output.shape == x.shape
    
    def test_output_range(self):
        """Test that embeddings don't explode."""
        module = HarmonicEmbedding(features=32)
        rng = random.PRNGKey(42)
        
        x = jnp.zeros((1, 10, 32))
        params = module.init(rng, x)
        output = module.apply(params, x)
        
        # Check reasonable output range
        assert jnp.all(jnp.isfinite(output))
        assert jnp.max(jnp.abs(output)) < 100.0


class TestElasticCoherenceAttention:
    """Test elastic coherence attention module."""
    
    def test_forward_pass(self):
        """Test forward pass with small tensor."""
        module = ElasticCoherenceAttention(num_heads=4)
        rng = random.PRNGKey(1)
        
        # Small input: [batch=2, seq_len=8, features=64]
        x = random.normal(rng, (2, 8, 64))
        params = module.init(rng, x, deterministic=True)
        output = module.apply(params, x, deterministic=True)
        
        # Output shape should match input
        assert output.shape == x.shape
    
    def test_attention_with_dropout(self):
        """Test attention with dropout."""
        module = ElasticCoherenceAttention(num_heads=4, dropout_rate=0.1)
        rng = random.PRNGKey(2)
        
        x = random.normal(rng, (2, 8, 64))
        params = module.init(rng, x, deterministic=False)
        
        # Training mode (dropout enabled)
        output_train = module.apply(
            params, x, deterministic=False, rngs={'dropout': random.PRNGKey(3)}
        )
        
        # Inference mode (dropout disabled)
        output_eval = module.apply(params, x, deterministic=True)
        
        assert output_train.shape == x.shape
        assert output_eval.shape == x.shape


class TestMagnetarMLP:
    """Test Magnetar MLP module."""
    
    def test_forward_pass(self):
        """Test forward pass with small tensor."""
        module = MagnetarMLP(mlp_dim=256, out_dim=64)
        rng = random.PRNGKey(4)
        
        # Small input: [batch=2, seq_len=8, features=64]
        x = random.normal(rng, (2, 8, 64))
        params = module.init(rng, x, deterministic=True)
        output = module.apply(params, x, deterministic=True)
        
        # Output shape should match input
        assert output.shape == x.shape


class TestCoherenceTransformerBlock:
    """Test coherence transformer block."""
    
    def test_forward_pass(self):
        """Test forward pass with small tensor."""
        module = CoherenceTransformerBlock(num_heads=4, mlp_dim=256)
        rng = random.PRNGKey(5)
        
        # Small input: [batch=2, seq_len=8, features=64]
        x = random.normal(rng, (2, 8, 64))
        params = module.init(rng, x, deterministic=True)
        output = module.apply(params, x, deterministic=True)
        
        # Output shape should match input
        assert output.shape == x.shape


class TestMagnetarEngine:
    """Test main Magnetar Elastic Coherence Engine."""
    
    def test_engine_creation(self):
        """Test engine creation and initialization."""
        config = CoherenceConfig(
            hidden_dim=64,
            num_heads=4,
            num_layers=2,
            mlp_dim=128,
            input_dim=32,
            output_dim=5,
        )
        
        model, state = create_engine(config=config, seed=42)
        
        assert model is not None
        assert state is not None
        assert state.params is not None
    
    def test_forward_pass(self):
        """Test forward pass through complete engine."""
        config = CoherenceConfig(
            hidden_dim=64,
            num_heads=4,
            num_layers=2,
            mlp_dim=128,
            input_dim=32,
            output_dim=5,
        )
        
        model, state = create_engine(config=config, seed=42)
        
        # Small input: [batch=4, seq_len=8, input_dim=32]
        rng = random.PRNGKey(42)
        x = random.normal(rng, (4, 8, 32))
        
        # Forward pass
        output = state.apply_fn(state.params, x, deterministic=True)
        
        # Check output shape: [batch=4, output_dim=5]
        assert output.shape == (4, 5)
        assert jnp.all(jnp.isfinite(output))
    
    def test_training_step(self):
        """Test training step execution."""
        config = CoherenceConfig(
            hidden_dim=64,
            num_heads=4,
            num_layers=2,
            mlp_dim=128,
            input_dim=32,
            output_dim=5,
        )
        
        rng = random.PRNGKey(42)
        input_shape = (4, 8, 32)
        state = create_train_state(rng, config, input_shape)
        
        # Generate batch
        rng, batch_rng, dropout_rng = random.split(rng, 3)
        batch = random.normal(batch_rng, input_shape)
        labels = random.randint(batch_rng, (4,), 0, 5)
        
        # Training step
        new_state, loss = train_step(state, batch, labels, dropout_rng)
        
        # Check that state was updated
        assert new_state.step == state.step + 1
        assert jnp.isfinite(loss)
        assert loss > 0  # Loss should be positive
    
    def test_eval_step(self):
        """Test evaluation step execution."""
        config = CoherenceConfig(
            hidden_dim=64,
            num_heads=4,
            num_layers=2,
            mlp_dim=128,
            input_dim=32,
            output_dim=5,
        )
        
        rng = random.PRNGKey(42)
        input_shape = (4, 8, 32)
        state = create_train_state(rng, config, input_shape)
        
        # Generate batch
        batch = random.normal(rng, input_shape)
        labels = random.randint(rng, (4,), 0, 5)
        
        # Eval step
        loss, accuracy = eval_step(state, batch, labels)
        
        # Check metrics
        assert jnp.isfinite(loss)
        assert jnp.isfinite(accuracy)
        assert 0.0 <= accuracy <= 1.0
    
    def test_deterministic_output(self):
        """Test that same seed produces same output."""
        config = CoherenceConfig(
            hidden_dim=64,
            num_heads=4,
            num_layers=2,
            mlp_dim=128,
            input_dim=32,
            output_dim=5,
        )
        
        # Create two engines with same seed
        model1, state1 = create_engine(config=config, seed=42)
        model2, state2 = create_engine(config=config, seed=42)
        
        # Same input
        rng = random.PRNGKey(100)
        x = random.normal(rng, (2, 8, 32))
        
        # Forward passes
        output1 = state1.apply_fn(state1.params, x, deterministic=True)
        output2 = state2.apply_fn(state2.params, x, deterministic=True)
        
        # Should be identical
        assert jnp.allclose(output1, output2, rtol=1e-5, atol=1e-5)


class TestDemo:
    """Test demo functionality."""
    
    def test_run_demo_minimal(self):
        """Test running a minimal demo."""
        results = run_demo(
            num_steps=5,
            batch_size=8,
            seq_len=8,
            seed=42,
            verbose=False,
        )
        
        # Check results structure
        assert 'final_loss' in results
        assert 'final_eval_loss' in results
        assert 'final_eval_accuracy' in results
        assert 'all_losses' in results
        assert 'num_params' in results
        
        # Check metrics are valid
        assert jnp.isfinite(results['final_loss'])
        assert jnp.isfinite(results['final_eval_loss'])
        assert 0.0 <= results['final_eval_accuracy'] <= 1.0
        assert len(results['all_losses']) == 5
        assert results['num_params'] > 0
    
    def test_demo_reproducibility(self):
        """Test that demo is reproducible with same seed."""
        results1 = run_demo(
            num_steps=3,
            batch_size=4,
            seq_len=8,
            seed=12345,
            verbose=False,
        )
        
        results2 = run_demo(
            num_steps=3,
            batch_size=4,
            seq_len=8,
            seed=12345,
            verbose=False,
        )
        
        # Same seed should give same final loss
        assert abs(results1['final_loss'] - results2['final_loss']) < 1e-5


class TestImports:
    """Test that all exports are accessible."""
    
    def test_public_api(self):
        """Test that public API is importable."""
        from engine_modules import (
            MagnetarElasticCoherenceEngine,
            CoherenceConfig,
            create_engine,
            run_demo,
        )
        
        assert MagnetarElasticCoherenceEngine is not None
        assert CoherenceConfig is not None
        assert create_engine is not None
        assert run_demo is not None
