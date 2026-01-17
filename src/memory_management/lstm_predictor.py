"""
LSTM-based Memory Prediction Module

Implements Long Short-Term Memory neural network for sophisticated
memory usage prediction with sequence learning.
"""

import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from collections import deque


class LSTMCell:
    """
    Single LSTM cell implementation for memory prediction.
    
    Implements forget gate, input gate, and output gate.
    """
    
    def __init__(self, input_size: int, hidden_size: int):
        """
        Initialize LSTM cell.
        
        Args:
            input_size: Size of input features
            hidden_size: Size of hidden state
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Initialize weights with Xavier initialization
        scale = np.sqrt(2.0 / (input_size + hidden_size))
        
        # Forget gate weights
        self.W_f = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.b_f = np.zeros(hidden_size)
        
        # Input gate weights
        self.W_i = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.b_i = np.zeros(hidden_size)
        
        # Cell state weights
        self.W_c = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.b_c = np.zeros(hidden_size)
        
        # Output gate weights
        self.W_o = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.b_o = np.zeros(hidden_size)
        
        # Hidden state and cell state
        self.h = np.zeros(hidden_size)
        self.c = np.zeros(hidden_size)
    
    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))
    
    @staticmethod
    def tanh(x: np.ndarray) -> np.ndarray:
        """Tanh activation function."""
        return np.tanh(np.clip(x, -500, 500))
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass through LSTM cell.
        
        Args:
            x: Input vector
            
        Returns:
            Hidden state output
        """
        # Concatenate input and previous hidden state
        combined = np.concatenate([x, self.h])
        
        # Forget gate
        f_t = self.sigmoid(self.W_f @ combined + self.b_f)
        
        # Input gate
        i_t = self.sigmoid(self.W_i @ combined + self.b_i)
        
        # Candidate cell state
        c_tilde = self.tanh(self.W_c @ combined + self.b_c)
        
        # Update cell state
        self.c = f_t * self.c + i_t * c_tilde
        
        # Output gate
        o_t = self.sigmoid(self.W_o @ combined + self.b_o)
        
        # Update hidden state
        self.h = o_t * self.tanh(self.c)
        
        return self.h
    
    def reset_state(self):
        """Reset hidden and cell states."""
        self.h = np.zeros(self.hidden_size)
        self.c = np.zeros(self.hidden_size)


class LSTMMemoryPredictor:
    """
    LSTM-based memory predictor for sophisticated pattern learning.
    
    Uses stacked LSTM cells with online learning capabilities.
    """
    
    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 32,
        num_layers: int = 2,
        sequence_length: int = 10,
        learning_rate: float = 0.001
    ):
        """
        Initialize LSTM predictor.
        
        Args:
            input_size: Number of input features (default: 1 for memory value)
            hidden_size: Size of LSTM hidden states
            num_layers: Number of stacked LSTM layers
            sequence_length: Length of input sequences
            learning_rate: Learning rate for online updates
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.sequence_length = sequence_length
        self.learning_rate = learning_rate
        
        # Create stacked LSTM cells
        self.lstm_cells: List[LSTMCell] = []
        for i in range(num_layers):
            in_size = input_size if i == 0 else hidden_size
            cell = LSTMCell(in_size, hidden_size)
            self.lstm_cells.append(cell)
        
        # Output layer
        self.W_out = np.random.randn(1, hidden_size) * 0.01
        self.b_out = np.zeros(1)
        
        # Data storage
        self.history: deque = deque(maxlen=1000)
        self.sequences: deque = deque(maxlen=100)
        
        # Normalization parameters
        self.mean: float = 0.0
        self.std: float = 1.0
        
        # Training statistics
        self.loss_history: List[float] = []
        
    def update(self, memory_value: float) -> None:
        """
        Update predictor with new memory observation.
        
        Args:
            memory_value: Current memory usage (MB)
        """
        self.history.append(memory_value)
        
        # Update normalization statistics
        if len(self.history) > 1:
            values = np.array(self.history)
            self.mean = np.mean(values)
            self.std = np.std(values) if np.std(values) > 1e-6 else 1.0
        
        # Create training sequences
        if len(self.history) >= self.sequence_length + 1:
            sequence = list(self.history)[-self.sequence_length-1:]
            self.sequences.append(sequence)
    
    def _normalize(self, value: float) -> float:
        """Normalize value using mean and std."""
        return (value - self.mean) / self.std
    
    def _denormalize(self, value: float) -> float:
        """Denormalize value back to original scale."""
        return value * self.std + self.mean
    
    def _forward_sequence(self, sequence: List[float]) -> float:
        """
        Forward pass through LSTM network.
        
        Args:
            sequence: Input sequence
            
        Returns:
            Predicted next value (normalized)
        """
        # Reset LSTM states
        for cell in self.lstm_cells:
            cell.reset_state()
        
        # Process sequence
        for val in sequence:
            # Normalize input
            x = np.array([self._normalize(val)])
            
            # Forward through LSTM layers
            h = x
            for cell in self.lstm_cells:
                h = cell.forward(h)
        
        # Output layer
        prediction = self.W_out @ h + self.b_out
        return prediction[0]
    
    def train_step(self) -> Optional[float]:
        """
        Perform one training step using recent sequences.
        
        Returns:
            Training loss if performed, None otherwise
        """
        if len(self.sequences) < 1:
            return None
        
        # Sample a recent sequence
        seq_with_target = list(self.sequences[-1])
        sequence = seq_with_target[:-1]
        target = seq_with_target[-1]
        
        # Forward pass
        prediction_norm = self._forward_sequence(sequence)
        prediction = self._denormalize(prediction_norm)
        
        # Calculate loss (MSE)
        error = prediction - target
        loss = 0.5 * error ** 2
        
        # Simplified gradient descent (update output layer only for efficiency)
        # In full implementation, would use BPTT (backpropagation through time)
        output_grad = error * self.learning_rate
        
        # Get last hidden state
        last_h = self.lstm_cells[-1].h
        
        # Update output weights
        self.W_out -= output_grad * last_h.reshape(1, -1)
        self.b_out -= output_grad
        
        self.loss_history.append(loss)
        return loss
    
    def predict(self, steps: int = 1) -> List[float]:
        """
        Predict future memory usage.
        
        Args:
            steps: Number of steps to predict ahead
            
        Returns:
            List of predicted memory values (MB)
        """
        if len(self.history) < self.sequence_length:
            # Not enough data
            if len(self.history) > 0:
                return [self.history[-1]] * steps
            return [self.mean] * steps
        
        predictions = []
        current_sequence = list(self.history)[-self.sequence_length:]
        
        for _ in range(steps):
            # Predict next value
            pred_norm = self._forward_sequence(current_sequence)
            pred = self._denormalize(pred_norm)
            
            # Ensure non-negative
            pred = max(0.0, pred)
            predictions.append(pred)
            
            # Update sequence for next prediction
            current_sequence = current_sequence[1:] + [pred]
        
        return predictions
    
    def get_confidence_interval(
        self,
        predictions: Optional[List[float]] = None,
        alpha: float = 0.05
    ) -> List[Tuple[float, float]]:
        """
        Calculate confidence intervals for predictions.
        
        Args:
            predictions: Predictions to compute intervals for
            alpha: Significance level
            
        Returns:
            List of (lower, upper) confidence bounds
        """
        if predictions is None:
            predictions = self.predict(1)
        
        # Use recent prediction variance as uncertainty estimate
        if len(self.loss_history) > 0:
            recent_losses = list(self.loss_history)[-10:]
            rmse = np.sqrt(np.mean(recent_losses))
        else:
            rmse = self.std * 0.1
        
        z_score = 1.96  # 95% confidence
        margin = z_score * rmse
        
        intervals = []
        for pred in predictions:
            lower = max(0.0, pred - margin)
            upper = pred + margin
            intervals.append((lower, upper))
        
        return intervals
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current predictor state.
        
        Returns:
            Dictionary containing predictor state
        """
        return {
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers,
            'sequence_length': self.sequence_length,
            'history_length': len(self.history),
            'mean': self.mean,
            'std': self.std,
            'last_value': self.history[-1] if self.history else None,
            'recent_loss': self.loss_history[-1] if self.loss_history else None,
            'total_sequences': len(self.sequences)
        }
    
    def online_update(self, num_steps: int = 5) -> List[float]:
        """
        Perform online learning updates.
        
        Args:
            num_steps: Number of training steps
            
        Returns:
            List of losses from training steps
        """
        losses = []
        for _ in range(num_steps):
            loss = self.train_step()
            if loss is not None:
                losses.append(loss)
        return losses
