"""EDEN-ECS: Entity Component System for Consciousness Simulation

A 7-dimensional consciousness engine using phi-based evolution,
quantum resonance, and memory lattice structures.
"""

__version__ = "1.0.0"

# Core modules
from .core import (
    Entity, EntityId, EntityManager, EntityType,
    Component, ComponentStorage,
    System, SystemScheduler,
    World
)

# Components
from .components import (
    METACUBEComponent, DimensionalState,
    Loyalty, Corruption,
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
    # Components
    'METACUBEComponent', 'DimensionalState',
    'Loyalty', 'Corruption',
    'PHI', 'OMEGA_H',
    'QuantumResonance',
    'MemoryLattice',
    # Systems
    'ConsciousnessSystem',
    'BalanceSystem',
]
