"""
Q-Learning Agent for Task Prioritization

Implements Q-learning algorithm for learning optimal task prioritization
strategies through reinforcement learning.
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import pickle


class Action(Enum):
    """Possible prioritization actions."""
    PRIORITY_CRITICAL = 0
    PRIORITY_HIGH = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_LOW = 3
    DEFER = 4
    BATCH = 5


@dataclass
class State:
    """
    State representation for RL agent.
    
    Represents the current system state for decision making.
    """
    memory_usage_ratio: float  # 0.0 - 1.0
    cpu_usage_ratio: float      # 0.0 - 1.0
    queue_depth: int            # Number of pending tasks
    task_urgency: float         # 0.0 - 1.0
    task_complexity: float      # 0.0 - 1.0
    
    def to_discrete(self, bins: int = 5) -> Tuple[int, ...]:
        """
        Convert continuous state to discrete bins for tabular Q-learning.
        
        Args:
            bins: Number of bins per dimension
            
        Returns:
            Tuple of discrete state indices
        """
        def discretize(value: float, bins: int) -> int:
            return min(int(value * bins), bins - 1)
        
        return (
            discretize(self.memory_usage_ratio, bins),
            discretize(self.cpu_usage_ratio, bins),
            min(self.queue_depth // 10, bins - 1),  # Group queue depth
            discretize(self.task_urgency, bins),
            discretize(self.task_complexity, bins)
        )
    
    def to_array(self) -> np.ndarray:
        """Convert state to numpy array."""
        return np.array([
            self.memory_usage_ratio,
            self.cpu_usage_ratio,
            min(self.queue_depth / 100.0, 1.0),  # Normalize queue depth
            self.task_urgency,
            self.task_complexity
        ])


class QLearningAgent:
    """
    Q-Learning agent for task prioritization.
    
    Learns optimal prioritization policy through interaction
    with the environment and reward feedback.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.95,
        epsilon: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        state_bins: int = 5
    ):
        """
        Initialize Q-learning agent.
        
        Args:
            learning_rate: Learning rate (alpha)
            discount_factor: Discount factor (gamma)
            epsilon: Initial exploration rate
            epsilon_decay: Epsilon decay rate
            epsilon_min: Minimum epsilon value
            state_bins: Number of bins for state discretization
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.state_bins = state_bins
        
        # Q-table: state -> action -> value
        # Using dictionary for sparse representation
        self.q_table: Dict[Tuple, np.ndarray] = {}
        
        # Action space
        self.actions = list(Action)
        self.n_actions = len(self.actions)
        
        # Learning statistics
        self.total_updates = 0
        self.episode_rewards: List[float] = []
        self.avg_q_values: List[float] = []
    
    def _get_q_values(self, state: State) -> np.ndarray:
        """
        Get Q-values for a state.
        
        Args:
            state: Current state
            
        Returns:
            Array of Q-values for all actions
        """
        state_key = state.to_discrete(self.state_bins)
        
        if state_key not in self.q_table:
            # Initialize Q-values optimistically
            self.q_table[state_key] = np.zeros(self.n_actions)
        
        return self.q_table[state_key]
    
    def select_action(self, state: State, explore: bool = True) -> Action:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current state
            explore: Whether to use exploration
            
        Returns:
            Selected action
        """
        if explore and np.random.random() < self.epsilon:
            # Explore: random action
            action_idx = np.random.randint(self.n_actions)
        else:
            # Exploit: best action
            q_values = self._get_q_values(state)
            action_idx = np.argmax(q_values)
        
        return self.actions[action_idx]
    
    def update(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
        done: bool = False
    ):
        """
        Update Q-values using Q-learning update rule.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
        """
        state_key = state.to_discrete(self.state_bins)
        action_idx = self.actions.index(action)
        
        # Get current Q-value
        q_values = self._get_q_values(state)
        current_q = q_values[action_idx]
        
        # Get max Q-value for next state
        if done:
            next_max_q = 0.0
        else:
            next_q_values = self._get_q_values(next_state)
            next_max_q = np.max(next_q_values)
        
        # Q-learning update
        td_target = reward + self.discount_factor * next_max_q
        td_error = td_target - current_q
        new_q = current_q + self.learning_rate * td_error
        
        # Update Q-table
        self.q_table[state_key][action_idx] = new_q
        
        # Update statistics
        self.total_updates += 1
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def get_best_action(self, state: State) -> Tuple[Action, float]:
        """
        Get best action and its Q-value for a state.
        
        Args:
            state: Current state
            
        Returns:
            Tuple of (best_action, q_value)
        """
        q_values = self._get_q_values(state)
        best_action_idx = np.argmax(q_values)
        best_q_value = q_values[best_action_idx]
        
        return self.actions[best_action_idx], best_q_value
    
    def record_episode_reward(self, total_reward: float):
        """Record total reward for an episode."""
        self.episode_rewards.append(total_reward)
        
        # Keep recent history
        if len(self.episode_rewards) > 1000:
            self.episode_rewards = self.episode_rewards[-1000:]
    
    def get_policy_stats(self) -> Dict[str, Any]:
        """
        Get statistics about learned policy.
        
        Returns:
            Dictionary of statistics
        """
        if not self.q_table:
            return {
                'states_visited': 0,
                'total_updates': self.total_updates,
                'epsilon': self.epsilon
            }
        
        # Calculate average Q-values
        all_q_values = []
        for q_vals in self.q_table.values():
            all_q_values.extend(q_vals)
        
        avg_q = np.mean(all_q_values) if all_q_values else 0.0
        max_q = np.max(all_q_values) if all_q_values else 0.0
        
        # Recent episode rewards
        recent_rewards = self.episode_rewards[-10:] if self.episode_rewards else []
        avg_recent_reward = np.mean(recent_rewards) if recent_rewards else 0.0
        
        return {
            'states_visited': len(self.q_table),
            'total_updates': self.total_updates,
            'epsilon': self.epsilon,
            'avg_q_value': avg_q,
            'max_q_value': max_q,
            'recent_avg_reward': avg_recent_reward,
            'total_episodes': len(self.episode_rewards)
        }
    
    def save(self, filepath: str):
        """
        Save Q-table to file.
        
        Args:
            filepath: Path to save file
        """
        data = {
            'q_table': self.q_table,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'epsilon': self.epsilon,
            'state_bins': self.state_bins,
            'total_updates': self.total_updates
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str):
        """
        Load Q-table from file.
        
        Args:
            filepath: Path to load file
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.q_table = data['q_table']
        self.learning_rate = data['learning_rate']
        self.discount_factor = data['discount_factor']
        self.epsilon = data['epsilon']
        self.state_bins = data['state_bins']
        self.total_updates = data['total_updates']
    
    def reset_epsilon(self, epsilon: Optional[float] = None):
        """
        Reset epsilon for new learning phase.
        
        Args:
            epsilon: New epsilon value (default: initial value)
        """
        if epsilon is not None:
            self.epsilon = epsilon
        else:
            # Reset to a value between min and max
            self.epsilon = 0.1
