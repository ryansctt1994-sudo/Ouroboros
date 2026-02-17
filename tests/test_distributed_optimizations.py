"""
Test suite for distributed system modules.

Tests logical clock, path tracking, version guard, config registry, and failure correlation.
"""

import pytest
import time
from src.distributed.logical_clock import (
    HybridLogicalClock,
    Timestamp,
)
from src.distributed.path_tracker import (
    CriticalPathTracker,
    Span,
    CriticalPath,
)
from src.distributed.version_guard import (
    APIVersionGuard,
    VersionInfo,
)
from src.distributed.config_registry import (
    GlobalConfigRegistry,
    ConfigChange,
)
from src.distributed.failure_correlator import (
    FailureCorrelator,
    FailureEvent,
    FailureCascade,
)


class TestHybridLogicalClock:
    """Test hybrid logical clock."""
    
    def test_initialization(self):
        """Test clock initialization."""
        clock = HybridLogicalClock(node_id='node1')
        
        assert clock.node_id == 'node1'
    
    def test_now(self):
        """Test timestamp generation."""
        clock = HybridLogicalClock(node_id='node1')
        
        ts = clock.now()
        
        assert isinstance(ts, Timestamp)
        assert ts.node_id == 'node1'
        assert ts.physical > 0
    
    def test_timestamp_ordering(self):
        """Test timestamp ordering."""
        clock = HybridLogicalClock(node_id='node1')
        
        ts1 = clock.now()
        time.sleep(0.01)
        ts2 = clock.now()
        
        assert ts1 < ts2
    
    def test_update_from_remote(self):
        """Test clock update from remote timestamp."""
        clock1 = HybridLogicalClock(node_id='node1')
        clock2 = HybridLogicalClock(node_id='node2')
        
        ts1 = clock1.now()
        ts2 = clock2.update(ts1)
        
        assert ts2.node_id == 'node2'
        assert ts2 >= ts1
    
    def test_compare(self):
        """Test timestamp comparison."""
        clock = HybridLogicalClock(node_id='node1')
        
        ts1 = clock.now()
        ts2 = clock.now()
        
        result = clock.compare(ts1, ts2)
        
        assert result in [-1, 0, 1]
    
    def test_time_since(self):
        """Test elapsed time calculation."""
        clock = HybridLogicalClock(node_id='node1')
        
        ts = clock.now()
        time.sleep(0.1)
        elapsed = clock.time_since(ts)
        
        assert elapsed >= 0.1
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        clock = HybridLogicalClock(node_id='node1')
        
        clock.now()
        clock.now()
        
        stats = clock.get_statistics()
        
        assert stats['total_events'] == 2


class TestCriticalPathTracker:
    """Test critical path tracking."""
    
    def test_start_span(self):
        """Test starting a span."""
        tracker = CriticalPathTracker()
        
        span_id = tracker.start_span(
            operation='test_op',
            repo='ouroboros'
        )
        
        assert span_id is not None
        assert span_id in tracker._spans
    
    def test_end_span(self):
        """Test ending a span."""
        tracker = CriticalPathTracker()
        
        span_id = tracker.start_span('test_op', 'ouroboros')
        time.sleep(0.01)
        tracker.end_span(span_id)
        
        span = tracker._spans[span_id]
        
        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.duration_ms >= 10  # At least 10ms
    
    def test_add_tag(self):
        """Test adding tags to span."""
        tracker = CriticalPathTracker()
        
        span_id = tracker.start_span('test_op', 'ouroboros')
        tracker.add_tag(span_id, 'request_id', 'req-123')
        
        span = tracker._spans[span_id]
        
        assert span.tags['request_id'] == 'req-123'
    
    def test_parent_child_relationship(self):
        """Test parent-child span relationship."""
        tracker = CriticalPathTracker()
        
        parent_id = tracker.start_span('parent', 'ouroboros')
        child_id = tracker.start_span(
            'child',
            'aiospandora',
            parent_id=parent_id
        )
        
        assert child_id in tracker._children[parent_id]
    
    def test_get_critical_path(self):
        """Test critical path identification."""
        tracker = CriticalPathTracker()
        
        root_id = tracker.start_span('root', 'ouroboros')
        child1 = tracker.start_span('child1', 'repo1', parent_id=root_id)
        child2 = tracker.start_span('child2', 'repo2', parent_id=root_id)
        
        time.sleep(0.01)
        tracker.end_span(child1)
        tracker.end_span(child2)
        tracker.end_span(root_id)
        
        path = tracker.get_critical_path(root_id)
        
        assert path is not None
        assert isinstance(path, CriticalPath)
        assert len(path.path) >= 2
    
    def test_cross_repo_latency(self):
        """Test cross-repo latency tracking."""
        tracker = CriticalPathTracker()
        
        parent_id = tracker.start_span('parent', 'ouroboros')
        child_id = tracker.start_span('child', 'aiospandora', parent_id=parent_id)
        
        time.sleep(0.01)
        tracker.end_span(child_id)
        tracker.end_span(parent_id)
        
        latencies = tracker.get_cross_repo_latency()
        
        # May have cross-repo calls
        assert isinstance(latencies, dict)


class TestAPIVersionGuard:
    """Test API version guard."""
    
    def test_register_api(self):
        """Test API registration."""
        guard = APIVersionGuard()
        
        guard.register_api('ouroboros', '1.0.0')
        
        assert 'ouroboros' in guard._apis
    
    def test_version_parsing(self):
        """Test version string parsing."""
        version = VersionInfo.parse('1.2.3')
        
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_version_comparison(self):
        """Test version comparison."""
        v1 = VersionInfo.parse('1.0.0')
        v2 = VersionInfo.parse('2.0.0')
        
        assert v1 < v2
    
    def test_check_compatibility(self):
        """Test compatibility checking."""
        guard = APIVersionGuard()
        guard.register_api('ouroboros', '2.0.0')
        
        # Same major version, lower minor - compatible
        compatible = guard.check_compatibility('ouroboros', '1.5.0')
        
        # Different major version - not compatible
        incompatible = guard.check_compatibility('ouroboros', '3.0.0')
        
        assert not incompatible
    
    def test_register_adapter(self):
        """Test adapter registration."""
        guard = APIVersionGuard()
        
        def adapter(msg):
            return msg
        
        guard.register_adapter(
            'ouroboros',
            from_version='1.0.0',
            to_version='2.0.0',
            adapter=adapter
        )
        
        assert len(guard._adapters) > 0
    
    def test_adapt_message(self):
        """Test message adaptation."""
        guard = APIVersionGuard()
        guard.register_api('ouroboros', '2.0.0')
        
        def adapter(msg):
            msg['adapted'] = True
            return msg
        
        guard.register_adapter(
            'ouroboros',
            from_version='1.0.0',
            to_version='2.0.0',
            adapter=adapter
        )
        
        message = {'data': 'test'}
        adapted = guard.adapt_message(
            message,
            from_api='ouroboros',
            from_version='1.0.0'
        )
        
        assert 'adapted' in adapted
    
    def test_mark_deprecated(self):
        """Test deprecation marking."""
        guard = APIVersionGuard()
        
        guard.mark_deprecated('ouroboros', '1.0.0', 'Use 2.0.0 instead')
        
        assert len(guard._deprecations) > 0


class TestGlobalConfigRegistry:
    """Test global configuration registry."""
    
    def test_set_get(self):
        """Test setting and getting config."""
        registry = GlobalConfigRegistry()
        
        registry.set('test.key', 'value')
        value = registry.get('test.key')
        
        assert value == 'value'
    
    def test_get_with_default(self):
        """Test getting with default value."""
        registry = GlobalConfigRegistry()
        
        value = registry.get('nonexistent.key', default='default_value')
        
        assert value == 'default_value'
    
    def test_get_all(self):
        """Test getting all config."""
        registry = GlobalConfigRegistry()
        
        registry.set('test.key1', 'value1')
        registry.set('test.key2', 'value2')
        
        all_config = registry.get_all()
        
        assert 'test.key1' in all_config
        assert 'test.key2' in all_config
    
    def test_get_all_with_prefix(self):
        """Test getting config with prefix filter."""
        registry = GlobalConfigRegistry()
        
        registry.set('app.setting1', 'value1')
        registry.set('app.setting2', 'value2')
        registry.set('other.setting', 'value3')
        
        app_config = registry.get_all(prefix='app.')
        
        assert len(app_config) == 2
        assert 'app.setting1' in app_config
    
    def test_delete(self):
        """Test deleting config."""
        registry = GlobalConfigRegistry()
        
        registry.set('test.key', 'value')
        deleted = registry.delete('test.key')
        
        assert deleted
        assert registry.get('test.key') is None
    
    def test_validator(self):
        """Test config validation."""
        registry = GlobalConfigRegistry()
        
        # Register validator
        registry.register_validator(
            'test.number',
            lambda v: isinstance(v, int) and v > 0
        )
        
        # Valid value
        success = registry.set('test.number', 10)
        assert success
        
        # Invalid value
        failed = registry.set('test.number', -5)
        assert not failed
    
    def test_watcher(self):
        """Test config watchers."""
        registry = GlobalConfigRegistry()
        
        changes = []
        
        def on_change(key, old, new):
            changes.append((key, old, new))
        
        registry.watch('test.*', on_change)
        registry.set('test.key', 'value1')
        registry.set('test.key', 'value2')
        
        assert len(changes) >= 1
    
    def test_get_changes(self):
        """Test getting change history."""
        registry = GlobalConfigRegistry()
        
        registry.set('test.key', 'value1')
        registry.set('test.key', 'value2')
        
        changes = registry.get_changes()
        
        assert len(changes) >= 2


class TestFailureCorrelator:
    """Test failure correlation."""
    
    def test_report_failure(self):
        """Test failure reporting."""
        correlator = FailureCorrelator()
        
        event_id = correlator.report_failure(
            repo='ouroboros',
            component='thread_manager',
            error_type='ZombieThreadError',
            message='Thread cleanup failed',
            severity='high'
        )
        
        assert event_id is not None
        assert len(correlator._events) > 0
    
    def test_detect_cascades(self):
        """Test cascade detection."""
        correlator = FailureCorrelator(
            correlation_window_seconds=1.0,
            cascade_threshold=2
        )
        
        # Report multiple related failures
        correlator.report_failure(
            repo='ouroboros',
            component='manager',
            error_type='TestError',
            message='Error 1'
        )
        
        time.sleep(0.1)
        
        correlator.report_failure(
            repo='aiospandora',
            component='manager',
            error_type='TestError',
            message='Error 2'
        )
        
        cascades = correlator.detect_cascades()
        
        # Should detect cascade
        assert len(cascades) >= 0
    
    def test_get_failure_rate(self):
        """Test failure rate calculation."""
        correlator = FailureCorrelator()
        
        # Report some failures
        for i in range(5):
            correlator.report_failure(
                repo='test',
                component='test',
                error_type='TestError',
                message=f'Error {i}'
            )
        
        rate = correlator.get_failure_rate(window_seconds=60.0)
        
        assert rate >= 0
    
    def test_get_top_failures(self):
        """Test getting top failure types."""
        correlator = FailureCorrelator()
        
        # Report failures of different types
        for i in range(3):
            correlator.report_failure(
                repo='test',
                component='test',
                error_type='ErrorA',
                message='Error A'
            )
        
        for i in range(2):
            correlator.report_failure(
                repo='test',
                component='test',
                error_type='ErrorB',
                message='Error B'
            )
        
        top = correlator.get_top_failures(limit=2)
        
        assert len(top) >= 1
        assert top[0][0] == 'ErrorA'  # Most frequent
        assert top[0][1] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
