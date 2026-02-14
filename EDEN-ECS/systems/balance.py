"""Balance System - Loyalty vs Corruption (φ vs ω_h)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.system import System
from components.loyalty import Loyalty, Corruption, PHI, OMEGA_H

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
            loyalty.grow()
            
            # Corruption decays via jealous entropy
            corruption.decay()
            
            # Warn if corruption is critical
            if corruption.is_critical():
                print(f"⚠️ {entity.name} corruption critical: {corruption.value:.1f}")
