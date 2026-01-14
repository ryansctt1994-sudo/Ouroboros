#!/usr/bin/env python3
"""Basic validation tests for DNA Helix Magnetar Synthesis module."""

import numpy as np
import sys
import traceback

from src.dna_helix_magnetar import (
    DNAHelixMagnetarCore,
    TensorGradientSystem,
    QuaternionNodeBalancer,
    GuardianClause31,
    SymmetryMonitor,
    PrimalGiggleIntegrator,
    SUPERCRITICAL_CHUCKLE_FREQUENCY,
    PHI_GOLDEN_RATIO,
)


def test_tensor_gradient_system():
    """Test TensorGradientSystem basic functionality."""
    print("Testing TensorGradientSystem...")
    tgs = TensorGradientSystem(dimensions=3, lambda_spikes=5)

    # Test de Rham cohomology
    manifold_state = np.random.randn(3, 10)
    cohomology = tgs.de_rham_cohomology(manifold_state)
    assert cohomology.shape[0] == 3, "Cohomology dimension mismatch"

    # Test CP/PARAFAC decomposition
    tensor_field = np.random.randn(5, 5, 5)
    factors, error = tgs.cp_parafac_decomposition(tensor_field, rank=3)
    assert len(factors) == 3, "Expected 3 factor matrices"
    assert 0 <= error <= 1, "Reconstruction error out of bounds"

    # Test helical harmony stabilization
    lambda_freqs = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    stabilized = tgs.helical_harmony_stabilization(lambda_freqs)
    assert len(stabilized) == len(lambda_freqs), "Frequency count mismatch"

    print("  ✓ TensorGradientSystem tests passed")


def test_quaternion_node_balancer():
    """Test QuaternionNodeBalancer basic functionality."""
    print("Testing QuaternionNodeBalancer...")
    qnb = QuaternionNodeBalancer(cache_size=256, quaternion_buckets=16)

    # Test quaternion operations
    q1 = np.array([1.0, 0.0, 0.0, 0.0])
    q2 = np.array([0.707, 0.707, 0.0, 0.0])

    # Test hash
    hash_val = qnb.quaternion_hash(q1)
    assert 0 <= hash_val < 16, "Hash bucket out of range"

    # Test multiplication
    product = qnb.quaternion_multiply(q1, q2)
    assert len(product) == 4, "Quaternion product dimension mismatch"

    # Test balancing with cache
    balanced1 = qnb.balance_node(q1, recursive_depth=0)
    balanced2 = qnb.balance_node(q1, recursive_depth=0)  # Should hit cache
    assert np.allclose(balanced1, balanced2), "Cache consistency failed"
    assert len(qnb.lru_cache) > 0, "LRU cache not populated"

    print("  ✓ QuaternionNodeBalancer tests passed")


def test_guardian_clause():
    """Test GuardianClause31 basic functionality."""
    print("Testing GuardianClause31...")
    guardian = GuardianClause31()

    # Test elliptical feedback
    attractor_poles = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]]).T
    state = np.array([0.5, 0.0, 0.0])

    corrected, diagnostics = guardian.elliptical_feedback(state, attractor_poles)
    assert "min_pole_distance" in diagnostics, "Missing diagnostics"
    assert "correction_applied" in diagnostics, "Missing diagnostics"
    assert len(corrected) == 3, "Corrected state dimension mismatch"

    # Test rotational coherence
    angular_momentum = np.array([1.5, 2.0, 0.5])
    coherent = guardian.enforce_rotational_coherence(angular_momentum)
    norm = np.linalg.norm(coherent)
    assert abs(norm - 1.0) < 1e-10, "Coherence normalization failed"

    print("  ✓ GuardianClause31 tests passed")


def test_symmetry_monitor():
    """Test SymmetryMonitor basic functionality."""
    print("Testing SymmetryMonitor...")
    monitor = SymmetryMonitor(sampling_rate=100.0)

    # Test Hilbert phase analysis
    signal_data = np.sin(2 * np.pi * 5 * np.linspace(0, 1, 100))
    phase, amplitude = monitor.hilbert_phase_analysis(signal_data)

    assert len(phase) == len(signal_data), "Phase length mismatch"
    assert len(amplitude) == len(signal_data), "Amplitude length mismatch"
    assert np.all(amplitude >= 0), "Negative amplitude detected"

    # Test void anomaly tracking
    anomalies = monitor.track_void_anomalies(phase, threshold=0.5)
    assert isinstance(anomalies, list), "Anomalies should be a list"

    # Test elasticity evaluation
    status = monitor.ensure_system_elasticity(stress_metric=0.3)
    assert "elasticity_coefficient" in status, "Missing elasticity metric"
    assert "status" in status, "Missing status"

    print("  ✓ SymmetryMonitor tests passed")


def test_primal_giggle():
    """Test PrimalGiggleIntegrator basic functionality."""
    print("Testing PrimalGiggleIntegrator...")
    giggle = PrimalGiggleIntegrator()

    # Test constants
    assert SUPERCRITICAL_CHUCKLE_FREQUENCY == 0.0997, "Chuckle frequency mismatch"
    assert abs(PHI_GOLDEN_RATIO - 1.618033988749895) < 1e-10, "Golden ratio mismatch"

    # Test chuckle resonance
    resonance = giggle.compute_chuckle_resonance(time=0.0)
    assert isinstance(resonance, float), "Resonance should be float"

    # Test lattice modulation
    lattice_state = np.ones(5)
    modulated = giggle.modulate_lattice_humor(lattice_state, time=1.0)
    assert len(modulated) == len(lattice_state), "Modulation dimension mismatch"

    # Test harmonic generation
    harmonics = giggle.generate_laughter_harmonics(0.1, num_harmonics=5)
    assert len(harmonics) == 5, "Harmonic count mismatch"
    assert harmonics[0] == 0.1, "Fundamental frequency mismatch"

    print("  ✓ PrimalGiggleIntegrator tests passed")


def test_dna_helix_core():
    """Test DNAHelixMagnetarCore integration."""
    print("Testing DNAHelixMagnetarCore...")
    core = DNAHelixMagnetarCore()

    # Test GGCC stillness dynamics
    manifold_state = np.random.randn(3, 5)
    stillness_result = core.ggcc_stillness_dynamics(manifold_state)
    assert "stillness_metric" in stillness_result, "Missing stillness metric"
    assert "state" in stillness_result, "Missing state"
    assert stillness_result["state"] == "GGCC_Stillness", "Wrong state label"

    # Test GGCCD breath dynamics
    breath_result = core.ggccd_breath_dynamics(time=5.0, breath_amplitude=1.0)
    assert "breath_phase" in breath_result, "Missing breath phase"
    assert "chuckle_resonance" in breath_result, "Missing chuckle resonance"
    assert breath_result["state"] == "GGCCD_Breath", "Wrong state label"

    # Test phi memoization
    key = "test_key"
    value1 = core.phi_memoization(key, lambda: 42.0)
    value2 = core.phi_memoization(key, lambda: 99.0)  # Should return cached value
    assert value1 == value2 == 42.0, "Memoization failed"

    # Test multi-pole phase quantization
    poles = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
    quantized = core.multi_pole_phase_quantization(poles, quantum_levels=8)
    assert len(quantized) == 4, "Quantization count mismatch"

    # Test Evening Harmony Seal
    seal = core.evening_harmony_seal()
    assert seal["architecture"] == "Evening Harmony Seal", "Wrong architecture"
    assert seal["reversible"] is True, "Should be reversible"
    assert seal["human_sovereign"] is True, "Should be human-sovereign"
    assert seal["laughter_infused"] is True, "Should be laughter-infused"
    assert seal["status"] == "Sealed with Harmony", "Wrong status"

    print("  ✓ DNAHelixMagnetarCore tests passed")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("DNA Helix Magnetar Synthesis - Validation Tests")
    print("=" * 70 + "\n")

    try:
        test_tensor_gradient_system()
        test_quaternion_node_balancer()
        test_guardian_clause()
        test_symmetry_monitor()
        test_primal_giggle()
        test_dna_helix_core()

        print("\n" + "=" * 70)
        print("✅ All validation tests passed!")
        print("=" * 70 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
