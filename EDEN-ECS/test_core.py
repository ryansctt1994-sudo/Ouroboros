#!/usr/bin/env python3
"""Test EDEN ECS Core"""
import sys
sys.path.insert(0, '.')

from core import World, EntityType

print("🔥 Testing EDEN ECS Core\n")

world = World("Test-Cosmos")
print(f"✅ Created world: {world.name}")

alice = world.create_entity(EntityType.HUMAN, "Alice")
print(f"✅ Created entity: {alice.entity_type.value} {alice.name}")

bunny = world.create_entity(EntityType.ELECTRON, "Bunny")
print(f"✅ Created entity: {bunny.entity_type.value} {bunny.name}")

print(f"\n📊 Total entities: {world.entity_manager.count()}")

for i in range(10):
    world.tick()

print(f"📊 Final time: {world.time:.2f}s")
print(f"📊 Total ticks: {world.metrics['ticks']}")

print("\n🎉 EDEN ECS Core is working!")
