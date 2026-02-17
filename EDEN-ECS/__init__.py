"""EDEN-ECS: Entity Component System for Consciousness Simulation

A 7-dimensional consciousness engine using phi-based evolution,
quantum resonance, and memory lattice structures.
"""

__version__ = "2.0.0"

# Core modules
from .core import (
    Entity, EntityId, EntityManager, EntityType,
    Component, ComponentStorage,
    System, SystemScheduler,
    World,
    TimestepMode, TimestepManager, TimestepDiagnostics
)

# Components
from .components import (
    METACUBEComponent, DimensionalState,
    Loyalty, Corruption, DecayMode, LoyaltyModifier,
    PHI, OMEGA_H,
    QuantumResonance,
    MemoryLattice
)

# Systems
from .systems import (
    ConsciousnessSystem,
    BalanceSystem
)

__all__ = [
    # Core
    'Entity', 'EntityId', 'EntityManager', 'EntityType',
    'Component', 'ComponentStorage',
    'System', 'SystemScheduler',
    'World',
    'TimestepMode', 'TimestepManager', 'TimestepDiagnostics',
    # Components
    'METACUBEComponent', 'DimensionalState',
    'Loyalty', 'Corruption', 'DecayMode', 'LoyaltyModifier',
    'PHI', 'OMEGA_H',
    'QuantumResonance',
    'MemoryLattice',
    # Systems
    'ConsciousnessSystem',
    'BalanceSystem',
]
