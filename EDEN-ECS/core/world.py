"""World container"""
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
    
    def get_timestep_diagnostics(self) -> TimestepDiagnostics:
        """Get timestep performance diagnostics (v2.0.0)"""
        return self.timestep_manager.get_diagnostics()
    
    def query(self, *component_types: Type[Component]) -> List[Entity]:
        return [e for e in self.entity_manager.entities.values() 
                if all(e.has_component(ct) for ct in component_types)]
