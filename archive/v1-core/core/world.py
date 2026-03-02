"""World - The cosmic container"""
from typing import List, Type
from .entity import Entity, EntityManager, EntityType
from .component import Component, ComponentStorage
from .system import System, SystemScheduler

class World:
    def __init__(self, name: str = "EDEN-Cosmos"):
        self.name = name
        self.entity_manager = EntityManager()
        self.component_storages = {}
        self.scheduler = SystemScheduler()
        self.time = 0.0
        self.metrics = {'ticks': 0, 'entities_created': 0}
    
    def create_entity(self, entity_type: EntityType, name: str = "") -> Entity:
        entity = self.entity_manager.create(entity_type, name)
        self.metrics['entities_created'] += 1
        return entity
    
    def add_component(self, entity: Entity, component: Component) -> None:
        comp_type = component.__class__.__name__
        if comp_type not in self.component_storages:
            self.component_storages[comp_type] = ComponentStorage()
        self.component_storages[comp_type].add(entity.id, component)
        entity.add_component(component)
    
    def add_system(self, system: System) -> None:
        self.scheduler.add_system(system)
    
    def tick(self, delta_time: float = 1.0/60.0) -> None:
        self.scheduler.tick(self, delta_time)
        self.time += delta_time
        self.metrics['ticks'] += 1
    
    def query(self, *component_types: Type[Component]) -> List[Entity]:
        return [e for e in self.entity_manager.entities.values() 
                if all(e.has_component(ct) for ct in component_types)]
