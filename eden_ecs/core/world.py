"""World container"""
from collections import defaultdict
from typing import List, Type, Optional
from .entity import Entity, EntityManager, EntityType
from .component import Component
from .system import System, SystemScheduler
from .timestep import TimestepMode, TimestepManager, TimestepDiagnostics

class World:
    def __init__(
        self, 
        name: str = "EDEN-Cosmos",
        timestep_mode: TimestepMode = TimestepMode.HYBRID,
        fixed_timestep: float = 1.0 / 60.0
    ):
        self.name = name
        self.entity_manager = EntityManager()
        self.scheduler = SystemScheduler()
        self.time = 0.0
        self.metrics = {'ticks': 0, 'entities_created': 0}
        self._event_handlers = defaultdict(list)
        self._pending_deletions: List[str] = []
        self._in_process: bool = False
        
        # v2.0.0: Hybrid timestep system
        self.timestep_manager = TimestepManager(
            mode=timestep_mode,
            fixed_timestep=fixed_timestep
        )
    
    def create_entity(self, entity_type: EntityType, name: str = "") -> Entity:
        entity = self.entity_manager.create(entity_type, name)
        self.metrics['entities_created'] += 1
        return entity
    
    def add_component(self, entity: Entity, component: Component) -> None:
        entity.add_component(component)
    
    def add_system(self, system: System) -> None:
        self.scheduler.add_system(system)
    
    def tick(self, delta_time: Optional[float] = None) -> None:
        """
        Execute one world update tick.
        
        In v2.0.0, this uses the hybrid timestep system when delta_time is None.
        For backwards compatibility, passing delta_time explicitly bypasses the timestep manager.
        """
        self._in_process = True
        try:
            if delta_time is not None:
                # Legacy mode: direct tick
                self.scheduler.tick(self, delta_time)
                self.time += delta_time
                self.metrics['ticks'] += 1
            else:
                # v2.0.0 mode: use timestep manager
                physics_deltas, alpha = self.timestep_manager.update()
                
                for dt in physics_deltas:
                    self.scheduler.tick(self, dt)
                    self.time += dt
                    self.metrics['ticks'] += 1
                
                # Store interpolation alpha for rendering
                self.metrics['interpolation_alpha'] = alpha
        finally:
            self._in_process = False
            for entity_id in self._pending_deletions:
                self.entity_manager.remove(entity_id)
            self._pending_deletions.clear()
    
    def get_timestep_diagnostics(self) -> TimestepDiagnostics:
        """Get timestep performance diagnostics (v2.0.0)"""
        return self.timestep_manager.get_diagnostics()
    
    def query(self, *component_types: Type[Component]) -> List[Entity]:
        return [e for e in self.entity_manager.entities.values() 
                if all(e.has_component(ct) for ct in component_types)]

    def emit(self, event) -> None:
        for handler in self._event_handlers[type(event)]:
            handler(event)

    def on(self, event_type, handler) -> None:
        self._event_handlers[event_type].append(handler)

    def has_entity(self, entity_id: str) -> bool:
        return entity_id in self.entity_manager.entities

    def remove_entity(self, entity_id: str) -> bool:
        if not self.has_entity(entity_id):
            return False
        if self._in_process:
            if entity_id not in self._pending_deletions:
                self._pending_deletions.append(entity_id)
            return True
        return self.entity_manager.remove(entity_id)

    def query_components(self, component_types: List[Type[Component]]) -> List[tuple]:
        result = []
        for entity in self.entity_manager.entities.values():
            if all(entity.has_component(ct) for ct in component_types):
                comps = tuple(entity.get_component(ct) for ct in component_types)
                result.append((entity.id, comps))
        return result
