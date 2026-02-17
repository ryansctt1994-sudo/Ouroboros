#!/usr/bin/env python3
"""
Performance Module Tests
========================

Unit tests for performance profiling and caching.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import sys
import time
import unittest
from pathlib import Path
from threading import Thread

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from performance import (
    profile,
    get_profiler,
    PerformanceProfiler,
    LRUCache
)


class TestPerformanceProfiler(unittest.TestCase):
    """Test PerformanceProfiler class."""
    
    def setUp(self):
        """Reset profiler before each test."""
        profiler = get_profiler()
        profiler.reset()
    
    def test_singleton(self):
        """Test that profiler is a singleton."""
        profiler1 = PerformanceProfiler()
        profiler2 = PerformanceProfiler()
        self.assertIs(profiler1, profiler2)
    
    def test_record_stats(self):
        """Test recording execution statistics."""
        profiler = get_profiler()
        
        # Record some executions
        profiler.record("test_func", 0.1)
        profiler.record("test_func", 0.2)
        profiler.record("test_func", 0.15)
        
        stats = profiler.get_stats("test_func")
        
        self.assertEqual(stats['calls'], 3)
        self.assertEqual(stats['min_time'], 0.1)
        self.assertEqual(stats['max_time'], 0.2)
        self.assertAlmostEqual(stats['avg_time'], 0.15, places=2)
        self.assertAlmostEqual(stats['total_time'], 0.45, places=2)
    
    def test_get_all_stats(self):
        """Test getting all statistics."""
        profiler = get_profiler()
        
        profiler.record("func1", 0.1)
        profiler.record("func2", 0.2)
        
        all_stats = profiler.get_stats()
        
        self.assertIn("func1", all_stats)
        self.assertIn("func2", all_stats)
        self.assertEqual(len(all_stats), 2)
    
    def test_reset(self):
        """Test reset functionality."""
        profiler = get_profiler()
        
        profiler.record("test_func", 0.1)
        self.assertEqual(len(profiler.get_stats()), 1)
        
        profiler.reset()
        self.assertEqual(len(profiler.get_stats()), 0)
    
    def test_report_generation(self):
        """Test report generation."""
        profiler = get_profiler()
        
        profiler.record("test_func", 0.1)
        profiler.record("test_func", 0.2)
        
        report = profiler.report()
        
        self.assertIn("Performance Profiling Report", report)
        self.assertIn("test_func", report)
        self.assertIn("Calls", report)
        self.assertIn("Avg(ms)", report)
    
    def test_thread_safety(self):
        """Test thread-safe recording."""
        profiler = get_profiler()
        
        def record_metrics():
            for i in range(100):
                profiler.record("test_func", 0.001)
        
        threads = [Thread(target=record_metrics) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        stats = profiler.get_stats("test_func")
        self.assertEqual(stats['calls'], 1000)


class TestProfileDecorator(unittest.TestCase):
    """Test profile decorator."""
    
    def setUp(self):
        """Reset profiler before each test."""
        profiler = get_profiler()
        profiler.reset()
    
    def test_basic_profiling(self):
        """Test basic function profiling."""
        @profile
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        
        self.assertEqual(result, "result")
        
        profiler = get_profiler()
        stats = profiler.get_stats()
        
        # Should have one function profiled
        self.assertEqual(len(stats), 1)
        
        # Check that execution time was recorded
        func_name = list(stats.keys())[0]
        self.assertIn("test_function", func_name)
        self.assertEqual(stats[func_name]['calls'], 1)
        self.assertGreater(stats[func_name]['total_time'], 0.01)
    
    def test_custom_name(self):
        """Test profiling with custom name."""
        @profile(name="custom_name")
        def test_function():
            pass
        
        test_function()
        
        profiler = get_profiler()
        stats = profiler.get_stats("custom_name")
        
        self.assertEqual(stats['calls'], 1)
    
    def test_multiple_calls(self):
        """Test profiling multiple calls."""
        @profile
        def test_function():
            time.sleep(0.001)
        
        for _ in range(5):
            test_function()
        
        profiler = get_profiler()
        stats = profiler.get_stats()
        
        func_name = list(stats.keys())[0]
        self.assertEqual(stats[func_name]['calls'], 5)
    
    def test_decorator_with_args(self):
        """Test decorator with arguments."""
        @profile(name="test", log_threshold_ms=10)
        def test_function(x, y):
            return x + y
        
        result = test_function(1, 2)
        
        self.assertEqual(result, 3)
        
        profiler = get_profiler()
        stats = profiler.get_stats("test")
        
        self.assertEqual(stats['calls'], 1)


class TestLRUCache(unittest.TestCase):
    """Test LRUCache class."""
    
    def test_basic_get_put(self):
        """Test basic cache operations."""
        cache = LRUCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertIsNone(cache.get("key3"))
    
    def test_eviction(self):
        """Test LRU eviction."""
        cache = LRUCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # key1 should be evicted when we add key4
        cache.put("key4", "value4")
        
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_lru_order(self):
        """Test LRU ordering."""
        cache = LRUCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1, making it most recently used
        cache.get("key1")
        
        # Add key4, should evict key2 (least recently used)
        cache.put("key4", "value4")
        
        self.assertEqual(cache.get("key1"), "value1")
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache.get("key3"), "value3")
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_update_existing(self):
        """Test updating existing key."""
        cache = LRUCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key1", "updated_value1")
        
        self.assertEqual(cache.get("key1"), "updated_value1")
        
        stats = cache.get_stats()
        self.assertEqual(stats['size'], 1)
    
    def test_clear(self):
        """Test cache clearing."""
        cache = LRUCache(max_size=3)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        self.assertEqual(cache.get_stats()['size'], 2)
        
        cache.clear()
        
        self.assertEqual(cache.get_stats()['size'], 0)
        self.assertIsNone(cache.get("key1"))
    
    def test_statistics(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=10)
        
        # Initial stats
        stats = cache.get_stats()
        self.assertEqual(stats['size'], 0)
        self.assertEqual(stats['hits'], 0)
        self.assertEqual(stats['misses'], 0)
        self.assertEqual(stats['hit_rate'], 0)
        
        # Add some entries
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        
        # Mix of hits and misses
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key3")  # miss
        
        stats = cache.get_stats()
        self.assertEqual(stats['size'], 2)
        self.assertEqual(stats['hits'], 2)
        self.assertEqual(stats['misses'], 1)
        self.assertAlmostEqual(stats['hit_rate'], 66.67, places=1)
    
    def test_thread_safety(self):
        """Test thread-safe cache operations."""
        cache = LRUCache(max_size=100)
        
        def cache_operations():
            for i in range(100):
                cache.put(f"key_{i % 50}", f"value_{i}")
                cache.get(f"key_{i % 50}")
        
        threads = [Thread(target=cache_operations) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should complete without errors
        stats = cache.get_stats()
        self.assertGreater(stats['total_requests'], 0)


if __name__ == "__main__":
    unittest.main()
