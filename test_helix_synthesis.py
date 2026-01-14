"""
Test suite for Helix DNA Magnetar Synthesis features.

This module tests the new features added to OuroborosVirtualProcessor:
- Tensor-integrated gradient systems
- Quaternion hypercomplex memory
- Guardian elliptical validation
- Phase-lock monitoring
- Topological analysis
"""

import math
import sys
from ouroboros_processor import OuroborosVirtualProcessor, EXTENDED_FEATURES

# Test constants
GRADIENT_TOLERANCE = 1e-10  # Tolerance for gradient component comparisons
QUATERNION_TOLERANCE = 1e-6  # Tolerance for quaternion normalization


def test_gradient_field_computation():
    """Test tensor-integrated gradient field computation."""
    print("Testing gradient field computation...")
    processor = OuroborosVirtualProcessor(radius=1.0)

    # Test at multiple points
    test_points = [
        (0.0, 0.0),  # Origin point
        (math.pi / 4, math.pi / 4),  # Mid-range
        (math.pi / 2, math.pi / 2),  # Quarter turn
    ]

    for phi, theta in test_points:
        grad_phi, grad_theta, magnitude = processor.compute_gradient_field(phi, theta)

        # Gradients should be positive and finite
        assert grad_phi >= 0, f"grad_phi should be non-negative at ({phi}, {theta})"
        assert grad_theta >= 0, f"grad_theta should be non-negative at ({phi}, {theta})"
        assert magnitude >= 0, f"magnitude should be non-negative at ({phi}, {theta})"
        assert math.isfinite(
            magnitude
        ), f"magnitude should be finite at ({phi}, {theta})"

        # Magnitude should be at least as large as either component
        assert magnitude >= grad_phi or abs(magnitude - grad_phi) < GRADIENT_TOLERANCE
        assert (
            magnitude >= grad_theta or abs(magnitude - grad_theta) < GRADIENT_TOLERANCE
        )

    print("✓ Gradient field computation tests passed")
    return True


def test_quaternion_state_representation():
    """Test quaternion hypercomplex memory."""
    print("Testing quaternion state representation...")
    processor = OuroborosVirtualProcessor(radius=1.0, zeta_seed=0.618)

    phi, theta = math.pi / 4, math.pi / 3
    w, x, y, z = processor.quaternion_state(phi, theta)

    # Quaternion should be normalized (unit quaternion)
    magnitude = math.sqrt(w**2 + x**2 + y**2 + z**2)
    assert (
        abs(magnitude - 1.0) < QUATERNION_TOLERANCE
    ), f"Quaternion should be normalized, got {magnitude}"

    # Test caching - calling again should return same result
    w2, x2, y2, z2 = processor.quaternion_state(phi, theta)
    assert (w, x, y, z) == (w2, x2, y2, z2), "Cached quaternion should match"

    # Test cache population
    assert len(processor._quaternion_cache) > 0, "Cache should be populated"

    print("✓ Quaternion state representation tests passed")
    return True


def test_guardian_elliptical_check():
    """Test Guardian Clause 3.1 elliptical validation."""
    print("Testing guardian elliptical check...")
    processor = OuroborosVirtualProcessor(radius=1.0)

    # Test at outer equator (should be elliptical and safe)
    result = processor.guardian_elliptical_check(0.0, gamma=0.98)
    assert result["is_elliptical"], "Outer equator should be elliptical"
    assert result["safe"], "Outer equator should be safe"
    assert result["curvature"] > 0, "Outer equator should have positive curvature"

    # Test near throat (may not be elliptical)
    result_throat = processor.guardian_elliptical_check(math.pi, gamma=0.98)
    assert result_throat["curvature"] < 0, "Throat should have negative curvature"
    assert not result_throat["is_elliptical"], "Throat should not be elliptical"

    print("✓ Guardian elliptical check tests passed")
    return True


def test_phi_invariant_resonance():
    """Test Φ-invariant PWM resonance computation."""
    print("Testing Φ-invariant resonance...")
    processor = OuroborosVirtualProcessor(radius=1.0)

    # Test with various ternary vectors
    test_vectors = [
        [0.4, 0.2, 0.4],
        [1.0, 0.0, 0.0],
        [0.33, 0.33, 0.34],
    ]

    for V in test_vectors:
        resonance = processor.phi_invariant_resonance(V)

        # Resonance should be in [0, 1]
        assert 0 <= resonance <= 1, f"Resonance should be in [0,1], got {resonance}"
        assert math.isfinite(resonance), "Resonance should be finite"

    print("✓ Φ-invariant resonance tests passed")
    return True


def test_phase_lock_monitoring():
    """Test phase-lock monitoring with Nyquist protection."""
    print("Testing phase-lock monitoring...")
    processor = OuroborosVirtualProcessor(radius=1.0)

    phi, theta = math.pi / 4, math.pi / 3

    # First call should succeed
    result1 = processor.monitor_phase_lock(phi, theta, rate_limit=True)
    assert "timestamp" in result1, "Should have timestamp"
    assert "phase_locked" in result1, "Should have phase_locked status"
    assert "gradient_magnitude" in result1, "Should have gradient magnitude"
    assert "quaternion" in result1, "Should have quaternion"

    # Immediate second call should be rate limited
    result2 = processor.monitor_phase_lock(phi, theta, rate_limit=True)
    assert result2.get("status") == "rate_limited", "Should be rate limited"

    # Without rate limiting, should succeed
    result3 = processor.monitor_phase_lock(phi, theta, rate_limit=False)
    assert "timestamp" in result3, "Should succeed without rate limiting"

    # Check monitoring buffer
    assert len(processor._monitoring_data) > 0, "Monitoring buffer should have entries"

    print("✓ Phase-lock monitoring tests passed")
    return True


def test_topological_analysis():
    """Test multi-dimensional topological automata analysis."""
    print("Testing topological analysis...")

    if not EXTENDED_FEATURES:
        print("⚠ Skipping topological analysis (requires numpy/scipy)")
        return True

    processor = OuroborosVirtualProcessor(radius=1.0)

    result = processor.topological_analysis(max_nodes=9)

    # Should have all required fields
    assert "num_poles" in result, "Should report number of poles"
    assert "pole_locations" in result, "Should report pole locations"
    assert "flux_differential" in result, "Should report flux differential"
    assert "mean_curvature" in result, "Should report mean curvature"

    # Poles should be reasonable
    assert result["num_poles"] >= 0, "Number of poles should be non-negative"
    assert (
        len(result["pole_locations"]) == result["num_poles"]
    ), "Pole locations should match count"

    # Flux differential should be non-negative
    assert result["flux_differential"] >= 0, "Flux differential should be non-negative"

    print("✓ Topological analysis tests passed")
    return True


def test_snapshot_state_integration():
    """Test that snapshot_state includes new features."""
    print("Testing snapshot state integration...")
    processor = OuroborosVirtualProcessor(radius=1.0, zeta_seed=0.618)

    # Generate some activity
    processor.quaternion_state(0.1, 0.2)
    processor.monitor_phase_lock(0.1, 0.2, rate_limit=False)

    snapshot = processor.snapshot_state()

    # Basic fields should be present
    assert "radius" in snapshot
    assert "threshold" in snapshot
    assert "extended_features" in snapshot

    # New fields should be included if extended features available
    if EXTENDED_FEATURES:
        assert "quaternion_cache_size" in snapshot
        assert "monitoring_entries" in snapshot
        assert "topological_properties" in snapshot

        assert snapshot["quaternion_cache_size"] > 0, "Cache should have entries"
        assert snapshot["monitoring_entries"] > 0, "Monitoring should have entries"

    print("✓ Snapshot state integration tests passed")
    return True


def run_all_tests():
    """Run all test suites."""
    print("=" * 70)
    print("Helix DNA Magnetar Synthesis - Test Suite")
    print("=" * 70)
    print()

    tests = [
        test_gradient_field_computation,
        test_quaternion_state_representation,
        test_guardian_elliptical_check,
        test_phi_invariant_resonance,
        test_phase_lock_monitoring,
        test_topological_analysis,
        test_snapshot_state_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test.__name__} returned False")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} failed with exception: {e}")
            import traceback

            traceback.print_exc()
        print()

    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
