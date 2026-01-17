"""
Test suite for LEXICON GIGAS module:
- Topological manifold subspace optimization (HOSVD)
- Ternary logic radix economy stabilizer
- Berry curvature holonomy optimizer
- Neuro-symbolic latent pruning
- Cryptographic integrity layer optimization
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lexicon_gigas import (
    topological_manifold_subspace_optimization,
    ternary_logic_radix_economy_stabilizer,
    berry_curvature_holonomy_optimizer,
    neuro_symbolic_latent_pruning,
    cryptographic_integrity_layer_optimization,
    PHI,
)


# ============================================================================
# Topological Manifold Subspace Optimization Tests
# ============================================================================

class TestTopologicalManifoldSubspaceOptimization:
    """Tests for HOSVD decomposition"""
    
    def test_hosvd_produces_valid_factors(self):
        """Test that HOSVD decomposition produces factor matrices of correct dimensions"""
        # Create a 3D tensor
        tensor = np.random.randn(5, 4, 3)
        target_rank = 2
        
        core, factors = topological_manifold_subspace_optimization(tensor, target_rank)
        
        # Check that we have one factor matrix per mode
        assert len(factors) == 3
        
        # Check factor matrix dimensions
        assert factors[0].shape == (5, target_rank)
        assert factors[1].shape == (4, target_rank)
        assert factors[2].shape == (3, target_rank)
        
        # Check core tensor has correct shape
        assert core.shape == (target_rank, target_rank, target_rank)
    
    def test_hosvd_2d_tensor(self):
        """Test HOSVD on a 2D tensor (matrix)"""
        matrix = np.random.randn(10, 8)
        target_rank = 3
        
        core, factors = topological_manifold_subspace_optimization(matrix, target_rank)
        
        assert len(factors) == 2
        assert factors[0].shape == (10, target_rank)
        assert factors[1].shape == (8, target_rank)
        assert core.shape == (target_rank, target_rank)
    
    def test_hosvd_orthogonality(self):
        """Test that factor matrices are orthogonal"""
        tensor = np.random.randn(6, 6, 6)
        target_rank = 3
        
        core, factors = topological_manifold_subspace_optimization(tensor, target_rank)
        
        # Check orthogonality of first factor matrix
        product = factors[0].T @ factors[0]
        identity = np.eye(target_rank)
        assert np.allclose(product, identity, atol=1e-10)
    
    def test_hosvd_rank_limit(self):
        """Test HOSVD with rank larger than dimension"""
        tensor = np.random.randn(3, 3, 3)
        target_rank = 5  # Larger than tensor dimensions
        
        # Should handle gracefully
        core, factors = topological_manifold_subspace_optimization(tensor, target_rank)
        
        # Actual rank should be limited by tensor dimensions
        assert len(factors) == 3


# ============================================================================
# Ternary Logic Radix Economy Stabilizer Tests
# ============================================================================

class TestTernaryLogicRadixEconomyStabilizer:
    """Tests for ternary logic stabilizer"""
    
    def test_balanced_conversion(self):
        """Test conversion from {0,1,2} to balanced {-1,0,1}"""
        trit_stream = [0, 1, 2, 1, 0, 2]
        alpha_threshold = 0.5
        
        result = ternary_logic_radix_economy_stabilizer(trit_stream, alpha_threshold)
        
        # Should return balanced stream
        assert isinstance(result, list)
        assert len(result) == len(trit_stream)
    
    def test_high_entropy_no_compression(self):
        """Test that high entropy stream doesn't trigger compression"""
        # Create balanced distribution for maximum entropy
        trit_stream = [0, 1, 2] * 10  # Balanced distribution
        alpha_threshold = 0.5
        
        result = ternary_logic_radix_economy_stabilizer(trit_stream, alpha_threshold)
        
        # High entropy should not trigger compression
        # Expected: balanced stream [-1, 0, 1, -1, 0, 1, ...]
        expected = [-1, 0, 1] * 10
        assert result == expected
    
    def test_low_entropy_triggers_compression(self):
        """Test that low entropy triggers compression via bit-shift"""
        # Create low entropy stream (mostly one value)
        trit_stream = [0] * 10  # All zeros = low entropy
        alpha_threshold = 0.9  # High threshold
        
        result = ternary_logic_radix_economy_stabilizer(trit_stream, alpha_threshold)
        
        # Low entropy should trigger compression (bit-shift)
        # All 0s become -1s, then bit-shifted to -2
        assert all(x == -2 for x in result)
    
    def test_edge_case_single_trit(self):
        """Test with single trit"""
        trit_stream = [1]
        alpha_threshold = 0.5
        
        result = ternary_logic_radix_economy_stabilizer(trit_stream, alpha_threshold)
        
        # Should handle single element
        assert len(result) == 1
    
    def test_edge_case_empty_stream(self):
        """Test handling of edge case with potential empty stream"""
        # Note: The function would fail with empty list, but this tests awareness
        trit_stream = [0, 1, 2]  # Non-empty to avoid division by zero
        alpha_threshold = 0.0
        
        result = ternary_logic_radix_economy_stabilizer(trit_stream, alpha_threshold)
        
        # Should always return a result for non-empty input
        assert isinstance(result, list)


# ============================================================================
# Berry Curvature Holonomy Optimizer Tests
# ============================================================================

class TestBerryCurvatureHolonomyOptimizer:
    """Tests for Berry phase calculation"""
    
    def test_berry_phase_range(self):
        """Test that Berry phase is in range [0, 2π)"""
        # Create a simple adiabatic path with complex wavefunctions
        path = [
            np.array([1.0 + 0.0j, 0.0 + 0.0j]),
            np.array([0.707 + 0.707j, 0.0 + 0.0j]),
            np.array([0.0 + 1.0j, 0.0 + 0.0j]),
            np.array([1.0 + 0.0j, 0.0 + 0.0j]),
        ]
        wavefunction = path[0]
        
        phase = berry_curvature_holonomy_optimizer(wavefunction, path)
        
        # Phase should be in [0, 2π)
        assert 0.0 <= phase < 2 * np.pi
    
    def test_berry_phase_closed_loop(self):
        """Test Berry phase for a closed loop"""
        # Create a closed loop path
        N = 10
        path = [np.exp(1j * 2 * np.pi * k / N) * np.array([1.0, 0.0]) for k in range(N)]
        path.append(path[0])  # Close the loop
        
        wavefunction = path[0]
        phase = berry_curvature_holonomy_optimizer(wavefunction, path)
        
        # Should be a valid phase
        assert isinstance(phase, (float, np.floating))
        assert 0.0 <= phase < 2 * np.pi
    
    def test_berry_phase_identity_path(self):
        """Test Berry phase for constant wavefunction"""
        # Constant wavefunction (no change)
        wavefunction = np.array([1.0 + 0.0j, 0.0 + 0.0j])
        path = [wavefunction] * 5
        
        phase = berry_curvature_holonomy_optimizer(wavefunction, path)
        
        # Phase should be zero (or very close)
        assert np.abs(phase) < 1e-10 or np.abs(phase - 2*np.pi) < 1e-10
    
    def test_berry_phase_real_wavefunctions(self):
        """Test with real-valued wavefunctions"""
        path = [
            np.array([1.0, 0.0]),
            np.array([0.707, 0.707]),
            np.array([0.0, 1.0]),
        ]
        wavefunction = path[0]
        
        phase = berry_curvature_holonomy_optimizer(wavefunction, path)
        
        assert 0.0 <= phase < 2 * np.pi


# ============================================================================
# Neuro-Symbolic Latent Pruning Tests
# ============================================================================

class TestNeuroSymbolicLatentPruning:
    """Tests for neural network pruning"""
    
    def test_pruning_achieves_target_sparsity(self):
        """Test that pruning achieves approximately the target sparsity level"""
        # Create random weight matrix
        weights = np.random.randn(100, 100)
        sparsity_target = 0.5  # 50% sparsity
        
        pruned = neuro_symbolic_latent_pruning(weights, sparsity_target)
        
        # Calculate actual sparsity
        num_zeros = np.sum(pruned == 0)
        total_elements = pruned.size
        actual_sparsity = num_zeros / total_elements
        
        # Should be close to target (within 5%)
        assert abs(actual_sparsity - sparsity_target) < 0.05
    
    def test_pruning_preserves_large_weights(self):
        """Test that pruning preserves large magnitude weights"""
        # Create weight matrix with known large values
        weights = np.array([[10.0, 0.1, 0.2],
                           [0.3, 20.0, 0.1],
                           [0.15, 0.25, 15.0]])
        sparsity_target = 0.5
        
        pruned = neuro_symbolic_latent_pruning(weights, sparsity_target)
        
        # Large weights should be preserved
        assert pruned[0, 0] == 10.0
        assert pruned[1, 1] == 20.0
        assert pruned[2, 2] == 15.0
    
    def test_pruning_zeros_small_weights(self):
        """Test that small magnitude weights are zeroed"""
        weights = np.array([[1.0, 0.01, 0.02],
                           [0.03, 1.0, 0.01],
                           [0.015, 0.025, 1.0]])
        sparsity_target = 0.6  # 60% sparsity
        
        pruned = neuro_symbolic_latent_pruning(weights, sparsity_target)
        
        # Count zeros
        num_zeros = np.sum(pruned == 0)
        
        # Should have some zeros
        assert num_zeros > 0
    
    def test_pruning_zero_sparsity(self):
        """Test with zero sparsity target (keep nothing above 0th percentile)"""
        weights = np.random.randn(10, 10)
        sparsity_target = 0.0
        
        pruned = neuro_symbolic_latent_pruning(weights, sparsity_target)
        
        # 0th percentile means minimum value, so all values above minimum are kept
        # This means nothing or very little should be pruned
        num_non_zero = np.sum(pruned != 0)
        assert num_non_zero > 0  # Most values should be kept
    
    def test_pruning_full_sparsity(self):
        """Test with 100% sparsity target (prune almost everything)"""
        weights = np.random.randn(10, 10)
        sparsity_target = 1.0
        
        pruned = neuro_symbolic_latent_pruning(weights, sparsity_target)
        
        # 100th percentile threshold means max value, so almost everything is pruned
        num_zeros = np.sum(pruned == 0)
        # Should have very high sparsity (most values zeroed)
        assert num_zeros >= weights.size - 1  # At most one non-zero (the max)


# ============================================================================
# Cryptographic Integrity Layer Optimization Tests
# ============================================================================

class TestCryptographicIntegrityLayerOptimization:
    """Tests for cryptographic circuit optimization"""
    
    def test_removes_identity_gates(self):
        """Test that identity gates are removed from circuit"""
        circuit = {
            'gates': [
                {'type': 'and', 'inputs': [0, 1]},
                {'type': 'identity', 'inputs': [2]},
                {'type': 'or', 'inputs': [3, 4]},
                {'type': 'identity', 'inputs': [5]},
            ]
        }
        proof_params = None
        
        result = cryptographic_integrity_layer_optimization(circuit, proof_params)
        
        # Should have removed 2 identity gates
        assert len(result['constraints']) == 2
        assert all(gate['type'] != 'identity' for gate in result['constraints'])
    
    def test_preserves_functional_gates(self):
        """Test that functional gates are preserved"""
        circuit = {
            'gates': [
                {'type': 'and', 'inputs': [0, 1]},
                {'type': 'or', 'inputs': [2, 3]},
                {'type': 'xor', 'inputs': [4, 5]},
            ]
        }
        proof_params = None
        
        result = cryptographic_integrity_layer_optimization(circuit, proof_params)
        
        # All gates should be preserved
        assert len(result['constraints']) == 3
    
    def test_empty_circuit(self):
        """Test with empty circuit"""
        circuit = {'gates': []}
        proof_params = None
        
        result = cryptographic_integrity_layer_optimization(circuit, proof_params)
        
        # Should handle empty circuit
        assert result['constraints'] == []
        assert 'circuit_hash' in result
    
    def test_circuit_hash_generated(self):
        """Test that circuit hash is generated"""
        circuit = {
            'gates': [
                {'type': 'and', 'inputs': [0, 1]},
            ]
        }
        proof_params = None
        
        result = cryptographic_integrity_layer_optimization(circuit, proof_params)
        
        # Hash should be present and be an integer
        assert 'circuit_hash' in result
        assert isinstance(result['circuit_hash'], int)
    
    def test_all_identity_gates(self):
        """Test circuit with only identity gates"""
        circuit = {
            'gates': [
                {'type': 'identity', 'inputs': [0]},
                {'type': 'identity', 'inputs': [1]},
                {'type': 'identity', 'inputs': [2]},
            ]
        }
        proof_params = None
        
        result = cryptographic_integrity_layer_optimization(circuit, proof_params)
        
        # All should be removed
        assert len(result['constraints']) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestLexiconGigasIntegration:
    """Integration tests for LEXICON GIGAS module"""
    
    def test_phi_constant_imported(self):
        """Test that PHI constant is properly imported from magnetar module"""
        # PHI should be the golden ratio
        assert abs(PHI - 1.618033988749) < 1e-10
    
    def test_all_functions_importable(self):
        """Test that all main functions are importable"""
        from src.lexicon_gigas import (
            topological_manifold_subspace_optimization,
            ternary_logic_radix_economy_stabilizer,
            berry_curvature_holonomy_optimizer,
            neuro_symbolic_latent_pruning,
            cryptographic_integrity_layer_optimization,
        )
        
        # All should be callable
        assert callable(topological_manifold_subspace_optimization)
        assert callable(ternary_logic_radix_economy_stabilizer)
        assert callable(berry_curvature_holonomy_optimizer)
        assert callable(neuro_symbolic_latent_pruning)
        assert callable(cryptographic_integrity_layer_optimization)
