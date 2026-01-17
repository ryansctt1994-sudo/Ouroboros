"""
Command Executor with Priority Handling

Executes validated commands with priority queuing and resource management.
"""

import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from queue import PriorityQueue
import threading

from .nlp_parser import ParsedCommand, CommandIntent
from .command_validator import ValidationResult


class ExecutionPriority(Enum):
    """Execution priority levels."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class ExecutionStatus(Enum):
    """Command execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandExecution:
    """Represents a command execution instance."""
    
    def __init__(
        self,
        command: ParsedCommand,
        priority: ExecutionPriority,
        execution_id: str
    ):
        self.command = command
        self.priority = priority
        self.execution_id = execution_id
        self.status = ExecutionStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __lt__(self, other):
        """Comparison for priority queue ordering."""
        return self.priority.value < other.priority.value
    
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class CommandExecutor:
    """
    Executes commands with priority queuing and resource management.
    
    Supports concurrent execution with priority-based scheduling.
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        enable_async: bool = True
    ):
        """
        Initialize command executor.
        
        Args:
            max_concurrent: Maximum concurrent executions
            enable_async: Enable asynchronous execution
        """
        self.max_concurrent = max_concurrent
        self.enable_async = enable_async
        
        # Priority queue for pending commands
        self.pending_queue: PriorityQueue = PriorityQueue()
        
        # Active executions
        self.active_executions: Dict[str, CommandExecution] = {}
        
        # Execution history
        self.execution_history: List[CommandExecution] = []
        
        # Command handlers (intent -> handler function)
        self.handlers: Dict[CommandIntent, Callable] = {}
        
        # Execution thread
        self.running = False
        self.executor_thread: Optional[threading.Thread] = None
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Execution counter for IDs
        self.execution_counter = 0
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default command handlers."""
        self.handlers[CommandIntent.GET_STATUS] = self._handle_get_status
        self.handlers[CommandIntent.ALLOCATE_MEMORY] = self._handle_allocate_memory
        self.handlers[CommandIntent.DEALLOCATE_MEMORY] = self._handle_deallocate_memory
        self.handlers[CommandIntent.OPTIMIZE_RESOURCES] = self._handle_optimize_resources
        self.handlers[CommandIntent.SET_PARAMETER] = self._handle_set_parameter
        self.handlers[CommandIntent.EXECUTE_TASK] = self._handle_execute_task
        self.handlers[CommandIntent.QUERY_DATA] = self._handle_query_data
    
    def register_handler(self, intent: CommandIntent, handler: Callable):
        """
        Register custom command handler.
        
        Args:
            intent: Command intent to handle
            handler: Handler function (receives ParsedCommand, returns Dict)
        """
        self.handlers[intent] = handler
    
    def submit(
        self,
        command: ParsedCommand,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM
    ) -> str:
        """
        Submit command for execution.
        
        Args:
            command: Parsed command to execute
            priority: Execution priority
            
        Returns:
            Execution ID
        """
        with self.lock:
            self.execution_counter += 1
            execution_id = f"exec_{self.execution_counter:06d}"
        
        execution = CommandExecution(command, priority, execution_id)
        
        # Add to queue
        self.pending_queue.put(execution)
        
        # Start executor if not running
        if self.enable_async and not self.running:
            self.start()
        
        return execution_id
    
    def start(self):
        """Start asynchronous executor thread."""
        if self.running:
            return
        
        self.running = True
        self.executor_thread = threading.Thread(target=self._executor_loop, daemon=True)
        self.executor_thread.start()
    
    def stop(self):
        """Stop executor thread."""
        self.running = False
        if self.executor_thread:
            self.executor_thread.join(timeout=5.0)
    
    def _executor_loop(self):
        """Main executor loop."""
        while self.running:
            # Check if we can run more commands
            with self.lock:
                active_count = len(self.active_executions)
            
            if active_count < self.max_concurrent and not self.pending_queue.empty():
                try:
                    execution = self.pending_queue.get(timeout=0.1)
                    self._execute_command(execution)
                except Exception:
                    pass
            else:
                time.sleep(0.1)
    
    def _execute_command(self, execution: CommandExecution):
        """Execute a single command."""
        # Mark as running
        execution.status = ExecutionStatus.RUNNING
        execution.start_time = time.time()
        
        with self.lock:
            self.active_executions[execution.execution_id] = execution
        
        try:
            # Get handler
            handler = self.handlers.get(execution.command.intent)
            
            if handler is None:
                execution.result = {
                    'success': False,
                    'message': f'No handler for intent: {execution.command.intent.value}'
                }
                execution.status = ExecutionStatus.FAILED
            else:
                # Execute handler
                result = handler(execution.command)
                execution.result = result
                execution.status = ExecutionStatus.COMPLETED
        
        except Exception as e:
            execution.error = str(e)
            execution.status = ExecutionStatus.FAILED
            execution.result = {'success': False, 'error': str(e)}
        
        finally:
            execution.end_time = time.time()
            
            # Move to history
            with self.lock:
                if execution.execution_id in self.active_executions:
                    del self.active_executions[execution.execution_id]
                self.execution_history.append(execution)
                
                # Keep history bounded
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-1000:]
    
    def execute_sync(self, command: ParsedCommand) -> Dict[str, Any]:
        """
        Execute command synchronously.
        
        Args:
            command: Command to execute
            
        Returns:
            Execution result
        """
        execution_id = f"sync_{int(time.time() * 1000000)}"
        execution = CommandExecution(command, ExecutionPriority.HIGH, execution_id)
        
        self._execute_command(execution)
        
        return execution.result or {'success': False, 'error': 'No result'}
    
    def get_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status."""
        # Check active
        with self.lock:
            if execution_id in self.active_executions:
                exec = self.active_executions[execution_id]
                return {
                    'execution_id': execution_id,
                    'status': exec.status.value,
                    'duration': time.time() - exec.start_time if exec.start_time else 0
                }
        
        # Check history
        for exec in self.execution_history:
            if exec.execution_id == execution_id:
                return {
                    'execution_id': execution_id,
                    'status': exec.status.value,
                    'duration': exec.duration(),
                    'result': exec.result
                }
        
        return None
    
    # Default handler implementations
    
    def _handle_get_status(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle GET_STATUS command."""
        with self.lock:
            active_count = len(self.active_executions)
        
        pending_count = self.pending_queue.qsize()
        completed_count = sum(1 for e in self.execution_history if e.status == ExecutionStatus.COMPLETED)
        
        return {
            'success': True,
            'active_executions': active_count,
            'pending_executions': pending_count,
            'completed_executions': completed_count,
            'total_executions': len(self.execution_history)
        }
    
    def _handle_allocate_memory(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle ALLOCATE_MEMORY command."""
        mem_entity = command.get_entity('memory_size')
        
        if mem_entity:
            return {
                'success': True,
                'action': 'allocate_memory',
                'amount_mb': mem_entity.value,
                'message': f'Allocated {mem_entity.value:.1f} MB'
            }
        
        return {
            'success': False,
            'error': 'Memory size not specified'
        }
    
    def _handle_deallocate_memory(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle DEALLOCATE_MEMORY command."""
        return {
            'success': True,
            'action': 'deallocate_memory',
            'message': 'Memory deallocated'
        }
    
    def _handle_optimize_resources(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle OPTIMIZE_RESOURCES command."""
        return {
            'success': True,
            'action': 'optimize_resources',
            'message': 'Resource optimization initiated'
        }
    
    def _handle_set_parameter(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle SET_PARAMETER command."""
        param_name = command.get_entity('parameter_name')
        param_value = command.get_entity('parameter_value')
        
        if param_name and param_value:
            return {
                'success': True,
                'action': 'set_parameter',
                'parameter': param_name.value,
                'value': param_value.value,
                'message': f'Set {param_name.value} to {param_value.value}'
            }
        
        return {
            'success': False,
            'error': 'Parameter name or value not specified'
        }
    
    def _handle_execute_task(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle EXECUTE_TASK command."""
        return {
            'success': True,
            'action': 'execute_task',
            'task': command.raw_text,
            'message': 'Task execution initiated'
        }
    
    def _handle_query_data(self, command: ParsedCommand) -> Dict[str, Any]:
        """Handle QUERY_DATA command."""
        return {
            'success': True,
            'action': 'query_data',
            'query': command.raw_text,
            'message': 'Data query executed',
            'results': []
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        with self.lock:
            active_count = len(self.active_executions)
        
        completed = sum(1 for e in self.execution_history if e.status == ExecutionStatus.COMPLETED)
        failed = sum(1 for e in self.execution_history if e.status == ExecutionStatus.FAILED)
        
        durations = [e.duration() for e in self.execution_history if e.duration() is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            'active_executions': active_count,
            'pending_executions': self.pending_queue.qsize(),
            'total_completed': completed,
            'total_failed': failed,
            'average_duration_sec': avg_duration,
            'total_executions': len(self.execution_history)
        }
