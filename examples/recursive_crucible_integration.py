#!/usr/bin/env python3
"""
Integration Example - Recursive Crucible with ECS Components

This example demonstrates how to integrate the Recursive Crucible Core
with the EDEN ECS system for self-improving agent code.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_interface.recursive_crucible import RecursiveCrucible
from core.gpu_vector_enhancement import ECSVectorBridge

print("="*70)
print("RECURSIVE CRUCIBLE + ECS INTEGRATION EXAMPLE")
print("="*70)
print()

# Example 1: Analyze and improve a simple ECS component
print("Example 1: Analyzing ECS Component Code")
print("-"*70)

component_code = """
from dataclasses import dataclass

@dataclass
class PositionComponent:
    x: float
    y: float
    z: float
    
    def distance_to(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return (dx*dx + dy*dy + dz*dz) ** 0.5
"""

crucible = RecursiveCrucible(max_iterations=2)
results = crucible.run_recursive(component_code, "PositionComponent.py")

print(f"\nAnalysis Results:")
print(f"  Total Iterations: {len(results)}")
print(f"  Total Weaknesses: {sum(len(r.weaknesses_found) for r in results)}")
print(f"  Total Fixes: {sum(len(r.fixes_applied) for r in results)}")

# Show some weaknesses
if results and results[0].weaknesses_found:
    print(f"\n  Sample Weaknesses:")
    for w in results[0].weaknesses_found[:3]:
        print(f"    - [{w.type.value}] {w.description}")

# Example 2: Use GPU Vector Enhancement with ECS entities
print("\n" + "="*70)
print("Example 2: GPU Vector Enhancement for ECS Entities")
print("-"*70)

bridge = ECSVectorBridge(use_gpu=False)

# Simulate ECS entities with position vectors
entities = {
    "player": [100.0, 50.0, 0.0],
    "enemy_1": [150.0, 60.0, 0.0],
    "enemy_2": [80.0, 40.0, 0.0],
    "powerup": [120.0, 55.0, 0.0]
}

print(f"\nRegistering {len(entities)} ECS entities with vectors...")
for entity_id, position in entities.items():
    bridge.register_entity_vector(entity_id, position)

# Compute interactions
print("\nComputing entity interactions:")
player_enemy1_interaction = bridge.compute_entity_interaction("player", "enemy_1")
player_enemy2_interaction = bridge.compute_entity_interaction("player", "enemy_2")

print(f"  Player <-> Enemy 1: {player_enemy1_interaction:.2f}")
print(f"  Player <-> Enemy 2: {player_enemy2_interaction:.2f}")

# Batch update all entities (simulate movement)
print("\nApplying movement delta to all entities...")
entity_ids = list(entities.keys())
deltas = [[5.0, 0.0, 0.0] for _ in entity_ids]  # Move all right by 5 units
bridge.batch_update_entities(entity_ids, deltas)

print("  Updated positions:")
for entity_id in entity_ids:
    new_pos = bridge.get_entity_vector(entity_id)
    print(f"    {entity_id}: {[f'{x:.1f}' for x in new_pos]}")

# Get stats
stats = bridge.get_stats()
print(f"\nBridge Statistics:")
print(f"  Total Entities: {stats['total_entities']}")
print(f"  Total Operations: {stats['processor_stats']['total_operations']}")
print(f"  Device: {stats['processor_stats']['device']}")

# Example 3: Analyze ECS System code
print("\n" + "="*70)
print("Example 3: Analyzing ECS System Code")
print("-"*70)

system_code = """
from core.system import System

class MovementSystem(System):
    def name(self):
        return "MovementSystem"
    
    def process(self, world, delta_time):
        # Move all entities with position and velocity
        for entity in world.entities:
            if hasattr(entity, 'position') and hasattr(entity, 'velocity'):
                entity.position.x += entity.velocity.x * delta_time
                entity.position.y += entity.velocity.y * delta_time
                entity.position.z += entity.velocity.z * delta_time
"""

crucible2 = RecursiveCrucible(max_iterations=2)
results2 = crucible2.run_recursive(system_code, "MovementSystem.py")

summary = crucible2.get_summary()
print(f"\nSystem Analysis Summary:")
print(f"  Total Iterations: {summary['total_iterations']}")
print(f"  Total Weaknesses: {summary['total_weaknesses']}")
print(f"  Total Fixes: {summary['total_fixes']}")
print(f"  Successful Fixes: {summary['successful_fixes']}")
print(f"  Avg Validation Score: {summary['average_validation_score']:.2f}")

# Example 4: Combined workflow
print("\n" + "="*70)
print("Example 4: Combined Self-Improvement Workflow")
print("-"*70)

print("""
Recommended Workflow for Self-Improving ECS Code:

1. Write initial ECS component/system code
2. Run Recursive Crucible to detect weaknesses
3. Review and apply suggested fixes
4. Use GPU Vector Enhancement for performance-critical operations
5. Re-run Crucible to validate improvements
6. Iterate until all weaknesses are resolved

Benefits:
- Automatic detection of code quality issues
- Performance optimization suggestions
- GPU-accelerated vector operations
- Validation of improvements
- Continuous self-improvement loop
""")

print("="*70)
print("INTEGRATION EXAMPLE COMPLETE")
print("="*70)
print()
print("Next Steps:")
print("  1. Integrate with live ECS workflows")
print("  2. Connect to GUI for real-time monitoring")
print("  3. Add LLM-powered analysis for deeper insights")
print("  4. Deploy in production for continuous improvement")
