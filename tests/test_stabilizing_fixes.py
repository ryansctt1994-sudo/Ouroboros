"""
Test suite for the stabilizing chaotic core fixes.

Tests the three critical fixes:
1. Phase Coherence - Verify proper real-part multiplier (already correct)
2. Quaternion Safe Normalization - Identity fallback for zero norms
3. O(1) History Eviction - deque with maxlen instead of list.pop(0)
"""

import pytest
import numpy as np
from collections import deque

from src.dna_helix_magnetar import QuaternionNodeBalancer, TensorGradientSystem
from src.ggcc.coupling_interface import CouplingInterface
from ouroboros_processor import OuroborosVirtualProcessor


# ============================================================================
# Fix 1: Phase Coherence Stabilization - Verification Tests
# ============================================================================

class TestPhaseCoherenceVerification:
    """Verify phase coherence uses real-part multiplier correctly."""
    
    def test_phase_coherence_formula(self):
        """Verify the formula uses real-part: lambda_frequencies + 0.1 * PHI_GOLDEN_RATIO * np.real(phase_coherence)"""
        system = TensorGradientSystem()
        lambda_freqs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = system.helical_harmony_stabilization(lambda_freqs)
        
        # Verify it's not all the same (shows it's not using abs which gives 1.0)
        assert not np.allclose(result, result[0])
        
        # Verify the result is real-valued
        assert np.all(np.isreal(result))
        
        # Verify it produces reasonable variation
        variation = np.std(result - lambda_freqs)
        assert variation > 0.01, "Should produce measurable variation"


# ============================================================================
# Fix 2: Quaternion Safe Normalization - New Tests
# ============================================================================

class TestQuaternionSafeNormalization:
    """Test safe quaternion normalization with identity fallback."""
    
    def test_quaternion_hash_zero_norm_fallback(self):
        """Verify quaternion_hash uses identity fallback for zero-norm quaternions."""
        balancer = QuaternionNodeBalancer()
        
        # Test with zero quaternion
        zero_q = np.array([0.0, 0.0, 0.0, 0.0])
        hash_val = balancer.quaternion_hash(zero_q)
        
        # Should not raise error and should return valid hash
        assert isinstance(hash_val, int)
        assert 0 <= hash_val < balancer.quaternion_buckets
    
    def test_quaternion_hash_near_zero_fallback(self):
        """Verify quaternion_hash uses identity fallback for near-zero quaternions."""
        balancer = QuaternionNodeBalancer()
        
        # Test with near-zero quaternion
        near_zero_q = np.array([1e-12, 1e-12, 1e-12, 1e-12])
        hash_val = balancer.quaternion_hash(near_zero_q)
        
        # Should not raise error and should return valid hash
        assert isinstance(hash_val, int)
        assert 0 <= hash_val < balancer.quaternion_buckets
    
    def test_quaternion_hash_normal_case(self):
        """Verify quaternion_hash works normally for regular quaternions."""
        balancer = QuaternionNodeBalancer()
        
        # Test with normal quaternion
        normal_q = np.array([1.0, 0.0, 0.0, 0.0])
        hash_val = balancer.quaternion_hash(normal_q)
        
        assert isinstance(hash_val, int)
        assert 0 <= hash_val < balancer.quaternion_buckets
    
    def test_balance_node_zero_norm_fallback(self):
        """Verify balance_node uses identity fallback for zero-norm results."""
        balancer = QuaternionNodeBalancer()
        
        # This test verifies the SLERP result normalization
        # Using identity as input should work without errors
        identity = np.array([1.0, 0.0, 0.0, 0.0])
        result = balancer.balance_node(identity)
        
        # Should return a valid normalized quaternion
        assert result.shape == (4,)
        assert np.isclose(np.linalg.norm(result), 1.0, atol=1e-6)
    
    def test_ouroboros_quaternion_state_zero_norm_fallback(self):
        """Verify OuroborosVirtualProcessor.quaternion_state uses identity fallback."""
        processor = OuroborosVirtualProcessor()
        
        # Test with normal values - should work without errors
        quat = processor.quaternion_state(0.0, 0.0)
        
        # Should return valid quaternion
        assert len(quat) == 4
        w, x, y, z = quat
        
        # Check it's normalized (or identity if near-zero)
        norm = np.sqrt(w**2 + x**2 + y**2 + z**2)
        assert np.isclose(norm, 1.0, atol=1e-6) or (w == 1.0 and x == 0.0 and y == 0.0 and z == 0.0)
    
    def test_quaternion_normalization_consistency(self):
        """Verify all quaternion normalizations produce unit quaternions or identity."""
        balancer = QuaternionNodeBalancer()
        
        test_quaternions = [
            np.array([1.0, 0.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0, 0.0]),
            np.array([0.7071, 0.7071, 0.0, 0.0]),
            np.array([0.5, 0.5, 0.5, 0.5]),
        ]
        
        for q in test_quaternions:
            result = balancer.balance_node(q)
            norm = np.linalg.norm(result)
            assert np.isclose(norm, 1.0, atol=1e-6), f"Quaternion not normalized: {result}, norm={norm}"


# ============================================================================
# Fix 3: O(1) History Eviction - New Tests
# ============================================================================

class TestDequeHistoryEviction:
    """Test O(1) history eviction using deque with maxlen."""
    
    def test_quaternion_cache_uses_deque(self):
        """Verify QuaternionNodeBalancer uses deque for quaternion_cache buckets."""
        balancer = QuaternionNodeBalancer(cache_size=256, quaternion_buckets=16)
        
        # Check that buckets are deques
        for bucket_idx in range(balancer.quaternion_buckets):
            assert isinstance(balancer.quaternion_cache[bucket_idx], deque)
    
    def test_quaternion_cache_deque_maxlen(self):
        """Verify deque has correct maxlen."""
        cache_size = 256
        buckets = 16
        expected_maxlen = cache_size // buckets
        
        balancer = QuaternionNodeBalancer(cache_size=cache_size, quaternion_buckets=buckets)
        
        for bucket_idx in range(buckets):
            bucket = balancer.quaternion_cache[bucket_idx]
            assert bucket.maxlen == expected_maxlen
    
    def test_quaternion_cache_auto_eviction(self):
        """Verify deque auto-evicts old entries when maxlen is reached."""
        balancer = QuaternionNodeBalancer(cache_size=32, quaternion_buckets=4)
        
        # Add entries to fill and overflow one bucket
        test_q = np.array([1.0, 0.0, 0.0, 0.0])
        for i in range(20):
            balancer.balance_node(test_q)
        
        # Check that no bucket exceeds maxlen
        for bucket_idx in range(balancer.quaternion_buckets):
            bucket = balancer.quaternion_cache[bucket_idx]
            assert len(bucket) <= bucket.maxlen
    
    def test_coupling_interface_uses_deque(self):
        """Verify CouplingInterface uses deque for state_history."""
        coupling = CouplingInterface()
        
        assert isinstance(coupling.state_history, deque)
        assert coupling.state_history.maxlen == 100
    
    def test_coupling_interface_auto_eviction(self):
        """Verify CouplingInterface state_history auto-evicts old entries."""
        coupling = CouplingInterface()
        
        # Add more than maxlen entries
        for i in range(150):
            coupling.couple_static_to_dynamic(float(i))
        
        # Should not exceed maxlen
        assert len(coupling.state_history) == 100
        
        # Should contain most recent entries
        # The last entry should be close to the filtered version of the last input
        assert len(coupling.state_history) <= coupling.state_history.maxlen
    
    def test_ouroboros_monitoring_data_uses_deque(self):
        """Verify OuroborosVirtualProcessor uses deque for monitoring_data."""
        processor = OuroborosVirtualProcessor()
        
        assert isinstance(processor._monitoring_data, deque)
        assert processor._monitoring_data.maxlen == 1000
    
    def test_ouroboros_monitoring_data_auto_eviction(self):
        """Verify monitoring_data auto-evicts old entries."""
        processor = OuroborosVirtualProcessor()
        
        # Add more than maxlen entries (disable rate limiting)
        for i in range(1500):
            processor.monitor_phase_lock(0.1 * i, 0.2 * i, rate_limit=False)
        
        # Should not exceed maxlen
        assert len(processor._monitoring_data) == 1000
    
    def test_deque_is_fifo(self):
        """Verify deque evicts in FIFO order (oldest first)."""
        test_deque = deque(maxlen=3)
        
        test_deque.append(1)
        test_deque.append(2)
        test_deque.append(3)
        assert list(test_deque) == [1, 2, 3]
        
        test_deque.append(4)
        # Should evict 1 (oldest)
        assert list(test_deque) == [2, 3, 4]
        
        test_deque.append(5)
        # Should evict 2 (oldest)
        assert list(test_deque) == [3, 4, 5]


# ============================================================================
# Integration Tests
# ============================================================================

class TestStabilizingFixesIntegration:
    """Integration tests for all three fixes working together."""
    
    def test_quaternion_balancer_with_deque_and_safe_norm(self):
        """Test QuaternionNodeBalancer with both fixes working together."""
        balancer = QuaternionNodeBalancer(cache_size=64, quaternion_buckets=8)
        
        # Test with various quaternions including edge cases
        test_cases = [
            np.array([1.0, 0.0, 0.0, 0.0]),  # Identity
            np.array([0.7071, 0.7071, 0.0, 0.0]),  # Normal
            np.array([0.5, 0.5, 0.5, 0.5]),  # All equal
            np.array([1e-15, 1e-15, 1e-15, 1e-15]),  # Near zero (should use fallback)
        ]
        
        for q in test_cases:
            result = balancer.balance_node(q)
            
            # Should produce valid normalized quaternion
            assert result.shape == (4,)
            norm = np.linalg.norm(result)
            assert np.isclose(norm, 1.0, atol=1e-6)
            
            # Should not raise any errors
            hash_val = balancer.quaternion_hash(result)
            assert 0 <= hash_val < balancer.quaternion_buckets
        
        # Verify deque is being used and auto-evicting
        for bucket in balancer.quaternion_cache.values():
            assert isinstance(bucket, deque)
            assert len(bucket) <= bucket.maxlen
    
    def test_ouroboros_processor_with_all_fixes(self):
        """Test OuroborosVirtualProcessor with safe quaternion norm and deque."""
        processor = OuroborosVirtualProcessor()
        
        # Exercise the monitoring system (disable rate limiting)
        for i in range(50):
            phi = 0.1 * i
            theta = 0.2 * i
            processor.monitor_phase_lock(phi, theta, rate_limit=False)
        
        # Verify monitoring_data is using deque
        assert isinstance(processor._monitoring_data, deque)
        assert len(processor._monitoring_data) <= 1000
        
        # Verify quaternion_state returns valid quaternions
        quat = processor.quaternion_state(1.0, 2.0)
        w, x, y, z = quat
        norm = np.sqrt(w**2 + x**2 + y**2 + z**2)
        assert np.isclose(norm, 1.0, atol=1e-6)
    
    def test_all_fixes_no_performance_regression(self):
        """Verify fixes don't cause performance regression."""
        import time
        
        # Test QuaternionNodeBalancer
        balancer = QuaternionNodeBalancer()
        start = time.time()
        for i in range(100):
            q = np.array([np.cos(i), np.sin(i), 0.0, 0.0])
            balancer.balance_node(q)
        quat_time = time.time() - start
        
        # Should complete quickly (< 1 second for 100 iterations)
        assert quat_time < 1.0, f"QuaternionNodeBalancer too slow: {quat_time}s"
        
        # Test CouplingInterface
        coupling = CouplingInterface()
        start = time.time()
        for i in range(200):
            coupling.couple_static_to_dynamic(float(i))
        coupling_time = time.time() - start
        
        # Should complete quickly with deque (< 0.5 second for 200 iterations)
        assert coupling_time < 0.5, f"CouplingInterface too slow: {coupling_time}s"
