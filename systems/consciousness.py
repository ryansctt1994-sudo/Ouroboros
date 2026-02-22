"""Consciousness Evolution System"""
from core import System

class ConsciousnessSystem(System):
    """Evolves 7D consciousness states"""
    
    def name(self) -> str:
        return "🧠 Consciousness Evolution"
    
    def priority(self) -> int:
        return 50
    
    def process(self, world, delta_time: float) -> None:
        # Import here to avoid circular imports
        from components import METACUBEComponent
        
        entities = world.query(METACUBEComponent)
        for entity in entities:
            mc = entity.get_component(METACUBEComponent)
            before = mc.coherence()
            mc.evolve(delta_time)
            after = mc.coherence()
            
            if abs(after - before) > 0.05:
                print(f"✨ {entity.name} coherence: {before:.3f} → {after:.3f}")
