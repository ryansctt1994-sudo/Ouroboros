#!/usr/bin/env python3
"""
Test BalanceSystem with updated delta_time support
"""
import sys
import os

# Add parent directory to path so we can import EDEN-ECS modules
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import using absolute path through parent
import importlib
eden_ecs = importlib.import_module('EDEN-ECS')
World = eden_ecs.World
EntityType = eden_ecs.EntityType
Loyalty = eden_ecs.Loyalty
Corruption = eden_ecs.Corruption
BalanceSystem = eden_ecs.BalanceSystem

print("🧪 Testing BalanceSystem with Delta Time\n")

# Create world and add system
world = World("Balance-Test")
world.add_system(BalanceSystem())

# Create entity with loyalty and corruption
alice = world.create_entity(EntityType.HUMAN, "Alice")
world.add_component(alice, Loyalty(value=50.0))
world.add_component(alice, Corruption(value=50.0))

print(f"Initial state:")
loyalty = alice.get_component(Loyalty)
corruption = alice.get_component(Corruption)
print(f"  Loyalty: {loyalty.value:.2f}")
print(f"  Corruption: {corruption.value:.2f}\n")

# Run simulation
print("Running 20 ticks with delta_time=0.5...")
for i in range(20):
    world.tick(delta_time=0.5)

print(f"\nFinal state:")
print(f"  Loyalty: {loyalty.value:.2f}")
print(f"  Corruption: {corruption.value:.2f}")

# Verify loyalty increased and corruption decreased
if loyalty.value > 50.0:
    print("✅ Loyalty is growing!")
else:
    print("⚠️  Loyalty didn't grow")

if corruption.value < 50.0:
    print("✅ Corruption is decaying!")
else:
    print("⚠️  Corruption didn't decay")

print("\n🎉 BalanceSystem test completed!")
