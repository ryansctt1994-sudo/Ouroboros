"""Loyalty and Corruption components with v2.0.0 enhancements"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
from enum import Enum
import json
import time

from ..core.component import Component

PHI = 1.618033988749895
OMEGA_H = 1.1


class DecayMode(Enum):
    """Loyalty decay modes for v2.0.0"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    CUSTOM = "custom"


@dataclass
class LoyaltyModifier:
    """Temporary modifier for loyalty values"""
    name: str
    amount: float
    duration: float  # seconds
    start_time: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if modifier has expired"""
        return (time.time() - self.start_time) >= self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'name': self.name,
            'amount': self.amount,
            'duration': self.duration,
            'start_time': self.start_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoyaltyModifier':
        """Deserialize from dictionary"""
        return cls(**data)


@dataclass
class Loyalty(Component):
    """Enhanced Loyalty component with v2.0.0 features"""
    value: float = 100.0
    growth_rate: float = PHI
    max_value: float = 100.0
    decay_mode: DecayMode = DecayMode.EXPONENTIAL
    custom_decay_fn: Optional[Callable[[float, float], float]] = None
    
    # v2.0.0: Temporary modifiers
    modifiers: List[LoyaltyModifier] = field(default_factory=list)
    
    # v2.0.0: Trend analysis
    history: List[float] = field(default_factory=list)
    max_history_size: int = 100
    
    def grow(self, delta_time: float = 1.0) -> None:
        """Asymptotic growth toward max_value using golden ratio."""
        base_growth = (self.growth_rate - 1.0) * (self.max_value - self.value) * delta_time * 0.01
        
        # Apply modifiers
        modifier_sum = sum(m.amount for m in self.modifiers)
        
        self.value += base_growth + modifier_sum * delta_time
        self.value = min(self.value, self.max_value)
        
        # Update history
        self._update_history()
    
    def decay(self, delta_time: float = 1.0) -> None:
        """Apply decay based on selected mode"""
        if self.decay_mode == DecayMode.LINEAR:
            decay_amount = 1.0 * delta_time
            self.value = max(0.0, self.value - decay_amount)
        
        elif self.decay_mode == DecayMode.EXPONENTIAL:
            # Exponential decay: faster at higher values
            decay_amount = self.value * 0.01 * delta_time
            self.value = max(0.0, self.value - decay_amount)
        
        elif self.decay_mode == DecayMode.LOGARITHMIC:
            # Logarithmic decay: slower at higher values
            import math
            if self.value > 1.0:
                decay_amount = math.log(self.value) * 0.1 * delta_time
                self.value = max(0.0, self.value - decay_amount)
        
        elif self.decay_mode == DecayMode.CUSTOM:
            # Custom decay function
            if self.custom_decay_fn:
                self.value = self.custom_decay_fn(self.value, delta_time)
                self.value = max(0.0, min(self.value, self.max_value))
        
        # Update history
        self._update_history()
    
    def add_modifier(self, name: str, amount: float, duration: float) -> None:
        """Add a temporary modifier"""
        self.modifiers.append(LoyaltyModifier(name, amount, duration))
    
    def cleanup_modifiers(self) -> int:
        """Remove expired modifiers. Returns count of removed modifiers."""
        initial_count = len(self.modifiers)
        self.modifiers = [m for m in self.modifiers if not m.is_expired()]
        return initial_count - len(self.modifiers)
    
    def _update_history(self) -> None:
        """Update value history for trend analysis"""
        self.history.append(self.value)
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
    
    def get_trend(self) -> str:
        """Analyze trend from history"""
        if len(self.history) < 2:
            return "stable"
        
        recent = self.history[-10:] if len(self.history) >= 10 else self.history
        
        # Calculate average change
        total_change = recent[-1] - recent[0]
        avg_change = total_change / len(recent)
        
        if avg_change > 0.1:  # More sensitive threshold
            return "increasing"
        elif avg_change < -0.1:  # More sensitive threshold
            return "decreasing"
        else:
            return "stable"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (v2.0.0 feature)"""
        return {
            'value': self.value,
            'growth_rate': self.growth_rate,
            'max_value': self.max_value,
            'decay_mode': self.decay_mode.value,
            'modifiers': [m.to_dict() for m in self.modifiers],
            'history': self.history[-20:],  # Save last 20 entries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Loyalty':
        """Deserialize from dictionary (v2.0.0 feature)"""
        loyalty = cls(
            value=data['value'],
            growth_rate=data['growth_rate'],
            max_value=data['max_value'],
            decay_mode=DecayMode(data['decay_mode']),
        )
        loyalty.modifiers = [LoyaltyModifier.from_dict(m) for m in data.get('modifiers', [])]
        loyalty.history = data.get('history', [])
        return loyalty


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

