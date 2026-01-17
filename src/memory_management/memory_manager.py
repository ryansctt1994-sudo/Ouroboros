"""
Advanced Memory Manager integrating ARIMA and LSTM predictors

Provides intelligent memory management with ensemble prediction,
resource optimization, and adaptive allocation strategies.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from .arima_predictor import ARIMAMemoryPredictor
from .lstm_predictor import LSTMMemoryPredictor


class PredictionStrategy(Enum):
    """Strategy for combining predictions."""
    ARIMA_ONLY = "arima"
    LSTM_ONLY = "lstm"
    ENSEMBLE_AVERAGE = "ensemble_avg"
    ENSEMBLE_WEIGHTED = "ensemble_weighted"
    ADAPTIVE = "adaptive"


class MemoryPressureLevel(Enum):
    """Memory pressure level classification."""
    LOW = 0
    MODERATE = 1
    HIGH = 2
    CRITICAL = 3


class AdvancedMemoryManager:
    """
    Advanced memory manager with predictive analytics.
    
    Integrates ARIMA and LSTM models for memory prediction and provides
    intelligent resource allocation and optimization strategies.
    """
    
    def __init__(
        self,
        max_memory_mb: int = 4096,
        warning_threshold: float = 0.75,
        critical_threshold: float = 0.90,
        prediction_horizon: int = 5,
        strategy: PredictionStrategy = PredictionStrategy.ENSEMBLE_WEIGHTED
    ):
        """
        Initialize Advanced Memory Manager.
        
        Args:
            max_memory_mb: Maximum memory limit (MB)
            warning_threshold: Warning level as fraction of max (default: 0.75)
            critical_threshold: Critical level as fraction of max (default: 0.90)
            prediction_horizon: How many steps ahead to predict
            strategy: Prediction strategy to use
        """
        self.max_memory_mb = max_memory_mb
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.prediction_horizon = prediction_horizon
        self.strategy = strategy
        
        # Initialize predictors
        self.arima_predictor = ARIMAMemoryPredictor(p=3, d=1, q=2, window_size=50)
        self.lstm_predictor = LSTMMemoryPredictor(
            input_size=1,
            hidden_size=32,
            num_layers=2,
            sequence_length=10,
            learning_rate=0.001
        )
        
        # Current state
        self.current_memory_mb: float = 0.0
        self.pressure_level: MemoryPressureLevel = MemoryPressureLevel.LOW
        
        # Prediction metadata
        self.last_predictions: Dict[str, List[float]] = {}
        self.prediction_accuracy: Dict[str, float] = {
            'arima': 1.0,
            'lstm': 1.0
        }
        
        # Allocation history
        self.allocation_history: List[Dict[str, Any]] = []
        
    def update(self, current_memory_mb: float) -> None:
        """
        Update manager with current memory usage.
        
        Args:
            current_memory_mb: Current memory usage in MB
        """
        self.current_memory_mb = current_memory_mb
        
        # Update predictors
        self.arima_predictor.update(current_memory_mb)
        self.lstm_predictor.update(current_memory_mb)
        
        # Perform online LSTM training
        if len(self.lstm_predictor.history) >= self.lstm_predictor.sequence_length:
            self.lstm_predictor.online_update(num_steps=1)
        
        # Update pressure level
        self._update_pressure_level()
        
        # Update prediction accuracy
        self._update_prediction_accuracy()
    
    def _update_pressure_level(self) -> None:
        """Update memory pressure level based on current usage."""
        usage_ratio = self.current_memory_mb / self.max_memory_mb
        
        if usage_ratio >= self.critical_threshold:
            self.pressure_level = MemoryPressureLevel.CRITICAL
        elif usage_ratio >= self.warning_threshold:
            self.pressure_level = MemoryPressureLevel.HIGH
        elif usage_ratio >= 0.5:
            self.pressure_level = MemoryPressureLevel.MODERATE
        else:
            self.pressure_level = MemoryPressureLevel.LOW
    
    def _update_prediction_accuracy(self) -> None:
        """
        Update prediction accuracy scores based on recent predictions.
        
        Compares last predictions with current observed values.
        """
        if not self.last_predictions:
            return
        
        # Calculate error for each predictor
        for predictor_name in ['arima', 'lstm']:
            if predictor_name in self.last_predictions:
                predictions = self.last_predictions[predictor_name]
                if predictions:
                    # Compare first prediction with current value
                    error = abs(predictions[0] - self.current_memory_mb)
                    mape = error / (self.current_memory_mb + 1e-6)  # Mean Absolute Percentage Error
                    
                    # Update accuracy with exponential smoothing
                    accuracy = 1.0 / (1.0 + mape)
                    alpha = 0.3
                    self.prediction_accuracy[predictor_name] = (
                        alpha * accuracy +
                        (1 - alpha) * self.prediction_accuracy[predictor_name]
                    )
    
    def predict(self, steps: Optional[int] = None) -> List[float]:
        """
        Predict future memory usage using configured strategy.
        
        Args:
            steps: Number of steps ahead (default: prediction_horizon)
            
        Returns:
            List of predicted memory values
        """
        if steps is None:
            steps = self.prediction_horizon
        
        # Get predictions from both models
        arima_pred = self.arima_predictor.predict(steps)
        lstm_pred = self.lstm_predictor.predict(steps)
        
        # Store for accuracy tracking
        self.last_predictions['arima'] = arima_pred
        self.last_predictions['lstm'] = lstm_pred
        
        # Combine based on strategy
        if self.strategy == PredictionStrategy.ARIMA_ONLY:
            return arima_pred
        elif self.strategy == PredictionStrategy.LSTM_ONLY:
            return lstm_pred
        elif self.strategy == PredictionStrategy.ENSEMBLE_AVERAGE:
            return [(a + l) / 2.0 for a, l in zip(arima_pred, lstm_pred)]
        elif self.strategy == PredictionStrategy.ENSEMBLE_WEIGHTED:
            # Weight by accuracy
            w_arima = self.prediction_accuracy['arima']
            w_lstm = self.prediction_accuracy['lstm']
            total_weight = w_arima + w_lstm
            
            if total_weight > 0:
                return [
                    (w_arima * a + w_lstm * l) / total_weight
                    for a, l in zip(arima_pred, lstm_pred)
                ]
            else:
                return [(a + l) / 2.0 for a, l in zip(arima_pred, lstm_pred)]
        elif self.strategy == PredictionStrategy.ADAPTIVE:
            # Choose best performing model
            if self.prediction_accuracy['arima'] > self.prediction_accuracy['lstm']:
                return arima_pred
            else:
                return lstm_pred
        
        return arima_pred
    
    def get_confidence_intervals(self, predictions: Optional[List[float]] = None) -> List[Tuple[float, float]]:
        """
        Get confidence intervals for predictions.
        
        Args:
            predictions: Predictions to compute intervals for
            
        Returns:
            List of (lower, upper) bounds
        """
        if predictions is None:
            predictions = self.predict()
        
        # Get intervals from both predictors
        arima_intervals = self.arima_predictor.get_confidence_interval()
        lstm_intervals = self.lstm_predictor.get_confidence_interval(predictions)
        
        # Combine intervals (use wider bounds for safety)
        combined = []
        for i in range(len(predictions)):
            if i < len(arima_intervals) and i < len(lstm_intervals):
                lower = min(arima_intervals[i][0], lstm_intervals[i][0])
                upper = max(arima_intervals[i][1], lstm_intervals[i][1])
                combined.append((lower, upper))
            else:
                combined.append((predictions[i] * 0.9, predictions[i] * 1.1))
        
        return combined
    
    def recommend_allocation(self, requested_mb: float) -> Dict[str, Any]:
        """
        Recommend whether to approve memory allocation request.
        
        Args:
            requested_mb: Requested memory size in MB
            
        Returns:
            Dictionary with recommendation and metadata
        """
        # Predict future usage
        predictions = self.predict()
        next_predicted = predictions[0] if predictions else self.current_memory_mb
        
        # Calculate if allocation would exceed limits
        projected_usage = next_predicted + requested_mb
        usage_ratio = projected_usage / self.max_memory_mb
        
        # Make recommendation
        should_approve = usage_ratio < self.warning_threshold
        
        recommendation = {
            'approve': should_approve,
            'requested_mb': requested_mb,
            'current_memory_mb': self.current_memory_mb,
            'predicted_next_mb': next_predicted,
            'projected_usage_mb': projected_usage,
            'usage_ratio': usage_ratio,
            'pressure_level': self.pressure_level.name,
            'confidence_interval': self.get_confidence_intervals(predictions)[0] if predictions else (0, 0),
            'recommendation': self._get_recommendation_message(should_approve, usage_ratio)
        }
        
        # Log allocation decision
        self.allocation_history.append(recommendation)
        
        return recommendation
    
    def _get_recommendation_message(self, approve: bool, usage_ratio: float) -> str:
        """Generate human-readable recommendation message."""
        if approve:
            if usage_ratio < 0.5:
                return "Safe to allocate - memory pressure is low"
            else:
                return "Allocation approved - monitor memory usage"
        else:
            if usage_ratio >= self.critical_threshold:
                return "CRITICAL: Allocation denied - memory critically low"
            else:
                return "WARNING: Allocation denied - approaching memory limits"
    
    def optimize_resources(self) -> Dict[str, Any]:
        """
        Suggest resource optimization strategies.
        
        Returns:
            Dictionary with optimization recommendations
        """
        predictions = self.predict()
        max_predicted = max(predictions) if predictions else self.current_memory_mb
        
        # Determine if optimization is needed
        needs_optimization = (
            self.pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]
            or max_predicted / self.max_memory_mb > self.warning_threshold
        )
        
        strategies = []
        
        if needs_optimization:
            if self.pressure_level == MemoryPressureLevel.CRITICAL:
                strategies.append({
                    'priority': 'CRITICAL',
                    'action': 'immediate_gc',
                    'description': 'Trigger immediate garbage collection'
                })
                strategies.append({
                    'priority': 'CRITICAL',
                    'action': 'reduce_cache',
                    'description': 'Clear all non-essential caches'
                })
            
            if self.pressure_level == MemoryPressureLevel.HIGH:
                strategies.append({
                    'priority': 'HIGH',
                    'action': 'compact_memory',
                    'description': 'Perform memory compaction'
                })
                strategies.append({
                    'priority': 'HIGH',
                    'action': 'reduce_buffers',
                    'description': 'Reduce buffer sizes'
                })
            
            strategies.append({
                'priority': 'MEDIUM',
                'action': 'defer_allocations',
                'description': 'Defer non-critical allocations'
            })
        
        return {
            'needs_optimization': needs_optimization,
            'pressure_level': self.pressure_level.name,
            'current_usage_ratio': self.current_memory_mb / self.max_memory_mb,
            'max_predicted_usage_ratio': max_predicted / self.max_memory_mb,
            'strategies': strategies
        }
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get comprehensive manager state.
        
        Returns:
            Dictionary containing manager state
        """
        return {
            'current_memory_mb': self.current_memory_mb,
            'max_memory_mb': self.max_memory_mb,
            'usage_ratio': self.current_memory_mb / self.max_memory_mb,
            'pressure_level': self.pressure_level.name,
            'prediction_strategy': self.strategy.value,
            'prediction_accuracy': self.prediction_accuracy.copy(),
            'arima_state': self.arima_predictor.get_state(),
            'lstm_state': self.lstm_predictor.get_state(),
            'recent_allocations': len(self.allocation_history),
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold
        }
