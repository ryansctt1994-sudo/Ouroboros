"""
Tests for ouroboros_processor task scheduler functionality.
"""

import unittest
import time
import threading
import heapq
from ouroboros_processor import OuroborosVirtualProcessor, Task


class TestTaskScheduler(unittest.TestCase):
    """Test suite for the task scheduler."""
    
    def setUp(self):
        """Create a fresh processor instance for each test."""
        self.processor = OuroborosVirtualProcessor()
    
    def tearDown(self):
        """Stop the event loop after each test."""
        self.processor.stop_event_loop()
    
    def test_scheduled_task_executes_after_delay(self):
        """Test that scheduled tasks execute after the specified delay."""
        execution_times = []
        
        def task_fn():
            execution_times.append(time.time())
        
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.01)
        
        # Schedule task with 0.1 second delay
        start_time = time.time()
        task_id = self.processor.schedule_task(task_fn, delay=0.1)
        
        # Wait for task to execute
        time.sleep(0.3)
        
        # Verify task executed
        self.assertEqual(len(execution_times), 1)
        
        # Verify timing (allow some tolerance)
        elapsed = execution_times[0] - start_time
        self.assertGreaterEqual(elapsed, 0.1)
        self.assertLess(elapsed, 0.2)  # Should execute within reasonable time
    
    def test_interval_tasks_execute_repeatedly(self):
        """Test that interval tasks execute repeatedly at the specified interval."""
        execution_count = []
        
        def task_fn():
            execution_count.append(time.time())
        
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.01)
        
        # Schedule interval task every 0.1 seconds
        task_id = self.processor.schedule_task(task_fn, interval=0.1, delay=0.0)
        
        # Wait for multiple executions
        time.sleep(0.35)
        
        # Should execute at least 3 times (0.0, 0.1, 0.2 seconds)
        self.assertGreaterEqual(len(execution_count), 3)
        
        # Verify intervals
        if len(execution_count) >= 2:
            for i in range(1, min(3, len(execution_count))):
                interval = execution_count[i] - execution_count[i-1]
                self.assertGreaterEqual(interval, 0.09)
                self.assertLess(interval, 0.15)
    
    def test_task_cancellation_prevents_execution(self):
        """Test that cancelled tasks do not execute."""
        execution_count = []
        
        def task_fn():
            execution_count.append(time.time())
        
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.01)
        
        # Schedule task with delay
        task_id = self.processor.schedule_task(task_fn, delay=0.2)
        
        # Cancel task before it executes
        time.sleep(0.05)
        cancelled = self.processor.cancel_task(task_id)
        
        self.assertTrue(cancelled)
        
        # Wait to ensure task would have executed
        time.sleep(0.3)
        
        # Task should not have executed
        self.assertEqual(len(execution_count), 0)
    
    def test_cancel_interval_task_stops_future_executions(self):
        """Test that cancelling an interval task stops future executions."""
        execution_count = []
        
        def task_fn():
            execution_count.append(time.time())
        
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.01)
        
        # Schedule interval task
        task_id = self.processor.schedule_task(task_fn, interval=0.1, delay=0.0)
        
        # Let it execute a couple times
        time.sleep(0.25)
        
        initial_count = len(execution_count)
        self.assertGreaterEqual(initial_count, 2)
        
        # Cancel task
        self.processor.cancel_task(task_id)
        
        # Wait and verify no more executions
        time.sleep(0.3)
        final_count = len(execution_count)
        
        # Should not have increased significantly (maybe one more due to timing)
        self.assertLessEqual(final_count - initial_count, 1)
    
    def test_max_tasks_per_tick_is_respected(self):
        """Test that max_tasks_per_tick limits task execution."""
        execution_count = []
        lock = threading.Lock()
        
        def task_fn():
            with lock:
                execution_count.append(time.time())
        
        # Start event loop with low max_tasks_per_tick
        self.processor.start_event_loop(
            poll_interval=0.1,
            max_tasks_per_tick=5
        )
        
        # Schedule many tasks to execute immediately
        for i in range(20):
            self.processor.schedule_task(task_fn, delay=0.0, priority=i)
        
        # Wait for first tick
        time.sleep(0.15)
        
        # Should have executed no more than max_tasks_per_tick in first tick
        # (might be slightly more due to second tick starting)
        self.assertLessEqual(len(execution_count), 10)  # Allow for 2 ticks
    
    def test_task_priority_ordering(self):
        """Test that higher priority tasks execute first when due at same time."""
        execution_order = []
        lock = threading.Lock()
        
        def make_task_fn(task_id):
            def task_fn():
                with lock:
                    execution_order.append(task_id)
            return task_fn
        
        # Schedule tasks in reverse priority order so higher priority tasks
        # have later next_run times if we don't fix it
        # But we'll schedule them fast enough that they're effectively simultaneous
        delay_time = 0.15
        
        # Schedule in quick succession
        task1 = self.processor.schedule_task(make_task_fn('high'), priority=1, delay=delay_time)
        task2 = self.processor.schedule_task(make_task_fn('medium'), priority=50, delay=delay_time)  
        task3 = self.processor.schedule_task(make_task_fn('low'), priority=100, delay=delay_time)
        
        # Manually fix next_run times to be exactly the same for fair comparison
        target_time = time.time() + delay_time
        with self.processor._lock:
            for task in self.processor._task_registry.values():
                task.next_run = target_time
            # Rebuild heap with corrected times
            heapq.heapify(self.processor._task_queue)
        
        # Start event loop after scheduling
        self.processor.start_event_loop(poll_interval=0.05)
        
        # Wait for execution
        time.sleep(delay_time + 0.15)
        
        # Verify high priority executed first
        self.assertEqual(len(execution_order), 3)
        self.assertEqual(execution_order[0], 'high')
        self.assertEqual(execution_order[1], 'medium')
        self.assertEqual(execution_order[2], 'low')
    
    def test_list_tasks_returns_active_tasks(self):
        """Test that list_tasks returns correct metadata."""
        def dummy_task():
            pass
        
        # Schedule some tasks
        task_id1 = self.processor.schedule_task(
            dummy_task, 
            name='task1', 
            priority=5, 
            delay=10.0
        )
        task_id2 = self.processor.schedule_task(
            dummy_task, 
            name='task2', 
            priority=10, 
            interval=5.0
        )
        
        # List tasks
        tasks = self.processor.list_tasks()
        
        # Should have 2 tasks
        self.assertEqual(len(tasks), 2)
        
        # Check metadata
        task_names = {t['name'] for t in tasks}
        self.assertEqual(task_names, {'task1', 'task2'})
        
        # Cancel one task
        self.processor.cancel_task(task_id1)
        
        # List should now have only 1 task
        tasks = self.processor.list_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['name'], 'task2')
    
    def test_task_exception_doesnt_crash_event_loop(self):
        """Test that exceptions in tasks are caught and don't crash the event loop."""
        success_count = []
        
        def failing_task():
            raise ValueError("Task error")
        
        def success_task():
            success_count.append(1)
        
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.05)
        
        # Schedule failing task and success task
        self.processor.schedule_task(failing_task, delay=0.0)
        self.processor.schedule_task(success_task, delay=0.1)
        
        # Wait for both to execute
        time.sleep(0.2)
        
        # Success task should still execute
        self.assertEqual(len(success_count), 1)
        
        # Error should be recorded
        state = self.processor.get_state()
        self.assertGreater(state['error_count'], 0)
    
    def test_backwards_compatible_event_loop(self):
        """Test that start_event_loop maintains backwards compatibility."""
        tick_count = []
        
        def on_tick():
            tick_count.append(1)
        
        # Start event loop with just poll_interval and on_tick
        self.processor.start_event_loop(poll_interval=0.05, on_tick=on_tick)
        
        # Wait for a few ticks
        time.sleep(0.2)
        
        # Should have ticked multiple times
        self.assertGreaterEqual(len(tick_count), 3)
    
    def test_monitoring_data_deque(self):
        """Test that monitoring data uses deque efficiently."""
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.01)
        
        # Wait for some ticks
        time.sleep(0.15)
        
        # Get monitoring data
        data = self.processor.get_monitoring_data()
        
        # Should have data
        self.assertGreater(len(data), 0)
        
        # Each entry should have expected fields
        for entry in data:
            self.assertIn('timestamp', entry)
            self.assertIn('tick_duration', entry)
            self.assertIn('queue_size', entry)
    
    def test_get_state_returns_current_state(self):
        """Test that get_state returns accurate state information."""
        # Get state before starting
        state = self.processor.get_state()
        self.assertFalse(state['running'])
        self.assertEqual(state['queue_size'], 0)
        
        # Start event loop
        self.processor.start_event_loop(poll_interval=0.05)
        
        # Schedule a task
        self.processor.schedule_task(lambda: None, delay=1.0)
        
        # Get state
        state = self.processor.get_state()
        self.assertTrue(state['running'])
        self.assertEqual(state['queue_size'], 1)
        self.assertEqual(state['active_tasks'], 1)


if __name__ == '__main__':
    unittest.main()
