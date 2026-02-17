"""
Dynamic Tensor Warden V2

Predictive memory eviction with fragmentation handling.
Manages tensor lifecycle and optimizes memory usage during training.
"""

import time
import threading
from typing import Dict, Optional, Any, Set, List, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class TensorMetadata:
    """Metadata for a tracked tensor."""
    tensor_id: str
    owner: str
    size_mb: float
    is_critical: bool
    creation_time: float
    last_access_time: float
    access_count: int
    predicted_next_access: float
    can_evict: bool


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_allocated_mb: float
    total_limit_mb: float
    utilization: float
    tensor_count: int
    critical_tensor_count: int
    eviction_count: int
    fragmentation_ratio: float


class DynamicTensorWardenV2:
    """
    Predictive tensor memory management with fragmentation handling.
    
    Features:
    - LRU-based eviction with criticality awareness
    - Predictive access pattern learning
    - Fragmentation monitoring and reduction
    - Per-owner memory tracking
    - Automatic defragmentation
    
    Example:
        warden = DynamicTensorWardenV2(memory_limit_gb=16)
        warden.register_tensor('attention_weights', tensor, critical=True)
        
        # Request tensor (may trigger eviction)
        result = warden.request_tensor('attention_weights', 'model_a')
        
        # Cleanup when done
        warden.release_tensor('attention_weights')
    """
    
    def __init__(
        self,
        memory_limit_gb: float = 16.0,
        eviction_threshold: float = 0.85,
        fragmentation_threshold: float = 0.3,
        prediction_window: int = 10,
    ):
        """
        Initialize tensor warden.
        
        Args:
            memory_limit_gb: Memory limit in gigabytes
            eviction_threshold: Utilization threshold for triggering eviction
            fragmentation_threshold: Threshold for defragmentation
            prediction_window: Number of accesses to use for prediction
        """
        self.memory_limit_mb = memory_limit_gb * 1024
        self.eviction_threshold = eviction_threshold
        self.fragmentation_threshold = fragmentation_threshold
        self.prediction_window = prediction_window
        
        self._tensors: Dict[str, TensorMetadata] = {}
        self._tensor_data: Dict[str, Any] = {}  # Actual tensor storage
        self._owner_tensors: Dict[str, Set[str]] = defaultdict(set)
        self._access_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=prediction_window)
        )
        
        self._allocated_mb = 0.0
        self._eviction_count = 0
        self._fragmented_space_mb = 0.0
        
        self._lock = threading.Lock()
        
    def register_tensor(
        self,
        tensor_id: str,
        tensor: Any,
        owner: str = 'default',
        size_mb: Optional[float] = None,
        critical: bool = False,
    ) -> bool:
        """
        Register a tensor for management.
        
        Args:
            tensor_id: Unique tensor identifier
            tensor: Tensor object
            owner: Owner identifier (e.g., model name)
            size_mb: Size in MB (estimated if not provided)
            critical: Whether tensor is critical (won't be evicted)
            
        Returns:
            True if registered successfully
        """
        current_time = time.time()
        
        # Estimate size if not provided
        if size_mb is None:
            size_mb = self._estimate_size(tensor)
        
        with self._lock:
            # Check if we need to evict
            if self._allocated_mb + size_mb > self.memory_limit_mb * self.eviction_threshold:
                if not critical:
                    # Try to make space
                    evicted_mb = self._evict_to_make_space(size_mb, critical)
                    if evicted_mb < size_mb:
                        logger.warning(
                            f"Could not free enough space for tensor {tensor_id} "
                            f"(need {size_mb} MB, freed {evicted_mb} MB)"
                        )
                        return False
            
            # Check hard limit
            if self._allocated_mb + size_mb > self.memory_limit_mb:
                logger.error(
                    f"Cannot register tensor {tensor_id}: "
                    f"would exceed memory limit ({self.memory_limit_mb} MB)"
                )
                return False
            
            # Register tensor
            metadata = TensorMetadata(
                tensor_id=tensor_id,
                owner=owner,
                size_mb=size_mb,
                is_critical=critical,
                creation_time=current_time,
                last_access_time=current_time,
                access_count=0,
                predicted_next_access=current_time + 1.0,  # Assume soon
                can_evict=not critical,
            )
            
            self._tensors[tensor_id] = metadata
            self._tensor_data[tensor_id] = tensor
            self._owner_tensors[owner].add(tensor_id)
            self._allocated_mb += size_mb
        
        logger.debug(f"Registered tensor {tensor_id} ({size_mb:.2f} MB) for {owner}")
        return True
    
    def _estimate_size(self, tensor: Any) -> float:
        """
        Estimate tensor size in MB.
        
        Args:
            tensor: Tensor object
            
        Returns:
            Estimated size in MB
        """
        # This is a simplified estimation
        # In production, would use actual tensor.nbytes or similar
        try:
            # Try to get actual size if available
            if hasattr(tensor, 'nbytes'):
                return tensor.nbytes / (1024 * 1024)
            elif hasattr(tensor, '__sizeof__'):
                return tensor.__sizeof__() / (1024 * 1024)
        except Exception:
            pass
        
        # Default estimate
        return 1.0
    
    def request_tensor(
        self,
        tensor_id: str,
        requesting_owner: str = 'default',
    ) -> Optional[Any]:
        """
        Request access to a tensor.
        
        Args:
            tensor_id: Tensor identifier
            requesting_owner: Requester identifier
            
        Returns:
            Tensor object if available, None if evicted
        """
        current_time = time.time()
        
        with self._lock:
            if tensor_id not in self._tensors:
                logger.warning(f"Tensor {tensor_id} not found")
                return None
            
            if tensor_id not in self._tensor_data:
                logger.info(f"Tensor {tensor_id} was evicted")
                return None
            
            # Update access metadata
            metadata = self._tensors[tensor_id]
            metadata.last_access_time = current_time
            metadata.access_count += 1
            
            # Record access for prediction
            self._access_history[tensor_id].append(current_time)
            
            # Update prediction
            metadata.predicted_next_access = self._predict_next_access(tensor_id)
            
            return self._tensor_data[tensor_id]
    
    def _predict_next_access(self, tensor_id: str) -> float:
        """
        Predict next access time for a tensor.
        
        Args:
            tensor_id: Tensor identifier
            
        Returns:
            Predicted next access timestamp
        """
        history = self._access_history[tensor_id]
        
        if len(history) < 2:
            # Not enough data, assume soon
            return time.time() + 1.0
        
        # Calculate average interval
        intervals = [
            history[i] - history[i-1]
            for i in range(1, len(history))
        ]
        avg_interval = sum(intervals) / len(intervals)
        
        # Predict next access
        last_access = history[-1]
        return last_access + avg_interval
    
    def _evict_to_make_space(
        self,
        required_mb: float,
        for_critical: bool,
    ) -> float:
        """
        Evict tensors to make space.
        
        Args:
            required_mb: Required space in MB
            for_critical: Whether space is for a critical tensor
            
        Returns:
            Amount of space freed in MB
        """
        current_time = time.time()
        freed_mb = 0.0
        
        # Build eviction candidates (non-critical tensors)
        candidates = []
        for tensor_id, metadata in self._tensors.items():
            if metadata.can_evict and tensor_id in self._tensor_data:
                # Score based on LRU and prediction
                inactivity = current_time - metadata.last_access_time
                predicted_wait = metadata.predicted_next_access - current_time
                
                # Higher score = better candidate for eviction
                score = inactivity + max(0, predicted_wait) * 0.5
                
                candidates.append((score, tensor_id, metadata))
        
        # Sort by score (descending)
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        # Evict tensors until we have enough space
        for score, tensor_id, metadata in candidates:
            if freed_mb >= required_mb:
                break
            
            # Evict tensor
            if tensor_id in self._tensor_data:
                del self._tensor_data[tensor_id]
                freed_mb += metadata.size_mb
                self._eviction_count += 1
                
                logger.debug(
                    f"Evicted tensor {tensor_id} ({metadata.size_mb:.2f} MB, "
                    f"score: {score:.2f})"
                )
        
        # Update fragmentation estimate
        if freed_mb > 0:
            self._fragmented_space_mb += freed_mb * 0.1  # Assume 10% fragmentation
        
        return freed_mb
    
    def release_tensor(self, tensor_id: str) -> bool:
        """
        Release a tensor from management.
        
        Args:
            tensor_id: Tensor identifier
            
        Returns:
            True if released successfully
        """
        with self._lock:
            if tensor_id not in self._tensors:
                logger.warning(f"Tensor {tensor_id} not registered")
                return False
            
            metadata = self._tensors[tensor_id]
            
            # Remove from owner tracking
            self._owner_tensors[metadata.owner].discard(tensor_id)
            
            # Free memory
            if tensor_id in self._tensor_data:
                del self._tensor_data[tensor_id]
                self._allocated_mb -= metadata.size_mb
            
            # Remove metadata
            del self._tensors[tensor_id]
            
            if tensor_id in self._access_history:
                del self._access_history[tensor_id]
        
        logger.debug(f"Released tensor {tensor_id}")
        return True
    
    def defragment(self) -> float:
        """
        Defragment memory by consolidating free space.
        
        Returns:
            Amount of space reclaimed in MB
        """
        with self._lock:
            if self._fragmented_space_mb < self.fragmentation_threshold * self.memory_limit_mb:
                return 0.0
            
            # Simulate defragmentation
            reclaimed = self._fragmented_space_mb
            self._fragmented_space_mb = 0.0
        
        logger.info(f"Defragmented memory, reclaimed {reclaimed:.2f} MB")
        return reclaimed
    
    def get_statistics(self) -> MemoryStats:
        """
        Get memory usage statistics.
        
        Returns:
            MemoryStats
        """
        with self._lock:
            utilization = self._allocated_mb / self.memory_limit_mb
            
            critical_count = sum(
                1 for t in self._tensors.values()
                if t.is_critical
            )
            
            fragmentation = self._fragmented_space_mb / self.memory_limit_mb
        
        return MemoryStats(
            total_allocated_mb=self._allocated_mb,
            total_limit_mb=self.memory_limit_mb,
            utilization=utilization,
            tensor_count=len(self._tensors),
            critical_tensor_count=critical_count,
            eviction_count=self._eviction_count,
            fragmentation_ratio=fragmentation,
        )
