"""
Multi-Level Priority Manager with RL Integration

Manages task prioritization using reinforcement learning for optimal scheduling.
"""

from typing import Dict, Any, List, Optional
from queue import PriorityQueue
import time

from .rl_agent import QLearningAgent, State, Action
from .reward_system import RewardCalculator, TaskOutcome


class Task:
    """Represents a task to be prioritized."""
    
    def __init__(
        self,
        task_id: str,
        urgency: float,
        complexity: float,
        deadline: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.urgency = urgency  # 0.0 - 1.0
        self.complexity = complexity  # 0.0 - 1.0
        self.deadline = deadline
        self.metadata = metadata or {}
        self.priority: Optional[int] = None
        self.created_at = time.time()


class MultiLevelPriorityManager:
    """
    Multi-level priority manager with RL-based optimization.
    
    Uses Q-learning to learn optimal task prioritization strategies.
    """
    
    def __init__(
        self,
        enable_rl: bool = True,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95
    ):
        """
        Initialize priority manager.
        
        Args:
            enable_rl: Enable reinforcement learning
            learning_rate: RL learning rate
            discount_factor: RL discount factor
        """
        self.enable_rl = enable_rl
        
        # RL components
        if enable_rl:
            self.agent = QLearningAgent(
                learning_rate=learning_rate,
                discount_factor=discount_factor
            )
            self.reward_calculator = RewardCalculator()
        else:
            self.agent = None
            self.reward_calculator = None
        
        # Task queues by priority level
        self.queues: Dict[int, PriorityQueue] = {
            0: PriorityQueue(),  # Critical
            1: PriorityQueue(),  # High
            2: PriorityQueue(),  # Medium
            3: PriorityQueue(),  # Low
        }
        
        # Task tracking
        self.pending_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[TaskOutcome] = []
        
        # System metrics
        self.memory_usage_ratio = 0.5
        self.cpu_usage_ratio = 0.5
    
    def update_system_metrics(self, memory_ratio: float, cpu_ratio: float):
        """Update current system resource usage."""
        self.memory_usage_ratio = memory_ratio
        self.cpu_usage_ratio = cpu_ratio
    
    def prioritize_task(self, task: Task) -> int:
        """
        Determine priority level for a task using RL if enabled.
        
        Args:
            task: Task to prioritize
            
        Returns:
            Priority level (0-3)
        """
        if not self.enable_rl or self.agent is None:
            # Fallback: rule-based prioritization
            return self._rule_based_priority(task)
        
        # Create state representation
        state = State(
            memory_usage_ratio=self.memory_usage_ratio,
            cpu_usage_ratio=self.cpu_usage_ratio,
            queue_depth=sum(q.qsize() for q in self.queues.values()),
            task_urgency=task.urgency,
            task_complexity=task.complexity
        )
        
        # Get action from RL agent
        action = self.agent.select_action(state, explore=True)
        
        # Map action to priority level
        priority_map = {
            Action.PRIORITY_CRITICAL: 0,
            Action.PRIORITY_HIGH: 1,
            Action.PRIORITY_MEDIUM: 2,
            Action.PRIORITY_LOW: 3,
            Action.DEFER: 3,
            Action.BATCH: 2
        }
        
        priority = priority_map.get(action, 2)
        return priority
    
    def _rule_based_priority(self, task: Task) -> int:
        """Fallback rule-based prioritization."""
        # Simple urgency-based rules
        if task.urgency >= 0.8:
            return 0  # Critical
        elif task.urgency >= 0.6:
            return 1  # High
        elif task.urgency >= 0.3:
            return 2  # Medium
        else:
            return 3  # Low
    
    def add_task(self, task: Task) -> int:
        """
        Add task to appropriate priority queue.
        
        Args:
            task: Task to add
            
        Returns:
            Assigned priority level
        """
        # Determine priority
        priority = self.prioritize_task(task)
        task.priority = priority
        
        # Add to queue
        self.queues[priority].put((task.created_at, task.task_id, task))
        self.pending_tasks[task.task_id] = task
        
        return priority
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get next task to execute (highest priority).
        
        Returns:
            Next task or None if no tasks available
        """
        # Try queues in priority order
        for priority in sorted(self.queues.keys()):
            queue = self.queues[priority]
            if not queue.empty():
                _, _, task = queue.get()
                return task
        
        return None
    
    def record_outcome(
        self,
        task: Task,
        completed: bool,
        execution_time: float,
        deadline_met: bool = True,
        resource_efficiency: float = 0.8,
        user_satisfaction: float = 0.9
    ):
        """
        Record task execution outcome and update RL agent.
        
        Args:
            task: Executed task
            completed: Whether task completed successfully
            execution_time: Execution time in seconds
            deadline_met: Whether deadline was met
            resource_efficiency: Resource usage efficiency
            user_satisfaction: User satisfaction score
        """
        outcome = TaskOutcome(
            task_id=task.task_id,
            completed=completed,
            execution_time=execution_time,
            deadline_met=deadline_met,
            resource_efficiency=resource_efficiency,
            user_satisfaction=user_satisfaction
        )
        
        self.completed_tasks.append(outcome)
        
        # Remove from pending
        if task.task_id in self.pending_tasks:
            del self.pending_tasks[task.task_id]
        
        # Update RL agent if enabled
        if self.enable_rl and self.agent is not None and self.reward_calculator is not None:
            # Calculate reward
            reward = self.reward_calculator.calculate_reward(
                outcome,
                system_stable=True,
                memory_pressure=self.memory_usage_ratio,
                cpu_pressure=self.cpu_usage_ratio
            )
            
            # Create next state
            next_state = State(
                memory_usage_ratio=self.memory_usage_ratio,
                cpu_usage_ratio=self.cpu_usage_ratio,
                queue_depth=sum(q.qsize() for q in self.queues.values()),
                task_urgency=0.5,  # Default for next state
                task_complexity=0.5
            )
            
            # Note: For proper RL update, we would need to store the previous state and action
            # This is a simplified version
            self.agent.record_episode_reward(reward)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        queue_depths = {
            f'priority_{p}': q.qsize()
            for p, q in self.queues.items()
        }
        
        completed_count = len(self.completed_tasks)
        success_rate = (
            sum(1 for o in self.completed_tasks if o.completed) / completed_count
            if completed_count > 0 else 0.0
        )
        
        stats = {
            'pending_tasks': len(self.pending_tasks),
            'completed_tasks': completed_count,
            'success_rate': success_rate,
            'queue_depths': queue_depths,
            'total_queue_depth': sum(queue_depths.values()),
            'memory_usage_ratio': self.memory_usage_ratio,
            'cpu_usage_ratio': self.cpu_usage_ratio
        }
        
        if self.enable_rl and self.agent is not None:
            stats['rl_stats'] = self.agent.get_policy_stats()
        
        return stats
