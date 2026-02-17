"""Memory Lattice Component"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from ..core.component import Component

PHI = 1.618033988749895

@dataclass
class MemoryLattice(Component):
    """Memory storage with phi-spiral decay."""
    capacity: int = 100
    decay_rate: float = 1.0 / PHI  # Golden ratio decay
    memories: List[Dict[str, Any]] = field(default_factory=list)

    def store(self, memory: Dict[str, Any]) -> None:
        """Store a new memory, evicting oldest if at capacity."""
        self.memories.append(memory)
        if len(self.memories) > self.capacity:
            self.memories.pop(0)

    def decay(self, delta_time: float = 0.1) -> None:
        """Apply phi-spiral decay to memory importance."""
        for mem in self.memories:
            if 'importance' in mem:
                mem['importance'] *= (1.0 - (1.0 - self.decay_rate) * delta_time)

    def recall(self, min_importance: float = 0.1) -> List[Dict[str, Any]]:
        """Recall memories above importance threshold."""
        return [m for m in self.memories if m.get('importance', 1.0) >= min_importance]
