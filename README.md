# Ouroboros

A lightweight task scheduler and event loop for Linux hybrid OS/AI runtime.

## Overview

Ouroboros provides a background event loop with priority-based task scheduling, backpressure controls, and monitoring capabilities. It's designed for efficient, concurrent task management with minimal overhead.

## Features

- **Priority-based task scheduling** using efficient heap queue
- **Interval/recurring tasks** with configurable execution frequency
- **Backpressure controls** to prevent event loop overload
- **Thread-safe operations** with built-in locking
- **Monitoring and statistics** with efficient deque-based buffering
- **Error resilience** - exceptions in tasks never crash the event loop
- **Lightweight** - stdlib-only dependencies

## Installation

Simply import the module:

```python
from ouroboros_processor import OuroborosVirtualProcessor
A research repository featuring the Magnetar Elastic Coherence Engine.

## Features

- **Magnetar Elastic Coherence Engine**: A neural architecture inspired by magnetar resonance patterns and elastic coherence principles. See [`engine_modules/README.md`](engine_modules/README.md) for details.

## Installation

```bash
# Install base dependencies
pip install -r requirements.txt

# Install ML dependencies for the Magnetar Engine
pip install -r requirements-ml.txt
```

## Quick Start

```python
from ouroboros_processor import OuroborosVirtualProcessor
import time

# Create processor instance
processor = OuroborosVirtualProcessor()

# Start the event loop
processor.start_event_loop(poll_interval=0.1)

# Schedule a one-time task
def my_task():
    print("Task executed!")

task_id = processor.schedule_task(my_task, delay=1.0)

# Schedule a recurring task
def periodic_task():
    print("Periodic task executed!")

recurring_id = processor.schedule_task(
    periodic_task,
    interval=5.0,  # Execute every 5 seconds
    priority=1     # High priority
)

# Let it run
time.sleep(10)

# Cancel a task
processor.cancel_task(recurring_id)

# Stop the event loop
processor.stop_event_loop()
```

## API Reference

### OuroborosVirtualProcessor

#### `schedule_task(fn, *, priority=10, delay=0.0, interval=None, args=None, kwargs=None, name=None) -> str`

Schedule a task for execution.

**Parameters:**
- `fn` (Callable): Function to execute
- `priority` (int): Task priority (lower number = higher priority, default: 10)
- `delay` (float): Initial delay before first execution in seconds (default: 0.0)
- `interval` (float): If set, task repeats every interval seconds (default: None)
- `args` (tuple): Positional arguments for fn (default: None)
- `kwargs` (dict): Keyword arguments for fn (default: None)
- `name` (str): Optional task name for debugging (default: None)

**Returns:**
- `str`: Unique task identifier

**Example:**
```python
# One-time task
task_id = processor.schedule_task(
    my_function,
    priority=5,
    delay=2.0,
    args=(arg1, arg2),
    kwargs={'key': 'value'},
    name='my_task'
)

# Recurring task
recurring_id = processor.schedule_task(
    periodic_function,
    interval=10.0,
    priority=1
)
```

#### `cancel_task(task_id) -> bool`

Cancel a scheduled task.

**Parameters:**
- `task_id` (str): Unique identifier of the task to cancel

**Returns:**
- `bool`: True if task was found and cancelled, False otherwise

**Example:**
```python
if processor.cancel_task(task_id):
    print("Task cancelled successfully")
```

#### `list_tasks() -> List[Dict[str, Any]]`

List all active (non-cancelled) tasks with metadata.

**Returns:**
- `List[Dict]`: List of task metadata dictionaries

**Example:**
```python
tasks = processor.list_tasks()
for task in tasks:
    print(f"Task {task['name']}: priority={task['priority']}, "
          f"executions={task['execution_count']}")
```

#### `start_event_loop(poll_interval=0.1, on_tick=None, max_tasks_per_tick=50, tick_time_budget_ms=10)`

Start the background event loop.

**Parameters:**
- `poll_interval` (float): Interval between event loop ticks in seconds (default: 0.1)
- `on_tick` (Callable): Optional callback invoked each tick (default: None)
- `max_tasks_per_tick` (int): Maximum tasks to execute per tick (default: 50)
- `tick_time_budget_ms` (int): Maximum time budget for task execution per tick in ms (default: 10)

**Example:**
```python
def on_tick_callback():
    print("Tick!")

processor.start_event_loop(
    poll_interval=0.1,
    on_tick=on_tick_callback,
    max_tasks_per_tick=100,
    tick_time_budget_ms=20
)
```

#### `stop_event_loop()`

Stop the background event loop.

#### `get_state() -> Dict[str, Any]`

Get current processor state (thread-safe).

**Returns:**
- `Dict`: State information including running status, statistics, and queue size

#### `get_monitoring_data() -> List[Dict[str, Any]]`

Get recent monitoring data (thread-safe).

**Returns:**
- `List[Dict]`: Recent monitoring entries (up to 1000)

## Usage Patterns

### Pattern 1: High-Priority System Tasks

```python
# System monitoring task with high priority
processor.schedule_task(
    check_system_health,
    priority=1,
    interval=60.0,
    name='health_check'
)

# Lower priority cleanup task
processor.schedule_task(
    cleanup_temp_files,
    priority=100,
    interval=3600.0,
    name='cleanup'
)
```

### Pattern 2: Delayed Initialization

```python
# Initialize components after startup delay
processor.schedule_task(
    initialize_ai_model,
    delay=5.0,
    priority=5,
    name='ai_init'
)
```

### Pattern 3: Backpressure Control

```python
# Configure for high-throughput scenario
processor.start_event_loop(
    poll_interval=0.01,      # Check frequently
    max_tasks_per_tick=100,  # Allow more tasks
    tick_time_budget_ms=50   # Allocate more time
)
```

### Pattern 4: Task with Arguments

```python
def process_data(data_id, validate=True):
    # Process data
    pass

task_id = processor.schedule_task(
    process_data,
    args=(123,),
    kwargs={'validate': False},
    delay=1.0
)
```

## Performance Considerations

1. **Monitoring Buffer**: Uses `collections.deque` with O(1) append/pop operations (maxlen=1000)
2. **Task Queue**: Priority queue implemented with `heapq` for O(log n) operations
3. **Backpressure**: Two-tier control system:
   - `max_tasks_per_tick`: Hard limit on task count per tick
   - `tick_time_budget_ms`: Soft limit on execution time per tick
4. **Thread Safety**: All public methods are thread-safe with lock protection

## Error Handling

Exceptions in tasks are automatically caught and recorded in `processor._state['errors']`. The event loop never crashes due to task failures.

```python
def failing_task():
    raise ValueError("Something went wrong")

# This won't crash the event loop
processor.schedule_task(failing_task)

# Check errors
state = processor.get_state()
print(f"Error count: {state['error_count']}")
Run the Magnetar Elastic Coherence Engine demo:

```bash
python -m engine_modules.magnetar_elastic_coherence_engine
```

## Testing

Run the test suite:

```bash
python -m unittest tests.test_task_scheduler -v
```

## License

MIT
```bash
pytest tests/ -v
```
