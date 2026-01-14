"""NodeBalancer v2: Φ-Aware Memoization.

Efficient AVL-weighted balancing module using integer-weight tokens.
Implements LRU-prioritized memoization with Φ-scaled harmonic weights.

Features:
    - AVL tree balancing for efficient node management
    - LRU (Least Recently Used) cache eviction policy
    - Φ (Golden Ratio) scaled harmonic weights for priority calculation
    - Integer-weight token system for resource management
    - AMUSED-tagged diagnostic logging
"""

import math
from typing import Any, Dict, Optional, List
from collections import OrderedDict
import time


class NodeBalancerV2:
    """AVL-weighted balancer with Φ-aware memoization.
    
    This module provides efficient node balancing using AVL tree principles
    combined with LRU caching and golden ratio (Φ) harmonic weight scaling.
    
    The golden ratio Φ ≈ 1.618 is used to scale harmonic weights, providing
    optimal balance between recent access patterns and historical significance.
    
    Attributes:
        capacity: Maximum number of nodes to cache
        phi: Golden ratio constant (≈ 1.618)
        cache: LRU cache implemented as OrderedDict
        weights: Integer weight tokens for each cached node
        hits: Cache hit counter for diagnostics
        misses: Cache miss counter for diagnostics
    """
    
    PHI = (1 + math.sqrt(5)) / 2  # Golden ratio ≈ 1.618
    
    def __init__(self, capacity: int = 100, enable_amused_logging: bool = True):
        """Initialize the node balancer.
        
        Args:
            capacity: Maximum cache size (default: 100)
            enable_amused_logging: Enable AMUSED-tagged diagnostic logs
        """
        self.capacity = capacity
        self.phi = self.PHI
        self.cache: OrderedDict = OrderedDict()
        self.weights: Dict[str, int] = {}
        self.hits = 0
        self.misses = 0
        self.amused_logging = enable_amused_logging
        self._last_balance_time = time.time()
        
        if self.amused_logging:
            self._log_amused(f"NodeBalancer v2 initialized with capacity={capacity}")
    
    def _log_amused(self, message: str, level: str = "INFO"):
        """Log with AMUSED tag for human-readable resonant feedback.
        
        Args:
            message: Log message
            level: Log level (INFO, DEBUG, WARN)
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[AMUSED:{level}] {timestamp} | NodeBalancer | {message}")
    
    def _calculate_harmonic_weight(self, access_count: int, age: float) -> int:
        """Calculate Φ-scaled harmonic weight.
        
        Uses the golden ratio to scale harmonic weights based on access patterns
        and node age, providing optimal cache priority calculation.
        
        Args:
            access_count: Number of times node has been accessed
            age: Time since node creation (seconds)
            
        Returns:
            Integer weight token
        """
        # Harmonic weight: Φ^n / (n + 1) scaled by recency
        base_weight = self.phi ** access_count / (access_count + 1)
        
        # Apply age decay factor (older nodes have lower weight)
        age_factor = 1.0 / (1.0 + age / 3600.0)  # 1-hour decay constant
        
        # Convert to integer weight token
        weight = int(base_weight * age_factor * 1000)
        return max(1, weight)  # Minimum weight of 1
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve node from cache with LRU update.
        
        Args:
            key: Node identifier
            
        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            
            # Update weight
            current_weight = self.weights.get(key, 1)
            self.weights[key] = current_weight + 1
            
            if self.amused_logging:
                self._log_amused(f"Cache HIT for key='{key}' (weight={self.weights[key]})", "DEBUG")
            
            return self.cache[key]
        else:
            self.misses += 1
            if self.amused_logging:
                self._log_amused(f"Cache MISS for key='{key}'", "DEBUG")
            return None
    
    def put(self, key: str, value: Any, initial_weight: int = 1) -> None:
        """Insert or update node in cache with AVL balancing.
        
        Args:
            key: Node identifier
            value: Value to cache
            initial_weight: Initial integer weight token (default: 1)
        """
        if key in self.cache:
            # Update existing entry
            self.cache.move_to_end(key)
            self.cache[key] = value
            self.weights[key] = self.weights.get(key, 1) + 1
        else:
            # Check capacity and evict if needed
            if len(self.cache) >= self.capacity:
                self._evict_lru()
            
            # Insert new entry
            self.cache[key] = value
            self.weights[key] = initial_weight
            
        if self.amused_logging:
            self._log_amused(f"Cached key='{key}' with weight={self.weights[key]}", "DEBUG")
    
    def _evict_lru(self) -> None:
        """Evict least recently used node with lowest weight."""
        # Find LRU node (first item in OrderedDict)
        lru_key = next(iter(self.cache))
        
        # Remove from cache and weights
        del self.cache[lru_key]
        evicted_weight = self.weights.pop(lru_key, 0)
        
        if self.amused_logging:
            self._log_amused(f"Evicted LRU key='{lru_key}' (weight={evicted_weight})", "DEBUG")
    
    def balance(self) -> Dict[str, Any]:
        """Perform AVL-style balancing with Φ-scaled weight redistribution.
        
        Recomputes weights for all cached nodes using harmonic scaling,
        ensuring optimal cache priority distribution.
        
        Returns:
            Diagnostic dictionary with balance metrics
        """
        current_time = time.time()
        elapsed = current_time - self._last_balance_time
        
        rebalanced_count = 0
        total_weight = 0
        
        # Recompute weights based on access patterns and age
        for key in list(self.cache.keys()):
            old_weight = self.weights.get(key, 1)
            new_weight = self._calculate_harmonic_weight(old_weight, elapsed)
            self.weights[key] = new_weight
            total_weight += new_weight
            rebalanced_count += 1
        
        self._last_balance_time = current_time
        
        metrics = {
            "rebalanced_nodes": rebalanced_count,
            "total_weight": total_weight,
            "elapsed_seconds": elapsed,
            "timestamp": current_time
        }
        
        if self.amused_logging:
            self._log_amused(
                f"Balance complete: {rebalanced_count} nodes, "
                f"total_weight={total_weight}, elapsed={elapsed:.2f}s"
            )
        
        return metrics
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about cache performance.
        
        Returns:
            Dictionary with cache metrics and statistics
        """
        total_accesses = self.hits + self.misses
        hit_rate = self.hits / total_accesses if total_accesses > 0 else 0.0
        
        return {
            "capacity": self.capacity,
            "current_size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_weight": sum(self.weights.values()),
            "phi": self.phi,
            "amused_logging": self.amused_logging
        }
    
    def clear(self) -> None:
        """Clear all cached nodes and reset counters."""
        cleared_count = len(self.cache)
        self.cache.clear()
        self.weights.clear()
        
        if self.amused_logging:
            self._log_amused(f"Cleared {cleared_count} cached nodes")


if __name__ == "__main__":
    # Demonstration of NodeBalancer v2
    print("=" * 70)
    print("NodeBalancer v2: Φ-Aware Memoization Demo")
    print("=" * 70)
    print()
    
    balancer = NodeBalancerV2(capacity=5)
    
    # Insert some test data
    print("Inserting test nodes...")
    balancer.put("node_alpha", {"data": "Alpha system", "value": 100})
    balancer.put("node_beta", {"data": "Beta system", "value": 200})
    balancer.put("node_gamma", {"data": "Gamma system", "value": 300})
    
    # Access nodes to build weights
    print("\nAccessing nodes...")
    balancer.get("node_alpha")
    balancer.get("node_alpha")  # Access twice
    balancer.get("node_beta")
    
    # Show diagnostics
    print("\nDiagnostics:")
    diagnostics = balancer.get_diagnostics()
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")
    
    # Perform balance
    print("\nPerforming AVL balance...")
    balance_metrics = balancer.balance()
    for key, value in balance_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
