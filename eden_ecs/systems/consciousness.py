"""Consciousness Evolution System"""

from ..core.system import System
from ..components.metacube import METACUBEComponent

class ConsciousnessSystem(System):
    def name(self) -> str:
        return "🧠 Consciousness Evolution"
    
    def priority(self) -> int:
        return 50
    
    def process(self, world, delta_time: float) -> None:
        entities = world.query(METACUBEComponent)
        for entity in entities:
            mc = entity.get_component(METACUBEComponent)
            before = mc.coherence()
            mc.evolve(delta_time)
            after = mc.coherence()
            
            if abs(after - before) > 0.05:
                print(f"✨ {entity.name} coherence: {before:.3f} → {after:.3f}")
