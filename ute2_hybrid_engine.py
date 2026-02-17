"""
UTe2 Hybrid System - Execution Engine

Hybrid execution engine with offline-first approach and optional cloud enhancements.
Supports multiple execution modes: Offline, Local, Hybrid, and Cloud.
Includes priority task queuing and dynamic fallback mechanisms.
"""

import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from queue import PriorityQueue
from threading import Lock

from ute2_simulation import UTe2SimulationEngine, SimulationResult
from ute2_cache import SimulationCache
from ute2_ai_advisor import AIAdvisor

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Available execution modes"""
    OFFLINE = "offline"
    LOCAL = "local"
    HYBRID = "hybrid"
    CLOUD = "cloud"


@dataclass
class Task:
    """Simulation task with priority"""
    priority: int  # Lower number = higher priority
    task_id: str
    parameters: Dict[str, Any]
    mode: ExecutionMode
    created_at: float
    
    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    success: bool
    result: Optional[SimulationResult]
    execution_mode: ExecutionMode
    execution_time: float
    metadata: Dict[str, Any]


class HybridExecutionEngine:
    """
    Hybrid execution engine for UTe2 simulations
    
    Features:
    - Multiple execution modes (offline, local, hybrid, cloud)
    - Automatic fallback to local when internet unavailable
    - Priority-based task queuing
    - Intelligent caching and optimization
    """
    
    def __init__(self, config: Dict[str, Any], knowledge_base_path: str = "knowledge_base.json"):
        """
        Initialize hybrid execution engine
        
        Args:
            config: Configuration dictionary
            knowledge_base_path: Path to AI knowledge base
        """
        self.config = config
        self.execution_config = config.get('execution', {})
        
        # Initialize components
        self.simulation_engine = UTe2SimulationEngine(config)
        self.cache = SimulationCache(config)
        self.advisor = AIAdvisor(config, knowledge_base_path)
        
        # Execution mode
        default_mode = self.execution_config.get('default_mode', 'local')
        self.current_mode = ExecutionMode(default_mode)
        
        # Task queue
        self.task_queue = PriorityQueue()
        self.task_lock = Lock()
        self.task_counter = 0
        self.completed_tasks: List[TaskResult] = []
        
        # Internet availability (would check in real implementation)
        self.internet_available = False
        
        logger.info(f"Hybrid Execution Engine initialized (mode={self.current_mode.value})")
    
    def set_mode(self, mode: str):
        """
        Set execution mode
        
        Args:
            mode: Mode name (offline, local, hybrid, cloud)
        """
        try:
            new_mode = ExecutionMode(mode.lower())
            
            # Check if mode is enabled
            modes_config = self.execution_config.get('modes', {})
            mode_config = modes_config.get(new_mode.value, {})
            
            if not mode_config.get('enabled', False) and new_mode != ExecutionMode.LOCAL:
                logger.warning(f"Mode {mode} is not enabled, falling back to LOCAL")
                self.current_mode = ExecutionMode.LOCAL
                return
            
            # Check internet availability for cloud modes
            if new_mode in [ExecutionMode.HYBRID, ExecutionMode.CLOUD]:
                if not self._check_internet():
                    logger.warning("Internet not available, falling back to LOCAL mode")
                    self.current_mode = ExecutionMode.LOCAL
                    return
            
            self.current_mode = new_mode
            logger.info(f"Execution mode set to: {self.current_mode.value}")
            
        except ValueError:
            logger.error(f"Invalid mode: {mode}")
    
    def _check_internet(self) -> bool:
        """
        Check if internet connection is available
        
        Returns:
            True if internet is available
        """
        # In real implementation, would ping cloud endpoint
        # For offline-first, default to False
        return self.internet_available
    
    def submit_task(self, 
                   parameters: Dict[str, Any],
                   priority: int = 5,
                   mode: Optional[str] = None) -> str:
        """
        Submit a simulation task to the queue
        
        Args:
            parameters: Simulation parameters
            priority: Task priority (0=highest, 10=lowest)
            mode: Override execution mode for this task
            
        Returns:
            Task ID
        """
        with self.task_lock:
            self.task_counter += 1
            task_id = f"task_{self.task_counter:06d}"
        
        # Determine execution mode
        exec_mode = self.current_mode
        if mode is not None:
            try:
                exec_mode = ExecutionMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode {mode}, using current mode")
        
        task = Task(
            priority=priority,
            task_id=task_id,
            parameters=parameters,
            mode=exec_mode,
            created_at=time.time()
        )
        
        self.task_queue.put(task)
        logger.info(f"Task {task_id} submitted (priority={priority}, mode={exec_mode.value})")
        
        return task_id
    
    def execute_task(self, task: Task) -> TaskResult:
        """
        Execute a single task
        
        Args:
            task: Task to execute
            
        Returns:
            TaskResult with execution details
        """
        start_time = time.time()
        logger.info(f"Executing task {task.task_id} in {task.mode.value} mode")
        
        metadata = {
            'priority': task.priority,
            'queue_time': start_time - task.created_at
        }
        
        # Check cache first
        cached_result = self.cache.get(task.parameters)
        if cached_result is not None:
            execution_time = time.time() - start_time
            logger.info(f"Task {task.task_id} served from cache")
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=cached_result,
                execution_mode=task.mode,
                execution_time=execution_time,
                metadata={**metadata, 'cache_hit': True}
            )
        
        metadata['cache_hit'] = False
        
        # Get AI advisor suggestions
        suggestions = self.advisor.suggest_parameters(
            temperature=task.parameters.get('temperature_K'),
            magnetic_field=task.parameters.get('magnetic_field_T'),
            device_type=self._detect_device_type()
        )
        
        # Merge suggestions with parameters
        final_params = {**suggestions, **task.parameters}
        
        # Execute based on mode
        try:
            if task.mode == ExecutionMode.OFFLINE:
                result = self._execute_offline(final_params)
            elif task.mode == ExecutionMode.LOCAL:
                result = self._execute_local(final_params)
            elif task.mode == ExecutionMode.HYBRID:
                result = self._execute_hybrid(final_params)
            elif task.mode == ExecutionMode.CLOUD:
                result = self._execute_cloud(final_params)
            else:
                raise ValueError(f"Unknown mode: {task.mode}")
            
            execution_time = time.time() - start_time
            
            # Cache successful results
            if result.success:
                self.cache.put(task.parameters, result)
            
            # Learn from execution
            performance_metrics = {
                'execution_time': execution_time,
                'mode': task.mode.value
            }
            self.advisor.learn_from_simulation(final_params, result, performance_metrics)
            
            task_result = TaskResult(
                task_id=task.task_id,
                success=result.success,
                result=result,
                execution_mode=task.mode,
                execution_time=execution_time,
                metadata=metadata
            )
            
            logger.info(f"Task {task.task_id} completed in {execution_time:.2f}s")
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task {task.task_id} failed: {e}")
            
            return TaskResult(
                task_id=task.task_id,
                success=False,
                result=None,
                execution_mode=task.mode,
                execution_time=execution_time,
                metadata={**metadata, 'error': str(e)}
            )
    
    def _execute_offline(self, parameters: Dict[str, Any]) -> SimulationResult:
        """
        Execute in offline mode with resource constraints
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            SimulationResult
        """
        # Apply offline mode constraints
        offline_config = self.execution_config.get('modes', {}).get('offline', {})
        max_grid = offline_config.get('max_grid_size', 24)
        
        constrained_params = parameters.copy()
        constrained_params['k_grid_size'] = min(
            constrained_params.get('k_grid_size', 32),
            max_grid
        )
        
        logger.debug(f"Offline execution with k_grid={constrained_params['k_grid_size']}")
        return self.simulation_engine.run_simulation(constrained_params)
    
    def _execute_local(self, parameters: Dict[str, Any]) -> SimulationResult:
        """
        Execute in local mode with full resources
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            SimulationResult
        """
        logger.debug("Local execution with full resources")
        return self.simulation_engine.run_simulation(parameters)
    
    def _execute_hybrid(self, parameters: Dict[str, Any]) -> SimulationResult:
        """
        Execute in hybrid mode - use cloud for large tasks, local otherwise
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            SimulationResult
        """
        hybrid_config = self.execution_config.get('modes', {}).get('hybrid', {})
        cloud_threshold = hybrid_config.get('cloud_threshold_size', 100)
        k_grid = parameters.get('k_grid_size', 32)
        
        # Decide between local and cloud
        if k_grid > cloud_threshold and self._check_internet():
            logger.info(f"Large task (k_grid={k_grid}), attempting cloud execution")
            try:
                return self._execute_cloud(parameters)
            except Exception as e:
                logger.warning(f"Cloud execution failed: {e}, falling back to local")
                if hybrid_config.get('fallback_to_local', True):
                    return self._execute_local(parameters)
                raise
        else:
            logger.debug("Task suitable for local execution")
            return self._execute_local(parameters)
    
    def _execute_cloud(self, parameters: Dict[str, Any]) -> SimulationResult:
        """
        Execute in cloud mode (placeholder - would connect to cloud service)
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            SimulationResult
        """
        cloud_config = self.execution_config.get('modes', {}).get('cloud', {})
        
        if not cloud_config.get('enabled', False):
            raise RuntimeError("Cloud mode is not enabled")
        
        endpoint = cloud_config.get('endpoint')
        if not endpoint:
            raise RuntimeError("Cloud endpoint not configured")
        
        # In real implementation, would send to cloud API
        # For now, fall back to local execution
        logger.warning("Cloud execution not implemented, falling back to local")
        return self._execute_local(parameters)
    
    def _detect_device_type(self) -> str:
        """
        Auto-detect device type for optimization
        
        Returns:
            Device type string
        """
        # Simple heuristic based on config
        # In real implementation, would check system specs
        perf_config = self.config.get('performance', {})
        max_memory = perf_config.get('max_memory_mb', 2048)
        
        if max_memory < 1024:
            return 'raspberry_pi'
        elif max_memory < 4096:
            return 'laptop'
        elif max_memory < 16384:
            return 'desktop'
        else:
            return 'hpc_cluster'
    
    def execute_next_task(self) -> Optional[TaskResult]:
        """
        Execute next task from queue
        
        Returns:
            TaskResult or None if queue is empty
        """
        if self.task_queue.empty():
            return None
        
        task = self.task_queue.get()
        result = self.execute_task(task)
        
        self.completed_tasks.append(result)
        return result
    
    def execute_all_tasks(self) -> List[TaskResult]:
        """
        Execute all tasks in queue
        
        Returns:
            List of TaskResults
        """
        results = []
        while not self.task_queue.empty():
            result = self.execute_next_task()
            if result:
                results.append(result)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'current_mode': self.current_mode.value,
            'internet_available': self.internet_available,
            'queued_tasks': self.task_queue.qsize(),
            'completed_tasks': len(self.completed_tasks),
            'cache_stats': self.cache.get_stats(),
            'advisor_stats': self.advisor.get_stats()
        }
    
    def get_completed_tasks(self) -> List[TaskResult]:
        """Get list of completed tasks"""
        return self.completed_tasks.copy()
    
    def clear_completed_tasks(self):
        """Clear completed tasks history"""
        self.completed_tasks.clear()
        logger.info("Cleared completed tasks history")
