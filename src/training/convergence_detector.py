"""
Enhanced Convergence Detector V2

Phase-aware loss smoothing with hyperparameter recommendations.
Provides intelligent early stopping and training optimization.
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConvergenceMetrics:
    """Metrics for convergence analysis."""
    epoch: int
    loss: float
    smoothed_loss: float
    loss_delta: float
    phase: str  # 'warmup', 'training', 'plateau', 'converged'
    recommended_action: str  # 'CONTINUE', 'REDUCE_LR', 'EARLY_STOP'
    recommended_lr: Optional[float]
    patience_remaining: int
    improvement_rate: float


class EnhancedConvergenceV2:
    """
    Phase-aware convergence detection with hyperparameter recommendations.
    
    Features:
    - Exponential moving average loss smoothing
    - Training phase detection (warmup, training, plateau, converged)
    - Adaptive patience based on training phase
    - Learning rate recommendations
    - Improvement rate tracking
    
    Example:
        guardian = EnhancedConvergenceV2(initial_patience=10)
        
        for epoch in range(max_epochs):
            loss = train_epoch()
            metrics = guardian.watch(epoch, loss, learning_rate)
            
            if metrics.recommended_action == "REDUCE_LR":
                learning_rate = metrics.recommended_lr
            elif metrics.recommended_action == "EARLY_STOP":
                break
    """
    
    def __init__(
        self,
        initial_patience: int = 10,
        min_delta: float = 1e-4,
        smoothing_alpha: float = 0.3,
        warmup_epochs: int = 5,
        plateau_threshold: float = 1e-5,
    ):
        """
        Initialize convergence detector.
        
        Args:
            initial_patience: Initial patience for early stopping
            min_delta: Minimum change to qualify as improvement
            smoothing_alpha: EMA smoothing factor (0-1)
            warmup_epochs: Number of warmup epochs before monitoring
            plateau_threshold: Threshold for plateau detection
        """
        self.initial_patience = initial_patience
        self.min_delta = min_delta
        self.smoothing_alpha = smoothing_alpha
        self.warmup_epochs = warmup_epochs
        self.plateau_threshold = plateau_threshold
        
        self._loss_history: deque = deque(maxlen=100)
        self._smoothed_loss_history: deque = deque(maxlen=100)
        self._improvement_history: deque = deque(maxlen=20)
        
        self._best_loss: Optional[float] = None
        self._best_epoch: int = 0
        self._patience_counter: int = 0
        self._current_patience: int = initial_patience
        self._current_phase: str = 'warmup'
        
        self._start_time: float = time.time()
        self._last_epoch: int = -1
    
    def watch(
        self,
        epoch: int,
        loss: float,
        learning_rate: float = 0.001,
    ) -> ConvergenceMetrics:
        """
        Monitor training convergence and provide recommendations.
        
        Args:
            epoch: Current epoch number
            loss: Current training/validation loss
            learning_rate: Current learning rate
            
        Returns:
            ConvergenceMetrics with analysis and recommendations
        """
        # Update histories
        self._loss_history.append(loss)
        
        # Calculate smoothed loss using EMA
        if len(self._smoothed_loss_history) == 0:
            smoothed_loss = loss
        else:
            prev_smoothed = self._smoothed_loss_history[-1]
            smoothed_loss = (
                self.smoothing_alpha * loss +
                (1 - self.smoothing_alpha) * prev_smoothed
            )
        
        self._smoothed_loss_history.append(smoothed_loss)
        
        # Calculate loss delta
        if len(self._smoothed_loss_history) >= 2:
            loss_delta = self._smoothed_loss_history[-2] - self._smoothed_loss_history[-1]
        else:
            loss_delta = 0.0
        
        # Update best loss
        is_improvement = False
        if self._best_loss is None or smoothed_loss < self._best_loss - self.min_delta:
            self._best_loss = smoothed_loss
            self._best_epoch = epoch
            is_improvement = True
            self._patience_counter = 0
        else:
            self._patience_counter += 1
        
        # Track improvement rate
        if is_improvement:
            self._improvement_history.append(loss_delta)
        
        # Detect training phase
        phase = self._detect_phase(epoch, smoothed_loss, loss_delta)
        self._current_phase = phase
        
        # Adapt patience based on phase
        self._adapt_patience(phase)
        
        # Calculate improvement rate
        improvement_rate = (
            statistics.mean(self._improvement_history)
            if self._improvement_history else 0.0
        )
        
        # Generate recommendations
        recommended_action, recommended_lr = self._recommend_action(
            epoch, smoothed_loss, loss_delta, learning_rate, phase
        )
        
        self._last_epoch = epoch
        
        return ConvergenceMetrics(
            epoch=epoch,
            loss=loss,
            smoothed_loss=smoothed_loss,
            loss_delta=loss_delta,
            phase=phase,
            recommended_action=recommended_action,
            recommended_lr=recommended_lr,
            patience_remaining=self._current_patience - self._patience_counter,
            improvement_rate=improvement_rate,
        )
    
    def _detect_phase(
        self,
        epoch: int,
        smoothed_loss: float,
        loss_delta: float,
    ) -> str:
        """
        Detect current training phase.
        
        Args:
            epoch: Current epoch
            smoothed_loss: Smoothed loss value
            loss_delta: Recent loss change
            
        Returns:
            Phase name
        """
        # Warmup phase
        if epoch < self.warmup_epochs:
            return 'warmup'
        
        # Not enough history
        if len(self._smoothed_loss_history) < 5:
            return 'training'
        
        # Calculate recent loss variance
        recent_losses = list(self._smoothed_loss_history)[-5:]
        loss_variance = statistics.variance(recent_losses) if len(recent_losses) > 1 else float('inf')
        
        # Converged phase
        if (loss_variance < self.plateau_threshold and
            abs(loss_delta) < self.plateau_threshold and
            self._patience_counter > self._current_patience // 2):
            return 'converged'
        
        # Plateau phase
        if (abs(loss_delta) < self.plateau_threshold * 10 and
            self._patience_counter > 0):
            return 'plateau'
        
        # Active training
        return 'training'
    
    def _adapt_patience(self, phase: str) -> None:
        """
        Adapt patience based on training phase.
        
        Args:
            phase: Current training phase
        """
        if phase == 'warmup':
            # High patience during warmup
            self._current_patience = self.initial_patience * 2
        elif phase == 'training':
            # Normal patience
            self._current_patience = self.initial_patience
        elif phase == 'plateau':
            # Reduced patience on plateau
            self._current_patience = max(3, self.initial_patience // 2)
        elif phase == 'converged':
            # Very low patience when converged
            self._current_patience = 2
    
    def _recommend_action(
        self,
        epoch: int,
        smoothed_loss: float,
        loss_delta: float,
        learning_rate: float,
        phase: str,
    ) -> Tuple[str, Optional[float]]:
        """
        Recommend action based on convergence status.
        
        Args:
            epoch: Current epoch
            smoothed_loss: Smoothed loss
            loss_delta: Recent loss change
            learning_rate: Current learning rate
            phase: Training phase
            
        Returns:
            (action, recommended_lr) tuple
        """
        # Early stop if patience exhausted
        if self._patience_counter >= self._current_patience:
            if phase == 'converged':
                return 'EARLY_STOP', None
            elif phase == 'plateau':
                # On plateau, try reducing LR first
                if learning_rate > 1e-6:
                    return 'REDUCE_LR', learning_rate * 0.5
                else:
                    return 'EARLY_STOP', None
        
        # Recommend LR reduction on plateau
        if phase == 'plateau' and self._patience_counter > self._current_patience // 2:
            if learning_rate > 1e-6:
                return 'REDUCE_LR', learning_rate * 0.7
        
        # Continue training
        return 'CONTINUE', None
    
    def get_summary(self) -> Dict:
        """
        Get training summary.
        
        Returns:
            Dictionary with summary statistics
        """
        elapsed_time = time.time() - self._start_time
        
        return {
            'total_epochs': self._last_epoch + 1,
            'best_loss': self._best_loss,
            'best_epoch': self._best_epoch,
            'current_phase': self._current_phase,
            'elapsed_time': elapsed_time,
            'avg_improvement_rate': (
                statistics.mean(self._improvement_history)
                if self._improvement_history else 0.0
            ),
        }
