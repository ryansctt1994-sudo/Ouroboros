"""
GPU Memory Optimizer

Zero-copy transfers with pinned memory pools for optimal GPU performance.
Manages GPU memory allocation and reduces fragmentation.
"""

import threading
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class MemoryBlock:
    """Represents a memory block in the pool."""
    block_id: str
    size_bytes: int
    is_pinned: bool
    is_allocated: bool
    allocation_time: float
    last_access_time: float
    access_count: int
    
    
@dataclass
class GPUMemoryStats:
    """GPU memory usage statistics."""
    total_allocated_mb: float
    total_pinned_mb: float
    fragmentation_ratio: float
    active_blocks: int
    free_blocks: int
    zero_copy_transfers: int


class GPUMemoryOptimizer:
    """
    GPU memory optimization with zero-copy transfers and pinned memory pools.
    
    Features:
    - Pinned memory pool management
    - Zero-copy transfer tracking
    - Fragmentation monitoring and reduction
    - Automatic memory pool resizing
    - Block reuse optimization
    
    Note: This is a simulation/abstraction layer. In production, this would
    integrate with actual GPU libraries like CUDA, cupy, or torch.
    
    Example:
        optimizer = GPUMemoryOptimizer(pool_size_mb=1024)
        block_id = optimizer.allocate_pinned(size_mb=10)
        optimizer.zero_copy_transfer(block_id, 'host_to_device')
        optimizer.free(block_id)
    """
    
    def __init__(
        self,
        pool_size_mb: float = 1024.0,
        enable_zero_copy: bool = True,
        fragmentation_threshold: float = 0.3,
        consolidation_interval: float = 60.0,
    ):
        """
        Initialize GPU memory optimizer.
        
        Args:
            pool_size_mb: Size of pinned memory pool in MB
            enable_zero_copy: Enable zero-copy transfers
            fragmentation_threshold: Threshold for triggering defragmentation
            consolidation_interval: Seconds between consolidation attempts
        """
        self.pool_size_mb = pool_size_mb
        self.enable_zero_copy = enable_zero_copy
        self.fragmentation_threshold = fragmentation_threshold
        self.consolidation_interval = consolidation_interval
        
        self._blocks: Dict[str, MemoryBlock] = {}
        self._free_blocks: List[str] = []
        self._allocated_size_mb = 0.0
        self._pinned_size_mb = 0.0
        self._zero_copy_count = 0
        self._block_counter = 0
        
        self._lock = threading.RLock()
        self._last_consolidation = time.time()
        
        # Initialize pinned memory pool
        self._init_pinned_pool()
    
    def _init_pinned_pool(self) -> None:
        """Initialize the pinned memory pool."""
        # In a real implementation, this would allocate actual pinned memory
        # For now, we simulate with tracking structures
        logger.info(f"Initialized pinned memory pool: {self.pool_size_mb} MB")
    
    def allocate_pinned(
        self,
        size_mb: float,
        block_id: Optional[str] = None,
    ) -> str:
        """
        Allocate a pinned memory block.
        
        Args:
            size_mb: Size in megabytes
            block_id: Optional custom block ID
            
        Returns:
            Block ID
        """
        with self._lock:
            if self._allocated_size_mb + size_mb > self.pool_size_mb:
                # Try to find a reusable block
                reusable = self._find_reusable_block(size_mb)
                if reusable:
                    logger.debug(f"Reusing block {reusable}")
                    self._blocks[reusable].is_allocated = True
                    self._blocks[reusable].allocation_time = time.time()
                    self._free_blocks.remove(reusable)
                    return reusable
                
                # No space available
                raise MemoryError(
                    f"Cannot allocate {size_mb} MB: "
                    f"pool size {self.pool_size_mb} MB, "
                    f"allocated {self._allocated_size_mb} MB"
                )
            
            # Create new block
            if block_id is None:
                self._block_counter += 1
                block_id = f"block_{self._block_counter}"
            
            current_time = time.time()
            block = MemoryBlock(
                block_id=block_id,
                size_bytes=int(size_mb * 1024 * 1024),
                is_pinned=True,
                is_allocated=True,
                allocation_time=current_time,
                last_access_time=current_time,
                access_count=0,
            )
            
            self._blocks[block_id] = block
            self._allocated_size_mb += size_mb
            self._pinned_size_mb += size_mb
        
        logger.debug(f"Allocated pinned block {block_id}: {size_mb} MB")
        return block_id
    
    def _find_reusable_block(self, size_mb: float) -> Optional[str]:
        """
        Find a reusable block of sufficient size.
        
        Args:
            size_mb: Required size in MB
            
        Returns:
            Block ID if found, None otherwise
        """
        size_bytes = size_mb * 1024 * 1024
        
        for block_id in self._free_blocks:
            block = self._blocks[block_id]
            if block.size_bytes >= size_bytes:
                return block_id
        
        return None
    
    def free(self, block_id: str) -> None:
        """
        Free a memory block.
        
        Args:
            block_id: ID of block to free
        """
        with self._lock:
            if block_id not in self._blocks:
                logger.warning(f"Attempted to free unknown block {block_id}")
                return
            
            block = self._blocks[block_id]
            
            if not block.is_allocated:
                logger.warning(f"Block {block_id} is already free")
                return
            
            block.is_allocated = False
            self._free_blocks.append(block_id)
        
        logger.debug(f"Freed block {block_id}")
    
    def zero_copy_transfer(
        self,
        block_id: str,
        direction: str = 'host_to_device',
    ) -> bool:
        """
        Perform a zero-copy transfer.
        
        Args:
            block_id: ID of block to transfer
            direction: 'host_to_device' or 'device_to_host'
            
        Returns:
            True if successful
        """
        if not self.enable_zero_copy:
            logger.warning("Zero-copy transfers are disabled")
            return False
        
        with self._lock:
            if block_id not in self._blocks:
                logger.error(f"Unknown block {block_id}")
                return False
            
            block = self._blocks[block_id]
            
            if not block.is_pinned:
                logger.warning(f"Block {block_id} is not pinned, cannot use zero-copy")
                return False
            
            # Simulate zero-copy transfer
            block.last_access_time = time.time()
            block.access_count += 1
            self._zero_copy_count += 1
        
        logger.debug(f"Zero-copy transfer {direction} for block {block_id}")
        return True
    
    def calculate_fragmentation(self) -> float:
        """
        Calculate memory fragmentation ratio.
        
        Returns:
            Fragmentation ratio (0.0 to 1.0)
        """
        with self._lock:
            if not self._blocks:
                return 0.0
            
            # Calculate fragmentation based on free block distribution
            total_blocks = len(self._blocks)
            free_count = len(self._free_blocks)
            
            if total_blocks == 0:
                return 0.0
            
            # Simple fragmentation metric: ratio of free blocks to total
            # In a real implementation, this would consider block sizes and gaps
            fragmentation = free_count / total_blocks
            
            return fragmentation
    
    def consolidate_memory(self) -> int:
        """
        Consolidate fragmented memory blocks.
        
        Returns:
            Number of blocks consolidated
        """
        current_time = time.time()
        
        with self._lock:
            if current_time - self._last_consolidation < self.consolidation_interval:
                return 0
            
            fragmentation = self.calculate_fragmentation()
            
            if fragmentation < self.fragmentation_threshold:
                return 0
            
            # Remove unused free blocks
            consolidated = 0
            blocks_to_remove = []
            
            for block_id in self._free_blocks:
                block = self._blocks[block_id]
                
                # Remove blocks that haven't been accessed recently
                if current_time - block.last_access_time > 300:  # 5 minutes
                    size_mb = block.size_bytes / (1024 * 1024)
                    self._allocated_size_mb -= size_mb
                    self._pinned_size_mb -= size_mb
                    blocks_to_remove.append(block_id)
                    consolidated += 1
            
            # Remove consolidated blocks
            for block_id in blocks_to_remove:
                self._free_blocks.remove(block_id)
                del self._blocks[block_id]
            
            self._last_consolidation = current_time
        
        if consolidated > 0:
            logger.info(f"Consolidated {consolidated} memory blocks")
        
        return consolidated
    
    def get_statistics(self) -> GPUMemoryStats:
        """
        Get memory usage statistics.
        
        Returns:
            GPUMemoryStats
        """
        with self._lock:
            active_blocks = sum(
                1 for block in self._blocks.values()
                if block.is_allocated
            )
            free_blocks = len(self._free_blocks)
            fragmentation = self.calculate_fragmentation()
        
        return GPUMemoryStats(
            total_allocated_mb=self._allocated_size_mb,
            total_pinned_mb=self._pinned_size_mb,
            fragmentation_ratio=fragmentation,
            active_blocks=active_blocks,
            free_blocks=free_blocks,
            zero_copy_transfers=self._zero_copy_count,
        )
    
    def resize_pool(self, new_size_mb: float) -> bool:
        """
        Resize the memory pool.
        
        Args:
            new_size_mb: New pool size in MB
            
        Returns:
            True if successful
        """
        with self._lock:
            if new_size_mb < self._allocated_size_mb:
                logger.error(
                    f"Cannot resize pool to {new_size_mb} MB: "
                    f"{self._allocated_size_mb} MB currently allocated"
                )
                return False
            
            old_size = self.pool_size_mb
            self.pool_size_mb = new_size_mb
        
        logger.info(f"Resized memory pool: {old_size} MB -> {new_size_mb} MB")
        return True
