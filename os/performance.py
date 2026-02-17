#!/usr/bin/env python3
"""
Performance Profiling Module
============================

Provides decorators and utilities for performance profiling and optimization.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import functools
import logging
import time
from typing import Callable, Any, Dict, Optional
from collections import defaultdict
from threading import Lock

logger = logging.getLogger("eden_performance")


class PerformanceProfiler:
    """
    Performance profiler for tracking execution times and bottlenecks.
    Thread-safe singleton implementation.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._stats = defaultdict(lambda: {
            'calls': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'avg_time': 0.0
        })
        self._lock = Lock()
        self._initialized = True
    
    def record(self, func_name: str, execution_time: float):
        """Record execution time for a function."""
        with self._lock:
            stats = self._stats[func_name]
            stats['calls'] += 1
            stats['total_time'] += execution_time
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['avg_time'] = stats['total_time'] / stats['calls']
    
    def get_stats(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """Get profiling statistics."""
        with self._lock:
            if func_name:
                return dict(self._stats.get(func_name, {}))
            return {k: dict(v) for k, v in self._stats.items()}
    
    def reset(self):
        """Reset all statistics."""
        with self._lock:
            self._stats.clear()
    
    def report(self) -> str:
        """Generate a formatted report of profiling statistics."""
        with self._lock:
            if not self._stats:
                return "No profiling data available."
            
            lines = ["Performance Profiling Report", "=" * 80]
            lines.append(f"{'Function':<40} {'Calls':>8} {'Avg(ms)':>10} {'Min(ms)':>10} {'Max(ms)':>10} {'Total(s)':>10}")
            lines.append("-" * 80)
            
            # Sort by total time (descending)
            sorted_stats = sorted(
                self._stats.items(),
                key=lambda x: x[1]['total_time'],
                reverse=True
            )
            
            for func_name, stats in sorted_stats:
                lines.append(
                    f"{func_name:<40} {stats['calls']:>8} "
                    f"{stats['avg_time']*1000:>10.2f} "
                    f"{stats['min_time']*1000:>10.2f} "
                    f"{stats['max_time']*1000:>10.2f} "
                    f"{stats['total_time']:>10.3f}"
                )
            
            lines.append("=" * 80)
            return "\n".join(lines)


# Global profiler instance
_profiler = PerformanceProfiler()


def profile(func: Callable = None, *, name: Optional[str] = None, log_threshold_ms: float = 100.0):
    """
    Decorator for profiling function execution time.
    
    Args:
        func: Function to profile (auto-filled when used as @profile)
        name: Custom name for the function (defaults to func.__name__)
        log_threshold_ms: Log warning if execution exceeds this threshold (ms)
    
    Example:
        @profile
        def slow_function():
            time.sleep(1)
        
        @profile(name="custom_name", log_threshold_ms=50)
        def another_function():
            pass
    """
    def decorator(f: Callable) -> Callable:
        func_name = name or f"{f.__module__}.{f.__qualname__}"
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = f(*args, **kwargs)
                return result
            finally:
                execution_time = time.perf_counter() - start_time
                _profiler.record(func_name, execution_time)
                
                # Log if execution time exceeds threshold
                execution_time_ms = execution_time * 1000
                if execution_time_ms > log_threshold_ms:
                    logger.warning(
                        f"{func_name} took {execution_time_ms:.2f}ms "
                        f"(threshold: {log_threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func_name} took {execution_time_ms:.2f}ms")
        
        return wrapper
    
    # Handle both @profile and @profile() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _profiler


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.
    Thread-safe and optimized for AI inference caching.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._cache = {}
        self._access_order = []
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._access_order.remove(key)
                self._access_order.append(key)
                self._hits += 1
                return self._cache[key]
            else:
                self._misses += 1
                return None
    
    def put(self, key: str, value: Any):
        """Put value in cache."""
        with self._lock:
            if key in self._cache:
                # Update existing
                self._access_order.remove(key)
            elif len(self._cache) >= self.max_size:
                # Evict least recently used
                lru_key = self._access_order.pop(0)
                del self._cache[lru_key]
            
            self._cache[key] = value
            self._access_order.append(key)
    
    def clear(self):
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total
            }
