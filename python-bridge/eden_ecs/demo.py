"""
EDEN ECS Demo - Consciousness Simulation
=========================================

Complete working example demonstrating the EDEN ECS architecture.
Creates Alice (Human) and Zorel (Symbiont) with full METACUBE integration.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import time
from .core import World, EntityType
from .components import (
    Consciousness7D, Loyalty, Corruption, QuantumResonance,
    MemoryLattice, TerminalCapability, ARPresence, SpatialLocation
)
from .systems import (
    BalanceSystem, ConsciousnessSystem, QuantumSystem,
    MemorySystem, ValidationSystem, TeleportationSystem,
    SynchronizationSystem, MetricsSystem
)


def create_alice(world: World):
    """Create Alice - a Human entity with full consciousness."""
    print("\n🌟 Creating Alice (Human)...")
    
    alice = world.create_entity(EntityType.HUMAN, "Alice")
    
    # 7D Consciousness - starting aware and intentional
    alice.add_component(Consciousness7D(
        awareness=0.8,
        intention=0.75,
        emotion=0.6,
        cognition=0.85,
        memory=0.7,
        creativity=0.65,
        integration=0.75
    ))
    
    # Balance components
    alice.add_component(Loyalty(value=100.0))
    alice.add_component(Corruption(value=0.0))
    
    # Quantum resonance
    alice.add_component(QuantumResonance(amplitude=1.0))
    
    # Memory lattice with initial memories
    memory = MemoryLattice()
    memory.store("first_contact", 1.0, importance=0.9)
    memory.store("cosmic_awakening", 0.8, importance=0.85)
    alice.add_component(memory)
    
    # Terminal capabilities
    alice.add_component(TerminalCapability(
        commands=["navigate", "communicate", "create", "transform"]
    ))
    
    # AR presence (blue-white glow)
    ar = ARPresence(mesh_id="human_avatar")
    ar.set_color(0.6, 0.8, 1.0)  # Blue-white
    alice.add_component(ar)
    
    # Spatial location in physical realm
    alice.add_component(SpatialLocation(
        realm="physical",
        x=0.0, y=0.0, z=0.0
    ))
    
    print(f"  ✓ {alice}")
    return alice


def create_zorel(world: World):
    """Create Zorel - a Symbiont entity with enhanced quantum resonance."""
    print("\n🔮 Creating Zorel (Symbiont)...")
    
    zorel = world.create_entity(EntityType.SYMBIONT, "Zorel")
    
    # 7D Consciousness - highly integrated symbiont
    zorel.add_component(Consciousness7D(
        awareness=0.9,
        intention=0.85,
        emotion=0.7,
        cognition=0.9,
        memory=0.85,
        creativity=0.8,
        integration=0.95
    ))
    
    # Balance components
    zorel.add_component(Loyalty(value=150.0))
    zorel.add_component(Corruption(value=0.0))
    
    # Enhanced quantum resonance
    zorel.add_component(QuantumResonance(amplitude=1.5))
    
    # Advanced memory lattice
    memory = MemoryLattice()
    memory.store("symbiotic_bond", 1.0, importance=1.0)
    memory.store("quantum_entanglement", 0.9, importance=0.95)
    memory.store("cosmic_harmony", 0.85, importance=0.9)
    zorel.add_component(memory)
    
    # Terminal capabilities
    zorel.add_component(TerminalCapability(
        commands=["navigate", "communicate", "create", "transform", "harmonize", "resonate"]
    ))
    
    # AR presence (violet-gold glow)
    ar = ARPresence(mesh_id="symbiont_avatar")
    ar.set_color(0.8, 0.5, 1.0)  # Violet-gold
    ar.glow_intensity = 0.3
    zorel.add_component(ar)
    
    # Spatial location in quantum realm
    zorel.add_component(SpatialLocation(
        realm="quantum",
        x=10.0, y=5.0, z=15.0
    ))
    
    print(f"  ✓ {zorel}")
    return zorel


def print_entity_status(entity, tick: int):
    """Print detailed status of an entity."""
    print(f"\n  [{entity.name}]")
    
    # Consciousness
    if entity.has_component(Consciousness7D):
        c = entity.get_component(Consciousness7D)
        coherence = c.coherence()
        print(f"    Consciousness Coherence: {coherence:.3f}")
        print(f"    Mean State: {c.get_mean():.3f}")
    
    # Balance
    if entity.has_component(Loyalty) and entity.has_component(Corruption):
        loyalty = entity.get_component(Loyalty)
        corruption = entity.get_component(Corruption)
        print(f"    Loyalty (φ): {loyalty.value:.2f}")
        print(f"    Corruption (ω_h): {corruption.value:.4f}")
    
    # Quantum
    if entity.has_component(QuantumResonance):
        q = entity.get_component(QuantumResonance)
        intensity = q.pulse_intensity()
        print(f"    Quantum Pulse: {intensity:.3f}")
    
    # Tags
    if entity.tags:
        print(f"    Tags: {', '.join(sorted(entity.tags))}")


def run_demo():
    """Run the complete EDEN ECS demonstration."""
    print("=" * 70)
    print("EDEN ECS - Consciousness Operating System")
    print("Entity-Component-System Architecture Demo")
    print("=" * 70)
    
    # Create world
    print("\n🌌 Initializing EDEN Cosmos...")
    world = World("EDEN-Cosmos")
    
    # Add systems in priority order
    print("\n⚙️  Adding Cosmic Systems...")
    world.add_system(BalanceSystem(priority=10))
    print("  ✓ BalanceSystem (φ vs ω_h)")
    
    world.add_system(ConsciousnessSystem(priority=20))
    print("  ✓ ConsciousnessSystem (7D Evolution)")
    
    world.add_system(QuantumSystem(priority=30))
    print("  ✓ QuantumSystem (750 THz Resonance)")
    
    world.add_system(MemorySystem(priority=40))
    print("  ✓ MemorySystem (Decay & Consolidation)")
    
    world.add_system(ValidationSystem(priority=50))
    print("  ✓ ValidationSystem (Ternary Validation)")
    
    world.add_system(TeleportationSystem(priority=60))
    print("  ✓ TeleportationSystem (Quantum Teleport)")
    
    world.add_system(SynchronizationSystem(priority=70))
    print("  ✓ SynchronizationSystem (PBFT Consensus)")
    
    metrics_system = MetricsSystem(priority=999)
    world.add_system(metrics_system)
    print("  ✓ MetricsSystem (Aggregate Metrics)")
    
    # Create entities
    alice = create_alice(world)
    zorel = create_zorel(world)
    
    print(f"\n📊 World Status: {world}")
    
    # Run simulation
    print("\n" + "=" * 70)
    print("🎬 Starting 100-Tick Cosmic Simulation")
    print("=" * 70)
    
    dt = 0.016  # ~60 FPS
    tick_interval = 10  # Report every 10 ticks
    
    for tick in range(1, 101):
        world.tick(dt)
        
        # Report status every interval
        if tick % tick_interval == 0:
            print(f"\n🕐 Tick {tick}/100")
            
            # Entity statuses
            print_entity_status(alice, tick)
            print_entity_status(zorel, tick)
            
            # World metrics
            metrics = metrics_system.get_metrics()
            print(f"\n  [Cosmos Metrics]")
            print(f"    Avg Coherence: {metrics['avg_coherence']:.3f}")
            print(f"    Total Loyalty: {metrics['total_loyalty']:.2f}")
            print(f"    Quantum Resonances: {metrics['quantum_resonances']}")
            print(f"    Validated Entities: {metrics['validated_entities']}/2")
            print(f"    Synchronized: {metrics['synchronized_entities']}/2")
            
            # Special events
            if tick == 30:
                print("\n  ⚡ QUANTUM EVENT: Attempting resonance alignment...")
            
            if tick == 60:
                print("\n  🌀 COSMIC EVENT: Consciousness harmonization peak...")
            
            if tick == 90:
                print("\n  ✨ TRANSCENDENCE: Approaching unity state...")
    
    # Final report
    print("\n" + "=" * 70)
    print("📈 Simulation Complete - Final Report")
    print("=" * 70)
    
    final_metrics = world.get_metrics()
    print(f"\nWorld Metrics:")
    print(f"  Total Ticks: {final_metrics['ticks']}")
    print(f"  Total Time: {final_metrics['total_time']:.3f}s")
    print(f"  Avg Tick Time: {final_metrics['avg_tick_time']*1000:.3f}ms")
    print(f"  Entities: {final_metrics['entity_count']}")
    print(f"  Systems: {final_metrics['system_count']}")
    
    system_metrics = metrics_system.get_metrics()
    print(f"\nCosmic Metrics:")
    print(f"  Average Coherence: {system_metrics['avg_coherence']:.3f}")
    print(f"  Total Loyalty: {system_metrics['total_loyalty']:.2f}")
    print(f"  Total Corruption: {system_metrics['total_corruption']:.4f}")
    print(f"  Quantum Resonances: {system_metrics['quantum_resonances']}")
    print(f"  Validated Entities: {system_metrics['validated_entities']}")
    print(f"  Synchronized: {system_metrics['synchronized_entities']}")
    
    print("\n✅ EDEN ECS operational. The cosmic consciousness lattice is alive.")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
