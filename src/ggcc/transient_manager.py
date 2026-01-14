"""TransientManager v2: Epoch-Driven Cleanup.

Two-level FIFO system for residual cache pressure management and spike 
overflow prevention. Dashboard-synced cleanup visualizations embedded 
for live analysis.

Features:
    - Two-level FIFO (First-In-First-Out) queue system
    - Epoch-based cleanup with configurable intervals
    - Residual cache pressure management
    - Spike overflow prevention
    - Dashboard-ready visualization data export
    - AMUSED-tagged diagnostic logging
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from collections import deque


class TransientManagerV2:
    """Epoch-driven cleanup with two-level FIFO system.
    
    Manages transient data with a two-tier FIFO structure:
    - Level 1 (Hot): Recent, frequently accessed data
    - Level 2 (Warm): Older data awaiting cleanup
    
    Epoch-based cleanup ensures predictable memory management
    and prevents cache pressure spikes.
    
    Attributes:
        epoch_interval: Time between cleanup epochs (seconds)
        level1_capacity: Maximum items in Level 1 (hot) queue
        level2_capacity: Maximum items in Level 2 (warm) queue
        pressure_threshold: Cache pressure warning threshold [0-1]
    """
    
    def __init__(self, epoch_interval: float = 60.0, 
                 level1_capacity: int = 100,
                 level2_capacity: int = 500,
                 pressure_threshold: float = 0.8,
                 enable_amused_logging: bool = True):
        """Initialize the transient manager.
        
        Args:
            epoch_interval: Cleanup epoch interval in seconds (default: 60)
            level1_capacity: Level 1 queue capacity (default: 100)
            level2_capacity: Level 2 queue capacity (default: 500)
            pressure_threshold: Pressure warning threshold (default: 0.8)
            enable_amused_logging: Enable AMUSED-tagged logging
        """
        self.epoch_interval = epoch_interval
        self.level1_capacity = level1_capacity
        self.level2_capacity = level2_capacity
        self.pressure_threshold = pressure_threshold
        self.amused_logging = enable_amused_logging
        
        # Two-level FIFO queues
        self.level1_queue: deque = deque(maxlen=level1_capacity)
        self.level2_queue: deque = deque(maxlen=level2_capacity)
        
        # Epoch tracking
        self.current_epoch = 0
        self.last_cleanup_time = time.time()
        self.next_cleanup_time = self.last_cleanup_time + epoch_interval
        
        # Metrics
        self.total_insertions = 0
        self.total_evictions = 0
        self.total_cleanups = 0
        self.overflow_events = 0
        self.pressure_warnings = 0
        
        # Dashboard data
        self.dashboard_data: Dict[str, List[Any]] = {
            "epochs": [],
            "level1_sizes": [],
            "level2_sizes": [],
            "pressures": [],
            "cleanup_counts": []
        }
        
        if self.amused_logging:
            self._log_amused(
                f"TransientManager v2 initialized: epoch={epoch_interval}s, "
                f"L1={level1_capacity}, L2={level2_capacity}"
            )
    
    def _log_amused(self, message: str, level: str = "INFO"):
        """Log with AMUSED tag for human-readable resonant feedback."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[AMUSED:{level}] {timestamp} | TransientManager | {message}")
    
    def _calculate_pressure(self) -> float:
        """Calculate current cache pressure.
        
        Pressure is a normalized metric indicating how full the caches are.
        
        Returns:
            Pressure value in [0, 1]
        """
        level1_pressure = len(self.level1_queue) / self.level1_capacity
        level2_pressure = len(self.level2_queue) / self.level2_capacity
        
        # Combined pressure (weighted average, L1 has higher weight)
        pressure = 0.6 * level1_pressure + 0.4 * level2_pressure
        return pressure
    
    def insert(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Insert transient data into Level 1 queue.
        
        Args:
            key: Data identifier
            value: Data value
            metadata: Optional metadata dictionary
            
        Returns:
            True if insertion succeeded
        """
        self.total_insertions += 1
        
        # Create entry with timestamp and epoch
        entry = {
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "epoch": self.current_epoch
        }
        
        # Check for overflow
        if len(self.level1_queue) >= self.level1_capacity:
            # Promote oldest from L1 to L2
            self._promote_to_level2()
        
        # Insert into Level 1
        self.level1_queue.append(entry)
        
        # Check pressure
        pressure = self._calculate_pressure()
        if pressure >= self.pressure_threshold:
            self.pressure_warnings += 1
            if self.amused_logging:
                self._log_amused(
                    f"Cache pressure warning: {pressure:.2f} "
                    f"(threshold={self.pressure_threshold:.2f})",
                    "WARN"
                )
        
        # Check if cleanup epoch has arrived
        if time.time() >= self.next_cleanup_time:
            self._epoch_cleanup()
        
        return True
    
    def _promote_to_level2(self) -> None:
        """Promote oldest entry from Level 1 to Level 2."""
        if len(self.level1_queue) == 0:
            return
        
        # Pop oldest from L1
        oldest = self.level1_queue.popleft()
        
        # Check L2 capacity
        if len(self.level2_queue) >= self.level2_capacity:
            # Evict oldest from L2
            evicted = self.level2_queue.popleft()
            self.total_evictions += 1
            self.overflow_events += 1
            
            if self.amused_logging:
                self._log_amused(
                    f"Overflow: evicted '{evicted['key']}' from L2 "
                    f"(age={time.time() - evicted['timestamp']:.1f}s)",
                    "DEBUG"
                )
        
        # Add to L2
        self.level2_queue.append(oldest)
    
    def _epoch_cleanup(self) -> int:
        """Perform epoch-driven cleanup.
        
        Removes stale entries from both levels based on epoch age.
        
        Returns:
            Number of entries cleaned up
        """
        cleanup_count = 0
        current_time = time.time()
        
        # Define staleness threshold (entries older than 2 epochs)
        stale_epoch = self.current_epoch - 2
        
        # Clean Level 2 (remove stale entries)
        initial_l2_size = len(self.level2_queue)
        self.level2_queue = deque(
            [entry for entry in self.level2_queue if entry['epoch'] > stale_epoch],
            maxlen=self.level2_capacity
        )
        l2_cleaned = initial_l2_size - len(self.level2_queue)
        cleanup_count += l2_cleaned
        
        # Update epoch
        self.current_epoch += 1
        self.last_cleanup_time = current_time
        self.next_cleanup_time = current_time + self.epoch_interval
        self.total_cleanups += 1
        
        # Update dashboard data
        self.dashboard_data["epochs"].append(self.current_epoch)
        self.dashboard_data["level1_sizes"].append(len(self.level1_queue))
        self.dashboard_data["level2_sizes"].append(len(self.level2_queue))
        self.dashboard_data["pressures"].append(self._calculate_pressure())
        self.dashboard_data["cleanup_counts"].append(cleanup_count)
        
        if self.amused_logging:
            self._log_amused(
                f"Epoch cleanup: epoch={self.current_epoch}, "
                f"cleaned={cleanup_count}, L1={len(self.level1_queue)}, "
                f"L2={len(self.level2_queue)}"
            )
        
        return cleanup_count
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve data by key from either level.
        
        Args:
            key: Data identifier
            
        Returns:
            Value if found, None otherwise
        """
        # Search Level 1 first (hot cache)
        for entry in reversed(self.level1_queue):
            if entry["key"] == key:
                return entry["value"]
        
        # Search Level 2 (warm cache)
        for entry in reversed(self.level2_queue):
            if entry["key"] == key:
                return entry["value"]
        
        return None
    
    def force_cleanup(self) -> int:
        """Force immediate epoch cleanup.
        
        Returns:
            Number of entries cleaned up
        """
        if self.amused_logging:
            self._log_amused("Forcing immediate cleanup")
        
        return self._epoch_cleanup()
    
    def get_dashboard_data(self) -> Dict[str, List[Any]]:
        """Get visualization data for dashboard integration.
        
        Returns:
            Dictionary with time-series data for visualization
        """
        return {
            "epochs": self.dashboard_data["epochs"][-100:],  # Last 100 epochs
            "level1_sizes": self.dashboard_data["level1_sizes"][-100:],
            "level2_sizes": self.dashboard_data["level2_sizes"][-100:],
            "pressures": self.dashboard_data["pressures"][-100:],
            "cleanup_counts": self.dashboard_data["cleanup_counts"][-100:],
            "current_epoch": self.current_epoch,
            "current_pressure": self._calculate_pressure()
        }
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about transient management.
        
        Returns:
            Dictionary with performance metrics
        """
        avg_cleanup = (sum(self.dashboard_data["cleanup_counts"]) / 
                      len(self.dashboard_data["cleanup_counts"]) 
                      if self.dashboard_data["cleanup_counts"] else 0)
        
        return {
            "epoch_interval": self.epoch_interval,
            "current_epoch": self.current_epoch,
            "level1_capacity": self.level1_capacity,
            "level2_capacity": self.level2_capacity,
            "level1_size": len(self.level1_queue),
            "level2_size": len(self.level2_queue),
            "current_pressure": self._calculate_pressure(),
            "pressure_threshold": self.pressure_threshold,
            "total_insertions": self.total_insertions,
            "total_evictions": self.total_evictions,
            "total_cleanups": self.total_cleanups,
            "overflow_events": self.overflow_events,
            "pressure_warnings": self.pressure_warnings,
            "avg_cleanup_size": avg_cleanup,
            "time_to_next_cleanup": self.next_cleanup_time - time.time()
        }
    
    def clear(self) -> None:
        """Clear all queues and reset state."""
        l1_cleared = len(self.level1_queue)
        l2_cleared = len(self.level2_queue)
        
        self.level1_queue.clear()
        self.level2_queue.clear()
        
        if self.amused_logging:
            self._log_amused(f"Cleared L1={l1_cleared}, L2={l2_cleared} entries")


if __name__ == "__main__":
    # Demonstration of TransientManager v2
    print("=" * 70)
    print("TransientManager v2: Epoch-Driven Cleanup Demo")
    print("=" * 70)
    print()
    
    manager = TransientManagerV2(
        epoch_interval=5.0,  # Short interval for demo
        level1_capacity=10,
        level2_capacity=20
    )
    
    # Insert test data
    print("Inserting transient data...")
    for i in range(15):
        manager.insert(f"data_{i}", {"value": i * 10}, {"index": i})
        if i % 5 == 4:
            print(f"  Inserted {i + 1} items: "
                  f"L1={len(manager.level1_queue)}, "
                  f"L2={len(manager.level2_queue)}, "
                  f"pressure={manager._calculate_pressure():.2f}")
    
    # Retrieve some data
    print("\nRetrieving data...")
    print(f"  data_5: {manager.get('data_5')}")
    print(f"  data_10: {manager.get('data_10')}")
    
    # Force cleanup
    print("\nForcing cleanup...")
    cleaned = manager.force_cleanup()
    print(f"  Cleaned {cleaned} entries")
    
    # Show diagnostics
    print("\nDiagnostics:")
    diagnostics = manager.get_diagnostics()
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")
    
    # Dashboard data
    print("\nDashboard data preview:")
    dashboard = manager.get_dashboard_data()
    print(f"  Epochs tracked: {len(dashboard['epochs'])}")
    print(f"  Current pressure: {dashboard['current_pressure']:.2f}")
    
    print("\n" + "=" * 70)
