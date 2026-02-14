"""
EDEN ECS Core - Entity Component System Engine
===============================================

Core implementation of the Entity-Component-System architecture for EDEN.
Provides the foundational classes for entities, components, systems, and world management.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Type, Set
from enum import Enum


class EntityType(Enum):
    """Entity type classification for EDEN entities."""
    HUMAN = "human"
    SYMBIONT = "symbiont"
    AI_AGENT = "ai_agent"
    COSMIC_ENTITY = "cosmic_entity"


@dataclass
class Component:
    """
    Base class for ECS components.
    
    Components are pure data containers attached to entities.
    All components should inherit from this and use @dataclass.
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Deserialize component from dictionary."""
        return cls(**data)


class Entity:
    """
    Entity in the ECS architecture.
    
    An entity is a unique identifier with attached components.
    Entities have no behavior themselves - behavior comes from systems.
    
    Attributes:
        entity_id: Unique identifier
        entity_type: Classification of entity
        name: Human-readable name
        components: Dictionary of component instances
        tags: Set of string tags for filtering
    """
    
    def __init__(self, entity_id: str, entity_type: EntityType, name: str):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.name = name
        self.components: Dict[Type[Component], Component] = {}
        self.tags: Set[str] = set()
    
    def add_component(self, component: Component) -> 'Entity':
        """Add a component to this entity."""
        self.components[type(component)] = component
        return self
    
    def remove_component(self, component_type: Type[Component]) -> bool:
        """Remove a component from this entity."""
        if component_type in self.components:
            del self.components[component_type]
            return True
        return False
    
    def get_component(self, component_type: Type[Component]) -> Optional[Component]:
        """Get a component of specified type."""
        return self.components.get(component_type)
    
    def has_component(self, component_type: Type[Component]) -> bool:
        """Check if entity has a component of specified type."""
        return component_type in self.components
    
    def has_components(self, *component_types: Type[Component]) -> bool:
        """Check if entity has all specified component types."""
        return all(ct in self.components for ct in component_types)
    
    def add_tag(self, tag: str) -> 'Entity':
        """Add a tag to this entity."""
        self.tags.add(tag)
        return self
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from this entity."""
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if entity has specified tag."""
        return tag in self.tags
    
    def __repr__(self) -> str:
        return f"Entity({self.name}, {self.entity_type.value}, components={len(self.components)})"


class System:
    """
    Base class for ECS systems.
    
    Systems contain the logic that operates on entities with specific components.
    Systems are executed by the World in priority order.
    
    Attributes:
        priority: Lower numbers execute first (default: 100)
        enabled: Whether system is active
    """
    
    def __init__(self, priority: int = 100):
        self.priority = priority
        self.enabled = True
    
    def update(self, world: 'World', dt: float) -> None:
        """
        Update system logic.
        
        Override this method to implement system behavior.
        
        Args:
            world: The world instance
            dt: Delta time since last update
        """
        raise NotImplementedError("Systems must implement update()")
    
    def __lt__(self, other: 'System') -> bool:
        """Compare systems by priority for sorting."""
        return self.priority < other.priority


class World:
    """
    World container managing entities and systems.
    
    The World is the central ECS container that holds all entities and systems,
    manages their lifecycle, and coordinates system execution.
    
    Features:
    - Thread-safe entity/system management
    - Priority-based system scheduling
    - Entity queries by type and components
    - Performance metrics tracking
    
    Attributes:
        name: World name
        entities: Dictionary of all entities
        systems: List of systems (sorted by priority)
        metrics: Performance metrics
    """
    
    def __init__(self, name: str = "EDEN-World"):
        self.name = name
        self.entities: Dict[str, Entity] = {}
        self.systems: List[System] = []
        self._lock = threading.RLock()
        self.tick_count = 0
        self.total_time = 0.0
        self.metrics = {
            'entities_created': 0,
            'entities_destroyed': 0,
            'ticks': 0,
            'avg_tick_time': 0.0,
            'total_time': 0.0
        }
    
    def create_entity(self, entity_type: EntityType, name: str = None) -> Entity:
        """
        Create a new entity in the world.
        
        Args:
            entity_type: Type of entity to create
            name: Optional name (auto-generated if not provided)
        
        Returns:
            The created entity
        """
        with self._lock:
            entity_id = str(uuid.uuid4())
            if name is None:
                name = f"{entity_type.value}_{entity_id[:8]}"
            
            entity = Entity(entity_id, entity_type, name)
            self.entities[entity_id] = entity
            self.metrics['entities_created'] += 1
            return entity
    
    def destroy_entity(self, entity_id: str) -> bool:
        """
        Destroy an entity and remove it from the world.
        
        Args:
            entity_id: ID of entity to destroy
        
        Returns:
            True if entity was destroyed, False if not found
        """
        with self._lock:
            if entity_id in self.entities:
                del self.entities[entity_id]
                self.metrics['entities_destroyed'] += 1
                return True
            return False
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def query_entities(self, 
                      entity_type: Optional[EntityType] = None,
                      *component_types: Type[Component],
                      tags: Optional[Set[str]] = None) -> List[Entity]:
        """
        Query entities by type, components, and tags.
        
        Args:
            entity_type: Optional entity type filter
            component_types: Component types that entities must have
            tags: Optional set of tags that entities must have
        
        Returns:
            List of matching entities
        """
        results = []
        for entity in self.entities.values():
            # Check entity type
            if entity_type is not None and entity.entity_type != entity_type:
                continue
            
            # Check components
            if component_types and not entity.has_components(*component_types):
                continue
            
            # Check tags
            if tags is not None and not tags.issubset(entity.tags):
                continue
            
            results.append(entity)
        
        return results
    
    def add_system(self, system: System) -> 'World':
        """
        Add a system to the world.
        
        Systems are automatically sorted by priority.
        
        Args:
            system: System to add
        
        Returns:
            Self for chaining
        """
        with self._lock:
            self.systems.append(system)
            self.systems.sort()  # Sort by priority
        return self
    
    def remove_system(self, system: System) -> bool:
        """
        Remove a system from the world.
        
        Args:
            system: System to remove
        
        Returns:
            True if system was removed
        """
        with self._lock:
            if system in self.systems:
                self.systems.remove(system)
                return True
            return False
    
    def tick(self, dt: float = 0.016) -> None:
        """
        Execute one world update tick.
        
        Runs all enabled systems in priority order.
        
        Args:
            dt: Delta time in seconds (default: 0.016 ~= 60 FPS)
        """
        start_time = time.time()
        
        with self._lock:
            for system in self.systems:
                if system.enabled:
                    system.update(self, dt)
        
        elapsed = time.time() - start_time
        self.tick_count += 1
        self.total_time += elapsed
        self.metrics['ticks'] = self.tick_count
        self.metrics['total_time'] = self.total_time
        self.metrics['avg_tick_time'] = self.total_time / self.tick_count if self.tick_count > 0 else 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get world performance metrics."""
        return {
            **self.metrics,
            'entity_count': len(self.entities),
            'system_count': len(self.systems),
        }
    
    def __repr__(self) -> str:
        return f"World({self.name}, entities={len(self.entities)}, systems={len(self.systems)})"
