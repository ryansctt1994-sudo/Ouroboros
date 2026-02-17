#!/usr/bin/env python3
"""Test EDEN ECS Core"""
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
