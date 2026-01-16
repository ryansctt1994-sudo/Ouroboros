"""
Ouroboros Virtual Processor - A lightweight task scheduler and event loop for Linux hybrid OS/AI runtime.

This module provides a background event loop with priority-based task scheduling,
backpressure controls, and monitoring capabilities.
"""

import threading
import time
import heapq
import uuid
from collections import deque
from typing import Optional, Callable, Any, Dict, List, Tuple


class Task:
    """Represents a scheduled task with priority and optional interval execution."""
    
    def __init__(
        self,
        task_id: str,
        fn: Callable,
        priority: int,
        next_run: float,
        args: tuple = None,
        kwargs: dict = None,
        interval: Optional[float] = None,
        name: Optional[str] = None,
    ):
        self.task_id = task_id
        self.fn = fn
        self.priority = priority
        self.next_run = next_run
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.interval = interval
        self.name = name or f"task_{task_id[:8]}"
        self.cancelled = False
        self.execution_count = 0
    
    def __lt__(self, other):
        """Comparison for heapq: prioritize by next_run, then priority (lower is higher priority)."""
        if self.next_run != other.next_run:
            return self.next_run < other.next_run
        return self.priority < other.priority
    
    def execute(self):
        """Execute the task callable."""
        self.execution_count += 1
        return self.fn(*self.args, **self.kwargs)
    
    def should_repeat(self) -> bool:
        """Check if task should be rescheduled after execution."""
        return self.interval is not None and not self.cancelled
    
    def reschedule(self):
        """Update next_run time for interval tasks."""
        if self.interval:
            self.next_run = time.time() + self.interval


class OuroborosVirtualProcessor:
    """
    Virtual processor with event loop and priority task scheduler.
    
    This class manages a background thread that processes scheduled tasks with
    priority ordering, backpressure controls, and monitoring capabilities.
    """
    
    def __init__(self):
        self._state = {
            'running': False,
            'errors': [],
            'stats': {
                'tasks_executed': 0,
                'tasks_cancelled': 0,
                'ticks': 0,
            }
        }
        self._monitoring_data = deque(maxlen=1000)  # O(1) append/pop instead of O(n)
        self._task_queue: List[Task] = []  # Min heap for priority queue
        self._task_registry: Dict[str, Task] = {}  # Fast lookup by task_id
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._poll_interval = 0.1
        self._on_tick: Optional[Callable] = None
        self._max_tasks_per_tick = 50
        self._tick_time_budget_ms = 10
    
    def schedule_task(
        self,
        fn: Callable,
        *,
        priority: int = 10,
        delay: float = 0.0,
        interval: Optional[float] = None,
        args: tuple = None,
        kwargs: dict = None,
        name: Optional[str] = None,
    ) -> str:
        """
        Schedule a task for execution.
        
        Args:
            fn: Callable to execute
            priority: Task priority (lower number = higher priority, default 10)
            delay: Initial delay before first execution (seconds, default 0.0)
            interval: If set, task repeats every interval seconds (default None)
            args: Positional arguments for fn (default None)
            kwargs: Keyword arguments for fn (default None)
            name: Optional task name for debugging (default None)
        
        Returns:
            task_id: Unique identifier for the scheduled task
        """
        task_id = str(uuid.uuid4())
        next_run = time.time() + delay
        
        task = Task(
            task_id=task_id,
            fn=fn,
            priority=priority,
            next_run=next_run,
            args=args,
            kwargs=kwargs,
            interval=interval,
            name=name,
        )
        
        with self._lock:
            self._task_registry[task_id] = task
            heapq.heappush(self._task_queue, task)
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Unique identifier of the task to cancel
        
        Returns:
            True if task was found and cancelled, False otherwise
        """
        with self._lock:
            task = self._task_registry.get(task_id)
            if task and not task.cancelled:
                task.cancelled = True
                self._state['stats']['tasks_cancelled'] += 1
                return True
            return False
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all active (non-cancelled) tasks with safe metadata.
        
        Returns:
            List of task metadata dictionaries
        """
        with self._lock:
            tasks_info = []
            for task in self._task_registry.values():
                if not task.cancelled:
                    tasks_info.append({
                        'task_id': task.task_id,
                        'name': task.name,
                        'priority': task.priority,
                        'next_run': task.next_run,
                        'interval': task.interval,
                        'execution_count': task.execution_count,
                    })
            return tasks_info
    
    def start_event_loop(
        self,
        poll_interval: float = 0.1,
        on_tick: Optional[Callable] = None,
        max_tasks_per_tick: int = 50,
        tick_time_budget_ms: int = 10,
    ):
        """
        Start the background event loop.
        
        Args:
            poll_interval: Interval between event loop ticks (seconds, default 0.1)
            on_tick: Optional callback invoked each tick (default None)
            max_tasks_per_tick: Maximum tasks to execute per tick (default 50)
            tick_time_budget_ms: Maximum time budget for task execution per tick (ms, default 10)
        """
        if self._state['running']:
            return
        
        self._poll_interval = poll_interval
        self._on_tick = on_tick
        self._max_tasks_per_tick = max_tasks_per_tick
        self._tick_time_budget_ms = tick_time_budget_ms
        self._state['running'] = True
        
        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()
    
    def stop_event_loop(self):
        """Stop the background event loop."""
        self._state['running'] = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
    
    def _event_loop(self):
        """Main event loop running in background thread."""
        while self._state['running']:
            tick_start = time.time()
            
            try:
                # Execute scheduled tasks with backpressure controls
                self._execute_due_tasks()
                
                # Invoke user tick callback if provided
                if self._on_tick:
                    self._on_tick()
                
                self._state['stats']['ticks'] += 1
                
                # Record monitoring data
                self._monitoring_data.append({
                    'timestamp': time.time(),
                    'tick_duration': time.time() - tick_start,
                    'queue_size': len(self._task_queue),
                })
                
            except Exception as e:
                # Never crash the event loop
                self._state['errors'].append({
                    'timestamp': time.time(),
                    'error': str(e),
                    'type': type(e).__name__,
                })
            
            # Sleep for remaining poll interval
            elapsed = time.time() - tick_start
            sleep_time = max(0, self._poll_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _execute_due_tasks(self):
        """Execute tasks that are due, respecting backpressure controls."""
        current_time = time.time()
        tick_start = time.time()
        tick_budget_seconds = self._tick_time_budget_ms / 1000.0
        tasks_executed = 0
        
        while tasks_executed < self._max_tasks_per_tick:
            # Check time budget
            if (time.time() - tick_start) >= tick_budget_seconds:
                break
            
            # Get next due task
            with self._lock:
                if not self._task_queue:
                    break
                
                # Peek at next task
                if self._task_queue[0].next_run > current_time:
                    break
                
                task = heapq.heappop(self._task_queue)
            
            # Skip cancelled tasks
            if task.cancelled:
                with self._lock:
                    self._task_registry.pop(task.task_id, None)
                continue
            
            # Execute task
            try:
                task.execute()
                self._state['stats']['tasks_executed'] += 1
                tasks_executed += 1
                
                # Reschedule interval tasks
                if task.should_repeat():
                    task.reschedule()
                    with self._lock:
                        heapq.heappush(self._task_queue, task)
                else:
                    with self._lock:
                        self._task_registry.pop(task.task_id, None)
                        
            except Exception as e:
                # Record error but continue execution
                self._state['errors'].append({
                    'timestamp': time.time(),
                    'error': str(e),
                    'type': type(e).__name__,
                    'task_id': task.task_id,
                    'task_name': task.name,
                })
                
                # Clean up failed task
                with self._lock:
                    self._task_registry.pop(task.task_id, None)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current processor state (thread-safe)."""
        with self._lock:
            return {
                'running': self._state['running'],
                'error_count': len(self._state['errors']),
                'stats': self._state['stats'].copy(),
                'queue_size': len(self._task_queue),
                'active_tasks': len([t for t in self._task_registry.values() if not t.cancelled]),
            }
    
    def get_monitoring_data(self) -> List[Dict[str, Any]]:
        """Get recent monitoring data (thread-safe)."""
        with self._lock:
            return list(self._monitoring_data)
