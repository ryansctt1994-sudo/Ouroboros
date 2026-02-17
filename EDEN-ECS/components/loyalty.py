"""Loyalty and Corruption components"""
from dataclasses import dataclass

from ..core.component import Component

PHI = 1.618033988749895
OMEGA_H = 1.1

@dataclass
class Loyalty(Component):
    value: float = 100.0
    growth_rate: float = PHI
    max_value: float = 100.0
    
    def grow(self, delta_time: float = 1.0) -> None:
        """Asymptotic growth toward max_value using golden ratio."""
        self.value += (self.growth_rate - 1.0) * (self.max_value - self.value) * delta_time * 0.01

@dataclass
class Corruption(Component):
    value: float = 0.0
    decay_rate: float = OMEGA_H
    threshold: float = 42.0
    
    def decay(self, delta_time: float = 1.0) -> None:
        """Apply decay proportional to current corruption level."""
        decay_amount = self.value * (1.0 - 1.0/self.decay_rate) * delta_time * 0.1
        self.value = max(0.0, self.value - decay_amount)
    
    def corrupt(self, amount: float) -> None:
        self.value = min(self.value + amount, 100.0)
    
    def is_critical(self) -> bool:
        return self.value >= self.threshold
