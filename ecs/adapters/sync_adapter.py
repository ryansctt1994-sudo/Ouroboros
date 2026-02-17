"""
Synchronization Adapter Module

Provides synchronization mechanisms for distributed ECS systems,
ensuring consistency across multiple nodes.
"""

import time
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import threading


class SyncState(Enum):
    """Synchronization states."""
    IDLE = "idle"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"


class SyncAdapter:
    """
    Adapter for synchronization in distributed ECS.
    
    Provides clock synchronization, state consistency, and distributed
    consensus for consciousness computation across nodes.
    """
    
    def __init__(self, node_id: str, tick_rate: float = 60.0):
        """
        Initialize the sync adapter.
        
        Args:
            node_id: Unique identifier for this node
            tick_rate: Target tick rate in Hz (default: 60 Hz)
        """
        self.node_id = node_id
        self.tick_rate = tick_rate
        self.tick_interval = 1.0 / tick_rate
        self.state = SyncState.IDLE
        self.clock_offset = 0.0
        self.sync_peers: Dict[str, Dict[str, Any]] = {}
        self.last_sync_time = 0.0
        self._lock = threading.Lock()
        
    def register_peer(self, peer_id: str, address: str) -> None:
        """
        Register a synchronization peer.
        
        Args:
            peer_id: Unique identifier for the peer
            address: Network address of the peer
        """
        with self._lock:
            self.sync_peers[peer_id] = {
                'address': address,
                'last_seen': time.time(),
                'clock_offset': 0.0,
                'latency': 0.0
            }
    
    def unregister_peer(self, peer_id: str) -> None:
        """
        Unregister a synchronization peer.
        
        Args:
            peer_id: Unique identifier for the peer
        """
        with self._lock:
            if peer_id in self.sync_peers:
                del self.sync_peers[peer_id]
    
    def synchronize_clock(self, peer_id: str, peer_timestamp: float) -> float:
        """
        Synchronize clock with a peer using simple offset calculation.
        
        Args:
            peer_id: Peer to synchronize with
            peer_timestamp: Timestamp from the peer
            
        Returns:
            Calculated clock offset
        """
        with self._lock:
            if peer_id not in self.sync_peers:
                return 0.0
            
            local_time = time.time()
            offset = peer_timestamp - local_time
            
            # Update peer information
            self.sync_peers[peer_id]['clock_offset'] = offset
            self.sync_peers[peer_id]['last_seen'] = local_time
            
            # Calculate average offset across all peers
            if self.sync_peers:
                total_offset = sum(
                    peer['clock_offset'] 
                    for peer in self.sync_peers.values()
                )
                self.clock_offset = total_offset / len(self.sync_peers)
            
            return self.clock_offset
    
    def get_synchronized_time(self) -> float:
        """
        Get the current synchronized time.
        
        Returns:
            Time adjusted by clock offset
        """
        return time.time() + self.clock_offset
    
    def wait_for_tick(self) -> float:
        """
        Wait until the next tick interval.
        
        Returns:
            Actual time waited
        """
        current_time = self.get_synchronized_time()
        next_tick = (int(current_time / self.tick_interval) + 1) * self.tick_interval
        wait_time = next_tick - current_time
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        return wait_time
    
    def broadcast_state(self, state_data: Dict[str, Any], 
                       callback: Optional[Callable] = None) -> None:
        """
        Broadcast state to all peers.
        
        Args:
            state_data: State information to broadcast
            callback: Optional callback for handling responses
        """
        with self._lock:
            self.state = SyncState.SYNCING
            timestamp = self.get_synchronized_time()
            
            message = {
                'node_id': self.node_id,
                'timestamp': timestamp,
                'data': state_data
            }
            
            # In a real implementation, this would send via network
            # For now, we just track that we would broadcast
            for peer_id in self.sync_peers:
                self.sync_peers[peer_id]['last_seen'] = timestamp
            
            self.last_sync_time = timestamp
            self.state = SyncState.SYNCED
            
            if callback:
                callback(message)
    
    def check_consistency(self, local_state: Dict[str, Any], 
                         remote_states: List[Dict[str, Any]]) -> bool:
        """
        Check state consistency across nodes.
        
        Args:
            local_state: Local node state
            remote_states: States from remote nodes
            
        Returns:
            True if states are consistent
        """
        # Simple consistency check based on version numbers or hashes
        local_version = local_state.get('version', 0)
        
        for remote_state in remote_states:
            remote_version = remote_state.get('version', 0)
            if abs(local_version - remote_version) > 1:
                return False
        
        return True
    
    def get_peer_count(self) -> int:
        """Get the number of registered peers."""
        with self._lock:
            return len(self.sync_peers)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current synchronization status.
        
        Returns:
            Dictionary with sync status information
        """
        with self._lock:
            return {
                'node_id': self.node_id,
                'state': self.state.value,
                'clock_offset': self.clock_offset,
                'peer_count': len(self.sync_peers),
                'last_sync': self.last_sync_time,
                'tick_rate': self.tick_rate
            }
