"""Memory Lattice Component with v2.0.0 enhancements"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time

from ..core.component import Component

PHI = 1.618033988749895


class MemoryAlignment(Enum):
    """Memory alignment levels for v2.0.0"""
    BYTE = 1
    WORD = 2
    DWORD = 4
    QWORD = 8
    PAGE = 4096
    CACHE_LINE = 64


@dataclass
class MemoryBlock:
    """Tagged memory block"""
    tag: str
    data: Any
    size_bytes: int
    alignment: MemoryAlignment
    allocated_time: float = field(default_factory=time.time)
    last_access_time: float = field(default_factory=time.time)
    access_count: int = 0
    critical: bool = False
    
    def access(self) -> None:
        """Record memory access"""
        self.last_access_time = time.time()
        self.access_count += 1
    
    def is_hot(self, threshold: int = 10) -> bool:
        """Check if this is a hot (frequently accessed) block"""
        return self.access_count >= threshold
    
    def is_cold(self, timeout: float = 60.0) -> bool:
        """Check if this is a cold (rarely accessed) block"""
        return (time.time() - self.last_access_time) >= timeout
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize block metadata"""
        return {
            'tag': self.tag,
            'size_bytes': self.size_bytes,
            'alignment': self.alignment.value,
            'access_count': self.access_count,
            'critical': self.critical,
            'age_seconds': time.time() - self.allocated_time
        }


@dataclass
class MemoryLattice(Component):
    """
    Memory storage with v2.0.0 enhancements.
    
    Features:
    - Tag-based allocation for debuggable retrieval
    - Six alignment levels (BYTE, WORD, DWORD, QWORD, PAGE, CACHE_LINE)
    - Defragmentation for tagged, critical blocks
    - Hot/cold access tracking for optimization
    """
    capacity: int = 100
    decay_rate: float = 1.0 / PHI  # Golden ratio decay
    memories: List[Dict[str, Any]] = field(default_factory=list)
    
    # v2.0.0: Enhanced memory management
    blocks: Dict[str, MemoryBlock] = field(default_factory=dict)
    total_allocated_bytes: int = 0
    fragmentation_count: int = 0
    max_capacity_bytes: int = 1024 * 1024  # 1 MB default

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
    
    # v2.0.0 Enhanced API
    
    def allocate(
        self,
        tag: str,
        data: Any,
        size_bytes: int,
        alignment: MemoryAlignment = MemoryAlignment.BYTE,
        critical: bool = False
    ) -> bool:
        """
        Allocate a tagged memory block.
        
        Args:
            tag: Unique identifier for this block
            data: Data to store
            size_bytes: Size in bytes
            alignment: Memory alignment requirement
            critical: Whether this block should be protected from eviction
            
        Returns:
            True if allocation succeeded, False otherwise
        """
        # Check if we have space
        if self.total_allocated_bytes + size_bytes > self.max_capacity_bytes:
            # Try to evict non-critical blocks
            if not self._evict_for_space(size_bytes):
                return False
        
        # Create block
        block = MemoryBlock(
            tag=tag,
            data=data,
            size_bytes=size_bytes,
            alignment=alignment,
            critical=critical
        )
        
        self.blocks[tag] = block
        self.total_allocated_bytes += size_bytes
        
        return True
    
    def retrieve(self, tag: str) -> Optional[Any]:
        """Retrieve data by tag and update access tracking"""
        if tag not in self.blocks:
            return None
        
        block = self.blocks[tag]
        block.access()
        return block.data
    
    def free(self, tag: str) -> bool:
        """Free a memory block by tag"""
        if tag not in self.blocks:
            return False
        
        block = self.blocks[tag]
        self.total_allocated_bytes -= block.size_bytes
        del self.blocks[tag]
        
        return True
    
    def _evict_for_space(self, required_bytes: int) -> bool:
        """Evict non-critical blocks to make space"""
        # Sort blocks by priority (non-critical, cold, old)
        evictable = [
            (tag, block) for tag, block in self.blocks.items()
            if not block.critical
        ]
        
        # Sort by access time (oldest first)
        evictable.sort(key=lambda x: x[1].last_access_time)
        
        freed = 0
        for tag, block in evictable:
            self.free(tag)
            freed += block.size_bytes
            
            if freed >= required_bytes:
                return True
        
        return False
    
    def defragment(self) -> int:
        """
        Defragment memory by removing fragmentation.
        
        In a real implementation, this would reorganize memory layout.
        Here we simulate by resetting fragmentation count.
        
        Returns:
            Number of fragmented blocks consolidated
        """
        # Sort blocks by access pattern (hot blocks together)
        hot_blocks = [(tag, block) for tag, block in self.blocks.items() if block.is_hot()]
        cold_blocks = [(tag, block) for tag, block in self.blocks.items() if not block.is_hot()]
        
        # Count fragmentation before
        initial_frag = self.fragmentation_count
        
        # Simulate defragmentation
        self.fragmentation_count = len(cold_blocks) // 4  # Reduced fragmentation
        
        return initial_frag - self.fragmentation_count
    
    def get_hot_blocks(self) -> List[str]:
        """Get tags of hot (frequently accessed) blocks"""
        return [tag for tag, block in self.blocks.items() if block.is_hot()]
    
    def get_cold_blocks(self) -> List[str]:
        """Get tags of cold (rarely accessed) blocks"""
        return [tag for tag, block in self.blocks.items() if block.is_cold()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics"""
        total_blocks = len(self.blocks)
        critical_blocks = sum(1 for b in self.blocks.values() if b.critical)
        hot_blocks = len(self.get_hot_blocks())
        cold_blocks = len(self.get_cold_blocks())
        
        return {
            'total_blocks': total_blocks,
            'critical_blocks': critical_blocks,
            'hot_blocks': hot_blocks,
            'cold_blocks': cold_blocks,
            'total_allocated_bytes': self.total_allocated_bytes,
            'capacity_bytes': self.max_capacity_bytes,
            'utilization': self.total_allocated_bytes / self.max_capacity_bytes if self.max_capacity_bytes > 0 else 0,
            'fragmentation_count': self.fragmentation_count,
            'average_access_count': sum(b.access_count for b in self.blocks.values()) / total_blocks if total_blocks > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory lattice"""
        return {
            'capacity': self.capacity,
            'blocks': {tag: block.to_dict() for tag, block in self.blocks.items()},
            'statistics': self.get_statistics()
        }

