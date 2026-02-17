# Thread Management Best Practices

## Overview

The `ResourceAwareZombieHunterV2` provides advanced thread management with ancestry tracking, resource profiling, and intelligent zombie detection for the Ouroboros system.

## Features

### 1. Thread Registration and Tracking

Register threads with optional parent-child relationships for hierarchical management:

```python
from src.performance import ResourceAwareZombieHunterV2

# Initialize hunter
hunter = ResourceAwareZombieHunterV2(
    inactivity_threshold=300.0,  # 5 minutes
    cpu_threshold=0.1,           # 0.1% CPU
    check_interval=60.0          # Check every minute
)

# Register main thread
main_thread = threading.Thread(target=main_work)
main_id = hunter.register_thread(main_thread, parent_id=None)

# Register child thread
worker_thread = threading.Thread(target=worker_func)
worker_id = hunter.register_thread(worker_thread, parent_id=main_id)
```

### 2. Activity Reporting

Report thread activity to prevent false zombie detection:

```python
# Report different activity types
hunter.report_activity(thread_id, activity_type='compute')
hunter.report_activity(thread_id, activity_type='io')
hunter.report_activity(thread_id, activity_type='network')
```

### 3. Zombie Detection

Automatically detect zombie threads based on multiple criteria:

```python
# Detect zombies
zombies = hunter.detect_zombies()

for thread_id, profile in zombies:
    print(f"Zombie thread {thread_id}:")
    print(f"  Inactive for: {profile.inactivity_duration:.1f}s")
    print(f"  CPU usage: {profile.cpu_percent:.2f}%")
    print(f"  Activity rate: {profile.activity_rate:.4f} ops/s")
```

### 4. Resource Profiling

Get detailed resource profiles for any thread:

```python
profile = hunter.get_resource_profile(thread_id)

if profile:
    print(f"CPU: {profile.cpu_percent:.2f}%")
    print(f"Memory: {profile.memory_mb:.2f} MB")
    print(f"Is zombie: {profile.is_zombie}")
```

### 5. Ancestry Tracking

Track thread lineage for hierarchical cleanup:

```python
# Get full ancestry chain
ancestry = hunter.get_thread_ancestry(thread_id)
print(f"Ancestry: {ancestry}")

# Get all descendants
descendants = hunter.get_descendants(parent_id)
print(f"Descendants: {descendants}")
```

### 6. Cleanup Operations

Clean up zombie threads and their descendants:

```python
# Clean up entire thread tree
cleaned_ids = hunter.cleanup_zombie_tree(zombie_thread_id)
print(f"Cleaned up {len(cleaned_ids)} threads")
```

## Best Practices

### 1. Set Appropriate Thresholds

Choose thresholds based on your workload:

```python
# For long-running batch jobs
hunter = ResourceAwareZombieHunterV2(
    inactivity_threshold=600.0,  # 10 minutes
    cpu_threshold=0.05           # Very low CPU
)

# For interactive services
hunter = ResourceAwareZombieHunterV2(
    inactivity_threshold=30.0,   # 30 seconds
    cpu_threshold=1.0            # More active threshold
)
```

### 2. Regular Activity Reporting

Report activity at regular intervals:

```python
def worker_loop():
    while running:
        # Do work
        process_batch()
        
        # Report activity
        hunter.report_activity(
            threading.current_thread().ident,
            activity_type='compute'
        )
        
        time.sleep(1)
```

### 3. Periodic Zombie Checks

Schedule regular zombie detection:

```python
def cleanup_scheduler():
    while True:
        # Check for zombies
        zombies = hunter.detect_zombies()
        
        # Clean up zombies
        for thread_id, profile in zombies:
            if profile.inactivity_duration > 600:  # 10 minutes
                hunter.cleanup_zombie_tree(thread_id)
        
        # Wait before next check
        time.sleep(hunter.check_interval)
```

### 4. Monitor Statistics

Track overall thread health:

```python
stats = hunter.get_statistics()

print(f"Total threads: {stats['total_threads']}")
print(f"Zombie count: {stats['zombie_count']}")
print(f"Activity types: {stats['activity_types']}")
print(f"Total activities: {stats['total_activities']}")
```

## Performance Impact

The thread hunter has minimal performance overhead:

- **Registration**: O(1) per thread
- **Activity reporting**: O(1) per report
- **Zombie detection**: O(n) where n is number of threads
- **Memory usage**: ~1KB per tracked thread

## Thread Safety

All operations are thread-safe and use internal locking to prevent race conditions.

## Common Patterns

### Pattern 1: Worker Pool Management

```python
class WorkerPool:
    def __init__(self, size):
        self.hunter = ResourceAwareZombieHunterV2()
        self.workers = []
        
        # Create worker threads
        for i in range(size):
            thread = threading.Thread(target=self.worker_loop)
            thread_id = self.hunter.register_thread(thread)
            self.workers.append((thread, thread_id))
            thread.start()
    
    def worker_loop(self):
        thread_id = threading.current_thread().ident
        
        while True:
            task = self.get_task()
            if task:
                task.execute()
                self.hunter.report_activity(thread_id, 'compute')
```

### Pattern 2: Parent-Child Task Hierarchy

```python
def spawn_subtasks(parent_id, tasks):
    child_threads = []
    
    for task in tasks:
        thread = threading.Thread(target=task.run)
        child_id = hunter.register_thread(thread, parent_id=parent_id)
        child_threads.append(child_id)
        thread.start()
    
    return child_threads
```

## Troubleshooting

### Issue: False Zombie Detection

**Solution**: Increase `inactivity_threshold` or report activity more frequently.

### Issue: Missed Zombies

**Solution**: Decrease thresholds or check more frequently.

### Issue: High Memory Usage

**Solution**: Regularly cleanup old thread records or reduce retention time.
