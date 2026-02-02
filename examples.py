#!/usr/bin/env python3
"""
Example usage of Ouroboros Virtual Processor task scheduler.

This demonstrates the key features:
- One-time tasks with delay
- Recurring interval tasks
- Priority-based execution
- Task cancellation
- Monitoring and statistics
"""

from ouroboros_processor import OuroborosVirtualProcessor
import time


def example_basic_scheduling():
    """Example 1: Basic task scheduling."""
    print("=== Example 1: Basic Scheduling ===\n")
    
    processor = OuroborosVirtualProcessor()
    processor.start_event_loop(poll_interval=0.1)
    
    # Schedule a one-time task
    def greet():
        print(f"[{time.time():.2f}] Hello from scheduled task!")
    
    task_id = processor.schedule_task(greet, delay=0.5, name='greeting')
    print(f"Scheduled task: {task_id}")
    
    time.sleep(1.0)
    processor.stop_event_loop()
    print()


def example_recurring_tasks():
    """Example 2: Recurring interval tasks."""
    print("=== Example 2: Recurring Tasks ===\n")
    
    processor = OuroborosVirtualProcessor()
    processor.start_event_loop(poll_interval=0.05)
    
    counter = {'value': 0}
    
    def increment():
        counter['value'] += 1
        print(f"[{time.time():.2f}] Counter: {counter['value']}")
    
    # Schedule recurring task every 0.3 seconds
    task_id = processor.schedule_task(
        increment,
        interval=0.3,
        name='counter',
        priority=5
    )
    
    # Let it run for a while
    time.sleep(1.5)
    
    # Cancel the task
    processor.cancel_task(task_id)
    print(f"\n[{time.time():.2f}] Task cancelled")
    
    # Verify no more executions
    time.sleep(0.5)
    
    processor.stop_event_loop()
    print()


def example_priority_ordering():
    """Example 3: Priority-based task execution."""
    print("=== Example 3: Priority Ordering ===\n")
    print("Note: When tasks are due at the same time, higher priority (lower number) executes first.\n")
    
    processor = OuroborosVirtualProcessor()
    processor.start_event_loop(poll_interval=0.05)
    
    # Schedule tasks with staggered times but show priority matters when timing overlaps
    # In real scenarios, priority helps when multiple tasks become due simultaneously
    
    # Schedule high-priority urgent task
    processor.schedule_task(
        lambda: print("  [Priority 1] Critical system check"),
        priority=1,
        delay=0.1,
        name='critical'
    )
    
    # Schedule medium-priority task
    processor.schedule_task(
        lambda: print("  [Priority 50] Regular maintenance"),
        priority=50,
        delay=0.1,
        name='maintenance'
    )
    
    # Schedule low-priority background task
    processor.schedule_task(
        lambda: print("  [Priority 100] Background cleanup"),
        priority=100,
        delay=0.1,
        name='cleanup'
    )
    
    print("Scheduled 3 tasks with different priorities...")
    time.sleep(0.3)
    
    processor.stop_event_loop()
    print()


def example_task_with_arguments():
    """Example 4: Tasks with arguments."""
    print("=== Example 4: Tasks with Arguments ===\n")
    
    processor = OuroborosVirtualProcessor()
    processor.start_event_loop(poll_interval=0.05)
    
    def process_data(item_id, operation='read', verbose=True):
        if verbose:
            print(f"[{time.time():.2f}] Processing item {item_id} with operation: {operation}")
    
    # Schedule with positional and keyword arguments
    processor.schedule_task(
        process_data,
        args=(42,),
        kwargs={'operation': 'write', 'verbose': True},
        delay=0.2,
        name='process_42'
    )
    
    processor.schedule_task(
        process_data,
        args=(99,),
        kwargs={'operation': 'delete'},
        delay=0.4,
        name='process_99'
    )
    
    time.sleep(0.7)
    processor.stop_event_loop()
    print()


def example_monitoring():
    """Example 5: Monitoring and statistics."""
    print("=== Example 5: Monitoring and Statistics ===\n")
    
    processor = OuroborosVirtualProcessor()
    processor.start_event_loop(poll_interval=0.1)
    
    # Schedule some tasks
    for i in range(5):
        processor.schedule_task(
            lambda x=i: print(f"Task {x} executed"),
            delay=0.1 * (i + 1),
            name=f'task_{i}'
        )
    
    # Check state before execution
    print("Initial state:")
    state = processor.get_state()
    print(f"  Running: {state['running']}")
    print(f"  Queue size: {state['queue_size']}")
    print(f"  Active tasks: {state['active_tasks']}")
    
    # List tasks
    print("\nActive tasks:")
    for task in processor.list_tasks():
        print(f"  - {task['name']} (priority: {task['priority']})")
    
    # Wait for execution
    time.sleep(1.0)
    
    # Check final state
    print("\nFinal state:")
    state = processor.get_state()
    print(f"  Tasks executed: {state['stats']['tasks_executed']}")
    print(f"  Total ticks: {state['stats']['ticks']}")
    print(f"  Queue size: {state['queue_size']}")
    
    # Get monitoring data
    monitoring = processor.get_monitoring_data()
    if monitoring:
        avg_tick_duration = sum(m['tick_duration'] for m in monitoring) / len(monitoring)
        print(f"  Average tick duration: {avg_tick_duration*1000:.2f}ms")
    
    processor.stop_event_loop()
    print()


def example_error_handling():
    """Example 6: Error handling and resilience."""
    print("=== Example 6: Error Handling ===\n")
    
    processor = OuroborosVirtualProcessor()
    processor.start_event_loop(poll_interval=0.05)
    
    def failing_task():
        print("Task is about to fail...")
        raise ValueError("Intentional error!")
    
    def healthy_task():
        print("Healthy task executed successfully")
    
    # Schedule failing task
    processor.schedule_task(failing_task, delay=0.1, name='failing')
    
    # Schedule healthy task after
    processor.schedule_task(healthy_task, delay=0.2, name='healthy')
    
    time.sleep(0.4)
    
    # Check error state
    state = processor.get_state()
    print(f"\nError count: {state['error_count']}")
    print("Event loop continued running despite the error!")
    
    processor.stop_event_loop()
    print()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Ouroboros Virtual Processor - Examples")
    print("="*60 + "\n")
    
    example_basic_scheduling()
    example_recurring_tasks()
    example_priority_ordering()
    example_task_with_arguments()
    example_monitoring()
    example_error_handling()
    
    print("="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
