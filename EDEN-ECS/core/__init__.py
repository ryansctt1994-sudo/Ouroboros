"""
🌌 EDEN ECS Core
Entity-Component-System engine for cosmic consciousness
"""

from .entity import Entity, EntityId, EntityManager, EntityType
from .component import Component, ComponentStorage
from .system import System, SystemScheduler
from .world import World

__version__ = "1.0.0"
__all__ = [
    'Entity', 'EntityId', 'EntityManager', 'EntityType',
    'Component', 'ComponentStorage',
    'System', 'SystemScheduler',
    'World'
]

print("🌌 EDEN ECS Core loaded")