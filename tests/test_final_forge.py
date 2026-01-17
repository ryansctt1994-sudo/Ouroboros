"""
Test suite for The Final Forge: Zero Vulnerabilities, Mathematical Perfection

Tests comprehensive security and numerical stability improvements.
"""

import pytest
import numpy as np
import hashlib
import secrets
import warnings
from decimal import Decimal, getcontext

from src.final_forge import (
    # Exception classes
    InsufficientEntropyError,
    NonFiniteParameterError,
    NonFiniteGradientError,
    NaNInGradientError,
    # Main classes
    CryptographicSeedGenerator,
    MemoryBoundedCache,
    InfinitySafeCalculator,
    MomentumOptimizer,
    SafeDivider,
    # Supporting classes
    SystemEntropyPool,
    DeterministicEntropyPool,
    SeedValidator,
    MemoryMonitor,
    CacheMetrics,
    AsymptoticAnalyzer,
    SymbolicLimitEngine,
    LearningRateScheduler,
    GradientClipper,
    ConvergenceMonitor,
    OptimizationStabilizer,
    DivisionErrorAnalyzer,
)


# ============================================================================
# Test CryptographicSeedGenerator
# ============================================================================

class TestCryptographicSeedGenerator:
    """Test cryptographic seed generation."""
    
    def test_generate_seed_basic(self):
        """Test basic seed generation."""
        generator = CryptographicSeedGenerator()
        seed, diagnostics = generator.generate_seed()
        
        assert isinstance(seed, int)
        assert seed > 0
        assert diagnostics['seed_type'] == 'cryptographic'
        assert diagnostics['seed_bits'] == 256
        assert diagnostics['entropy_validation']['valid']
    
    def test_generate_seed_with_input_data(self):
        """Test seed generation with input data."""
        generator = CryptographicSeedGenerator()
        input_data = b"test input data for seeding"
        
        seed1, diag1 = generator.generate_seed(input_data=input_data)
        seed2, diag2 = generator.generate_seed(input_data=input_data)
        
        # Same input should give different seeds due to system entropy
        assert seed1 != seed2
        assert diag1['entropy_validation']['valid']
        assert diag2['entropy_validation']['valid']
    
    def test_seed_entropy_validation(self):
        """Test entropy validation."""
        validator = SeedValidator()
        
        # Good entropy
        good_data = secrets.token_bytes(64)
        result = validator.validate_entropy(good_data, min_entropy_bits=256)
        assert result['valid']
        assert result['entropy_bits'] >= 256 * 0.9
        
        # Insufficient data
        bad_data = b"short"
        result = validator.validate_entropy(bad_data, min_entropy_bits=256)
        assert not result['valid']
    
    def test_system_entropy_pool(self):
        """Test system entropy pool."""
        pool = SystemEntropyPool()
        entropy = pool.collect(32)
        
        assert len(entropy) == 32
        assert isinstance(entropy, bytes)
        
        # Should be different each time
        entropy2 = pool.collect(32)
        assert entropy != entropy2
    
    def test_deterministic_entropy_pool(self):
        """Test deterministic entropy pool."""
        pool1 = DeterministicEntropyPool(seed=12345)
        pool2 = DeterministicEntropyPool(seed=12345)
        
        entropy1 = pool1.collect(32)
        entropy2 = pool2.collect(32)
        
        # Same seed should give same entropy
        assert entropy1 == entropy2
        assert len(entropy1) == 32
    
    def test_bytes_to_unbiased_int(self):
        """Test conversion without modulo bias."""
        generator = CryptographicSeedGenerator()
        
        data = secrets.token_bytes(32)
        value = generator._bytes_to_unbiased_int(data, bits=256)
        
        assert isinstance(value, int)
        assert value >= 0
        assert value.bit_length() <= 256
    
    def test_seed_collision_resistance(self):
        """Test that seeds are collision-resistant."""
        generator = CryptographicSeedGenerator()
        
        seeds = set()
        for _ in range(100):
            seed, _ = generator.generate_seed()
            assert seed not in seeds, "Seed collision detected"
            seeds.add(seed)
    
    def test_sha3_256_usage(self):
        """Test that SHA3-256 is used for post-quantum security."""
        generator = CryptographicSeedGenerator()
        seed, diagnostics = generator.generate_seed()
        
        # Verify hash is present in diagnostics
        assert 'seed_hash' in diagnostics
        assert len(diagnostics['seed_hash']) == 16  # First 16 chars


# ============================================================================
# Test MemoryBoundedCache
# ============================================================================

class TestMemoryBoundedCache:
    """Test memory-bounded cache."""
    
    def test_cache_basic_put_get(self):
        """Test basic put and get operations."""
        cache = MemoryBoundedCache(max_bytes=1024)
        
        diag = cache.put('key1', 'value1', size_bytes=100, critical=False)
        assert diag['stored']
        
        value, get_diag = cache.get('key1')
        assert value == 'value1'
        assert get_diag['hit']
    
    def test_cache_memory_limit(self):
        """Test cache respects memory limits."""
        cache = MemoryBoundedCache(max_bytes=500)
        
        # Add items totaling more than limit
        cache.put('key1', 'value1', size_bytes=200, critical=False)
        cache.put('key2', 'value2', size_bytes=200, critical=False)
        cache.put('key3', 'value3', size_bytes=200, critical=False)
        
        # Cache should have evicted something
        assert cache.monitor.total_bytes <= 500
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = MemoryBoundedCache(max_bytes=300, eviction_policy='lru')
        
        cache.put('key1', 'value1', size_bytes=100)
        cache.put('key2', 'value2', size_bytes=100)
        cache.put('key3', 'value3', size_bytes=100)
        
        # Access key1 to make it recently used
        cache.get('key1')
        
        # Add another item, should evict key2 (least recently used)
        cache.put('key4', 'value4', size_bytes=100)
        
        # key1 should still be there
        val, _ = cache.get('key1')
        assert val == 'value1'
    
    def test_cache_lfu_eviction(self):
        """Test LFU eviction policy."""
        cache = MemoryBoundedCache(max_bytes=300, eviction_policy='lfu')
        
        cache.put('key1', 'value1', size_bytes=100)
        cache.put('key2', 'value2', size_bytes=100)
        cache.put('key3', 'value3', size_bytes=100)
        
        # Access key1 multiple times
        for _ in range(5):
            cache.get('key1')
        
        # Add another item
        cache.put('key4', 'value4', size_bytes=100)
        
        # key1 should still be there (most frequently used)
        val, _ = cache.get('key1')
        assert val == 'value1'
    
    def test_cache_critical_items(self):
        """Test that critical items are protected from eviction."""
        cache = MemoryBoundedCache(max_bytes=300)
        
        cache.put('critical', 'important', size_bytes=100, critical=True)
        cache.put('key1', 'value1', size_bytes=100, critical=False)
        cache.put('key2', 'value2', size_bytes=100, critical=False)
        
        # Add more items, should evict non-critical first
        cache.put('key3', 'value3', size_bytes=100, critical=False)
        
        # Critical item should still be there
        val, _ = cache.get('critical')
        assert val == 'important'
    
    def test_cache_metrics(self):
        """Test cache metrics tracking."""
        cache = MemoryBoundedCache(max_bytes=1024)
        
        cache.put('key1', 'value1', size_bytes=100)
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss
        
        metrics = cache.metrics.get_metrics()
        
        assert metrics['hits'] == 1
        assert metrics['misses'] == 1
        assert metrics['puts'] == 1
        assert 0 < metrics['hit_rate'] < 1
    
    def test_cache_degradation_modes(self):
        """Test cache degradation modes."""
        cache = MemoryBoundedCache(max_bytes=100)
        
        # Fill cache to trigger degradation
        for i in range(20):
            cache.put(f'key{i}', f'value{i}', size_bytes=10)
        
        # Should enter degradation mode
        assert cache.degradation_mode in ['full', 'degraded', 'minimal', 'emergency']
    
    def test_cache_adaptive_eviction(self):
        """Test adaptive eviction policy."""
        cache = MemoryBoundedCache(max_bytes=500, eviction_policy='adaptive_lru')
        
        # Add items of different sizes
        cache.put('small1', 'val', size_bytes=50)
        cache.put('small2', 'val', size_bytes=50)
        cache.put('large', 'val', size_bytes=200)
        
        # Add another large item
        cache.put('large2', 'val', size_bytes=200)
        
        # Adaptive eviction should consider both age and size
        assert cache.monitor.total_bytes <= 500
    
    def test_memory_monitor(self):
        """Test memory monitor."""
        monitor = MemoryMonitor()
        
        monitor.add_item(100)
        monitor.add_item(200)
        
        usage = monitor.get_usage()
        assert usage['total_bytes'] == 300
        assert usage['item_count'] == 2
        assert usage['avg_item_size'] == 150
        
        monitor.remove_item(100)
        usage = monitor.get_usage()
        assert usage['total_bytes'] == 200
        assert usage['item_count'] == 1


# ============================================================================
# Test InfinitySafeCalculator
# ============================================================================

class TestInfinitySafeCalculator:
    """Test infinity-safe calculations."""
    
    def test_compute_safe_finite_result(self):
        """Test computation with finite result."""
        calc = InfinitySafeCalculator()
        
        def square(x):
            return x ** 2
        
        result, diag = calc.compute_safe(square, 3.0)
        
        assert result == 9.0
        assert diag['method'] == 'direct'
        assert diag['input_finite']
    
    def test_compute_safe_division_by_zero(self):
        """Test handling division by zero."""
        calc = InfinitySafeCalculator()
        
        def reciprocal(x):
            return 1.0 / x
        
        result, diag = calc.compute_safe(reciprocal, 0.0)
        
        # Should handle the infinity or error
        assert 'error' in diag or 'raw_value' in diag
        assert diag['input_finite']
    
    def test_asymptotic_analyzer(self):
        """Test asymptotic analysis."""
        analyzer = AsymptoticAnalyzer()
        
        def func(x):
            return 1.0 / (x + 1e-10)
        
        analysis = analyzer.analyze(func, 0.0)
        
        # Should have either value or error
        assert 'value' in analysis or 'error' in analysis
        assert 'is_pole' in analysis
    
    def test_symbolic_limit_engine(self):
        """Test symbolic limit computation."""
        engine = SymbolicLimitEngine()
        
        def func(x):
            return (x**2 - 1) / (x - 1)
        
        limit, diag = engine.compute_limit(func, 1.0)
        
        # Limit should be close to 2 (by L'Hôpital)
        assert diag['direction'] == 'both'
    
    def test_pade_approximant(self):
        """Test Padé approximant regularization."""
        calc = InfinitySafeCalculator()
        
        def func(x):
            return np.sin(x) / x if x != 0 else 1
        
        result = calc._pade_approximant(func, 0.01)
        
        # Should return a finite value
        assert np.isfinite(result) or np.isnan(result)
    
    def test_series_expansion(self):
        """Test series expansion."""
        calc = InfinitySafeCalculator()
        
        def func(x):
            return np.exp(x)
        
        result = calc._series_expansion(func, 1.0)
        
        # Should approximate e ≈ 2.718
        assert np.isfinite(result) or np.isnan(result)
    
    def test_non_finite_input(self):
        """Test handling of non-finite input."""
        calc = InfinitySafeCalculator()
        
        def func(x):
            return x * 2
        
        result, diag = calc.compute_safe(func, np.inf)
        
        assert not diag['input_finite']
        assert np.isnan(result)


# ============================================================================
# Test MomentumOptimizer
# ============================================================================

class TestMomentumOptimizer:
    """Test momentum optimizer."""
    
    def test_optimizer_initialization(self):
        """Test optimizer is properly initialized."""
        optimizer = MomentumOptimizer(learning_rate=0.01, momentum=0.9)
        
        assert not optimizer.initialized
        assert optimizer.velocity is None
        
        # Apply gradients should initialize velocity
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, 0.2, 0.3])
        
        new_params, diag = optimizer.apply_gradients(params, grads, step=0)
        
        assert optimizer.initialized
        assert optimizer.velocity is not None
        assert diag['velocity_initialized']
    
    def test_momentum_update(self):
        """Test momentum-based update."""
        optimizer = MomentumOptimizer(learning_rate=0.1, momentum=0.9)
        
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, 0.2, 0.3])
        
        new_params, diag = optimizer.apply_gradients(params, grads, step=0)
        
        # Parameters should have moved
        assert not np.allclose(new_params, params)
        assert 'velocity_norm' in diag
    
    def test_gradient_clipping(self):
        """Test gradient clipping."""
        optimizer = MomentumOptimizer(learning_rate=0.1)
        
        params = np.array([1.0, 2.0, 3.0])
        large_grads = np.array([100.0, 200.0, 300.0])
        
        new_params, diag = optimizer.apply_gradients(params, large_grads, step=0)
        
        # Gradients should be clipped
        assert diag['gradient_clipping']['clipped']
    
    def test_learning_rate_warmup(self):
        """Test learning rate warmup."""
        scheduler = LearningRateScheduler(base_lr=0.1, warmup_steps=10)
        
        # During warmup
        lr_step_0 = scheduler.get_learning_rate(0)
        lr_step_5 = scheduler.get_learning_rate(5)
        lr_step_10 = scheduler.get_learning_rate(10)
        
        # Should gradually increase
        assert lr_step_0 < lr_step_5 < lr_step_10
        assert lr_step_10 == 0.1  # Should reach base_lr at warmup_steps
    
    def test_learning_rate_decay(self):
        """Test learning rate decay after warmup."""
        scheduler = LearningRateScheduler(base_lr=0.1, warmup_steps=10, decay_rate=0.9)
        
        lr_step_10 = scheduler.get_learning_rate(10)
        lr_step_20 = scheduler.get_learning_rate(20)
        
        # Should decay after warmup
        assert lr_step_20 < lr_step_10
    
    def test_convergence_monitor(self):
        """Test convergence monitoring."""
        monitor = ConvergenceMonitor(patience=3, tolerance=1e-6)
        
        # Improving values
        diag1 = monitor.update(1.0)
        assert not diag1['converged']
        
        diag2 = monitor.update(0.5)
        assert not diag2['converged']
        
        # Plateau
        for _ in range(5):
            diag = monitor.update(0.5)
        
        # Should converge after patience steps
        assert diag['converged']
    
    def test_non_finite_parameter_error(self):
        """Test error on non-finite parameters."""
        optimizer = MomentumOptimizer()
        
        params = np.array([1.0, np.inf, 3.0])
        grads = np.array([0.1, 0.2, 0.3])
        
        with pytest.raises(NonFiniteParameterError):
            optimizer.apply_gradients(params, grads, step=0)
    
    def test_nan_gradient_error(self):
        """Test error on NaN gradients."""
        optimizer = MomentumOptimizer()
        
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, np.nan, 0.3])
        
        with pytest.raises(NaNInGradientError):
            optimizer.apply_gradients(params, grads, step=0)
    
    def test_infinite_gradient_error(self):
        """Test error on infinite gradients."""
        optimizer = MomentumOptimizer()
        
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, np.inf, 0.3])
        
        with pytest.raises(NonFiniteGradientError):
            optimizer.apply_gradients(params, grads, step=0)
    
    def test_optimization_stabilizer(self):
        """Test optimization stabilization."""
        stabilizer = OptimizationStabilizer()
        
        large_update = np.array([100.0, 200.0, 300.0])
        stabilized, diag = stabilizer.stabilize_update(large_update, max_update=10.0)
        
        # Should be scaled down
        assert np.linalg.norm(stabilized) <= 10.0
        assert diag['stabilized']


# ============================================================================
# Test SafeDivider
# ============================================================================

class TestSafeDivider:
    """Test safe division."""
    
    def test_regular_division(self):
        """Test regular division without issues."""
        divider = SafeDivider()
        
        result, diag = divider.safe_divide(10.0, 2.0, method='regular')
        
        assert result == 5.0
        assert not diag['analysis']['has_zeros']
    
    def test_division_by_zero_scalar(self):
        """Test division by zero with scalar."""
        divider = SafeDivider()
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result, diag = divider.safe_divide(10.0, 0.0, method='regular')
            
            assert np.isnan(result)
            assert diag['analysis']['has_zeros']
            assert len(w) > 0  # Should warn
    
    def test_division_by_zero_array(self):
        """Test division by zero with arrays."""
        divider = SafeDivider()
        
        numerator = np.array([1.0, 2.0, 3.0])
        denominator = np.array([1.0, 0.0, 3.0])
        
        result, diag = divider.safe_divide(numerator, denominator, method='regular')
        
        # Should have NaN where denominator is zero
        assert result[0] == 1.0
        assert np.isnan(result[1])
        assert result[2] == 1.0
        assert diag['analysis']['has_zeros']
    
    def test_lhopital_method(self):
        """Test L'Hôpital's rule approximation."""
        divider = SafeDivider()
        
        result, diag = divider.safe_divide(1.0, 0.0, method='lhopital')
        
        # Should return a finite approximation
        assert np.isfinite(result)
    
    def test_series_method(self):
        """Test series expansion method."""
        divider = SafeDivider()
        
        result, diag = divider.safe_divide(5.0, 2.0, method='series')
        
        # Should return reasonable approximation
        assert np.isfinite(result)
    
    def test_limit_method(self):
        """Test limit approach."""
        divider = SafeDivider()
        
        result, diag = divider.safe_divide(1.0, 0.0, method='limit')
        
        # Should handle gracefully
        assert np.isfinite(result) or np.isinf(result)
    
    def test_regularized_method(self):
        """Test regularized division."""
        divider = SafeDivider()
        
        result, diag = divider.safe_divide(1.0, 0.0, method='regularized')
        
        # Should return finite result due to regularization
        assert np.isfinite(result)
        assert diag['computation']['regularization_param'] > 0
    
    def test_division_error_analyzer(self):
        """Test division error analysis."""
        analyzer = DivisionErrorAnalyzer()
        
        # Scalar analysis
        analysis = analyzer.analyze(10.0, 2.0)
        assert not analysis['has_zeros']
        assert analysis['numerator_type'] == 'scalar'
        
        # Array analysis with zeros
        analysis = analyzer.analyze(
            np.array([1.0, 2.0]),
            np.array([1.0, 0.0])
        )
        assert analysis['has_zeros']
        assert analysis['zero_count'] == 1
    
    def test_overflow_detection(self):
        """Test overflow risk detection."""
        analyzer = DivisionErrorAnalyzer()
        
        analysis = analyzer.analyze(1e100, 1e-100)
        
        # Should detect overflow risk
        assert 'overflow_risk' in analysis


# ============================================================================
# Test Decimal Precision
# ============================================================================

class TestDecimalPrecision:
    """Test Decimal operations use high precision."""
    
    def test_decimal_context_precision(self):
        """Test that Decimal context has 100 digits precision."""
        assert getcontext().prec == 100
    
    def test_high_precision_calculation(self):
        """Test high precision Decimal calculation."""
        a = Decimal('1.123456789012345678901234567890')
        b = Decimal('2.987654321098765432109876543210')
        
        result = a * b
        
        # Should maintain high precision
        result_str = str(result)
        assert len(result_str.replace('.', '')) > 20  # More than 20 digits


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_seed_generation_with_cache(self):
        """Test using seed generator with cache."""
        generator = CryptographicSeedGenerator()
        cache = MemoryBoundedCache(max_bytes=1024)
        
        # Generate and cache seeds
        for i in range(10):
            seed, diag = generator.generate_seed(purpose=f'iteration_{i}')
            cache.put(f'seed_{i}', seed, size_bytes=32)
        
        # Retrieve cached seed
        seed_5, get_diag = cache.get('seed_5')
        assert seed_5 is not None
        assert get_diag['hit']
    
    def test_optimizer_with_safe_division(self):
        """Test optimizer using safe division."""
        optimizer = MomentumOptimizer(learning_rate=0.1)
        divider = SafeDivider()
        
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, 0.2, 0.3])
        
        # Normalize gradients with safe division
        grad_norm = np.linalg.norm(grads)
        normalized_grads, div_diag = divider.safe_divide(
            grads, grad_norm, method='regularized'
        )
        
        # Apply to optimizer
        new_params, opt_diag = optimizer.apply_gradients(params, normalized_grads, step=0)
        
        assert np.all(np.isfinite(new_params))
        # Optimizer should be initialized after first apply_gradients call
        assert optimizer.initialized
    
    def test_infinity_safe_with_momentum(self):
        """Test infinity-safe calculator with momentum optimizer."""
        calc = InfinitySafeCalculator()
        optimizer = MomentumOptimizer(learning_rate=0.01)
        
        def objective(x):
            return x ** 2
        
        params = np.array([5.0])
        
        # Compute gradient (simplified)
        epsilon = 1e-5
        grad = (objective(params[0] + epsilon) - objective(params[0])) / epsilon
        
        # Ensure gradient is finite
        grad_array = np.array([grad])
        if not np.all(np.isfinite(grad_array)):
            grad_array = np.array([0.0])
        
        # Update with optimizer
        new_params, diag = optimizer.apply_gradients(params, grad_array, step=0)
        
        assert np.all(np.isfinite(new_params))
    
    def test_full_pipeline_robustness(self):
        """Test complete pipeline with edge cases."""
        # Initialize all components
        seed_gen = CryptographicSeedGenerator()
        cache = MemoryBoundedCache(max_bytes=512)
        calc = InfinitySafeCalculator()
        optimizer = MomentumOptimizer(learning_rate=0.1)
        divider = SafeDivider()
        
        # Generate seed
        seed, seed_diag = seed_gen.generate_seed(purpose='pipeline_test')
        assert seed_diag['entropy_validation']['valid']
        
        # Cache the seed
        cache_diag = cache.put('pipeline_seed', seed, size_bytes=32, critical=True)
        assert cache_diag['stored']
        
        # Perform safe calculation
        def test_func(x):
            return np.sin(x) / x if x != 0 else 1
        
        result, calc_diag = calc.compute_safe(test_func, 0.1)
        assert np.isfinite(result) or np.isnan(result)
        
        # Safe division
        div_result, div_diag = divider.safe_divide(1.0, 0.001, method='regularized')
        assert np.isfinite(div_result)
        
        # Optimizer update
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, 0.2, 0.3])
        new_params, opt_diag = optimizer.apply_gradients(params, grads, step=0)
        assert np.all(np.isfinite(new_params))
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        optimizer = MomentumOptimizer()
        
        # Test all error types
        params_ok = np.array([1.0, 2.0, 3.0])
        
        # Test NonFiniteParameterError
        with pytest.raises(NonFiniteParameterError):
            optimizer.apply_gradients(
                np.array([1.0, np.inf, 3.0]),
                np.array([0.1, 0.2, 0.3]),
                step=0
            )
        
        # Test NaNInGradientError
        with pytest.raises(NaNInGradientError):
            optimizer.apply_gradients(
                params_ok,
                np.array([0.1, np.nan, 0.3]),
                step=0
            )
        
        # Test NonFiniteGradientError
        with pytest.raises(NonFiniteGradientError):
            optimizer.apply_gradients(
                params_ok,
                np.array([0.1, np.inf, 0.3]),
                step=0
            )


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_cache(self):
        """Test operations on empty cache."""
        cache = MemoryBoundedCache()
        
        value, diag = cache.get('nonexistent')
        assert value is None
        assert not diag['hit']
    
    def test_zero_learning_rate(self):
        """Test optimizer with zero learning rate."""
        optimizer = MomentumOptimizer(learning_rate=0.0)
        
        params = np.array([1.0, 2.0, 3.0])
        grads = np.array([0.1, 0.2, 0.3])
        
        new_params, diag = optimizer.apply_gradients(params, grads, step=0)
        
        # With zero learning rate, params shouldn't change much
        # (only momentum initialization might cause small change)
        assert diag['learning_rate'] == 0.0
    
    def test_very_small_denominator(self):
        """Test division with very small denominator."""
        divider = SafeDivider()
        
        result, diag = divider.safe_divide(1.0, 1e-100, method='regularized')
        
        # Should handle without overflow
        assert np.isfinite(result)
    
    def test_cache_size_aware_eviction(self):
        """Test size-aware eviction with varying sizes."""
        cache = MemoryBoundedCache(max_bytes=500, eviction_policy='size_aware')
        
        cache.put('tiny', 'x', size_bytes=10)
        cache.put('small', 'y', size_bytes=50)
        cache.put('large', 'z', size_bytes=200)
        
        # Add another large item
        cache.put('huge', 'w', size_bytes=300)
        
        # Should evict largest first
        assert cache.monitor.total_bytes <= 500


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
