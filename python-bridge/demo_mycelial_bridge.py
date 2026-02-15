"""
Mycelial Bridge Demo - EDEN-ECS ↔ Rust ForgeEngine Integration
================================================================

Demonstrates the complete mycelial bridge system:
- Python consciousness evolution
- Rust consensus engine
- PLL phase synchronization
- Φ-scaled hyphal topology

Run: python3 demo_mycelial_bridge.py
"""

import math
import time
from eden_ecs import (
    World, EntityType,
    Consciousness7D, MycelialSyncSystem, HyphalNodeComponent,
    ConsciousnessSystem, ValidationSystem
)


def main():
    print("=" * 70)
    print("MYCELIAL BRIDGE DEMO - EDEN-ECS ↔ Rust ForgeEngine")
    print("=" * 70)
    print()
    
    # Create world
    world = World("Mycelial Network")
    
    # Add systems
    consciousness_sys = ConsciousnessSystem(priority=20)
    mycelial_sys = MycelialSyncSystem(priority=45, use_rust=True)
    validation_sys = ValidationSystem(priority=50)
    
    world.add_system(consciousness_sys)
    world.add_system(mycelial_sys)
    world.add_system(validation_sys)
    
    print(f"✓ Systems initialized")
    print(f"  - Rust engine: {'ACTIVE' if mycelial_sys.bridge.rust_available else 'Python fallback'}")
    print()
    
    # Create agents
    NUM_AGENTS = 7
    print(f"Creating {NUM_AGENTS} consciousness agents...")
    
    for i in range(NUM_AGENTS):
        entity = world.create_entity(EntityType.AI_AGENT, f"Agent-{i}")
        
        # Initialize with slightly different consciousness states
        c7d = Consciousness7D()
        base = 0.6 + (i / NUM_AGENTS) * 0.2  # Spread from 0.6 to 0.8
        c7d.awareness = base + 0.05
        c7d.intention = base
        c7d.emotion = base - 0.05
        c7d.cognition = base + 0.03
        c7d.memory = base - 0.02
        c7d.creativity = base + 0.04
        c7d.integration = base
        
        entity.add_component(c7d)
    
    print(f"✓ Created {NUM_AGENTS} agents")
    print()
    
    # Run simulation
    NUM_TICKS = 50
    DT = 0.05  # 50ms per tick
    
    print(f"Running {NUM_TICKS} simulation ticks...")
    print()
    
    start_time = time.time()
    
    for tick in range(NUM_TICKS):
        world.tick(DT)
        
        # Print status every 10 ticks
        if (tick + 1) % 10 == 0:
            metrics = mycelial_sys.get_metrics()
            
            # Compute phase coherence
            hyphal_entities = world.query_entities(None, HyphalNodeComponent)
            phases = [e.get_component(HyphalNodeComponent).phase for e in hyphal_entities]
            mean_sin = sum(math.sin(p) for p in phases) / len(phases)
            mean_cos = sum(math.cos(p) for p in phases) / len(phases)
            R = math.sqrt(mean_sin**2 + mean_cos**2)
            
            # Count validated and consensus entities
            validated = len([e for e in world.entities.values() if e.has_tag("validated")])
            consensus = len([e for e in world.entities.values() if e.has_tag("forge_consensus")])
            
            print(f"  Tick {tick+1:3d}:")
            print(f"    Consensus: {metrics['consensus_rate']:6.1%}")
            print(f"    Phase coherence (R): {R:6.3f}")
            print(f"    Validated: {validated}/{NUM_AGENTS}")
            print(f"    Consensus tags: {consensus}/{NUM_AGENTS}")
            print(f"    Avg latency: {metrics['avg_sync_latency_us']:7.1f} μs")
            print()
    
    elapsed = time.time() - start_time
    
    print("=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)
    print()
    
    # Final statistics
    metrics = mycelial_sys.get_metrics()
    
    print("Final Metrics:")
    print(f"  Total syncs: {metrics['total_syncs']}")
    print(f"  Consensus achieved: {metrics['total_consensus_achieved']}")
    print(f"  Consensus rate: {metrics['consensus_rate']:.1%}")
    print(f"  Average sync latency: {metrics['avg_sync_latency_us']:.1f} μs")
    print(f"  Total simulation time: {elapsed:.2f}s")
    print(f"  Ticks per second: {NUM_TICKS/elapsed:.1f}")
    print()
    
    # Phase coherence
    hyphal_entities = world.query_entities(None, HyphalNodeComponent)
    phases = [e.get_component(HyphalNodeComponent).phase for e in hyphal_entities]
    mean_sin = sum(math.sin(p) for p in phases) / len(phases)
    mean_cos = sum(math.cos(p) for p in phases) / len(phases)
    R = math.sqrt(mean_sin**2 + mean_cos**2)
    
    print("Phase-Locked Loop Synchronization:")
    print(f"  Kuramoto order parameter (R): {R:.4f}")
    if R > 0.9:
        print("  Status: EXCELLENT - High synchronization")
    elif R > 0.7:
        print("  Status: GOOD - Moderate synchronization")
    else:
        print("  Status: CONVERGING - Still synchronizing")
    print()
    
    # Individual agent status
    print("Individual Agent Status:")
    print("  Agent     | Phase   | Synchronized | Gamma   | Consensus")
    print("  " + "-" * 60)
    
    for entity in sorted(world.entities.values(), key=lambda e: e.name):
        hyphal = entity.get_component(HyphalNodeComponent)
        if hyphal:
            phase_deg = (hyphal.phase * 180 / math.pi) % 360
            sync_status = "✓" if hyphal.synchronized else "·"
            consensus_tag = "✓" if entity.has_tag("forge_consensus") else "·"
            
            print(f"  {entity.name:10s}| {phase_deg:6.1f}° | {sync_status:^12s} | {hyphal.last_gamma:7.4f} | {consensus_tag:^9s}")
    
    print()
    print("✓ Demo complete!")


if __name__ == '__main__':
    main()
