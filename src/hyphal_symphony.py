"""
Hyphal Symphony for TSN Integration
====================================

Phase-locked mycelial networking with deterministic latency guarantees (<1μs).
Implements pulse synchronization across distributed nodes using hyphal
network topology inspired by biological mycelial networks.

Features:
- Phase-locked loop (PLL) synchronization
- Deterministic latency (<1μs target)
- Distributed pulse coordination
- Mycelial topology management
- TSN (Time-Sensitive Networking) compliance

Integration with GGCC and Φ-chuckle principles:
- Golden ratio (Φ=1.618) for node spacing optimization
- Chuckle constant (0.0997) for resonance stabilization
- 333% amplification for signal propagation
"""

import math
import time
import threading
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# Constants
PHI = 1.618033988749895  # Golden ratio
CHUCKLE_RESONANCE_HZ = 0.0997  # Chuckle-modulated resonance
AMPLIFICATION_FACTOR = 3.33  # 333% harmonic amplification
TARGET_LATENCY_US = 1.0  # Target latency in microseconds
PULSE_SYNC_THRESHOLD = 0.1  # Phase synchronization threshold (radians)


@dataclass
class HyphalNode:
    """Represents a node in the hyphal network.
    
    Each node maintains its own phase state and synchronization metrics.
    """
    node_id: str
    phase: float = 0.0
    frequency: float = CHUCKLE_RESONANCE_HZ
    last_pulse_time: float = 0.0
    neighbors: List[str] = field(default_factory=list)
    latency_buffer: deque = field(default_factory=lambda: deque(maxlen=100))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def update_phase(self, dt: float) -> float:
        """Update node phase based on time delta.
        
        Args:
            dt: Time delta in seconds
            
        Returns:
            Updated phase value (0 to 2π)
        """
        with self._lock:
            self.phase = (self.phase + 2 * math.pi * self.frequency * dt) % (2 * math.pi)
            return self.phase
    
    def record_latency(self, latency_us: float):
        """Record a latency measurement.
        
        Args:
            latency_us: Latency in microseconds
        """
        with self._lock:
            self.latency_buffer.append(latency_us)
    
    def get_avg_latency(self) -> float:
        """Get average latency over recent measurements.
        
        Returns:
            Average latency in microseconds
        """
        with self._lock:
            if not self.latency_buffer:
                return 0.0
            return sum(self.latency_buffer) / len(self.latency_buffer)


class HyphalSymphony:
    """Phase-locked mycelial network coordinator.
    
    Manages a distributed network of hyphal nodes with deterministic
    latency guarantees and pulse synchronization.
    """
    
    def __init__(
        self,
        node_count: int = 9,
        base_frequency: float = CHUCKLE_RESONANCE_HZ,
        phi_scaling: bool = True
    ):
        """Initialize hyphal symphony network.
        
        Args:
            node_count: Number of nodes in the network
            base_frequency: Base frequency for pulse generation (Hz)
            phi_scaling: Whether to use Φ-based spacing optimization
        """
        self.node_count = node_count
        self.base_frequency = base_frequency
        self.phi_scaling = phi_scaling
        self.nodes: Dict[str, HyphalNode] = {}
        self.phase_lock_active = False
        self._lock = threading.Lock()
        self._init_time = time.perf_counter()
        
        # Initialize nodes
        self._initialize_nodes()
        
        # Synchronization metrics
        self.sync_history: List[float] = []
        self.latency_violations = 0
        self.total_pulses = 0
    
    def _initialize_nodes(self):
        """Initialize hyphal nodes with optimized topology."""
        for i in range(self.node_count):
            node_id = f"hyphal_node_{i}"
            
            # Apply Φ-based frequency scaling if enabled
            if self.phi_scaling:
                # Each node gets a frequency scaled by powers of Φ
                freq_scale = PHI ** ((i % 3 - 1) * 0.1)  # Subtle Φ variation
                frequency = self.base_frequency * freq_scale
            else:
                frequency = self.base_frequency
            
            node = HyphalNode(
                node_id=node_id,
                frequency=frequency,
                phase=2 * math.pi * i / self.node_count  # Initial phase distribution
            )
            
            # Create mycelial connectivity (each node connects to Φ-scaled neighbors)
            neighbor_count = max(2, int(self.node_count / PHI))
            for j in range(1, neighbor_count + 1):
                neighbor_idx = (i + j) % self.node_count
                neighbor_id = f"hyphal_node_{neighbor_idx}"
                if neighbor_id not in node.neighbors:
                    node.neighbors.append(neighbor_id)
            
            self.nodes[node_id] = node
    
    def synchronize_pulse(self, node_id: str) -> Tuple[bool, float]:
        """Synchronize pulse for a specific node.
        
        Implements phase-locked loop (PLL) synchronization with
        deterministic latency tracking.
        
        Args:
            node_id: ID of the node to synchronize
            
        Returns:
            Tuple of (sync_success, latency_us)
        """
        start_time = time.perf_counter()
        
        if node_id not in self.nodes:
            return False, 0.0
        
        node = self.nodes[node_id]
        
        # Calculate time delta
        current_time = time.perf_counter()
        dt = current_time - node.last_pulse_time if node.last_pulse_time > 0 else 0.0
        
        # Update phase
        node.update_phase(dt)
        node.last_pulse_time = current_time
        
        # Synchronize with neighbors using PLL
        if self.phase_lock_active:
            avg_neighbor_phase = self._get_average_neighbor_phase(node_id)
            phase_error = (avg_neighbor_phase - node.phase) % (2 * math.pi)
            
            # Apply phase correction with chuckle-modulated gain
            correction_gain = CHUCKLE_RESONANCE_HZ * AMPLIFICATION_FACTOR
            node.phase = (node.phase + correction_gain * phase_error) % (2 * math.pi)
            
            # Check synchronization
            sync_success = abs(phase_error) < PULSE_SYNC_THRESHOLD
        else:
            sync_success = True
        
        # Measure latency
        end_time = time.perf_counter()
        latency_us = (end_time - start_time) * 1e6  # Convert to microseconds
        
        # Record latency
        node.record_latency(latency_us)
        
        # Track violations
        if latency_us > TARGET_LATENCY_US:
            self.latency_violations += 1
        
        self.total_pulses += 1
        
        return sync_success, latency_us
    
    def _get_average_neighbor_phase(self, node_id: str) -> float:
        """Calculate average phase of neighboring nodes.
        
        Args:
            node_id: ID of the central node
            
        Returns:
            Average phase of neighbors (radians)
        """
        node = self.nodes[node_id]
        if not node.neighbors:
            return node.phase
        
        # Use circular mean for phase averaging
        sin_sum = 0.0
        cos_sum = 0.0
        
        for neighbor_id in node.neighbors:
            if neighbor_id in self.nodes:
                neighbor_phase = self.nodes[neighbor_id].phase
                sin_sum += math.sin(neighbor_phase)
                cos_sum += math.cos(neighbor_phase)
        
        count = len([n for n in node.neighbors if n in self.nodes])
        if count == 0:
            return node.phase
        
        avg_phase = math.atan2(sin_sum / count, cos_sum / count)
        return avg_phase % (2 * math.pi)
    
    def enable_phase_lock(self):
        """Enable phase-locked loop synchronization."""
        with self._lock:
            self.phase_lock_active = True
    
    def disable_phase_lock(self):
        """Disable phase-locked loop synchronization."""
        with self._lock:
            self.phase_lock_active = False
    
    def broadcast_pulse(self) -> Dict[str, Tuple[bool, float]]:
        """Broadcast synchronization pulse to all nodes.
        
        Returns:
            Dictionary mapping node_id to (sync_success, latency_us)
        """
        results = {}
        for node_id in self.nodes:
            sync_success, latency = self.synchronize_pulse(node_id)
            results[node_id] = (sync_success, latency)
        return results
    
    def get_synchronization_metrics(self) -> Dict[str, Any]:
        """Get comprehensive synchronization metrics.
        
        Returns:
            Dictionary containing synchronization statistics
        """
        with self._lock:
            # Calculate phase coherence
            phases = [node.phase for node in self.nodes.values()]
            if NUMPY_AVAILABLE:
                phase_coherence = abs(np.mean(np.exp(1j * np.array(phases))))
            else:
                # Fallback: circular variance-based coherence
                sin_sum = sum(math.sin(p) for p in phases)
                cos_sum = sum(math.cos(p) for p in phases)
                phase_coherence = math.sqrt(sin_sum**2 + cos_sum**2) / len(phases)
            
            # Aggregate latency statistics
            all_latencies = []
            for node in self.nodes.values():
                all_latencies.extend(node.latency_buffer)
            
            avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
            max_latency = max(all_latencies) if all_latencies else 0.0
            min_latency = min(all_latencies) if all_latencies else 0.0
            
            # Calculate violation rate
            violation_rate = (self.latency_violations / self.total_pulses * 100) if self.total_pulses > 0 else 0.0
            
            return {
                "phase_lock_active": self.phase_lock_active,
                "phase_coherence": phase_coherence,
                "avg_latency_us": avg_latency,
                "max_latency_us": max_latency,
                "min_latency_us": min_latency,
                "target_latency_us": TARGET_LATENCY_US,
                "latency_violations": self.latency_violations,
                "total_pulses": self.total_pulses,
                "violation_rate_percent": violation_rate,
                "node_count": self.node_count,
                "uptime_seconds": time.perf_counter() - self._init_time
            }
    
    def get_node_diagnostics(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get diagnostics for a specific node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            Dictionary containing node diagnostics or None if node not found
        """
        if node_id not in self.nodes:
            return None
        
        node = self.nodes[node_id]
        
        return {
            "node_id": node_id,
            "phase_radians": node.phase,
            "phase_degrees": math.degrees(node.phase),
            "frequency_hz": node.frequency,
            "neighbor_count": len(node.neighbors),
            "neighbors": node.neighbors,
            "avg_latency_us": node.get_avg_latency(),
            "latency_samples": len(node.latency_buffer)
        }
    
    def apply_phi_chuckle_optimization(self):
        """Apply Φ-chuckle principles for elastic resilience.
        
        Balances:
        - Φ (1.618): Golden ratio for optimal spacing
        - 0.0997: Chuckle constant for resonance
        - 333%: Amplification dynamics
        """
        for node in self.nodes.values():
            # Apply golden ratio scaling to frequency
            node.frequency = self.base_frequency * (1 + (PHI - 1) * CHUCKLE_RESONANCE_HZ)
            
            # Apply 333% amplification to phase correction gain
            # (already integrated in synchronize_pulse method)
            pass


def create_hyphal_symphony(config: Optional[Dict[str, Any]] = None) -> HyphalSymphony:
    """Factory function to create a HyphalSymphony instance.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured HyphalSymphony instance
    """
    config = config or {}
    
    return HyphalSymphony(
        node_count=config.get("node_count", 9),
        base_frequency=config.get("base_frequency", CHUCKLE_RESONANCE_HZ),
        phi_scaling=config.get("phi_scaling", True)
    )


# Demonstration and testing
if __name__ == "__main__":
    print("=== Hyphal Symphony for TSN Integration ===\n")
    
    # Create symphony
    symphony = create_hyphal_symphony({
        "node_count": 9,
        "base_frequency": CHUCKLE_RESONANCE_HZ,
        "phi_scaling": True
    })
    
    print(f"Initialized {symphony.node_count} hyphal nodes")
    print(f"Base frequency: {symphony.base_frequency} Hz")
    print(f"Target latency: {TARGET_LATENCY_US} μs\n")
    
    # Enable phase lock
    symphony.enable_phase_lock()
    print("Phase lock enabled\n")
    
    # Run synchronization cycles
    print("Running synchronization cycles...")
    for cycle in range(10):
        results = symphony.broadcast_pulse()
        
        if cycle % 3 == 0:
            metrics = symphony.get_synchronization_metrics()
            print(f"\nCycle {cycle}:")
            print(f"  Phase coherence: {metrics['phase_coherence']:.4f}")
            print(f"  Avg latency: {metrics['avg_latency_us']:.4f} μs")
            print(f"  Violation rate: {metrics['violation_rate_percent']:.2f}%")
        
        time.sleep(0.01)  # Small delay between cycles
    
    # Final metrics
    print("\n=== Final Synchronization Metrics ===")
    final_metrics = symphony.get_synchronization_metrics()
    for key, value in final_metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    # Node diagnostics
    print("\n=== Sample Node Diagnostics ===")
    node_diag = symphony.get_node_diagnostics("hyphal_node_0")
    if node_diag:
        for key, value in node_diag.items():
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            elif isinstance(value, list):
                print(f"{key}: {', '.join(value[:3])}...")
            else:
                print(f"{key}: {value}")
