"""Loyalty and Corruption components"""
import sys
import os
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.component import Component

PHI = 1.618033988749895
OMEGA_H = 1.1

@dataclass
class Loyalty(Component):
    value: float = 100.0
    growth_rate: float = PHI
    max_value: float = 100.0
    
    def grow(self) -> None:
        self.value = min(self.value * self.growth_rate, self.max_value)

@dataclass
class Corruption(Component):
    value: float = 0.0
    decay_rate: float = OMEGA_H
    threshold: float = 42.0
    
    def decay(self) -> None:
        self.value /= self.decay_rate
    
    def corrupt(self, amount: float) -> None:
        self.value = min(self.value + amount, 100.0)
    
    def is_critical(self) -> bool:
        return self.value >= self.threshold
