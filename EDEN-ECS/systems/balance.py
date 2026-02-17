"""Balance System - Loyalty vs Corruption (φ vs ω_h)"""

from ..core.system import System
from ..components.loyalty import Loyalty, Corruption, PHI, OMEGA_H

class BalanceSystem(System):
    def name(self) -> str:
        return "⚖️ Balance System"
    
    def priority(self) -> int:
        return 100
    
    def process(self, world, delta_time: float) -> None:
        """Evolve Loyalty (φ growth) and Corruption (ω_h decay)"""
        entities = world.query(Loyalty, Corruption)
        
        for entity in entities:
            loyalty = entity.get_component(Loyalty)
            corruption = entity.get_component(Corruption)
            
            # Loyalty grows via golden ratio
            loyalty.grow(delta_time)
            
            # Corruption decays via jealous entropy
            corruption.decay(delta_time)
            
            # Warn if corruption is critical
            if corruption.is_critical():
                print(f"⚠️ {entity.name} corruption critical: {corruption.value:.1f}")
