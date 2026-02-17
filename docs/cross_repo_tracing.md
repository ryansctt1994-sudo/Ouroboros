# Cross-Repo Distributed Tracing

## Overview

This guide covers distributed tracing and monitoring across Ouroboros, AIOSPANDORA, and EDEN-ECS repositories using the integrated tracing tools.

## Components

### 1. Hybrid Logical Clock

Provides causal ordering of events across distributed systems.

### 2. Critical Path Tracker

Tracks execution spans and identifies performance bottlenecks.

### 3. API Version Guard

Ensures compatibility across different API versions.

### 4. Global Config Registry

Centralized configuration management.

### 5. Failure Correlator

Detects and correlates failures across repositories.

## Hybrid Logical Clock

### Basic Usage

```python
from src.distributed import HybridLogicalClock

# Initialize clock for each node
ouroboros_clock = HybridLogicalClock(node_id='ouroboros-node-1')
aiospandora_clock = HybridLogicalClock(node_id='aiospandora-node-1')

# Generate timestamp for local event
ts = ouroboros_clock.now()

# Send with message to remote node
message = {
    'data': 'request',
    'timestamp': ts
}
send_to_remote(message)
```

### Receiving Remote Messages

```python
# On receiving message
def handle_message(message):
    remote_ts = message['timestamp']
    
    # Update local clock
    local_ts = aiospandora_clock.update(remote_ts)
    
    # Process message
    process(message['data'])
    
    # Return response with updated timestamp
    return {
        'data': 'response',
        'timestamp': local_ts
    }
```

### Causal Ordering

```python
# Compare events
ts1 = clock1.now()
time.sleep(0.1)
ts2 = clock2.now()

# Check ordering
if clock1.compare(ts1, ts2) < 0:
    print("Event 1 happened before event 2")

# Check if concurrent
if clock1.is_concurrent(ts1, ts2):
    print("Events are concurrent")
```

## Critical Path Tracking

### Span Creation

```python
from src.distributed import CriticalPathTracker

# Initialize tracker
tracker = CriticalPathTracker()

# Start root span
request_span = tracker.start_span(
    operation='process_request',
    repo='ouroboros',
    tags={'request_id': 'req-123', 'user_id': 'user-456'}
)

# Start child span in different repo
db_span = tracker.start_span(
    operation='database_query',
    repo='aiospandora',
    parent_id=request_span,
    tags={'query_type': 'SELECT'}
)

# End spans
tracker.end_span(db_span)
tracker.end_span(request_span)
```

### Critical Path Analysis

```python
# Analyze critical path
path = tracker.get_critical_path(request_span)

if path:
    print(f"Total latency: {path.total_latency_ms:.2f} ms")
    print(f"Repos involved: {path.repos_involved}")
    print(f"Bottleneck: {path.bottleneck_span.operation}")
    
    # Print full path
    for span in path.path:
        print(f"  {span.repo}/{span.operation}: {span.duration_ms:.2f} ms")
```

### Cross-Repo Latency Monitoring

```python
# Get cross-repo latencies
latencies = tracker.get_cross_repo_latency()

for (from_repo, to_repo), latency_list in latencies.items():
    avg_latency = sum(latency_list) / len(latency_list)
    print(f"{from_repo} -> {to_repo}: {avg_latency:.2f} ms avg")
```

## API Version Guard

### Version Management

```python
from src.distributed import APIVersionGuard

# Initialize guard
guard = APIVersionGuard()

# Register API versions
guard.register_api('ouroboros', '2.0.0')
guard.register_api('aiospandora', '1.5.0')

# Check compatibility
if guard.check_compatibility('ouroboros', '1.9.0'):
    print("Version 1.9.0 is compatible")
```

### Message Adaptation

```python
# Define adapter
def migrate_v1_to_v2(message):
    # V1 -> V2 migration logic
    if 'old_field' in message:
        message['new_field'] = message.pop('old_field')
    return message

# Register adapter
guard.register_adapter(
    api_name='ouroboros',
    from_version='1.0.0',
    to_version='2.0.0',
    adapter=migrate_v1_to_v2
)

# Adapt incoming message
incoming_message = {'old_field': 'value'}
adapted = guard.adapt_message(
    incoming_message,
    from_api='ouroboros',
    from_version='1.0.0'
)

assert 'new_field' in adapted
```

### Deprecation Handling

```python
# Mark version as deprecated
guard.mark_deprecated(
    'ouroboros',
    '1.0.0',
    'Please upgrade to v2.0.0. V1.0.0 will be removed in March 2026.'
)

# Automatically warns when old version is used
message = guard.adapt_message(
    {'data': 'test'},
    from_api='ouroboros',
    from_version='1.0.0'
)
```

## Global Config Registry

### Configuration Management

```python
from src.distributed import GlobalConfigRegistry

# Initialize registry
registry = GlobalConfigRegistry()

# Set configuration
registry.set('ouroboros.thread.max_workers', 10, source='config_file')
registry.set('aiospandora.batch_size', 32, source='env_var')

# Get configuration
max_workers = registry.get('ouroboros.thread.max_workers', default=5)
```

### Configuration Validation

```python
# Register validator
def validate_positive_int(value):
    return isinstance(value, int) and value > 0

registry.register_validator(
    'ouroboros.thread.max_workers',
    validate_positive_int
)

# This will succeed
registry.set('ouroboros.thread.max_workers', 10)

# This will fail
registry.set('ouroboros.thread.max_workers', -1)  # Returns False
```

### Configuration Watchers

```python
# Watch for changes
def on_worker_count_change(key, old_value, new_value):
    print(f"Worker count changed: {old_value} -> {new_value}")
    # Adjust thread pool
    adjust_thread_pool(new_value)

registry.watch('ouroboros.thread.*', on_worker_count_change)

# Changes trigger callback
registry.set('ouroboros.thread.max_workers', 20)
```

### Configuration History

```python
# Get change history
changes = registry.get_changes(
    since_timestamp=time.time() - 3600,  # Last hour
    key_prefix='ouroboros.'
)

for change in changes:
    print(f"{change.key}: {change.old_value} -> {change.new_value}")
    print(f"  Source: {change.source}")
    print(f"  Time: {change.timestamp}")
```

## Failure Correlator

### Failure Reporting

```python
from src.distributed import FailureCorrelator

# Initialize correlator
correlator = FailureCorrelator(
    correlation_window_seconds=60.0,
    cascade_threshold=3
)

# Report failures
correlator.report_failure(
    repo='ouroboros',
    component='thread_manager',
    error_type='ZombieThreadError',
    message='Thread cleanup failed for worker-123',
    severity='high',
    tags={'worker_id': 'worker-123'}
)

correlator.report_failure(
    repo='aiospandora',
    component='data_loader',
    error_type='TimeoutError',
    message='Data loading timeout for batch-456',
    severity='medium',
    tags={'batch_id': 'batch-456'}
)
```

### Cascade Detection

```python
# Detect failure cascades
cascades = correlator.detect_cascades()

for cascade in cascades:
    print(f"Cascade {cascade.cascade_id}:")
    print(f"  Root cause: {cascade.root_cause.message}")
    print(f"  Repos affected: {cascade.repos_affected}")
    print(f"  Total failures: {cascade.total_failures}")
    print(f"  Duration: {cascade.duration_seconds:.1f}s")
    print(f"  Severity: {cascade.severity}")
    
    # Related failures
    for failure in cascade.related_failures:
        print(f"    - {failure.repo}/{failure.component}: {failure.message}")
```

### Failure Analytics

```python
# Get failure rate
rate = correlator.get_failure_rate(
    repo='ouroboros',
    window_seconds=300
)
print(f"Failure rate: {rate:.4f} failures/sec")

# Get top failures
top_failures = correlator.get_top_failures(limit=10)

print("Top 10 failure types:")
for error_type, count in top_failures:
    print(f"  {error_type}: {count}")
```

## End-to-End Tracing Example

### Complete Request Flow

```python
class DistributedRequest:
    def __init__(self):
        self.clock = HybridLogicalClock(node_id='ouroboros')
        self.tracker = CriticalPathTracker()
        self.guard = APIVersionGuard()
        self.correlator = FailureCorrelator()
    
    def process_request(self, request_data):
        # Start timing
        timestamp = self.clock.now()
        root_span = self.tracker.start_span(
            'process_request',
            'ouroboros',
            tags={'request_id': request_data['id']}
        )
        
        try:
            # Validate and adapt message
            adapted = self.guard.adapt_message(
                request_data,
                from_api='client',
                from_version=request_data.get('api_version', '1.0.0')
            )
            
            # Call AIOSPANDORA
            result = self.call_aiospandora(adapted, root_span, timestamp)
            
            # Call EDEN-ECS
            final_result = self.call_eden(result, root_span, timestamp)
            
            self.tracker.end_span(root_span)
            
            # Analyze performance
            path = self.tracker.get_critical_path(root_span)
            if path.total_latency_ms > 1000:  # 1 second threshold
                print(f"WARNING: Slow request ({path.total_latency_ms:.2f} ms)")
                print(f"Bottleneck: {path.bottleneck_span.operation}")
            
            return final_result
            
        except Exception as e:
            # Report failure
            self.correlator.report_failure(
                repo='ouroboros',
                component='request_processor',
                error_type=type(e).__name__,
                message=str(e),
                severity='high'
            )
            
            self.tracker.end_span(root_span)
            raise
    
    def call_aiospandora(self, data, parent_span, parent_timestamp):
        span = self.tracker.start_span(
            'aiospandora_call',
            'aiospandora',
            parent_id=parent_span
        )
        
        # Include timestamp for clock sync
        message = {
            'data': data,
            'timestamp': parent_timestamp
        }
        
        result = aiospandora_api.process(message)
        
        self.tracker.end_span(span)
        return result
    
    def call_eden(self, data, parent_span, parent_timestamp):
        span = self.tracker.start_span(
            'eden_call',
            'eden-ecs',
            parent_id=parent_span
        )
        
        result = eden_api.execute(data)
        
        self.tracker.end_span(span)
        return result
```

## Best Practices

### 1. Consistent Clock Usage

```python
# Initialize clocks at startup
clocks = {
    'ouroboros': HybridLogicalClock('ouroboros'),
    'aiospandora': HybridLogicalClock('aiospandora'),
    'eden': HybridLogicalClock('eden')
}

# Always include timestamps in messages
def send_message(data, from_repo):
    return {
        'data': data,
        'timestamp': clocks[from_repo].now()
    }
```

### 2. Comprehensive Span Tagging

```python
# Add useful tags
tracker.start_span(
    'database_query',
    'aiospandora',
    tags={
        'query_type': 'SELECT',
        'table': 'users',
        'cache_hit': 'false',
        'row_count': '1000'
    }
)
```

### 3. Regular Cleanup

```python
def maintenance():
    # Clean old spans
    tracker.cleanup_old_spans()
    
    # Check for cascades
    cascades = correlator.detect_cascades()
    if cascades:
        alert_team(cascades)
```

### 4. Centralized Configuration

```python
# Use registry for all cross-repo config
registry.set('distributed.timeout_ms', 5000)
registry.set('distributed.retry_attempts', 3)

# Other repos read from registry
timeout = registry.get('distributed.timeout_ms', default=1000)
```

## Monitoring Dashboard

```python
def print_distributed_stats():
    print("=== Distributed System Status ===")
    
    # Clock stats
    for node, clock in clocks.items():
        stats = clock.get_statistics()
        print(f"\n{node} Clock:")
        print(f"  Events: {stats['total_events']}")
        print(f"  Updates: {stats['total_updates']}")
        print(f"  Drift corrections: {stats['drift_corrections']}")
    
    # Tracing stats
    print("\nTracing:")
    stats = tracker.get_statistics()
    print(f"  Active spans: {stats['active_spans']}")
    print(f"  Completed: {stats['completed_spans']}")
    
    # Failure stats
    print("\nFailures:")
    stats = correlator.get_statistics()
    print(f"  Recent failures: {stats['recent_failures']}")
    print(f"  Cascades detected: {stats['total_cascades']}")
    print(f"  Failure rate: {stats['current_failure_rate']:.4f}/s")
```
