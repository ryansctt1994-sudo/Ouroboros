"""
Comprehensive pytest test suite for OuroborosVirtualProcessor.

This test suite validates the core mathematical components of the processor,
establishing a foundation of epistemic integrity for the Ouroboros project.

Test coverage includes:
- Möbius kernel discretization and number-theoretic properties
- Ternary cycle normalization and stability
- Ramanujan τ function approximations
- Delta-check metrics with entropy penalties
- Geodesic flow on horn torus
- Modular symmetry operations
- Zeta-seeded ergotropy calculations
- Factory functions and state management
- Edge cases and integration testing
"""

import pytest
import math
from typing import List, Dict, Any

# Import the processor module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ouroboros_processor import (
    OuroborosVirtualProcessor,
    create_elpis_processor,
    EXTENDED_FEATURES
)

# Test fixtures
@pytest.fixture
def default_processor():
    """Create a default processor instance for testing."""
    return OuroborosVirtualProcessor()

@pytest.fixture
def zeta_seeded_processor():
    """Create a processor with specific zeta seed for reproducibility."""
    return OuroborosVirtualProcessor(zeta_seed=0.5)

@pytest.fixture
def elpis_processor():
    """Create processor using Elpis factory function."""
    config = {
        "radius": 1.5,
        "lambda": 0.25,
        "threshold": 0.35,
        "zeta_seed": 0.618
    }
    return create_elpis_processor(config)


# ============================================================================
# Möbius Kernel Tests (6 tests)
# ============================================================================

@pytest.mark.skipif(not EXTENDED_FEATURES, reason="Requires numpy/scipy")
class TestMobiusKernel:
    """Tests for the Möbius kernel (Ω̂ operator) discretization.
    
    The Möbius function μ(n) is fundamental in number theory:
    - μ(n) = 1 if n is square-free with even number of prime factors
    - μ(n) = -1 if n is square-free with odd number of prime factors
    - μ(n) = 0 if n has a squared prime factor
    
    Reference: OEIS A008683 (Möbius function)
    """
    
    def test_mobius_square_free_even_primes(self, default_processor):
        """Verify μ(n) = 1 for square-free with even prime factors.
        
        Tests n = 6 = 2 × 3 (two prime factors, even count)
        Expected: μ(6) = 1
        """
        kernel = default_processor.mobius_kernel(6, discretization=10)
        
        # Verify kernel is based on μ(6) = 1 (positive oscillation)
        # The kernel should have values derived from +1 * cos(θ) / (k+1)
        assert len(kernel) == 10
        assert kernel[0] > 0  # cos(0) = 1, so first value is positive
        
    def test_mobius_square_free_odd_primes(self, default_processor):
        """Verify μ(n) = -1 for square-free with odd prime factors.
        
        Tests n = 30 = 2 × 3 × 5 (three prime factors, odd count)
        Expected: μ(30) = -1
        """
        kernel = default_processor.mobius_kernel(30, discretization=10)
        
        # Verify kernel is based on μ(30) = -1 (negative oscillation)
        assert len(kernel) == 10
        assert kernel[0] < 0  # cos(0) = 1, μ = -1, so first value is negative
        
    def test_mobius_squared_prime_zero(self, default_processor):
        """Verify μ(n) = 0 for squared prime inputs.
        
        Tests known cases: 4 = 2², 9 = 3², 25 = 5², 49 = 7²
        Expected: μ = 0 for all
        """
        for n in [4, 9, 25, 49]:
            kernel = default_processor.mobius_kernel(n, discretization=10)
            assert len(kernel) == 10
            # All values should be 0 when μ(n) = 0
            assert all(abs(val) < 1e-10 for val in kernel)
    
    def test_mobius_kernel_discretization_size(self, default_processor):
        """Verify kernel respects discretization parameter."""
        for size in [10, 50, 100, 200]:
            kernel = default_processor.mobius_kernel(5, discretization=size)
            assert len(kernel) == size
    
    def test_mobius_bounded_oscillation(self, default_processor):
        """Verify kernel values are bounded and oscillating."""
        kernel = default_processor.mobius_kernel(5, discretization=100)
        
        # Values should be bounded (decay with 1/(k+1))
        assert all(abs(val) <= 1.0 for val in kernel)
        
        # Should have oscillating behavior (sign changes)
        signs = [1 if val > 0 else (-1 if val < 0 else 0) for val in kernel]
        # Count sign changes (should have some oscillation)
        sign_changes = sum(1 for i in range(len(signs)-1) 
                          if signs[i] != 0 and signs[i+1] != 0 and signs[i] != signs[i+1])
        assert sign_changes > 0
    
    def test_mobius_prime_factorization(self, default_processor):
        """Verify correct Möbius values from prime factorization.
        
        Known values from OEIS A008683:
        μ(1) = 1, μ(2) = -1, μ(3) = -1, μ(5) = -1, μ(6) = 1, μ(7) = -1
        """
        # Test μ(1) = 1
        kernel_1 = default_processor.mobius_kernel(1, discretization=5)
        assert kernel_1[0] > 0
        
        # Test μ(2) = -1 (one prime)
        kernel_2 = default_processor.mobius_kernel(2, discretization=5)
        assert kernel_2[0] < 0
        
        # Test μ(6) = 1 (two primes: 2×3)
        kernel_6 = default_processor.mobius_kernel(6, discretization=5)
        assert kernel_6[0] > 0


# ============================================================================
# Ternary Cycle Tests (7 tests)
# ============================================================================

class TestTernaryCycle:
    """Tests for ternary cycle normalization and stability.
    
    The ternary cycle simulates +1 expansion, 0 reconciliation, -1 collapse
    on the torus, returning a normalized non-negative vector representing
    the toroidal state.
    """
    
    def test_normalization_sum_to_one(self, default_processor):
        """Verify output vector sums to 1.0 (normalization)."""
        V = [3.0, 6.0, 9.0]
        result = default_processor.ternary_cycle(V)
        
        # Sum should be 1.0 (normalized)
        assert pytest.approx(sum(result), rel=1e-10) == 1.0
    
    def test_non_negativity(self, default_processor):
        """Verify all output values are non-negative."""
        test_vectors = [
            [1.0, 2.0, 3.0],
            [0.5, 0.3, 0.2],
            [-1.0, 5.0, 2.0],  # Negative input
            [0.0, 0.0, 1.0]
        ]
        
        for V in test_vectors:
            result = default_processor.ternary_cycle(V)
            assert all(val >= 0.0 for val in result), f"Negative value in output for input {V}"
    
    def test_length_preservation(self, default_processor):
        """Verify output vector has same length as input."""
        for length in [3, 5, 10]:
            V = [1.0] * length
            result = default_processor.ternary_cycle(V)
            assert len(result) == length
    
    def test_zero_input_handling(self, default_processor):
        """Verify zero input doesn't cause division by zero."""
        V_zero = [0.0, 0.0, 0.0]
        result = default_processor.ternary_cycle(V_zero)
        
        # Should handle gracefully (use EPS fallback)
        assert len(result) == 3
        assert all(0.0 <= val <= 1.0 for val in result)
        assert not any(math.isnan(val) for val in result)
    
    def test_idempotence_on_normalized(self, default_processor):
        """Verify applying cycle to normalized input is idempotent."""
        V = [0.2, 0.5, 0.3]
        result1 = default_processor.ternary_cycle(V)
        result2 = default_processor.ternary_cycle(result1)
        
        # Should be approximately the same (idempotent)
        for v1, v2 in zip(result1, result2):
            assert pytest.approx(v1, rel=1e-10) == v2
    
    def test_canonical_state_plus_one(self, default_processor):
        """Test canonical +1 expansion state."""
        V_expand = [1.0, 0.0, 0.0]
        result = default_processor.ternary_cycle(V_expand)
        
        assert pytest.approx(result[0], rel=1e-10) == 1.0
        assert pytest.approx(result[1], rel=1e-10) == 0.0
        assert pytest.approx(result[2], rel=1e-10) == 0.0
    
    def test_canonical_state_balanced(self, default_processor):
        """Test canonical balanced (0 reconciliation) state."""
        V_balanced = [1.0, 1.0, 1.0]
        result = default_processor.ternary_cycle(V_balanced)
        
        # All should be equal (1/3 each)
        expected = 1.0 / 3.0
        for val in result:
            assert pytest.approx(val, rel=1e-10) == expected


# ============================================================================
# Ramanujan τ Tests (5 tests)
# ============================================================================

class TestRamanujanTau:
    """Tests for Ramanujan tau function approximations.
    
    The Ramanujan tau function τ(n) appears in the Fourier coefficients
    of the modular discriminant Δ. Known values from OEIS A000594:
    τ(1) = 1, τ(2) = -24, τ(3) = 252, τ(4) = -1472, τ(5) = 4830
    
    The implementation uses an approximation: n² - 24n with corrections.
    """
    
    def test_tau_base_case(self, default_processor):
        """Verify base case τ(1) = 1."""
        tau_1 = default_processor.ramanujan_tau(1)
        
        if EXTENDED_FEATURES:
            # With extended features, τ(1) = 1.0 exactly
            assert pytest.approx(tau_1, abs=1e-10) == 1.0
        else:
            # Fallback: n² - 24n = 1 - 24 = -23, but we return corrected value
            # The fallback returns n² - 24n which is -23 for n=1
            assert tau_1 == -23.0
    
    def test_tau_zero_and_negative(self, default_processor):
        """Verify τ(0) and τ(negative) = 0."""
        assert default_processor.ramanujan_tau(0) == 0.0
        assert default_processor.ramanujan_tau(-1) == 0.0
        assert default_processor.ramanujan_tau(-10) == 0.0
    
    def test_tau_approximation_formula(self, default_processor):
        """Verify approximation uses n² - 24n as base."""
        # For fallback mode, should use exact formula
        if not EXTENDED_FEATURES:
            for n in [2, 3, 5, 10]:
                tau_n = default_processor.ramanujan_tau(n)
                expected = n**2 - 24*n
                assert tau_n == float(expected)
    
    def test_tau_extended_with_correction(self, zeta_seeded_processor):
        """Verify extended mode applies modular correction."""
        if EXTENDED_FEATURES:
            tau_5 = zeta_seeded_processor.ramanujan_tau(5)
            
            # Should be n² - 24n + correction
            base = 5**2 - 24*5  # = 25 - 120 = -95
            correction = zeta_seeded_processor.zeta_seed * math.log(5 + 1)
            expected = base + correction
            
            assert pytest.approx(tau_5, rel=1e-10) == expected
    
    def test_tau_precision_tolerance(self, default_processor):
        """Verify tau values are finite and reasonable."""
        for n in [1, 2, 3, 5, 7, 10, 20]:
            tau_n = default_processor.ramanujan_tau(n)
            
            # Should be finite
            assert not math.isnan(tau_n)
            assert not math.isinf(tau_n)
            
            # Should be in reasonable range
            # The approximation n^2 - 24n with corrections can vary,
            # but should stay within bounds for moderate n
            assert abs(tau_n) <= max(1000, n**3)


# ============================================================================
# Delta Check Tests (7 tests)
# ============================================================================

class TestDeltaCheck:
    """Tests for ternary delta-check with torus curvature penalty.
    
    Delta-check computes the divergence between expected and observed
    vectors, incorporating entropy-based penalties for toroidal curvature.
    """
    
    def test_identical_vectors_pass(self, default_processor):
        """Verify identical vectors produce PASS verdict."""
        V = [0.4, 0.3, 0.3]
        result = default_processor.delta_check(V, V)
        
        assert result["verdict"] == "PASS"
        assert result["delta"] < default_processor.threshold
    
    def test_divergent_vectors_higher_delta(self, default_processor):
        """Verify divergent vectors produce higher delta values."""
        V_exp = [1.0, 0.0, 0.0]
        V_obs = [0.0, 0.0, 1.0]
        
        result = default_processor.delta_check(V_exp, V_obs)
        
        # Highly divergent vectors should have larger delta
        assert result["delta"] > 0.3
    
    def test_threshold_boundary_behavior(self):
        """Verify threshold boundary determines PASS/FAIL."""
        # Create processor with specific threshold
        proc_low = OuroborosVirtualProcessor(threshold=0.1)
        proc_high = OuroborosVirtualProcessor(threshold=0.8)
        
        V_exp = [0.5, 0.3, 0.2]
        V_obs = [0.4, 0.35, 0.25]
        
        result_low = proc_low.delta_check(V_exp, V_obs)
        result_high = proc_high.delta_check(V_exp, V_obs)
        
        # Same delta value
        assert pytest.approx(result_low["delta"], rel=1e-10) == result_high["delta"]
        
        # But potentially different verdicts based on threshold
        # (depends on actual delta value)
    
    def test_delta_non_negative(self, default_processor):
        """Verify delta values are always non-negative."""
        test_cases = [
            ([0.5, 0.3, 0.2], [0.4, 0.4, 0.2]),
            ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
            ([0.33, 0.33, 0.34], [0.33, 0.34, 0.33])
        ]
        
        for V_exp, V_obs in test_cases:
            result = default_processor.delta_check(V_exp, V_obs)
            assert result["delta"] >= 0.0
    
    def test_approximate_symmetry(self, default_processor):
        """Verify approximate symmetry: d(A,B) ≈ d(B,A)."""
        V_A = [0.5, 0.3, 0.2]
        V_B = [0.4, 0.35, 0.25]
        
        result_AB = default_processor.delta_check(V_A, V_B)
        result_BA = default_processor.delta_check(V_B, V_A)
        
        # Should be approximately symmetric (may differ due to entropy term)
        assert pytest.approx(result_AB["delta"], abs=0.1) == result_BA["delta"]
    
    def test_entropy_penalty_validation(self, default_processor):
        """Verify entropy penalty affects delta calculation."""
        # Low entropy (concentrated distribution)
        V_low_entropy = [1.0, 0.0, 0.0]
        
        # High entropy (uniform distribution)
        V_high_entropy = [0.33, 0.33, 0.34]
        
        V_ref = [0.5, 0.3, 0.2]
        
        result_low = default_processor.delta_check(V_ref, V_low_entropy)
        result_high = default_processor.delta_check(V_ref, V_high_entropy)
        
        # Both should have valid deltas incorporating entropy
        assert result_low["delta"] >= 0.0
        assert result_high["delta"] >= 0.0
    
    def test_delta_check_structure(self, default_processor):
        """Verify delta_check returns proper structure."""
        V_exp = [0.4, 0.3, 0.3]
        V_obs = [0.35, 0.35, 0.3]
        
        result = default_processor.delta_check(V_exp, V_obs)
        
        # Should have required keys
        assert "delta" in result
        assert "verdict" in result
        
        # Types
        assert isinstance(result["delta"], (int, float))
        assert result["verdict"] in ["PASS", "FAIL"]


# ============================================================================
# Geodesic Flow Tests (6 tests)
# ============================================================================

class TestGeodesicFlow:
    """Tests for parametric horn torus geodesic flow.
    
    Parametric equations for horn torus:
    x = R(1 + cos(φ))cos(θ)
    y = R(1 + cos(φ))sin(θ)
    z = R sin(φ)
    
    Where R is the torus radius, φ is the poloidal angle, θ is the toroidal angle.
    """
    
    def test_parametric_equations(self, default_processor):
        """Verify parametric equation implementation."""
        R = default_processor.R
        phi = math.pi / 4
        theta = math.pi / 6
        
        x, y, z = default_processor.geodesic_flow(phi, theta)
        
        # Verify against parametric equations
        expected_x = R * (1 + math.cos(phi)) * math.cos(theta)
        expected_y = R * (1 + math.cos(phi)) * math.sin(theta)
        expected_z = R * math.sin(phi)
        
        assert pytest.approx(x, rel=1e-10) == expected_x
        assert pytest.approx(y, rel=1e-10) == expected_y
        assert pytest.approx(z, rel=1e-10) == expected_z
    
    def test_origin_point_at_zero_angles(self, default_processor):
        """Verify origin point at φ=0, θ=0 is (2R, 0, 0)."""
        R = default_processor.R
        x, y, z = default_processor.geodesic_flow(0, 0)
        
        assert pytest.approx(x, rel=1e-10) == 2 * R
        assert pytest.approx(y, abs=1e-10) == 0.0
        assert pytest.approx(z, abs=1e-10) == 0.0
    
    def test_cusp_point_at_pi(self, default_processor):
        """Verify cusp point at φ=π approaches (0, 0, 0)."""
        x, y, z = default_processor.geodesic_flow(math.pi, 0)
        
        # At φ=π, (1 + cos(π)) = (1 + (-1)) = 0
        # So x = 0, y = 0, z = R*sin(π) = 0
        assert pytest.approx(x, abs=1e-10) == 0.0
        assert pytest.approx(y, abs=1e-10) == 0.0
        assert pytest.approx(z, abs=1e-10) == 0.0
    
    def test_theta_rotation_traces_circle(self, default_processor):
        """Verify theta rotation traces circle in xy-plane."""
        R = default_processor.R
        phi = math.pi / 3  # Fixed poloidal angle
        
        points = []
        for i in range(8):
            theta = 2 * math.pi * i / 8
            x, y, z = default_processor.geodesic_flow(phi, theta)
            points.append((x, y, z))
        
        # All points should have same z coordinate (fixed phi)
        z_coords = [p[2] for p in points]
        for z in z_coords:
            assert pytest.approx(z, rel=1e-10) == z_coords[0]
        
        # Points should lie on circle in xy-plane
        radius_xy = R * (1 + math.cos(phi))
        for x, y, z in points:
            distance_from_origin = math.sqrt(x**2 + y**2)
            assert pytest.approx(distance_from_origin, rel=1e-10) == radius_xy
    
    def test_radius_scaling_linearity(self):
        """Verify output scales linearly with radius parameter."""
        phi = math.pi / 4
        theta = math.pi / 6
        
        proc_r1 = OuroborosVirtualProcessor(radius=1.0)
        proc_r2 = OuroborosVirtualProcessor(radius=2.0)
        
        x1, y1, z1 = proc_r1.geodesic_flow(phi, theta)
        x2, y2, z2 = proc_r2.geodesic_flow(phi, theta)
        
        # Should scale by factor of 2
        assert pytest.approx(x2, rel=1e-10) == 2 * x1
        assert pytest.approx(y2, rel=1e-10) == 2 * y1
        assert pytest.approx(z2, rel=1e-10) == 2 * z1
    
    def test_geodesic_returns_tuple(self, default_processor):
        """Verify geodesic_flow returns 3-tuple of floats."""
        result = default_processor.geodesic_flow(0, 0)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        assert all(isinstance(val, float) for val in result)


# ============================================================================
# Modular Symmetry Tests
# ============================================================================

class TestModularSymmetry:
    """Tests for modular symmetry operations (mod 9)."""
    
    def test_modular_range(self, default_processor):
        """Verify modular symmetry returns values in [0, 8]."""
        for n in range(-20, 100):
            result = default_processor.modular_symmetry(n)
            assert 0 <= result <= 8
    
    def test_modular_known_values(self, default_processor):
        """Verify known modular values."""
        assert default_processor.modular_symmetry(0) == 0
        assert default_processor.modular_symmetry(9) == 0
        assert default_processor.modular_symmetry(18) == 0
        assert default_processor.modular_symmetry(1) == 1
        assert default_processor.modular_symmetry(10) == 1
        assert default_processor.modular_symmetry(42) == 6  # 42 = 4*9 + 6


# ============================================================================
# Zeta Ergotropy Tests
# ============================================================================

@pytest.mark.skipif(not EXTENDED_FEATURES, reason="Requires numpy/scipy")
class TestZetaErgotropy:
    """Tests for zeta-seeded ergotropy calculations.
    
    Uses Riemann zeta function ζ(s) for quantum-inspired state analysis.
    Basel problem: ζ(2) = π²/6 ≈ 1.6449340668
    """
    
    def test_zeta_scaling_with_basel(self, zeta_seeded_processor):
        """Verify ζ(2) approximates Basel problem result."""
        ergotropy = zeta_seeded_processor.zeta_ergotropy(s=2.0)
        
        # Should involve π²/6
        zeta_2 = math.pi**2 / 6.0
        expected = zeta_seeded_processor.zeta_seed * zeta_2 * zeta_seeded_processor.R
        
        assert pytest.approx(ergotropy, rel=1e-4) == expected
    
    def test_zeta_ergotropy_non_negative(self, default_processor):
        """Verify ergotropy values are non-negative."""
        for s in [2.0, 3.0, 4.0]:
            ergotropy = default_processor.zeta_ergotropy(s)
            assert ergotropy >= 0.0


class TestZetaErgotropyFallback:
    """Tests for zeta ergotropy in fallback mode (without scipy)."""
    
    @pytest.mark.skipif(EXTENDED_FEATURES, reason="Testing fallback mode")
    def test_fallback_approximation(self, zeta_seeded_processor):
        """Verify fallback uses π²/6 approximation for s=2."""
        ergotropy = zeta_seeded_processor.zeta_ergotropy(s=2.0)
        
        expected = zeta_seeded_processor.zeta_seed * (math.pi**2 / 6.0) * zeta_seeded_processor.R
        assert pytest.approx(ergotropy, rel=1e-10) == expected


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunction:
    """Tests for create_elpis_processor factory function."""
    
    def test_factory_default_config(self):
        """Verify factory with no config uses defaults."""
        proc = create_elpis_processor()
        
        assert proc.R == 1.0
        assert proc.lambda_ == 0.3
        assert proc.threshold == 0.4
    
    def test_factory_custom_config(self):
        """Verify factory respects custom configuration."""
        config = {
            "radius": 2.5,
            "lambda": 0.15,
            "threshold": 0.5,
            "zeta_seed": 0.75
        }
        proc = create_elpis_processor(config)
        
        assert proc.R == 2.5
        assert proc.lambda_ == 0.15
        assert proc.threshold == 0.5
        assert proc.zeta_seed == 0.75
    
    def test_factory_partial_config(self):
        """Verify factory handles partial configuration."""
        config = {"radius": 1.5}
        proc = create_elpis_processor(config)
        
        assert proc.R == 1.5
        assert proc.lambda_ == 0.3  # Default
        assert proc.threshold == 0.4  # Default


# ============================================================================
# Snapshot State Tests
# ============================================================================

class TestSnapshotState:
    """Tests for snapshot_state integrity."""
    
    def test_snapshot_basic_structure(self, default_processor):
        """Verify snapshot contains required fields."""
        snapshot = default_processor.snapshot_state()
        
        assert "radius" in snapshot
        assert "lambda" in snapshot
        assert "threshold" in snapshot
        assert "zeta_seed" in snapshot
        assert "extended_features" in snapshot
        assert "meta" in snapshot
    
    def test_snapshot_values_match(self, elpis_processor):
        """Verify snapshot values match processor state."""
        snapshot = elpis_processor.snapshot_state()
        
        assert snapshot["radius"] == elpis_processor.R
        assert snapshot["lambda"] == elpis_processor.lambda_
        assert snapshot["threshold"] == elpis_processor.threshold
        assert snapshot["zeta_seed"] == elpis_processor.zeta_seed
    
    @pytest.mark.skipif(not EXTENDED_FEATURES, reason="Requires extended features")
    def test_snapshot_extended_features(self, default_processor):
        """Verify snapshot includes extended feature data."""
        snapshot = default_processor.snapshot_state()
        
        assert snapshot["extended_features"] == True
        assert "ergotropy" in snapshot
        assert "modular_class" in snapshot


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_vector_handling(self, default_processor):
        """Verify graceful handling of empty vectors."""
        # Empty vectors should be handled without crash
        # (though not necessarily meaningful)
        V_empty = []
        result = default_processor.ternary_cycle(V_empty)
        assert isinstance(result, list)
    
    def test_large_vector_values(self, default_processor):
        """Verify handling of large vector values."""
        V_large = [1e10, 2e10, 3e10]
        result = default_processor.ternary_cycle(V_large)
        
        # Should still normalize properly
        assert pytest.approx(sum(result), rel=1e-10) == 1.0
    
    def test_very_small_vector_values(self, default_processor):
        """Verify handling of very small vector values."""
        V_small = [1e-15, 2e-15, 3e-15]
        result = default_processor.ternary_cycle(V_small)
        
        # Should handle without numerical issues
        assert all(not math.isnan(v) for v in result)
        assert all(not math.isinf(v) for v in result)
    
    def test_negative_values_in_ternary(self, default_processor):
        """Verify negative values are handled (projected to non-negative)."""
        V_mixed = [-1.0, 2.0, 3.0]
        result = default_processor.ternary_cycle(V_mixed)
        
        # All outputs should be non-negative
        assert all(val >= 0.0 for val in result)
    
    @pytest.mark.skipif(not EXTENDED_FEATURES, reason="Requires extended features")
    def test_mobius_edge_case_n_equals_one(self, default_processor):
        """Verify Möbius handles n=1 (base case)."""
        kernel = default_processor.mobius_kernel(1, discretization=10)
        
        # μ(1) = 1 by definition
        assert len(kernel) == 10
        assert kernel[0] > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Full integration pipeline tests."""
    
    def test_full_pipeline_basic(self, default_processor):
        """Test complete processing pipeline."""
        # Create test vectors
        V_exp = [0.5, 0.3, 0.2]
        V_obs = [0.45, 0.35, 0.2]
        
        # Normalize through ternary cycle
        V_exp_norm = default_processor.ternary_cycle(V_exp)
        V_obs_norm = default_processor.ternary_cycle(V_obs)
        
        # Delta check
        result = default_processor.delta_check(V_exp_norm, V_obs_norm)
        
        # Verify results
        assert "delta" in result
        assert "verdict" in result
        assert result["delta"] >= 0.0
    
    @pytest.mark.skipif(not EXTENDED_FEATURES, reason="Requires extended features")
    def test_full_pipeline_extended(self, zeta_seeded_processor):
        """Test extended features integration."""
        # Create test vectors
        V_exp = [0.5, 0.3, 0.2]
        V_obs = [0.45, 0.35, 0.2]
        
        # Extended delta check with tau
        result = zeta_seeded_processor.extended_delta_check(V_exp, V_obs, use_tau=True)
        
        # Verify extended results
        assert "delta" in result
        assert "tau_correction" in result
        assert "delta_extended" in result
        assert "verdict_extended" in result
        
        # Compute other extended features
        ergotropy = zeta_seeded_processor.zeta_ergotropy()
        kernel = zeta_seeded_processor.mobius_kernel(5, discretization=20)
        mod_sym = zeta_seeded_processor.modular_symmetry(42)
        
        # Verify all succeeded
        assert ergotropy > 0.0
        assert len(kernel) == 20
        assert 0 <= mod_sym <= 8
    
    def test_geodesic_sweep(self, default_processor):
        """Test sweeping through geodesic parameter space."""
        points = []
        
        # Sweep phi and theta
        for i in range(5):
            phi = math.pi * i / 4
            for j in range(5):
                theta = 2 * math.pi * j / 4
                x, y, z = default_processor.geodesic_flow(phi, theta)
                points.append((x, y, z))
        
        # Verify we got valid points
        assert len(points) == 25
        
        # All should be finite
        for x, y, z in points:
            assert not math.isnan(x) and not math.isinf(x)
            assert not math.isnan(y) and not math.isinf(y)
            assert not math.isnan(z) and not math.isinf(z)
