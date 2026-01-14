"""Integration tests for GGCC Phase 3 modules.

Tests all five modules and the controller to ensure:
- Individual module functionality
- Zero-cascade deployment
- Module independence
- Coordinated operation
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ggcc import (
    NodeBalancerV2,
    GradientEngineV2,
    SymmetryMonitorV2,
    TransientManagerV2,
    CouplingInterface,
    GGCCPhase3Controller
)


def test_node_balancer():
    """Test NodeBalancer v2 functionality."""
    print("Testing NodeBalancer v2...")
    
    balancer = NodeBalancerV2(capacity=10, enable_amused_logging=False)
    
    # Test insertion
    balancer.put("key1", {"value": 1})
    balancer.put("key2", {"value": 2})
    
    # Test retrieval
    assert balancer.get("key1") == {"value": 1}
    assert balancer.get("key2") == {"value": 2}
    assert balancer.get("nonexistent") is None
    
    # Test diagnostics
    diag = balancer.get_diagnostics()
    assert diag["current_size"] == 2
    assert diag["hits"] == 2
    assert diag["misses"] == 1
    
    # Test balance
    metrics = balancer.balance()
    assert "rebalanced_nodes" in metrics
    assert metrics["rebalanced_nodes"] == 2
    
    print("✓ NodeBalancer v2 tests passed")


def test_gradient_engine():
    """Test GradientEngine v2 functionality."""
    print("Testing GradientEngine v2...")
    
    engine = GradientEngineV2(enable_amused_logging=False)
    
    # Test gradient computation
    grad = engine.compute_gradient(0.5, use_proxy=False)
    assert len(grad) == 2
    assert grad[0] == 1.0  # dx/dt is always 1
    
    # Test segment gradients
    seg_grads = engine.compute_segment_gradients(0)
    assert len(seg_grads) > 0
    
    # Test priority update
    engine.update_segment_priorities()
    assert len(engine.segment_priorities) == engine.segments
    
    # Test diagnostics
    diag = engine.get_diagnostics()
    assert diag["evaluations"] > 0
    assert diag["segments"] == 10
    
    print("✓ GradientEngine v2 tests passed")


def test_symmetry_monitor():
    """Test SymmetryMonitor v2 functionality."""
    print("Testing SymmetryMonitor v2...")
    
    monitor = SymmetryMonitorV2(enable_amused_logging=False)
    
    # Test phase measurement
    result = monitor.measure_phase(0.05)
    assert "drift" in result
    assert "drift_detected" in result
    assert result["measurement_count"] == 1
    
    # Test multiple measurements
    for i in range(5):
        monitor.measure_phase(0.01 * i)
    
    assert monitor.measurement_count == 6
    
    # Test diagnostics
    diag = monitor.get_diagnostics()
    assert diag["measurement_count"] == 6
    assert "avg_drift" in diag
    
    print("✓ SymmetryMonitor v2 tests passed")


def test_transient_manager():
    """Test TransientManager v2 functionality."""
    print("Testing TransientManager v2...")
    
    manager = TransientManagerV2(
        epoch_interval=1.0,
        level1_capacity=5,
        level2_capacity=10,
        enable_amused_logging=False
    )
    
    # Test insertion
    manager.insert("data1", {"value": 1})
    manager.insert("data2", {"value": 2})
    
    # Test retrieval
    assert manager.get("data1") == {"value": 1}
    assert manager.get("data2") == {"value": 2}
    
    # Test diagnostics
    diag = manager.get_diagnostics()
    assert diag["level1_size"] == 2
    assert diag["total_insertions"] == 2
    
    # Test cleanup
    cleaned = manager.force_cleanup()
    assert isinstance(cleaned, int)
    
    # Test dashboard data
    dashboard = manager.get_dashboard_data()
    assert "current_epoch" in dashboard
    assert "current_pressure" in dashboard
    
    print("✓ TransientManager v2 tests passed")


def test_coupling_interface():
    """Test CouplingInterface functionality."""
    print("Testing CouplingInterface...")
    
    interface = CouplingInterface(enable_amused_logging=False)
    
    # Test static-to-dynamic coupling
    coupled = interface.couple_static_to_dynamic(0.5)
    assert isinstance(coupled, float)
    
    # Test dynamic-to-static coupling
    coupled = interface.couple_dynamic_to_static(0.8)
    assert isinstance(coupled, float)
    
    # Test impedance mismatch
    mismatch = interface.measure_impedance_mismatch()
    assert isinstance(mismatch, float)
    assert mismatch >= 0.0
    
    # Test frequency analysis
    spectrum = interface.analyze_frequency_spectrum()
    assert "low_freq_power" in spectrum
    assert "high_freq_power" in spectrum
    
    # Test diagnostics
    diag = interface.get_diagnostics()
    assert diag["coupling_events"] > 0
    
    print("✓ CouplingInterface tests passed")


def test_controller():
    """Test GGCC Phase 3 Controller."""
    print("Testing GGCC Phase 3 Controller...")
    
    controller = GGCCPhase3Controller(enable_amused_logging=False)
    
    # Test module activation states
    assert len(controller.modules_active) == 5
    assert all(controller.modules_active.values())
    
    # Test operation processing
    operation = {
        "key": "test_op",
        "gradient_param": 0.5,
        "phase": 0.1,
        "transient_key": "test_trans",
        "static_value": 0.7
    }
    result = controller.process_operation(operation)
    assert "modules" in result
    assert len(result["modules"]) == 5
    
    # Test system health
    health = controller.get_system_health()
    assert health["overall_status"] == "HEALTHY"
    assert health["version"] == "3.0.0"
    assert len(health["modules"]) == 5
    
    # Test module deactivation (zero-cascade)
    assert controller.deactivate_module("gradient_engine")
    assert not controller.modules_active["gradient_engine"]
    
    # Process operation with deactivated module
    result = controller.process_operation(operation)
    assert "gradient_engine" not in result["modules"]
    assert len(result["modules"]) == 4
    
    # Test module reactivation (reversible)
    assert controller.activate_module("gradient_engine")
    assert controller.modules_active["gradient_engine"]
    
    result = controller.process_operation(operation)
    assert "gradient_engine" in result["modules"]
    assert len(result["modules"]) == 5
    
    # Test maintenance
    maintenance = controller.perform_maintenance()
    assert "node_balancer" in maintenance
    assert "gradient_engine" in maintenance
    
    print("✓ GGCC Phase 3 Controller tests passed")


def test_module_independence():
    """Test that modules operate independently."""
    print("Testing module independence...")
    
    # Create all modules separately
    balancer = NodeBalancerV2(enable_amused_logging=False)
    engine = GradientEngineV2(enable_amused_logging=False)
    monitor = SymmetryMonitorV2(enable_amused_logging=False)
    manager = TransientManagerV2(enable_amused_logging=False)
    interface = CouplingInterface(enable_amused_logging=False)
    
    # Each module should work independently
    balancer.put("test", {"data": 1})
    assert balancer.get("test") == {"data": 1}
    
    grad = engine.compute_gradient(0.5)
    assert len(grad) == 2
    
    result = monitor.measure_phase(0.05)
    assert "drift" in result
    
    manager.insert("test", {"value": 1})
    assert manager.get("test") == {"value": 1}
    
    coupled = interface.couple_static_to_dynamic(0.5)
    assert isinstance(coupled, float)
    
    print("✓ Module independence tests passed")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("GGCC Phase 3: Integration Test Suite")
    print("=" * 70)
    print()
    
    try:
        test_node_balancer()
        test_gradient_engine()
        test_symmetry_monitor()
        test_transient_manager()
        test_coupling_interface()
        test_controller()
        test_module_independence()
        
        print()
        print("=" * 70)
        print("✓ All integration tests passed successfully!")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"✗ Test failed: {e}")
        print("=" * 70)
        return False
    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ Unexpected error: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
