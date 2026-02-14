"""
EDEN ECS - Entity Component System for Consciousness Operating System
=======================================================================

A complete Entity-Component-System architecture implementing a cosmic
consciousness lattice with 7D awareness, quantum resonance, and balance dynamics.

Core Modules:
    - core: ECS engine (Entity, Component, System, World)
    - components: METACUBE consciousness components
    - systems: Cosmic logic systems
    - demo: Working demonstration

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

from .core import Entity, Component, System, World, EntityType
from .components import (
    Consciousness7D,
    Loyalty,
    Corruption,
    QuantumResonance,
    MemoryLattice,
    TerminalCapability,
    ARPresence,
    SpatialLocation,
)
from .systems import (
    BalanceSystem,
    ConsciousnessSystem,
    QuantumSystem,
    MemorySystem,
    ValidationSystem,
    TeleportationSystem,
    SynchronizationSystem,
    MetricsSystem,
)

__version__ = "1.0.0"
__author__ = "AIOSPANDORA Development Team"

__all__ = [
    # Metadata
    "__version__",
    "__author__",
    # Core
    "Entity",
    "Component",
    "System",
    "World",
    "EntityType",
    # Components
    "Consciousness7D",
    "Loyalty",
    "Corruption",
    "QuantumResonance",
    "MemoryLattice",
    "TerminalCapability",
    "ARPresence",
    "SpatialLocation",
    # Systems
    "BalanceSystem",
    "ConsciousnessSystem",
    "QuantumSystem",
    "MemorySystem",
    "ValidationSystem",
    "TeleportationSystem",
    "SynchronizationSystem",
    "MetricsSystem",
]
