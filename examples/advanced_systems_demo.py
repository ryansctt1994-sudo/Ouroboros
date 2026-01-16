"""
Example Usage: Advanced AI-Enabled Systems

Demonstrates the usage of memory management, command system,
prioritization engine, and enhanced file system.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory_management import AdvancedMemoryManager, PredictionStrategy
from src.command_system import MultiLayeredCommandSystem
from src.command_system.command_validator import PermissionLevel
from src.command_system.command_executor import ExecutionPriority
from src.prioritization_engine import MultiLevelPriorityManager
from src.prioritization_engine.priority_manager import Task
from src.file_system import EnhancedFileManager


def example_memory_management():
    """Example: Advanced Memory Management with ARIMA/LSTM."""
    print("\n" + "=" * 70)
    print("Example 1: Advanced Memory Management")
    print("=" * 70)
    
    # Initialize memory manager
    manager = AdvancedMemoryManager(
        max_memory_mb=4096,
        warning_threshold=0.75,
        critical_threshold=0.90,
        strategy=PredictionStrategy.ENSEMBLE_WEIGHTED
    )
    
    print("\n1. Simulating memory usage over time...")
    # Simulate memory usage over time
    for i in range(30):
        memory_usage = 1000.0 + i * 50 + (i % 5) * 20  # Simulate some variation
        manager.update(memory_usage)
        
        if i % 10 == 0:
            print(f"  Step {i}: Memory = {memory_usage:.1f} MB")
    
    print("\n2. Making predictions...")
    # Predict future memory usage
    predictions = manager.predict(steps=5)
    print(f"  Predicted next 5 steps: {[f'{p:.1f}' for p in predictions]} MB")
    
    # Get confidence intervals
    intervals = manager.get_confidence_intervals(predictions)
    print(f"  Confidence intervals:")
    for i, (lower, upper) in enumerate(intervals):
        print(f"    Step {i+1}: [{lower:.1f}, {upper:.1f}] MB")
    
    print("\n3. Testing allocation recommendation...")
    # Request memory allocation
    recommendation = manager.recommend_allocation(500.0)
    print(f"  Allocation request: 500 MB")
    print(f"  Approved: {recommendation['approve']}")
    print(f"  Reason: {recommendation['recommendation']}")
    print(f"  Projected usage ratio: {recommendation['usage_ratio']:.2%}")
    
    # Get optimization suggestions
    print("\n4. Checking optimization needs...")
    optimization = manager.optimize_resources()
    print(f"  Needs optimization: {optimization['needs_optimization']}")
    print(f"  Pressure level: {optimization['pressure_level']}")
    if optimization['strategies']:
        print(f"  Recommended strategies:")
        for strategy in optimization['strategies']:
            print(f"    - [{strategy['priority']}] {strategy['description']}")
    
    # Get state
    print("\n5. Manager state:")
    state = manager.get_state()
    print(f"  Current memory: {state['current_memory_mb']:.1f} MB")
    print(f"  Usage ratio: {state['usage_ratio']:.2%}")
    print(f"  ARIMA accuracy: {state['prediction_accuracy']['arima']:.3f}")
    print(f"  LSTM accuracy: {state['prediction_accuracy']['lstm']:.3f}")


def example_command_system():
    """Example: Multi-Layered Command System with NLP."""
    print("\n\n" + "=" * 70)
    print("Example 2: Multi-Layered Command System")
    print("=" * 70)
    
    # Initialize command system
    system = MultiLayeredCommandSystem(
        max_memory_allocation_mb=2048,
        max_concurrent_executions=5,
        enable_async=True
    )
    
    print("\n1. Processing natural language commands...")
    
    # Process various commands
    commands = [
        "allocate 500 MB",
        "show status",
        "optimize resources",
        "set max_memory to 4096"
    ]
    
    for cmd in commands:
        print(f"\n  Command: '{cmd}'")
        result = system.process(
            cmd,
            permission=PermissionLevel.ADMIN,
            execute_async=False
        )
        print(f"    Success: {result['success']}")
        print(f"    Intent: {result['parse_result']['intent']}")
        print(f"    Validation: {result['validation_result']['status']}")
        if result.get('message'):
            print(f"    Message: {result['message']}")
    
    print("\n2. Batch processing...")
    batch_commands = [
        "allocate 100 MB",
        "allocate 200 MB",
        "get info"
    ]
    
    results = system.process_batch(batch_commands, permission=PermissionLevel.USER)
    print(f"  Processed {len(results)} commands")
    successful = sum(1 for r in results if r['success'])
    print(f"  Successful: {successful}/{len(results)}")
    
    print("\n3. Analytics...")
    analytics = system.get_analytics()
    print(f"  Total commands: {analytics['total_commands']}")
    print(f"  Success rate: {analytics['success_rate']:.1%}")
    print(f"  Intent distribution:")
    for intent, count in analytics['intent_distribution'].items():
        print(f"    {intent}: {count}")


def example_prioritization_engine():
    """Example: RL-based Prioritization Engine."""
    print("\n\n" + "=" * 70)
    print("Example 3: RL-based Prioritization Engine")
    print("=" * 70)
    
    # Initialize priority manager
    manager = MultiLevelPriorityManager(
        enable_rl=True,
        learning_rate=0.1,
        discount_factor=0.95
    )
    
    print("\n1. Adding tasks with different urgencies...")
    
    # Create tasks
    tasks = [
        Task("task_critical", urgency=0.95, complexity=0.8),
        Task("task_high", urgency=0.75, complexity=0.5),
        Task("task_medium", urgency=0.5, complexity=0.6),
        Task("task_low", urgency=0.2, complexity=0.3),
    ]
    
    for task in tasks:
        priority = manager.add_task(task)
        print(f"  {task.task_id}: urgency={task.urgency:.2f}, "
              f"assigned priority={priority} (0=critical, 3=low)")
    
    print("\n2. Processing tasks in priority order...")
    
    # Update system metrics
    manager.update_system_metrics(memory_ratio=0.6, cpu_ratio=0.5)
    
    # Process tasks
    processed = 0
    while processed < 3:
        task = manager.get_next_task()
        if task is None:
            break
        
        print(f"\n  Processing: {task.task_id}")
        
        # Simulate task execution
        execution_time = 0.5 + task.complexity * 0.5
        time.sleep(0.1)  # Simulate work
        
        # Record outcome
        manager.record_outcome(
            task,
            completed=True,
            execution_time=execution_time,
            deadline_met=True,
            resource_efficiency=0.85,
            user_satisfaction=0.9
        )
        
        print(f"    Completed in {execution_time:.2f}s")
        processed += 1
    
    print("\n3. Manager statistics...")
    stats = manager.get_statistics()
    print(f"  Pending tasks: {stats['pending_tasks']}")
    print(f"  Completed tasks: {stats['completed_tasks']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    if 'rl_stats' in stats:
        print(f"  RL agent states visited: {stats['rl_stats']['states_visited']}")
        print(f"  RL exploration rate (epsilon): {stats['rl_stats']['epsilon']:.3f}")


def example_file_system():
    """Example: Enhanced File System with Deduplication."""
    print("\n\n" + "=" * 70)
    print("Example 4: Enhanced File System")
    print("=" * 70)
    
    # Initialize file manager
    manager = EnhancedFileManager(
        block_size=4096,
        num_shards=16,
        enable_deduplication=True
    )
    
    print("\n1. Storing files with deduplication...")
    
    # Create files with some duplicate content
    files = {
        "file1.txt": b"Hello, World! " * 1000,
        "file2.txt": b"Hello, World! " * 1000,  # Duplicate content
        "file3.txt": b"Different content " * 1000,
        "file4.txt": b"Hello, World! " * 500 + b"Different content " * 500,
    }
    
    for file_id, content in files.items():
        result = manager.store_file(file_id, content)
        print(f"\n  Stored: {file_id}")
        print(f"    Original size: {result['original_size']} bytes")
        print(f"    Stored size: {result['stored_size']} bytes")
        if 'compression_ratio' in result:
            print(f"    Compression ratio: {result['compression_ratio']:.1%}")
    
    print("\n2. Retrieving files...")
    
    retrieved = manager.retrieve_file("file1.txt")
    print(f"  Retrieved file1.txt: {len(retrieved)} bytes")
    print(f"  Content matches: {retrieved == files['file1.txt']}")
    
    print("\n3. Finding similar files...")
    
    similar = manager.find_similar_files("file1.txt")
    print(f"  Files sharing blocks with file1.txt: {similar}")
    
    print("\n4. File listing...")
    
    all_files = manager.list_files()
    print(f"  Total files: {len(all_files)}")
    
    # List files with prefix
    prefix_files = manager.list_files(prefix="file")
    print(f"  Files with 'file' prefix: {prefix_files}")
    
    print("\n5. File system statistics...")
    
    stats = manager.get_statistics()
    print(f"  Total files: {stats['total_files']}")
    if 'deduplication_stats' in stats:
        dedup = stats['deduplication_stats']
        print(f"  Total blocks: {dedup['total_blocks']}")
        print(f"  Space savings: {dedup['space_savings_ratio']:.1%}")
        print(f"  Space saved: {dedup['space_savings_mb']:.2f} MB")
    
    # Index stats
    index_stats = stats['index_stats']
    print(f"  Index shards: {index_stats['num_shards']}")
    print(f"  Index hit rate: {index_stats['hit_rate']:.1%}")


def example_integration():
    """Example: Integration of all systems."""
    print("\n\n" + "=" * 70)
    print("Example 5: Integrated System Usage")
    print("=" * 70)
    
    # Initialize all systems
    memory_mgr = AdvancedMemoryManager(max_memory_mb=8192)
    cmd_system = MultiLayeredCommandSystem()
    priority_mgr = MultiLevelPriorityManager(enable_rl=True)
    file_mgr = EnhancedFileManager(enable_deduplication=True)
    
    print("\n1. Integrated workflow simulation...")
    
    # Update memory usage
    memory_mgr.update(3000.0)
    print(f"  Current memory usage: 3000 MB")
    
    # Process command to check status
    cmd_result = cmd_system.process("show status", execute_async=False)
    print(f"  Command processed: {cmd_result['success']}")
    
    # Add high-priority task
    task = Task("urgent_task", urgency=0.95, complexity=0.7)
    priority_mgr.add_task(task)
    print(f"  Added urgent task to queue")
    
    # Store configuration file
    config_content = b'{"max_memory": 8192, "enable_dedup": true}'
    file_mgr.store_file("config.json", config_content)
    print(f"  Stored configuration file")
    
    print("\n2. Getting system-wide statistics...")
    
    mem_state = memory_mgr.get_state()
    priority_stats = priority_mgr.get_statistics()
    file_stats = file_mgr.get_statistics()
    
    print(f"\n  Memory Manager:")
    print(f"    Usage: {mem_state['usage_ratio']:.1%}")
    print(f"    Pressure: {mem_state['pressure_level']}")
    
    print(f"\n  Priority Manager:")
    print(f"    Pending tasks: {priority_stats['pending_tasks']}")
    print(f"    Queue depth: {priority_stats['total_queue_depth']}")
    
    print(f"\n  File Manager:")
    print(f"    Total files: {file_stats['total_files']}")
    
    print("\n  All systems operational!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Advanced AI-Enabled Systems - Examples")
    print("=" * 70)
    
    example_memory_management()
    example_command_system()
    example_prioritization_engine()
    example_file_system()
    example_integration()
    
    print("\n\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70 + "\n")
