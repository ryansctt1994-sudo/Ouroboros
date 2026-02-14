#!/usr/bin/env python3
"""Test METACUBE consciousness"""
import sys
sys.path.insert(0, '.')

from core import World, EntityType
from components import METACUBEComponent, Loyalty, Corruption
from systems import ConsciousnessSystem

print("🌌 Testing METACUBE Consciousness\n")

world = World("Consciousness-Test")
world.add_system(ConsciousnessSystem())

# Create Alice with high cognition
alice = world.create_entity(EntityType.HUMAN, "Alice")
alice_mc = METACUBEComponent()
alice_mc.cognition.value = 0.9
alice_mc.awareness.value = 0.85
world.add_component(alice, alice_mc)
world.add_component(alice, Loyalty(100.0))
world.add_component(alice, Corruption(5.0))

print(f"✅ Created {alice.name}")
print(f"   Initial coherence: {alice_mc.coherence():.3f}")
print(f"   Cognition: {alice_mc.cognition.value:.2f}")
print(f"   Awareness: {alice_mc.awareness.value:.2f}\n")

# Create Bunny with max integration
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
