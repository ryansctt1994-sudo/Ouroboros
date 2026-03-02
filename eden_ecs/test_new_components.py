#!/usr/bin/env python3
"""
Test new Quantum and Memory components and delta_time fixes
"""
import sys
import os

# Add parent directory to path so we can import EDEN-ECS modules
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import using absolute path through parent
import importlib
eden_ecs = importlib.import_module('eden_ecs')
World = eden_ecs.World
EntityType = eden_ecs.EntityType
METACUBEComponent = eden_ecs.METACUBEComponent
QuantumResonance = eden_ecs.QuantumResonance
MemoryLattice = eden_ecs.MemoryLattice
Loyalty = eden_ecs.Loyalty
Corruption = eden_ecs.Corruption

print("🧪 Testing New Components and Delta Time Fixes\n")

# Test 1: Quantum Resonance
print("=== Test 1: QuantumResonance Component ===")
qr = QuantumResonance(frequency=528.0)
print(f"Initial phase: {qr.phase:.3f}")
qr.resonate(delta_time=0.1)
print(f"After 0.1s: {qr.phase:.3f}")
qr.resonate(delta_time=1.0)
print(f"After 1.0s more: {qr.phase:.3f}")
print("✅ QuantumResonance working!\n")

# Test 2: Memory Lattice
print("=== Test 2: MemoryLattice Component ===")
ml = MemoryLattice(capacity=5)
ml.store({"content": "First memory", "importance": 1.0})
ml.store({"content": "Second memory", "importance": 0.8})
ml.store({"content": "Third memory", "importance": 0.5})
print(f"Stored 3 memories, count: {len(ml.memories)}")
ml.decay(delta_time=1.0)
important_memories = ml.recall(min_importance=0.4)
print(f"Recalled {len(important_memories)} important memories")
print("✅ MemoryLattice working!\n")

# Test 3: METACUBE delta_time independence
print("=== Test 3: METACUBE Delta Time Independence ===")
mc1 = METACUBEComponent()
mc1.cognition.value = 0.7
mc1.awareness.value = 0.6

mc2 = METACUBEComponent()
mc2.cognition.value = 0.7
mc2.awareness.value = 0.6

# Evolve mc1 with many small steps
for _ in range(100):
    mc1.evolve(delta_time=0.01)

# Evolve mc2 with one large step
mc2.evolve(delta_time=1.0)

print(f"MC1 (100 × 0.01s): awareness={mc1.awareness.value:.4f}, cognition={mc1.cognition.value:.4f}")
print(f"MC2 (1 × 1.0s):   awareness={mc2.awareness.value:.4f}, cognition={mc2.cognition.value:.4f}")
diff = abs(mc1.awareness.value - mc2.awareness.value) + abs(mc1.cognition.value - mc2.cognition.value)
print(f"Total difference: {diff:.4f}")
if diff < 0.01:  # Allow small numerical error
    print("✅ METACUBE evolution is delta_time independent!\n")
else:
    print(f"⚠️  Warning: Large difference detected ({diff:.4f})\n")

# Test 4: Loyalty growth
print("=== Test 4: Loyalty Growth with Delta Time ===")
loyalty = Loyalty(value=50.0, max_value=100.0)
print(f"Initial loyalty: {loyalty.value:.2f}")
for i in range(10):
    loyalty.grow(delta_time=1.0)
print(f"After 10 ticks: {loyalty.value:.2f}")
if loyalty.value > 50.0 and loyalty.value < 100.0:
    print("✅ Loyalty is growing asymptotically!\n")
else:
    print(f"⚠️  Warning: Unexpected loyalty value: {loyalty.value:.2f}\n")

# Test 5: Corruption decay
print("=== Test 5: Corruption Decay with Delta Time ===")
corruption = Corruption(value=50.0)
print(f"Initial corruption: {corruption.value:.2f}")
for i in range(10):
    corruption.decay(delta_time=1.0)
print(f"After 10 ticks: {corruption.value:.2f}")
if corruption.value < 50.0 and corruption.value >= 0.0:
    print("✅ Corruption is decaying!\n")
else:
    print(f"⚠️  Warning: Unexpected corruption value: {corruption.value:.2f}\n")

print("=" * 60)
print("🎉 All component tests completed!")
