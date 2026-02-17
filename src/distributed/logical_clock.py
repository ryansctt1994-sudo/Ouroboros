"""
Hybrid Logical Clock

Distributed time synchronization for cross-repo coordination.
Implements hybrid logical clocks for causal ordering of events.
"""

import time
import threading
from typing import Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Timestamp:
    """Hybrid logical clock timestamp."""
    physical: int  # Physical time in nanoseconds
    logical: int   # Logical counter
    node_id: str   # Node identifier
    
    def __lt__(self, other: 'Timestamp') -> bool:
        """Compare timestamps for ordering."""
        if self.physical != other.physical:
            return self.physical < other.physical
        if self.logical != other.logical:
            return self.logical < other.logical
        return self.node_id < other.node_id
    
    def __le__(self, other: 'Timestamp') -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, Timestamp):
            return False
        return (
            self.physical == other.physical and
            self.logical == other.logical and
            self.node_id == other.node_id
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.node_id}@{self.physical}.{self.logical}"


class HybridLogicalClock:
    """
    Hybrid logical clock for distributed time synchronization.
    
    Provides causal ordering of events across distributed systems while
    maintaining close relationship with physical time.
    
    Features:
    - Causal ordering guarantees
    - Physical time correlation
    - Thread-safe operations
    - Clock drift detection
    
    Example:
        clock = HybridLogicalClock(node_id='ouroboros-node-1')
        
        # Generate timestamp for local event
        ts1 = clock.now()
        
        # Process remote message with timestamp
        ts2 = clock.update(remote_timestamp)
        
        # Compare timestamps
        if ts1 < ts2:
            print("Event 1 happened before event 2")
    """
    
    def __init__(
        self,
        node_id: str,
        max_drift_ms: float = 1000.0,
    ):
        """
        Initialize hybrid logical clock.
        
        Args:
            node_id: Unique identifier for this node
            max_drift_ms: Maximum allowed drift in milliseconds
        """
        self.node_id = node_id
        self.max_drift_ns = int(max_drift_ms * 1_000_000)
        
        self._logical = 0
        self._last_physical = self._physical_time()
        self._lock = threading.Lock()
        
        # Statistics
        self._event_count = 0
        self._update_count = 0
        self._drift_corrections = 0
        
    def _physical_time(self) -> int:
        """
        Get current physical time in nanoseconds.
        
        Returns:
            Physical time as integer nanoseconds
        """
        return int(time.time() * 1_000_000_000)
    
    def now(self) -> Timestamp:
        """
        Generate timestamp for a local event.
        
        Returns:
            Timestamp for the current event
        """
        with self._lock:
            physical = self._physical_time()
            
            # If physical time has advanced, reset logical counter
            if physical > self._last_physical:
                self._last_physical = physical
                self._logical = 0
            else:
                # Physical time hasn't advanced, increment logical counter
                self._logical += 1
            
            timestamp = Timestamp(
                physical=self._last_physical,
                logical=self._logical,
                node_id=self.node_id,
            )
            
            self._event_count += 1
        
        return timestamp
    
    def update(self, remote_timestamp: Timestamp) -> Timestamp:
        """
        Update clock based on remote timestamp.
        
        This is called when receiving a message with a timestamp from
        another node. It ensures causal ordering is maintained.
        
        Args:
            remote_timestamp: Timestamp from remote node
            
        Returns:
            Updated timestamp for this event
        """
        with self._lock:
            physical = self._physical_time()
            
            # Check for clock drift
            drift = abs(physical - remote_timestamp.physical)
            if drift > self.max_drift_ns:
                logger.warning(
                    f"Large clock drift detected: {drift / 1_000_000:.2f} ms "
                    f"with node {remote_timestamp.node_id}"
                )
                self._drift_corrections += 1
            
            # Take maximum of physical times
            max_physical = max(physical, remote_timestamp.physical)
            
            # Update logical counter
            if max_physical == self._last_physical:
                # Same physical time, increment past both logical counters
                self._logical = max(self._logical, remote_timestamp.logical) + 1
            elif max_physical == remote_timestamp.physical:
                # Remote physical time is ahead
                self._last_physical = max_physical
                self._logical = remote_timestamp.logical + 1
            else:
                # Local physical time is ahead
                self._last_physical = max_physical
                self._logical = 0
            
            timestamp = Timestamp(
                physical=self._last_physical,
                logical=self._logical,
                node_id=self.node_id,
            )
            
            self._update_count += 1
        
        return timestamp
    
    def compare(self, ts1: Timestamp, ts2: Timestamp) -> int:
        """
        Compare two timestamps.
        
        Args:
            ts1: First timestamp
            ts2: Second timestamp
            
        Returns:
            -1 if ts1 < ts2, 0 if equal, 1 if ts1 > ts2
        """
        if ts1 < ts2:
            return -1
        elif ts1 == ts2:
            return 0
        else:
            return 1
    
    def is_concurrent(self, ts1: Timestamp, ts2: Timestamp) -> bool:
        """
        Check if two events are concurrent (unordered).
        
        In HLC, events are always totally ordered, but we can check
        if they occurred very close in time.
        
        Args:
            ts1: First timestamp
            ts2: Second timestamp
            
        Returns:
            True if events appear concurrent
        """
        # Events are concurrent if their physical times are very close
        # and they're from different nodes
        if ts1.node_id == ts2.node_id:
            return False
        
        time_diff = abs(ts1.physical - ts2.physical)
        # Consider concurrent if within 1ms and same logical time
        return time_diff < 1_000_000 and ts1.logical == ts2.logical
    
    def time_since(self, timestamp: Timestamp) -> float:
        """
        Calculate time elapsed since a timestamp.
        
        Args:
            timestamp: Reference timestamp
            
        Returns:
            Elapsed time in seconds
        """
        current = self._physical_time()
        elapsed_ns = current - timestamp.physical
        return elapsed_ns / 1_000_000_000
    
    def get_statistics(self) -> dict:
        """
        Get clock statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                'node_id': self.node_id,
                'current_physical': self._last_physical,
                'current_logical': self._logical,
                'total_events': self._event_count,
                'total_updates': self._update_count,
                'drift_corrections': self._drift_corrections,
            }
