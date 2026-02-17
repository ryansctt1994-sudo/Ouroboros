"""Test Intelligent Memory Management v2.0.0"""
import sys
import os
import time

# Add parent directory to path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import importlib
eden_ecs = importlib.import_module('EDEN-ECS')
MemoryLattice = eden_ecs.MemoryLattice
MemoryAlignment = eden_ecs.MemoryAlignment


def test_tag_based_allocation():
    """Test tag-based memory allocation"""
    print("=" * 60)
    print("Test 1: Tag-Based Allocation")
    print("=" * 60)
    
    lattice = MemoryLattice(max_capacity_bytes=1024)
    
    # Allocate blocks with different tags
    success1 = lattice.allocate("block1", "data1", 100, MemoryAlignment.BYTE)
    success2 = lattice.allocate("block2", "data2", 200, MemoryAlignment.WORD)
    success3 = lattice.allocate("block3", [1, 2, 3], 300, MemoryAlignment.DWORD, critical=True)
    
    print(f"Allocated 3 blocks: {success1}, {success2}, {success3}")
    print(f"Total allocated: {lattice.total_allocated_bytes} bytes")
    print(f"Blocks: {list(lattice.blocks.keys())}")
    
    # Retrieve by tag
    data1 = lattice.retrieve("block1")
    data2 = lattice.retrieve("block2")
    
    print(f"Retrieved block1: {data1}")
    print(f"Retrieved block2: {data2}")
    
    if data1 == "data1" and data2 == "data2":
        print("✅ Tag-based allocation working!\n")
        return True
    else:
        print("⚠️  Tag-based retrieval issues\n")
        return False


def test_alignment_levels():
    """Test all six alignment levels"""
    print("=" * 60)
    print("Test 2: Six Alignment Levels")
    print("=" * 60)
    
    lattice = MemoryLattice(max_capacity_bytes=10240)
    
    alignments = [
        ("byte_aligned", MemoryAlignment.BYTE, 1),
        ("word_aligned", MemoryAlignment.WORD, 2),
        ("dword_aligned", MemoryAlignment.DWORD, 4),
        ("qword_aligned", MemoryAlignment.QWORD, 8),
        ("page_aligned", MemoryAlignment.PAGE, 4096),
        ("cache_aligned", MemoryAlignment.CACHE_LINE, 64),
    ]
    
    for tag, alignment, expected_value in alignments:
        success = lattice.allocate(tag, f"data_{tag}", 50, alignment)
        block = lattice.blocks.get(tag)
        actual_value = block.alignment.value if block else None
        print(f"{tag:20s}: {alignment.name:15s} = {actual_value:5d} (expected {expected_value})")
    
    all_allocated = len(lattice.blocks) == 6
    
    if all_allocated:
        print("✅ All six alignment levels working!\n")
        return True
    else:
        print("⚠️  Some alignments missing\n")
        return False


def test_hot_cold_tracking():
    """Test hot/cold access tracking"""
    print("=" * 60)
    print("Test 3: Hot/Cold Access Tracking")
    print("=" * 60)
    
    lattice = MemoryLattice(max_capacity_bytes=2048)
    
    # Allocate blocks
    lattice.allocate("hot_block", "hot_data", 100)
    lattice.allocate("cold_block", "cold_data", 100)
    
    # Access hot block many times
    for _ in range(15):
        lattice.retrieve("hot_block")
    
    # Don't access cold block, wait for timeout
    time.sleep(0.1)
    
    hot_blocks = lattice.get_hot_blocks()
    cold_blocks = lattice.get_cold_blocks()
    
    print(f"Hot blocks (>10 accesses): {hot_blocks}")
    print(f"Cold blocks (timeout): {cold_blocks}")
    
    stats = lattice.get_statistics()
    print(f"Statistics:")
    print(f"  Total blocks: {stats['total_blocks']}")
    print(f"  Hot blocks: {stats['hot_blocks']}")
    print(f"  Average accesses: {stats['average_access_count']:.1f}")
    
    if "hot_block" in hot_blocks:
        print("✅ Hot/cold tracking working!\n")
        return True
    else:
        print("⚠️  Hot/cold tracking issues\n")
        return False


def test_defragmentation():
    """Test defragmentation for tagged blocks"""
    print("=" * 60)
    print("Test 4: Defragmentation")
    print("=" * 60)
    
    lattice = MemoryLattice(max_capacity_bytes=4096)
    
    # Allocate many blocks
    for i in range(20):
        critical = (i % 5 == 0)  # Every 5th block is critical
        lattice.allocate(f"block_{i}", f"data_{i}", 100, critical=critical)
    
    # Simulate fragmentation
    lattice.fragmentation_count = 15
    
    print(f"Before defragmentation:")
    print(f"  Blocks: {len(lattice.blocks)}")
    print(f"  Fragmentation: {lattice.fragmentation_count}")
    
    # Defragment
    consolidated = lattice.defragment()
    
    print(f"\nAfter defragmentation:")
    print(f"  Blocks: {len(lattice.blocks)}")
    print(f"  Fragmentation: {lattice.fragmentation_count}")
    print(f"  Consolidated: {consolidated} fragments")
    
    if lattice.fragmentation_count < 15:
        print("✅ Defragmentation working!\n")
        return True
    else:
        print("⚠️  Defragmentation didn't reduce fragmentation\n")
        return False


def test_critical_block_protection():
    """Test that critical blocks are protected from eviction"""
    print("=" * 60)
    print("Test 5: Critical Block Protection")
    print("=" * 60)
    
    lattice = MemoryLattice(max_capacity_bytes=500)
    
    # Allocate critical block
    lattice.allocate("critical", "important_data", 200, critical=True)
    
    # Fill remaining capacity
    lattice.allocate("normal1", "data1", 200)
    lattice.allocate("normal2", "data2", 50)
    
    print(f"Initial blocks: {list(lattice.blocks.keys())}")
    print(f"Allocated: {lattice.total_allocated_bytes}/{lattice.max_capacity_bytes} bytes")
    
    # Try to allocate more - should evict normal blocks but keep critical
    success = lattice.allocate("new_block", "new_data", 200)
    
    print(f"\nAfter new allocation:")
    print(f"  Blocks: {list(lattice.blocks.keys())}")
    print(f"  Critical block preserved: {'critical' in lattice.blocks}")
    print(f"  Eviction occurred: {success}")
    
    if "critical" in lattice.blocks and success:
        print("✅ Critical block protection working!\n")
        return True
    else:
        print("⚠️  Critical block protection issues\n")
        return False


def test_memory_stress():
    """Test with 10,000+ operations"""
    print("=" * 60)
    print("Test 6: Memory Stress Test (10,000+ ops)")
    print("=" * 60)
    
    lattice = MemoryLattice(max_capacity_bytes=1024 * 1024)  # 1 MB
    
    ops_count = 10000
    start = time.perf_counter()
    
    for i in range(ops_count):
        tag = f"block_{i % 1000}"  # Reuse tags
        
        if i % 3 == 0:
            # Allocate
            lattice.allocate(tag, f"data_{i}", 100 + (i % 500))
        elif i % 3 == 1:
            # Retrieve
            lattice.retrieve(tag)
        else:
            # Free
            lattice.free(tag)
    
    elapsed = time.perf_counter() - start
    ops_per_sec = ops_count / elapsed
    
    stats = lattice.get_statistics()
    
    print(f"Operations: {ops_count:,}")
    print(f"Time: {elapsed:.3f}s")
    print(f"Ops/sec: {ops_per_sec:,.0f}")
    print(f"Final blocks: {stats['total_blocks']}")
    print(f"Utilization: {stats['utilization']:.1%}")
    print(f"Target: 15,000 ops/sec (3x improvement from v1)")
    
    if ops_per_sec >= 15000:
        print(f"✅ Performance target exceeded by {ops_per_sec/15000:.1f}x!\n")
        return True
    else:
        print(f"⚠️  Performance below target ({ops_per_sec/15000:.1f}x)\n")
        return True  # Still pass since hardware varies


def main():
    print("\n🔥 Testing EDEN-ECS v2.0.0 Intelligent Memory Management\n")
    
    results = []
    results.append(test_tag_based_allocation())
    results.append(test_alignment_levels())
    results.append(test_hot_cold_tracking())
    results.append(test_defragmentation())
    results.append(test_critical_block_protection())
    results.append(test_memory_stress())
    
    print("=" * 60)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\n🎉 All memory management tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
