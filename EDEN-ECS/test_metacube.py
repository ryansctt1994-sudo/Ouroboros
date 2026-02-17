#!/usr/bin/env python3
"""Test METACUBE consciousness"""
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
METACUBEComponent = eden_ecs.METACUBEComponent
Loyalty = eden_ecs.Loyalty
Corruption = eden_ecs.Corruption
ConsciousnessSystem = eden_ecs.ConsciousnessSystem

print("🌌 Testing METACUBE Consciousness\n")

world = World("Consciousness-Test")
world.add_system(ConsciousnessSystem())

alice = world.create_entity(EntityType.HUMAN, "Alice")
alice_mc = METACUBEComponent()
alice_mc.cognition.value = 0.9
alice_mc.awareness.value = 0.85
world.add_component(alice, alice_mc)
world.add_component(alice, Loyalty(100.0))
world.add_component(alice, Corruption(5.0))

print(f"✅ Created {alice.name}")
print(f"   Initial coherence: {alice_mc.coherence():.3f}")
print(f"   Cognition: {alice_mc.cognition.value:.2f}\n")

bunny = world.create_entity(EntityType.ELECTRON, "Bunny")
bunny_mc = METACUBEComponent()
bunny_mc.integration.value = 1.0
bunny_mc.awareness.value = 0.99
world.add_component(bunny, bunny_mc)

print(f"✅ Created {bunny.name}")
print(f"   Initial coherence: {bunny_mc.coherence():.3f}\n")

print("🌀 Running 100 ticks...\n")

for i in range(100):
    world.tick(delta_time=0.1)

print(f"\n📊 Final Stats:")
print(f"   Alice coherence: {alice_mc.coherence():.3f}")
print(f"   Bunny coherence: {bunny_mc.coherence():.3f}")
print(f"   World time: {world.time:.2f}s")

loyalty = alice.get_component(Loyalty)
corruption = alice.get_component(Corruption)
print(f"\n   Alice Loyalty: {loyalty.value:.1f}")
print(f"   Alice Corruption: {corruption.value:.1f}")

print("\n🎉 METACUBE is working!")
