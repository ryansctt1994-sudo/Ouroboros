"""Test Hybrid Timestep System"""
import sys
import time
from core import World, TimestepMode


def test_fixed_mode():
    """Test FIXED timestep mode"""
    print("=" * 60)
    print("Test 1: FIXED Timestep Mode")
    print("=" * 60)
    
    world = World(name="Fixed-World", timestep_mode=TimestepMode.FIXED, fixed_timestep=0.01)
    
    # Run 10 ticks
    for _ in range(10):
        world.tick()
    
    # In FIXED mode, time should be exactly 10 * 0.01 = 0.1
    expected_time = 10 * 0.01
    actual_time = world.time
    
    print(f"Expected time: {expected_time:.3f}s")
    print(f"Actual time: {actual_time:.3f}s")
    print(f"Difference: {abs(actual_time - expected_time):.6f}s")
    
    if abs(actual_time - expected_time) < 0.0001:
        print("✅ FIXED mode is deterministic!\n")
        return True
    else:
        print("⚠️  FIXED mode timing mismatch\n")
        return False


def test_variable_mode():
    """Test VARIABLE timestep mode"""
    print("=" * 60)
    print("Test 2: VARIABLE Timestep Mode")
    print("=" * 60)
    
    world = World(name="Variable-World", timestep_mode=TimestepMode.VARIABLE)
    
    # Simulate variable frame times
    start = time.perf_counter()
    for i in range(5):
        world.tick()
        time.sleep(0.01)  # Simulate frame time
    elapsed = time.perf_counter() - start
    
    print(f"Elapsed real time: {elapsed:.3f}s")
    print(f"World time: {world.time:.3f}s")
    print(f"Ticks: {world.metrics['ticks']}")
    
    # In VARIABLE mode, world time should approximate real time
    if abs(world.time - elapsed) < 0.02:
        print("✅ VARIABLE mode tracks real time!\n")
        return True
    else:
        print("⚠️  VARIABLE mode timing off\n")
        return False


def test_hybrid_mode():
    """Test HYBRID timestep mode with diagnostics"""
    print("=" * 60)
    print("Test 3: HYBRID Timestep Mode")
    print("=" * 60)
    
    world = World(name="Hybrid-World", timestep_mode=TimestepMode.HYBRID, fixed_timestep=1.0/60.0)
    
    # Run simulation with realistic delays (reduced count for faster test)
    for i in range(20):
        world.tick()
        time.sleep(0.016)  # Simulate ~60 FPS frame time
    
    # Get diagnostics
    diag = world.get_timestep_diagnostics()
    
    print(f"FPS: {diag.fps:.1f}")
    print(f"Frame time: {diag.frame_time_ms:.2f}ms")
    print(f"Accumulator: {diag.accumulator_ms:.2f}ms")
    print(f"Drift: {diag.drift_percentage:.3f}%")
    print(f"Spiral warning: {diag.spiral_warning}")
    print(f"Ticks: {world.metrics['ticks']}")
    
    # Check that we processed physics steps and drift is minimal
    if world.metrics['ticks'] > 0 and diag.drift_percentage < 1.0:
        print("✅ HYBRID mode working with good performance!\n")
        return True
    else:
        print("⚠️  HYBRID mode has issues\n")
        return False


def test_drift_detection():
    """Test drift detection and spiral-of-death prevention"""
    print("=" * 60)
    print("Test 4: Drift Detection")
    print("=" * 60)
    
    world = World(name="Drift-World", timestep_mode=TimestepMode.HYBRID, fixed_timestep=1.0/60.0)
    
    # Simulate slow frames to trigger accumulator buildup
    world.timestep_manager.last_time = time.perf_counter() - 0.5  # Pretend 500ms passed
    world.tick()
    
    diag = world.get_timestep_diagnostics()
    
    print(f"Drift after slow frame: {diag.drift_percentage:.3f}%")
    print(f"Spiral warning: {diag.spiral_warning}")
    print(f"Accumulator clamped: {diag.accumulator_ms:.2f}ms")
    
    # Reset for normal operation
    world.timestep_manager.reset()
    for _ in range(10):
        world.tick()
    
    diag = world.get_timestep_diagnostics()
    print(f"Drift after recovery: {diag.drift_percentage:.3f}%")
    print(f"Spiral warning: {diag.spiral_warning}")
    
    if diag.drift_percentage < 0.1:
        print("✅ Drift detection and recovery working!\n")
        return True
    else:
        print("⚠️  Drift issues persist\n")
        return False


def test_backwards_compatibility():
    """Test that legacy tick(delta_time) still works"""
    print("=" * 60)
    print("Test 5: Backwards Compatibility")
    print("=" * 60)
    
    world = World(name="Legacy-World")
    
    # Use legacy tick method
    for _ in range(10):
        world.tick(delta_time=0.016)  # Explicit delta_time
    
    expected_time = 10 * 0.016
    actual_time = world.time
    
    print(f"Expected time: {expected_time:.3f}s")
    print(f"Actual time: {actual_time:.3f}s")
    
    if abs(actual_time - expected_time) < 0.0001:
        print("✅ Legacy tick() method still works!\n")
        return True
    else:
        print("⚠️  Legacy compatibility broken\n")
        return False


def main():
    print("\n🔥 Testing EDEN-ECS v2.0.0 Hybrid Timestep System\n")
    
    results = []
    results.append(test_fixed_mode())
    results.append(test_variable_mode())
    results.append(test_hybrid_mode())
    results.append(test_drift_detection())
    results.append(test_backwards_compatibility())
    
    print("=" * 60)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\n🎉 All timestep tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
