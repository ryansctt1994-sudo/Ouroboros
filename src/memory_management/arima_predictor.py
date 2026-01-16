"""
ARIMA-based Memory Prediction Module

Implements Auto-Regressive Integrated Moving Average model for time-series
memory usage prediction and forecasting.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from collections import deque


class ARIMAMemoryPredictor:
    """
    ARIMA predictor for memory usage forecasting.
    
    Uses (p, d, q) parameters:
    - p: Auto-regressive order
    - d: Differencing order
    - q: Moving average order
    """
    
    def __init__(self, p: int = 3, d: int = 1, q: int = 2, window_size: int = 50):
        """
        Initialize ARIMA predictor.
        
        Args:
            p: Auto-regressive order (default: 3)
            d: Differencing order (default: 1)
            q: Moving average order (default: 2)
            window_size: Maximum history window size
        """
        self.p = p
        self.d = d
        self.q = q
        self.window_size = window_size
        
        # Time series data storage
        self.history: deque = deque(maxlen=window_size)
        self.residuals: deque = deque(maxlen=q)
        
        # Model parameters (learned online)
        self.ar_coefficients: Optional[np.ndarray] = None
        self.ma_coefficients: Optional[np.ndarray] = None
        
        # Statistics for normalization
        self.mean: float = 0.0
        self.std: float = 1.0
        
        # Prediction metadata
        self.predictions: List[float] = []
        self.confidence_intervals: List[Tuple[float, float]] = []
        
    def update(self, memory_value: float) -> None:
        """
        Update the model with new memory observation.
        
        Args:
            memory_value: Current memory usage (MB)
        """
        self.history.append(memory_value)
        
        # Update statistics
        if len(self.history) > 1:
            values = np.array(self.history)
            self.mean = np.mean(values)
            self.std = np.std(values) if np.std(values) > 1e-6 else 1.0
    
    def _difference(self, data: np.ndarray, order: int) -> np.ndarray:
        """Apply differencing to make series stationary."""
        result = data.copy()
        for _ in range(order):
            if len(result) > 1:
                result = np.diff(result)
        return result
    
    def _fit_ar_coefficients(self, data: np.ndarray) -> np.ndarray:
        """
        Fit auto-regressive coefficients using least squares.
        
        Args:
            data: Stationary time series data
            
        Returns:
            AR coefficients
        """
        if len(data) <= self.p:
            return np.zeros(self.p)
        
        # Build design matrix for AR(p)
        X = []
        y = []
        
        for i in range(self.p, len(data)):
            X.append(data[i-self.p:i][::-1])
            y.append(data[i])
        
        X = np.array(X)
        y = np.array(y)
        
        # Solve least squares: X @ coeffs = y
        if len(X) > 0:
            try:
                coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
                return coeffs
            except np.linalg.LinAlgError:
                return np.zeros(self.p)
        
        return np.zeros(self.p)
    
    def predict(self, steps: int = 1) -> List[float]:
        """
        Predict future memory usage.
        
        Args:
            steps: Number of steps to predict ahead
            
        Returns:
            List of predicted memory values (MB)
        """
        if len(self.history) < max(self.p, self.q):
            # Not enough data, return last value or mean
            if len(self.history) > 0:
                return [self.history[-1]] * steps
            return [self.mean] * steps
        
        # Normalize data
        data = np.array(self.history)
        normalized = (data - self.mean) / self.std
        
        # Apply differencing
        stationary = self._difference(normalized, self.d)
        
        if len(stationary) < self.p:
            return [self.history[-1]] * steps
        
        # Fit AR coefficients
        self.ar_coefficients = self._fit_ar_coefficients(stationary)
        
        # Initialize MA coefficients (simplified: exponential decay)
        if self.ma_coefficients is None:
            self.ma_coefficients = np.array([0.5 ** (i+1) for i in range(self.q)])
        
        predictions = []
        current_series = list(stationary)
        
        for _ in range(steps):
            # AR component
            ar_pred = 0.0
            if len(current_series) >= self.p:
                ar_terms = np.array(current_series[-self.p:][::-1])
                ar_pred = np.dot(self.ar_coefficients, ar_terms)
            
            # MA component (using recent residuals)
            ma_pred = 0.0
            if len(self.residuals) > 0:
                ma_terms = np.array(list(self.residuals)[-self.q:][::-1])
                ma_coeffs = self.ma_coefficients[:len(ma_terms)]
                ma_pred = np.dot(ma_coeffs, ma_terms)
            
            # Combined prediction
            next_val = ar_pred + ma_pred
            current_series.append(next_val)
            
            # Calculate residual (for MA component)
            residual = 0.0  # Simplified: assume zero residual for future
            self.residuals.append(residual)
        
        # Reverse differencing (integration)
        predictions_stationary = current_series[-steps:]
        
        # Simplified reverse differencing: add back the drift
        if len(data) > 0:
            last_normalized = normalized[-1]
            integrated = []
            current = last_normalized
            
            for pred in predictions_stationary:
                current = current + pred
                integrated.append(current)
            
            predictions_stationary = integrated
        
        # Denormalize
        predictions = [p * self.std + self.mean for p in predictions_stationary]
        
        # Ensure non-negative memory predictions
        predictions = [max(0.0, p) for p in predictions]
        
        self.predictions = predictions
        return predictions
    
    def get_confidence_interval(self, alpha: float = 0.05) -> List[Tuple[float, float]]:
        """
        Calculate confidence intervals for predictions.
        
        Args:
            alpha: Significance level (default: 0.05 for 95% CI)
            
        Returns:
            List of (lower, upper) confidence bounds
        """
        if not self.predictions:
            return []
        
        # Simplified confidence interval using historical std
        z_score = 1.96  # 95% confidence
        margin = z_score * self.std
        
        intervals = []
        for pred in self.predictions:
            lower = max(0.0, pred - margin)
            upper = pred + margin
            intervals.append((lower, upper))
        
        self.confidence_intervals = intervals
        return intervals
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current predictor state.
        
        Returns:
            Dictionary containing predictor state
        """
        return {
            'p': self.p,
            'd': self.d,
            'q': self.q,
            'window_size': self.window_size,
            'history_length': len(self.history),
            'mean': self.mean,
            'std': self.std,
            'last_value': self.history[-1] if self.history else None,
            'ar_coefficients': self.ar_coefficients.tolist() if self.ar_coefficients is not None else None
        }
