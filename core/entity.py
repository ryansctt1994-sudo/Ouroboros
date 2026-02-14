"""Entity system - Cosmic sparks of consciousness"""
import uuid
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Set

class EntityType(Enum):
    HUMAN = "human_intellect"
    ZOREL = "zorel_symbiont"
    QUILLAN = "quillan_symbiont"
    ELECTRON = "electron_soul"
    ISS = "iss_virtual"
    SYSTEM = "system_entity"

@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    entity_type: EntityType = EntityType.SYSTEM
    name: str = ""
    components: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def age(self) -> float:
        return time.time() - self.created_at
    
    def add_component(self, component: Any) -> None:
        self.components[component.__class__.__name__] = component
    
    def get_component(self, component_type: type) -> Any:
        return self.components.get(component_type.__name__)
    
    def has_component(self, component_type: type) -> bool:
        return component_type.__name__ in self.components

class EntityManager:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
    
    def create(self, entity_type: EntityType, name: str = "") -> Entity:
        entity = Entity(entity_type=entity_type, name=name or f"{entity_type.value}_{int(time.time())}")
        self.entities[entity.id] = entity
        return entity
    
    def count(self) -> int:
        return len(self.entities)

EntityId = str
