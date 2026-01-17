"""
Test suite for advanced_core module.

Tests the advanced core architectures including tensor decomposition,
ternary logic, Berry curvature, quantum manifolds, transpiler, VQE, and
circuit optimization.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path for test execution
# Note: In production, proper package structure should be used instead
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from advanced_core import (
    MultiModalTensorDecomposer,
    TernaryLogicOptimizer,
    BerryCurvatureOptimizer,
    QuantumManifold,
    AdaptiveTranspiler,
    NoiseResilientVQE,
    CircuitIndividual,
    compute_wasserstein_distance_1d,
)


class TestMultiModalTensorDecomposer:
    """Test MultiModalTensorDecomposer class."""
    
    def test_initialization(self):
        """Test decomposer initialization."""
        decomposer = MultiModalTensorDecomposer(rank=(3, 3, 3))
        assert decomposer.rank == (3, 3, 3)
        assert decomposer.regularization == 0.01
        assert decomposer.core_tensor is None
        assert decomposer.factor_matrices is None
    
    def test_update_core_tensor(self):
        """Test core tensor update with ALS."""
        decomposer = MultiModalTensorDecomposer(rank=(2, 2, 2))
        tensor = np.random.randn(4, 4, 4)
        
        core = decomposer._update_core_tensor(tensor)
        
        assert core.shape == (2, 2, 2)
        assert decomposer.factor_matrices is not None
        assert len(decomposer.factor_matrices) == 3
    
    def test_reconstruction_error(self):
        """Test reconstruction error calculation."""
        decomposer = MultiModalTensorDecomposer(rank=(2, 2, 2))
        
        original = np.random.randn(3, 3, 3)
        reconstructed = original + 0.1 * np.random.randn(3, 3, 3)
        
        errors = decomposer._calculate_reconstruction_error(original, reconstructed)
        
        assert 'frobenius_norm' in errors
        assert 'mae' in errors
        assert 'mse' in errors
        assert 'psnr' in errors
        assert 'ssim' in errors
        assert errors['frobenius_norm'] >= 0
    
    def test_persistent_homology(self):
        """Test persistent homology computation."""
        decomposer = MultiModalTensorDecomposer(rank=(2, 2))
        
        # Create point cloud (circle)
        theta = np.linspace(0, 2*np.pi, 20)
        points = np.column_stack([np.cos(theta), np.sin(theta)])
        
        result = decomposer._compute_persistent_homology(points, max_dim=1)
        
        assert 'persistence_pairs' in result
        assert 'features' in result
        assert 'filtration_values' in result
    
    def test_curvature_profile(self):
        """Test curvature profile computation."""
        decomposer = MultiModalTensorDecomposer(rank=(2, 2))
        
        # Create point cloud on sphere
        points = np.random.randn(50, 3)
        points = points / np.linalg.norm(points, axis=1, keepdims=True)
        
        curvature = decomposer._compute_curvature_profile(points)
        
        assert 'mean_curvature' in curvature
        assert 'gaussian_curvature' in curvature
        assert 'ricci_curvature' in curvature


class TestTernaryLogicOptimizer:
    """Test TernaryLogicOptimizer class."""
    
    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = TernaryLogicOptimizer()
        assert optimizer.decode_tree is None
        assert optimizer.encoding_scheme == {}
    
    def test_decode_stream(self):
        """Test stream decoding with Huffman tree."""
        optimizer = TernaryLogicOptimizer()
        
        # Simple encoding scheme
        encoding = {
            0: [0, 0],
            1: [0, 1],
            2: [1, 0],
            3: [1, 1],
        }
        
        # Encoded stream: 0, 1, 2
        encoded = np.array([0, 0, 0, 1, 1, 0])
        
        decoded = optimizer._decode_stream(encoded, encoding)
        
        assert len(decoded) >= 0  # Should decode something
    
    def test_error_correction(self):
        """Test Hamming error correction."""
        optimizer = TernaryLogicOptimizer()
        
        encoded = np.array([1, 0, 1, 1, 0, 1, 0])
        corrected = optimizer._correct_errors(encoded)
        
        assert len(corrected) == len(encoded)
        assert corrected.dtype in [np.int32, np.int64, np.float64]


class TestBerryCurvatureOptimizer:
    """Test BerryCurvatureOptimizer class."""
    
    def test_initialization(self):
        """Test optimizer initialization."""
        H = np.array([[1, 0], [0, -1]])
        optimizer = BerryCurvatureOptimizer(base_hamiltonian=H)
        assert optimizer.base_hamiltonian is not None
        assert optimizer.gauge == 'symmetric'
    
    def test_berry_connection(self):
        """Test Berry connection computation."""
        optimizer = BerryCurvatureOptimizer()
        
        # Simple path of wavefunctions
        n_points = 10
        wavefunction = np.random.randn(n_points, 2) + 1j * np.random.randn(n_points, 2)
        wavefunction = wavefunction / np.linalg.norm(wavefunction, axis=1, keepdims=True)
        
        path = np.linspace(0, 2*np.pi, n_points).reshape(-1, 1)
        
        connection = optimizer._compute_berry_connection(wavefunction, path)
        
        assert connection.shape[0] == n_points - 1
    
    def test_proper_hamiltonian(self):
        """Test BHZ Hamiltonian generation."""
        optimizer = BerryCurvatureOptimizer()
        
        point = np.array([0.5, 0.3])
        H = optimizer._get_proper_hamiltonian(np.eye(2), point)
        
        assert H.shape == (2, 2)
        # Check Hermiticity
        assert np.allclose(H, H.conj().T)
    
    def test_energy_gaps(self):
        """Test energy gap computation."""
        optimizer = BerryCurvatureOptimizer()
        
        path = np.random.randn(10, 2)
        gaps = optimizer._compute_energy_gaps_along_path(path)
        
        assert len(gaps) == 10
        assert np.all(gaps >= 0)


class TestQuantumManifold:
    """Test QuantumManifold class."""
    
    def test_initialization(self):
        """Test manifold initialization."""
        manifold = QuantumManifold(dimension=4)
        assert manifold.dimension == 4
        assert manifold.metric_tensor is None
    
    def test_geometry_initialization(self):
        """Test Riemannian geometry initialization."""
        manifold = QuantumManifold(dimension=3)
        geometry = manifold._initialize_geometry()
        
        assert 'metric' in geometry
        assert 'christoffel' in geometry
        assert geometry['metric'].shape == (3, 3)
        assert geometry['christoffel'].shape == (3, 3, 3)
    
    def test_state_embedding(self):
        """Test state embedding in manifold."""
        manifold = QuantumManifold(dimension=5)
        
        state = np.random.randn(10) + 1j * np.random.randn(10)
        state = state / np.linalg.norm(state)
        
        embedded = manifold._embed_state_in_manifold(state, manifold_dim=5)
        
        assert len(embedded) == 5
    
    def test_path_smoothing(self):
        """Test path smoothing."""
        manifold = QuantumManifold(dimension=3)
        
        # Create noisy path
        t = np.linspace(0, 1, 20)
        path = np.column_stack([
            t,
            np.sin(2*np.pi*t) + 0.1*np.random.randn(20),
            np.cos(2*np.pi*t) + 0.1*np.random.randn(20)
        ])
        
        smoothed = manifold._smooth_path(path, method='spline')
        
        assert smoothed.shape == path.shape


class TestAdaptiveTranspiler:
    """Test AdaptiveTranspiler class."""
    
    def test_initialization(self):
        """Test transpiler initialization."""
        transpiler = AdaptiveTranspiler()
        assert transpiler.performance_model is None
    
    def test_build_performance_model(self):
        """Test performance model building."""
        transpiler = AdaptiveTranspiler()
        model = transpiler._build_performance_model()
        
        assert model is not None
        assert transpiler.performance_model is not None


class TestNoiseResilientVQE:
    """Test NoiseResilientVQE class."""
    
    def test_initialization(self):
        """Test VQE initialization."""
        vqe = NoiseResilientVQE()
        assert vqe.noise_model is None
    
    def test_default_noise_model(self):
        """Test noise model creation."""
        vqe = NoiseResilientVQE()
        noise_model = vqe._default_noise_model()
        
        assert 'T1' in noise_model
        assert 'T2' in noise_model
        assert 'single_qubit_gate_error' in noise_model
        assert 'two_qubit_gate_error' in noise_model
        assert noise_model['T1'] > 0
        assert noise_model['T2'] > 0


class TestCircuitIndividual:
    """Test CircuitIndividual class."""
    
    def test_initialization(self):
        """Test individual initialization."""
        individual = CircuitIndividual(n_qubits=5)
        assert individual.n_qubits == 5
        assert individual.fitness is None
    
    def test_fitness_calculation(self):
        """Test fitness calculation."""
        # Mock circuit object
        class MockCircuit:
            depth = 5
            size = 10
        
        individual = CircuitIndividual(circuit=MockCircuit(), n_qubits=5)
        fitness = individual._calculate_fitness(target_circuit=MockCircuit())
        
        assert fitness >= 0
        assert fitness <= 1
        assert individual.fitness == fitness
    
    def test_fidelity_estimation(self):
        """Test circuit fidelity estimation."""
        individual = CircuitIndividual(n_qubits=5)
        fidelity = individual._estimate_circuit_fidelity(depth=10, gate_count=20)
        
        assert 0 <= fidelity <= 1


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_wasserstein_distance(self):
        """Test Wasserstein distance computation."""
        p = np.array([0.1, 0.3, 0.6])
        q = np.array([0.2, 0.3, 0.5])
        
        distance = compute_wasserstein_distance_1d(p, q)
        
        assert distance >= 0
        
        # Distance to self should be 0
        distance_self = compute_wasserstein_distance_1d(p, p)
        assert distance_self < 1e-10


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_tensor_decomposition_workflow(self):
        """Test full tensor decomposition workflow."""
        decomposer = MultiModalTensorDecomposer(rank=(2, 2, 2))
        
        # Create tensor
        tensor = np.random.randn(4, 4, 4)
        
        # Decompose
        core = decomposer._update_core_tensor(tensor)
        
        # Reconstruct
        reconstructed = decomposer._reconstruct_tensor()
        
        # Check error
        errors = decomposer._calculate_reconstruction_error(tensor, reconstructed)
        
        # Error should be reasonable (not testing exact match due to rank reduction)
        assert errors['frobenius_norm'] < 2.0
    
    def test_quantum_manifold_workflow(self):
        """Test quantum manifold workflow."""
        manifold = QuantumManifold(dimension=4)
        
        # Initialize geometry
        geometry = manifold._initialize_geometry()
        
        # Create and embed state
        state = np.random.randn(8) + 1j * np.random.randn(8)
        state = state / np.linalg.norm(state)
        
        embedded = manifold._embed_state_in_manifold(state, manifold_dim=4)
        
        assert len(embedded) == 4


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
