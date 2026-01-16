"""
Reward System for RL-based Prioritization

Calculates rewards based on task execution outcomes and system performance.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TaskOutcome:
    """Represents the outcome of a task execution."""
    task_id: str
    completed: bool
    execution_time: float
    deadline_met: bool
    resource_efficiency: float  # 0.0 - 1.0
    user_satisfaction: float    # 0.0 - 1.0


class RewardCalculator:
    """
    Calculates rewards for reinforcement learning agent.
    
    Rewards are based on multiple factors:
    - Task completion
    - Deadline adherence
    - Resource efficiency
    - User satisfaction
    - System stability
    """
    
    def __init__(
        self,
        completion_weight: float = 1.0,
        deadline_weight: float = 0.8,
        efficiency_weight: float = 0.6,
        satisfaction_weight: float = 0.7,
        stability_weight: float = 0.5
    ):
        """
        Initialize reward calculator.
        
        Args:
            completion_weight: Weight for task completion
            deadline_weight: Weight for deadline adherence
            efficiency_weight: Weight for resource efficiency
            satisfaction_weight: Weight for user satisfaction
            stability_weight: Weight for system stability
        """
        self.completion_weight = completion_weight
        self.deadline_weight = deadline_weight
        self.efficiency_weight = efficiency_weight
        self.satisfaction_weight = satisfaction_weight
        self.stability_weight = stability_weight
        
        # Normalize weights
        total_weight = (
            completion_weight + deadline_weight + efficiency_weight +
            satisfaction_weight + stability_weight
        )
        
        self.completion_weight /= total_weight
        self.deadline_weight /= total_weight
        self.deadline_weight /= total_weight
        self.efficiency_weight /= total_weight
        self.satisfaction_weight /= total_weight
        self.stability_weight /= total_weight
    
    def calculate_reward(
        self,
        outcome: TaskOutcome,
        system_stable: bool = True,
        memory_pressure: float = 0.0,
        cpu_pressure: float = 0.0
    ) -> float:
        """
        Calculate reward for a task outcome.
        
        Args:
            outcome: Task execution outcome
            system_stable: Whether system remained stable
            memory_pressure: Memory pressure (0.0 - 1.0)
            cpu_pressure: CPU pressure (0.0 - 1.0)
            
        Returns:
            Calculated reward value
        """
        reward = 0.0
        
        # Component 1: Task completion
        if outcome.completed:
            reward += self.completion_weight * 10.0
        else:
            reward -= self.completion_weight * 5.0
        
        # Component 2: Deadline adherence
        if outcome.deadline_met:
            reward += self.deadline_weight * 8.0
        else:
            # Penalty proportional to how late
            reward -= self.deadline_weight * 3.0
        
        # Component 3: Resource efficiency
        efficiency_reward = outcome.resource_efficiency * 6.0
        reward += self.efficiency_weight * efficiency_reward
        
        # Component 4: User satisfaction
        satisfaction_reward = outcome.user_satisfaction * 7.0
        reward += self.satisfaction_weight * satisfaction_reward
        
        # Component 5: System stability
        if system_stable:
            reward += self.stability_weight * 5.0
        else:
            reward -= self.stability_weight * 10.0
        
        # Penalties for resource pressure
        pressure_penalty = (memory_pressure + cpu_pressure) * 2.0
        reward -= pressure_penalty
        
        return reward
    
    def calculate_batch_reward(
        self,
        outcomes: list,
        avg_memory_pressure: float = 0.0,
        avg_cpu_pressure: float = 0.0
    ) -> float:
        """
        Calculate reward for a batch of task outcomes.
        
        Args:
            outcomes: List of TaskOutcome objects
            avg_memory_pressure: Average memory pressure
            avg_cpu_pressure: Average CPU pressure
            
        Returns:
            Total reward for the batch
        """
        if not outcomes:
            return 0.0
        
        total_reward = 0.0
        
        for outcome in outcomes:
            reward = self.calculate_reward(
                outcome,
                system_stable=True,
                memory_pressure=avg_memory_pressure,
                cpu_pressure=avg_cpu_pressure
            )
            total_reward += reward
        
        # Bonus for batch efficiency (completing multiple tasks)
        batch_size = len(outcomes)
        if batch_size > 1:
            completed = sum(1 for o in outcomes if o.completed)
            batch_bonus = (completed / batch_size) * 5.0
            total_reward += batch_bonus
        
        return total_reward
    
    def get_reward_breakdown(
        self,
        outcome: TaskOutcome,
        system_stable: bool = True,
        memory_pressure: float = 0.0,
        cpu_pressure: float = 0.0
    ) -> Dict[str, float]:
        """
        Get detailed breakdown of reward components.
        
        Args:
            outcome: Task execution outcome
            system_stable: Whether system remained stable
            memory_pressure: Memory pressure
            cpu_pressure: CPU pressure
            
        Returns:
            Dictionary with reward component breakdown
        """
        components = {}
        
        # Completion component
        if outcome.completed:
            components['completion'] = self.completion_weight * 10.0
        else:
            components['completion'] = -self.completion_weight * 5.0
        
        # Deadline component
        if outcome.deadline_met:
            components['deadline'] = self.deadline_weight * 8.0
        else:
            components['deadline'] = -self.deadline_weight * 3.0
        
        # Efficiency component
        components['efficiency'] = (
            self.efficiency_weight * outcome.resource_efficiency * 6.0
        )
        
        # Satisfaction component
        components['satisfaction'] = (
            self.satisfaction_weight * outcome.user_satisfaction * 7.0
        )
        
        # Stability component
        if system_stable:
            components['stability'] = self.stability_weight * 5.0
        else:
            components['stability'] = -self.stability_weight * 10.0
        
        # Pressure penalty
        components['pressure_penalty'] = -(memory_pressure + cpu_pressure) * 2.0
        
        components['total'] = sum(components.values())
        
        return components
