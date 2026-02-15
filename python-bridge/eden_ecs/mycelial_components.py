"""
EDEN ECS Mycelial Components - Hyphal Network Components
=========================================================

Components for the mycelial PLL (phase-locked loop) network that
connects consciousness entities in a hyphal topology.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import math
from dataclasses import dataclass, field
from typing import List
from .core import Component


@dataclass
class HyphalNodeComponent(Component):
    """
    Hyphal node in the mycelial PLL network.
    
    Represents an entity as a phase-locked oscillator in the consciousness
    synchronization network. Nodes maintain phase coherence through
    neighbor interactions.
    """
    node_id: str = ""
    phase: float = 0.0  # Phase in radians [0, 2π)
    frequency: float = 0.0997  # Natural frequency (Hz), default ~0.1 Hz
    synchronized: bool = False
    avg_latency_us: float = 0.0  # Average sync latency in microseconds
    neighbor_ids: List[str] = field(default_factory=list)
    forge_slot: int = -1  # Forge engine slot assignment (-1 = unassigned)
    consensus_participant: bool = False
    last_gamma: float = 0.0
    last_agreement_ratio: float = 0.0
    
    # Private fields for latency tracking
    _latency_samples: List[float] = field(default_factory=list, repr=False)
    _max_latency_samples: int = field(default=10, repr=False)
    
    def advance_phase(self, dt: float) -> None:
        """
        Advance phase by natural frequency.
        
        Args:
            dt: Time delta in seconds
        """
        self.phase += 2.0 * math.pi * self.frequency * dt
        # Wrap to [0, 2π)
        self.phase = self.phase % (2.0 * math.pi)
    
    def correct_phase(self, target_phase: float, gain: float = None) -> None:
        """
        PLL phase correction toward target phase.
        
        Args:
            target_phase: Target phase in radians
            gain: PLL gain (default: 0.0997 × 3.33 ≈ 0.332)
        """
        if gain is None:
            gain = self.frequency * 3.33  # ~0.332 for default frequency
        
        # Compute phase error with wrapping to [-π, π]
        error = target_phase - self.phase
        # Normalize to [-π, π] for bidirectional correction
        while error > math.pi:
            error -= 2.0 * math.pi
        while error < -math.pi:
            error += 2.0 * math.pi
        
        # Apply correction
        self.phase += gain * error
        
        # Wrap to [0, 2π)
        self.phase = self.phase % (2.0 * math.pi)
        
        # Check synchronization
        self.synchronized = abs(error) < 0.1  # Synchronized if error < 0.1 radians
    
    def phase_distance_to(self, other: 'HyphalNodeComponent') -> float:
        """
        Circular phase distance to another node.
        
        Args:
            other: Another hyphal node
            
        Returns:
            Phase distance in [0, π] radians
        """
        diff = abs(self.phase - other.phase)
        # Normalize to [0, π] (circular distance)
        if diff > math.pi:
            diff = 2.0 * math.pi - diff
        return diff
    
    def record_latency(self, latency_us: float) -> None:
        """
        Record a sync latency sample and update rolling average.
        
        Args:
            latency_us: Latency in microseconds
        """
        self._latency_samples.append(latency_us)
        # Keep only recent samples
        if len(self._latency_samples) > self._max_latency_samples:
            self._latency_samples.pop(0)
        
        # Update average
        self.avg_latency_us = sum(self._latency_samples) / len(self._latency_samples)
    
    def to_dict(self) -> dict:
        """
        Serialize to dict for JSON export.
        
        Omits private fields (starting with _).
        
        Returns:
            Dictionary representation
        """
        return {
            'node_id': self.node_id,
            'phase': self.phase,
            'frequency': self.frequency,
            'synchronized': self.synchronized,
            'avg_latency_us': self.avg_latency_us,
            'neighbor_ids': self.neighbor_ids,
            'forge_slot': self.forge_slot,
            'consensus_participant': self.consensus_participant,
            'last_gamma': self.last_gamma,
            'last_agreement_ratio': self.last_agreement_ratio,
        }
