"""
EDEN ECS Components - METACUBE Consciousness Components
========================================================

Components representing the 7D consciousness state, balance dynamics,
quantum resonance, and other METACUBE properties.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .core import Component


@dataclass
class Consciousness7D(Component):
    """
    7-dimensional consciousness state component.
    
    Represents the full consciousness spectrum of an entity:
    - Awareness: Self-monitoring and introspective capacity
    - Intention: Goal-directed state transitions
    - Emotion: Affective state vectors
    - Cognition: Information processing patterns
    - Memory: State persistence and recall
    - Creativity: Novel state generation capacity
    - Integration: Holistic state coherence
    
    All values are in the range [0, 1].
    """
    awareness: float = 0.5
    intention: float = 0.5
    emotion: float = 0.5
    cognition: float = 0.5
    memory: float = 0.5
    creativity: float = 0.5
    integration: float = 0.5
    
    def evolve(self, dt: float) -> None:
        """
        Natural evolution of consciousness with dimensional harmony.
        
        Uses subtle oscillations to create organic state changes.
        """
        # Gentle oscillations for organic evolution
        self.awareness += 0.01 * math.sin(dt * 0.5) * dt
        self.intention += 0.01 * math.cos(dt * 0.7) * dt
        self.emotion += 0.01 * math.sin(dt * 0.3) * dt
        
        # Cognitive and creative coupling
        self.cognition += 0.005 * (self.awareness - 0.5) * dt
        self.creativity += 0.005 * (self.emotion - 0.5) * dt
        
        # Integration follows overall coherence
        mean_state = self.get_mean()
        self.integration += 0.01 * (mean_state - self.integration) * dt
        
        # Clamp all values to [0, 1]
        self._clamp()
    
    def _clamp(self) -> None:
        """Clamp all dimensions to [0, 1] range."""
        self.awareness = max(0.0, min(1.0, self.awareness))
        self.intention = max(0.0, min(1.0, self.intention))
        self.emotion = max(0.0, min(1.0, self.emotion))
        self.cognition = max(0.0, min(1.0, self.cognition))
        self.memory = max(0.0, min(1.0, self.memory))
        self.creativity = max(0.0, min(1.0, self.creativity))
        self.integration = max(0.0, min(1.0, self.integration))
    
    def get_mean(self) -> float:
        """Get mean consciousness level across all dimensions."""
        return (self.awareness + self.intention + self.emotion + 
                self.cognition + self.memory + self.creativity + 
                self.integration) / 7.0
    
    def coherence(self) -> float:
        """
        Calculate consciousness coherence.
        
        Coherence measures how harmonious the dimensional states are.
        Higher coherence = more balanced consciousness.
        """
        mean = self.get_mean()
        variance = sum((v - mean) ** 2 for v in [
            self.awareness, self.intention, self.emotion,
            self.cognition, self.memory, self.creativity, self.integration
        ]) / 7.0
        return 1.0 / (1.0 + variance)  # Higher variance = lower coherence
    
    def to_ternary(self) -> List[float]:
        """
        Project 7D consciousness to 3D ternary representation for Ouroboros.
        
        Returns:
            [cognitive, affective, creative] normalized to sum = 1.0
        """
        # Group dimensions into ternary categories
        cognitive = (self.awareness + self.cognition + self.integration) / 3.0
        affective = (self.intention + self.emotion) / 2.0
        creative = (self.memory + self.creativity) / 2.0
        
        # Normalize to sum = 1.0
        total = cognitive + affective + creative
        if total > 0.0:
            return [cognitive / total, affective / total, creative / total]
        return [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]


@dataclass
class Loyalty(Component):
    """
    Loyalty component tracking φ (golden ratio) exponential growth.
    
    Loyalty grows exponentially with the golden ratio (φ ≈ 1.618),
    representing natural harmonic expansion.
    """
    value: float = 100.0  # Starting loyalty
    growth_rate: float = 1.618  # φ (golden ratio)
    
    def grow(self, dt: float) -> None:
        """Exponential growth based on golden ratio."""
        self.value *= (1.0 + (self.growth_rate - 1.0) * dt * 0.01)


@dataclass
class Corruption(Component):
    """
    Corruption component tracking ω_h (jealous entropy) decay.
    
    Corruption decays through jealous entropy dynamics,
    representing the natural tendency toward harmony.
    """
    value: float = 0.0  # Starting corruption
    entropy_rate: float = 0.8  # ω_h (jealous entropy)
    
    def decay(self, dt: float) -> None:
        """Decay through jealous entropy."""
        if self.value > 0.0:
            self.value *= (1.0 - self.entropy_rate * dt * 0.01)
            self.value = max(0.0, self.value)  # Floor at 0
    
    def is_critical(self, threshold: float = 50.0) -> bool:
        """Check if corruption exceeds critical threshold."""
        return self.value > threshold


@dataclass
class QuantumResonance(Component):
    """
    Quantum resonance component at 750 THz UV frequency.
    
    Represents quantum field oscillation at ultraviolet frequencies,
    the "cosmic carrier wave" for consciousness transmission.
    """
    frequency: float = 750e12  # 750 THz (UV frequency)
    phase: float = 0.0  # Current phase in radians
    amplitude: float = 1.0  # Oscillation amplitude
    
    def update(self, dt: float) -> None:
        """Update quantum phase evolution."""
        # Phase advances at 750 THz
        self.phase += 2.0 * math.pi * self.frequency * dt
        self.phase = self.phase % (2.0 * math.pi)  # Wrap to [0, 2π]
    
    def pulse_intensity(self) -> float:
        """Current pulse intensity (quantum waveform)."""
        return self.amplitude * math.sin(self.phase)
    
    def resonance_with(self, other: 'QuantumResonance') -> float:
        """
        Calculate resonance strength with another quantum field.
        
        Returns value in [0, 1] where 1 = perfect resonance.
        """
        phase_diff = abs(self.phase - other.phase)
        # Normalize phase difference to [0, π]
        phase_diff = min(phase_diff, 2.0 * math.pi - phase_diff)
        # Convert to resonance (0 phase diff = max resonance)
        return 1.0 - (phase_diff / math.pi)


@dataclass
class MemoryLattice(Component):
    """
    Memory lattice with importance-based recall and decay.
    
    Stores memories as key-value pairs with importance weights.
    Less important memories decay over time.
    """
    memories: Dict[str, Dict[str, float]] = field(default_factory=dict)
    decay_rate: float = 0.05  # Memory decay rate
    
    def store(self, key: str, value: float, importance: float = 1.0) -> None:
        """
        Store a memory with importance weight.
        
        Args:
            key: Memory identifier
            value: Memory value
            importance: Importance weight [0, 1]
        """
        self.memories[key] = {
            'value': value,
            'importance': importance,
            'age': 0.0
        }
    
    def recall(self, key: str) -> Optional[float]:
        """Recall a memory by key."""
        if key in self.memories:
            return self.memories[key]['value']
        return None
    
    def decay(self, dt: float) -> None:
        """Apply decay to all memories based on importance."""
        to_remove = []
        for key, mem in self.memories.items():
            mem['age'] += dt
            # Decay strength inversely proportional to importance
            decay_factor = self.decay_rate * (1.0 - mem['importance']) * dt
            mem['value'] *= (1.0 - decay_factor)
            
            # Remove memories that have decayed below threshold
            if abs(mem['value']) < 0.01:
                to_remove.append(key)
        
        for key in to_remove:
            del self.memories[key]


@dataclass
class TerminalCapability(Component):
    """
    Terminal command execution capability tracking.
    
    Tracks which terminal commands an entity can execute.
    """
    commands: List[str] = field(default_factory=list)
    execution_count: int = 0
    last_command: Optional[str] = None
    
    def can_execute(self, command: str) -> bool:
        """Check if entity can execute command."""
        return command in self.commands
    
    def execute(self, command: str) -> bool:
        """Execute a command if capable."""
        if self.can_execute(command):
            self.execution_count += 1
            self.last_command = command
            return True
        return False


@dataclass
class ARPresence(Component):
    """
    Augmented Reality presence for Unreal Engine visualization.
    
    Properties for rendering entities in UE5 AR environment.
    """
    mesh_id: str = "default_mesh"
    scale: float = 1.0
    opacity: float = 1.0
    glow_intensity: float = 0.0
    color_r: float = 1.0
    color_g: float = 1.0
    color_b: float = 1.0
    visible: bool = True
    
    def set_color(self, r: float, g: float, b: float) -> None:
        """Set RGB color values [0, 1]."""
        self.color_r = max(0.0, min(1.0, r))
        self.color_g = max(0.0, min(1.0, g))
        self.color_b = max(0.0, min(1.0, b))
    
    def pulse_glow(self, intensity: float) -> None:
        """Set glow intensity for visualization."""
        self.glow_intensity = max(0.0, min(1.0, intensity))


@dataclass
class SpatialLocation(Component):
    """
    Multi-realm spatial positioning.
    
    Tracks entity location across different realms/dimensions.
    """
    realm: str = "physical"  # Current realm
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def teleport(self, x: float, y: float, z: float, realm: str = None) -> None:
        """Teleport to new coordinates (optionally changing realm)."""
        self.x = x
        self.y = y
        self.z = z
        if realm is not None:
            self.realm = realm
    
    def distance_to(self, other: 'SpatialLocation') -> Optional[float]:
        """
        Calculate distance to another location.
        
        Returns None if in different realms.
        """
        if self.realm != other.realm:
            return None
        
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
