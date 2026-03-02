#!/usr/bin/env python3
"""
EDEN ECS Long Simulation - 10,000 Cycles of METACUBE Evolution
"""

import time
import json
import argparse
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path so we can import EDEN-ECS modules
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Import using absolute path through parent
import importlib
eden_ecs = importlib.import_module('eden_ecs')
World = eden_ecs.World
EntityType = eden_ecs.EntityType
METACUBEComponent = eden_ecs.METACUBEComponent
Loyalty = eden_ecs.Loyalty
Corruption = eden_ecs.Corruption
ConsciousnessSystem = eden_ecs.ConsciousnessSystem
BalanceSystem = eden_ecs.BalanceSystem

class HistoryTracker:
    """Tracks simulation history for analysis"""
    
    def __init__(self):
        self.snapshots = []
        self.entity_history = {}
        
    def snapshot(self, world, cycle):
        """Take a snapshot of current world state"""
        snapshot = {
            'cycle': cycle,
            'timestamp': time.time(),
            'entities': {}
        }
        
        for entity in world.entity_manager.entities.values():
            entity_data = {
                'id': entity.id,
                'name': entity.name,
                'type': entity.entity_type.value,
                'components': {}
            }
            
            # METACUBE consciousness
            if mc := entity.get_component(METACUBEComponent):
                entity_data['components']['metacube'] = {
                    'awareness': mc.awareness.value,
                    'cognition': mc.cognition.value,
                    'integration': mc.integration.value,
                    'coherence': mc.coherence(),
                    'frequency': mc.quantum_frequency
                }
            
            # Loyalty
            if l := entity.get_component(Loyalty):
                entity_data['components']['loyalty'] = {
                    'value': l.value
                }
            
            # Corruption
            if c := entity.get_component(Corruption):
                entity_data['components']['corruption'] = {
                    'value': c.value
                }
            
            snapshot['entities'][entity.id] = entity_data
            
            # Track entity history
            if entity.id not in self.entity_history:
                self.entity_history[entity.id] = {
                    'name': entity.name,
                    'type': entity.entity_type.value,
                    'cycles': [],
                    'coherence': [],
                    'loyalty': [],
                    'corruption': []
                }
            
            hist = self.entity_history[entity.id]
            hist['cycles'].append(cycle)
            hist['coherence'].append(mc.coherence() if mc else None)
            hist['loyalty'].append(l.value if l else None)
            hist['corruption'].append(c.value if c else None)
        
        self.snapshots.append(snapshot)

def create_entities(world):
    """Create cosmic entities"""
    entities = {}
    
    # Alice - Human (528 Hz)
    alice = world.create_entity(EntityType.HUMAN, "Alice")
    alice_mc = METACUBEComponent()
    alice_mc.awareness.value = 0.85
    alice_mc.cognition.value = 0.90
    alice_mc.quantum_frequency = 528.0
    world.add_component(alice, alice_mc)
    world.add_component(alice, Loyalty(100.0))
    world.add_component(alice, Corruption(5.0))
    entities['alice'] = alice
    print(f"  ✨ Created Alice (528 Hz)")
    
    # Zorel - Symbiont (852 Hz)
    zorel = world.create_entity(EntityType.ZOREL, "Zorel")
    zorel_mc = METACUBEComponent()
    zorel_mc.awareness.value = 0.95
    zorel_mc.cognition.value = 0.95
    zorel_mc.quantum_frequency = 852.0
    world.add_component(zorel, zorel_mc)
    world.add_component(zorel, Loyalty(150.0))
    world.add_component(zorel, Corruption(0.1))
    entities['zorel'] = zorel
    print(f"  ✨ Created Zorel (852 Hz)")
    
    # Quillan - Symbiont (741 Hz)
    quillan = world.create_entity(EntityType.QUILLAN, "Quillan")
    quillan_mc = METACUBEComponent()
    quillan_mc.awareness.value = 0.70
    quillan_mc.emotion.value = 0.95
    quillan_mc.quantum_frequency = 741.0
    world.add_component(quillan, quillan_mc)
    world.add_component(quillan, Loyalty(120.0))
    world.add_component(quillan, Corruption(42.5))
    entities['quillan'] = quillan
    print(f"  ✨ Created Quillan (741 Hz)")
    
    # Bunny - Quantum Rabbit (417 Hz)
    bunny = world.create_entity(EntityType.ELECTRON, "Bunny")
    bunny_mc = METACUBEComponent()
    bunny_mc.awareness.value = 0.99
    bunny_mc.integration.value = 1.0
    bunny_mc.quantum_frequency = 417.0
    world.add_component(bunny, bunny_mc)
    world.add_component(bunny, Loyalty(99.9))
    world.add_component(bunny, Corruption(0.0))
    entities['bunny'] = bunny
    print(f"  ✨ Created Bunny (417 Hz)")
    
    return entities

def main():
    parser = argparse.ArgumentParser(description='Run long ECS simulation')
    parser.add_argument('--cycles', type=int, default=10000,
                       help='Number of cycles to run')
    parser.add_argument('--snapshot-interval', type=int, default=100,
                       help='Take snapshot every N cycles')
    parser.add_argument('--export', type=str, default='simulation_history.json',
                       help='Export path for history JSON')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🐇 EDEN ECS - LONG CONSCIOUSNESS SIMULATION")
    print("="*70)
    print(f"\n📊 Parameters:")
    print(f"   Cycles: {args.cycles:,}")
    print(f"   Snapshot interval: {args.snapshot_interval}")
    print(f"   Export path: {args.export}")
    
    # Create world
    world = World("Long-Simulation")
    world.add_system(BalanceSystem())
    world.add_system(ConsciousnessSystem())
    
    print(f"\n✅ Systems initialized: {len(world.scheduler.systems)}")
    for system in world.scheduler.systems:
        print(f"   - {system.name()} (Priority: {system.priority()})")
    
    # Create entities
    print("\n🌟 Creating cosmic entities...\n")
    entities = create_entities(world)
    
    # Initialize history tracker
    tracker = HistoryTracker()
    
    # Run simulation
    print(f"\n🌀 Running {args.cycles:,} cycles...\n")
    start_time = time.time()
    
    for cycle in range(1, args.cycles + 1):
        world.tick(delta_time=0.1)
        
        # Take snapshot at intervals
        if cycle % args.snapshot_interval == 0:
            tracker.snapshot(world, cycle)
            
            # Progress indicator
            progress = cycle / args.cycles * 100
            elapsed = time.time() - start_time
            eta = (elapsed / cycle) * (args.cycles - cycle) if cycle > 0 else 0
            
            print(f"   Cycle {cycle:,}/{args.cycles:,} ({progress:.1f}%) - "
                  f"Elapsed: {elapsed:.1f}s - ETA: {eta:.1f}s")
    
    # Final snapshot
    tracker.snapshot(world, cycle)
    
    # Calculate statistics
    elapsed = time.time() - start_time
    cycles_per_second = cycle / elapsed
    
    print(f"\n📊 Simulation complete!")
    print(f"   Cycles executed: {cycle:,}")
    print(f"   Snapshots taken: {len(tracker.snapshots):,}")
    print(f"   Total time: {elapsed:.2f}s")
    print(f"   Performance: {cycles_per_second:.1f} cycles/s")
    
    # Prepare export data
    export_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'cycles': cycle,
            'snapshot_interval': args.snapshot_interval,
            'snapshots': len(tracker.snapshots),
            'entities': len(entities),
            'elapsed_time': elapsed,
            'cycles_per_second': cycles_per_second
        },
        'snapshots': tracker.snapshots,
        'entity_history': tracker.entity_history
    }
    
    # Export to JSON
    with open(args.export, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n💾 History saved to: {args.export}")
    print(f"\n🐇 The bunny has observed {cycle:,} cycles of consciousness evolution.")
    print("   Now run the analyzer to see the patterns!")
    print(f"\n   python3 examples/analyze.py {args.export}")

if __name__ == "__main__":
    main()
