"""
Adaptive Backpressure Manager V2

Self-tuning queue management with systemic latency awareness.
Provides intelligent backpressure control for high-throughput systems.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from collections import deque
from queue import Queue, Full, Empty
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueueMetrics:
    """Metrics for a managed queue."""
    queue_id: str
    size: int
    capacity: int
    utilization: float
    avg_latency_ms: float
    drop_rate: float
    throughput: float  # items per second
    
    
@dataclass
class BackpressureSignal:
    """Backpressure signal for flow control."""
    severity: str  # 'none', 'low', 'medium', 'high', 'critical'
    recommended_rate: float  # items per second
    queue_utilization: float
    system_latency_ms: float
    action: str  # 'continue', 'slow_down', 'pause', 'drop'


class AdaptiveBackpressureManagerV2:
    """
    Self-tuning queue management with systemic latency awareness.
    
    Features:
    - Adaptive queue sizing based on load
    - Latency-aware backpressure signals
    - Automatic drop strategy during overload
    - Per-queue and system-wide monitoring
    - Throughput optimization
    
    Example:
        manager = AdaptiveBackpressureManagerV2()
        queue_id = manager.create_queue('processing', initial_capacity=1000)
        
        # Producer
        signal = manager.check_backpressure(queue_id)
        if signal.action != 'drop':
            manager.enqueue(queue_id, item)
        
        # Consumer
        item = manager.dequeue(queue_id)
    """
    
    def __init__(
        self,
        latency_target_ms: float = 100.0,
        utilization_target: float = 0.7,
        adaptation_interval: float = 5.0,
        min_capacity: int = 100,
        max_capacity: int = 100000,
    ):
        """
        Initialize backpressure manager.
        
        Args:
            latency_target_ms: Target latency in milliseconds
            utilization_target: Target queue utilization (0.0-1.0)
            adaptation_interval: Seconds between capacity adjustments
            min_capacity: Minimum queue capacity
            max_capacity: Maximum queue capacity
        """
        self.latency_target_ms = latency_target_ms
        self.utilization_target = utilization_target
        self.adaptation_interval = adaptation_interval
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        
        self._queues: Dict[str, Queue] = {}
        self._capacities: Dict[str, int] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        self._latency_windows: Dict[str, deque] = {}
        self._drop_counts: Dict[str, int] = {}
        self._enqueue_times: Dict[str, Dict[Any, float]] = {}
        
        self._lock = threading.Lock()
        self._last_adaptation = time.time()
        
        # System-wide metrics
        self._system_latency_window = deque(maxlen=1000)
        
    def create_queue(
        self,
        queue_id: str,
        initial_capacity: int = 1000,
    ) -> str:
        """
        Create a managed queue.
        
        Args:
            queue_id: Unique identifier for the queue
            initial_capacity: Initial queue capacity
            
        Returns:
            Queue ID
        """
        with self._lock:
            if queue_id in self._queues:
                raise ValueError(f"Queue {queue_id} already exists")
            
            capacity = max(self.min_capacity, min(initial_capacity, self.max_capacity))
            self._queues[queue_id] = Queue(maxsize=capacity)
            self._capacities[queue_id] = capacity
            self._metrics[queue_id] = {
                'enqueue_count': 0,
                'dequeue_count': 0,
                'drop_count': 0,
                'last_throughput_check': time.time(),
            }
            self._latency_windows[queue_id] = deque(maxlen=100)
            self._drop_counts[queue_id] = 0
            self._enqueue_times[queue_id] = {}
        
        logger.info(f"Created queue {queue_id} with capacity {capacity}")
        return queue_id
    
    def enqueue(
        self,
        queue_id: str,
        item: Any,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Enqueue an item with backpressure handling.
        
        Args:
            queue_id: Queue identifier
            item: Item to enqueue
            timeout: Optional timeout in seconds
            
        Returns:
            True if enqueued, False if dropped
        """
        if queue_id not in self._queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue = self._queues[queue_id]
        enqueue_time = time.time()
        
        try:
            queue.put(item, block=True, timeout=timeout if timeout else 0.1)
            
            with self._lock:
                self._metrics[queue_id]['enqueue_count'] += 1
                # Store enqueue time for latency tracking
                self._enqueue_times[queue_id][id(item)] = enqueue_time
            
            return True
            
        except Full:
            # Queue is full, apply drop strategy
            with self._lock:
                self._metrics[queue_id]['drop_count'] += 1
                self._drop_counts[queue_id] += 1
            
            logger.debug(f"Dropped item from queue {queue_id} (full)")
            return False
    
    def dequeue(
        self,
        queue_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[Any]:
        """
        Dequeue an item and update metrics.
        
        Args:
            queue_id: Queue identifier
            timeout: Optional timeout in seconds
            
        Returns:
            Dequeued item or None if empty/timeout
        """
        if queue_id not in self._queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue = self._queues[queue_id]
        
        try:
            item = queue.get(block=True, timeout=timeout if timeout else 0.1)
            dequeue_time = time.time()
            
            with self._lock:
                self._metrics[queue_id]['dequeue_count'] += 1
                
                # Calculate latency if we have enqueue time
                item_id = id(item)
                if item_id in self._enqueue_times[queue_id]:
                    latency_ms = (dequeue_time - self._enqueue_times[queue_id][item_id]) * 1000
                    self._latency_windows[queue_id].append(latency_ms)
                    self._system_latency_window.append(latency_ms)
                    del self._enqueue_times[queue_id][item_id]
            
            return item
            
        except Empty:
            return None
    
    def check_backpressure(self, queue_id: str) -> BackpressureSignal:
        """
        Check current backpressure status.
        
        Args:
            queue_id: Queue identifier
            
        Returns:
            BackpressureSignal with current status
        """
        if queue_id not in self._queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue = self._queues[queue_id]
        
        with self._lock:
            size = queue.qsize()
            capacity = self._capacities[queue_id]
            utilization = size / capacity if capacity > 0 else 0.0
            
            # Calculate average latency
            latency_window = self._latency_windows[queue_id]
            avg_latency = statistics.mean(latency_window) if latency_window else 0.0
            
            # System-wide latency
            system_latency = (
                statistics.mean(self._system_latency_window)
                if self._system_latency_window else 0.0
            )
        
        # Determine severity and action
        if utilization > 0.95 or avg_latency > self.latency_target_ms * 3:
            severity = 'critical'
            action = 'drop'
            recommended_rate = 0.0
        elif utilization > 0.85 or avg_latency > self.latency_target_ms * 2:
            severity = 'high'
            action = 'pause'
            recommended_rate = 10.0  # Very low rate
        elif utilization > 0.75 or avg_latency > self.latency_target_ms * 1.5:
            severity = 'medium'
            action = 'slow_down'
            recommended_rate = 50.0
        elif utilization > 0.65:
            severity = 'low'
            action = 'slow_down'
            recommended_rate = 100.0
        else:
            severity = 'none'
            action = 'continue'
            recommended_rate = 1000.0  # High rate
        
        return BackpressureSignal(
            severity=severity,
            recommended_rate=recommended_rate,
            queue_utilization=utilization,
            system_latency_ms=system_latency,
            action=action,
        )
    
    def adapt_capacity(self, queue_id: str) -> int:
        """
        Adapt queue capacity based on recent metrics.
        
        Args:
            queue_id: Queue identifier
            
        Returns:
            New capacity
        """
        if queue_id not in self._queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        current_time = time.time()
        
        with self._lock:
            # Only adapt if enough time has passed
            if current_time - self._last_adaptation < self.adaptation_interval:
                return self._capacities[queue_id]
            
            queue = self._queues[queue_id]
            current_capacity = self._capacities[queue_id]
            current_size = queue.qsize()
            utilization = current_size / current_capacity if current_capacity > 0 else 0.0
            
            # Adjust capacity based on utilization
            new_capacity = current_capacity
            
            if utilization > self.utilization_target + 0.2:
                # Increase capacity by 50%
                new_capacity = int(current_capacity * 1.5)
            elif utilization < self.utilization_target - 0.2 and current_capacity > self.min_capacity:
                # Decrease capacity by 25%
                new_capacity = int(current_capacity * 0.75)
            
            # Clamp to min/max
            new_capacity = max(self.min_capacity, min(new_capacity, self.max_capacity))
            
            if new_capacity != current_capacity:
                # Create new queue with new capacity and transfer items
                old_queue = self._queues[queue_id]
                new_queue = Queue(maxsize=new_capacity)
                
                # Transfer existing items
                items_transferred = 0
                while not old_queue.empty() and items_transferred < new_capacity:
                    try:
                        item = old_queue.get_nowait()
                        new_queue.put_nowait(item)
                        items_transferred += 1
                    except (Empty, Full):
                        break
                
                self._queues[queue_id] = new_queue
                self._capacities[queue_id] = new_capacity
                
                logger.info(
                    f"Adapted queue {queue_id} capacity: {current_capacity} -> {new_capacity} "
                    f"(utilization: {utilization:.2%})"
                )
            
            self._last_adaptation = current_time
            return new_capacity
    
    def get_metrics(self, queue_id: str) -> QueueMetrics:
        """
        Get current metrics for a queue.
        
        Args:
            queue_id: Queue identifier
            
        Returns:
            QueueMetrics
        """
        if queue_id not in self._queues:
            raise ValueError(f"Queue {queue_id} not found")
        
        queue = self._queues[queue_id]
        
        with self._lock:
            size = queue.qsize()
            capacity = self._capacities[queue_id]
            utilization = size / capacity if capacity > 0 else 0.0
            
            # Calculate metrics
            latency_window = self._latency_windows[queue_id]
            avg_latency = statistics.mean(latency_window) if latency_window else 0.0
            
            metrics = self._metrics[queue_id]
            enqueue_count = metrics['enqueue_count']
            dequeue_count = metrics['dequeue_count']
            drop_count = metrics['drop_count']
            
            # Calculate drop rate
            total_attempts = enqueue_count + drop_count
            drop_rate = drop_count / total_attempts if total_attempts > 0 else 0.0
            
            # Calculate throughput
            current_time = time.time()
            time_elapsed = current_time - metrics['last_throughput_check']
            throughput = dequeue_count / time_elapsed if time_elapsed > 0 else 0.0
            
            # Reset counters for next interval
            metrics['enqueue_count'] = 0
            metrics['dequeue_count'] = 0
            metrics['drop_count'] = 0
            metrics['last_throughput_check'] = current_time
        
        return QueueMetrics(
            queue_id=queue_id,
            size=size,
            capacity=capacity,
            utilization=utilization,
            avg_latency_ms=avg_latency,
            drop_rate=drop_rate,
            throughput=throughput,
        )
    
    def get_all_metrics(self) -> Dict[str, QueueMetrics]:
        """
        Get metrics for all queues.
        
        Returns:
            Dictionary mapping queue IDs to QueueMetrics
        """
        return {
            queue_id: self.get_metrics(queue_id)
            for queue_id in self._queues.keys()
        }
