"""
Quantum Adapter Module

Provides quantum computing integration for ECS,
enabling quantum state manipulation and entanglement.
"""

import numpy as np
from typing import List, Optional, Tuple
import cmath


class QuantumState:
    """Represents a quantum state in the ECS."""
    
    def __init__(self, amplitudes: np.ndarray):
        """
        Initialize a quantum state.
        
        Args:
            amplitudes: Complex amplitudes for the quantum state
        """
        self.amplitudes = np.array(amplitudes, dtype=complex)
        self._normalize()
        
    def _normalize(self) -> None:
        """Normalize the quantum state."""
        norm = np.sqrt(np.sum(np.abs(self.amplitudes) ** 2))
        if norm > 0:
            self.amplitudes = self.amplitudes / norm
    
    def measure(self) -> int:
        """
        Measure the quantum state, collapsing to a classical state.
        
        Returns:
            Index of the measured state
        """
        probabilities = np.abs(self.amplitudes) ** 2
        return np.random.choice(len(self.amplitudes), p=probabilities)
    
    def get_probability(self, index: int) -> float:
        """Get the probability of measuring a specific state."""
        if 0 <= index < len(self.amplitudes):
            return float(np.abs(self.amplitudes[index]) ** 2)
        return 0.0


class QuantumAdapter:
    """
    Adapter for quantum operations in the ECS.
    
    Provides quantum state management, gate operations, and entanglement
    for consciousness computation.
    """
    
    def __init__(self, num_qubits: int = 3):
        """
        Initialize the quantum adapter.
        
        Args:
            num_qubits: Number of qubits to simulate
        """
        self.num_qubits = num_qubits
        self.dimension = 2 ** num_qubits
        self.state: Optional[QuantumState] = None
        self.reset()
        
    def reset(self) -> None:
        """Reset to |0...0⟩ state."""
        amplitudes = np.zeros(self.dimension, dtype=complex)
        amplitudes[0] = 1.0
        self.state = QuantumState(amplitudes)
    
    def apply_hadamard(self, qubit_index: int) -> None:
        """
        Apply Hadamard gate to a specific qubit.
        
        Args:
            qubit_index: Index of the qubit (0-based)
        """
        if qubit_index >= self.num_qubits:
            raise ValueError(f"Qubit index {qubit_index} out of range")
        
        # Hadamard matrix
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        
        # Apply to full state
        new_amplitudes = np.zeros_like(self.state.amplitudes)
        for i in range(self.dimension):
            bit = (i >> qubit_index) & 1
            i_flipped = i ^ (1 << qubit_index)
            
            new_amplitudes[i] += H[bit, 0] * self.state.amplitudes[i & ~(1 << qubit_index)]
            new_amplitudes[i] += H[bit, 1] * self.state.amplitudes[i_flipped & ~(1 << qubit_index) | (1 << qubit_index)]
        
        self.state.amplitudes = new_amplitudes
        self.state._normalize()
    
    def apply_phase_gate(self, qubit_index: int, phase: float) -> None:
        """
        Apply phase gate to a specific qubit.
        
        Args:
            qubit_index: Index of the qubit (0-based)
            phase: Phase angle in radians
        """
        if qubit_index >= self.num_qubits:
            raise ValueError(f"Qubit index {qubit_index} out of range")
        
        phase_factor = cmath.exp(1j * phase)
        
        for i in range(self.dimension):
            if (i >> qubit_index) & 1:
                self.state.amplitudes[i] *= phase_factor
    
    def entangle(self, qubit1: int, qubit2: int) -> None:
        """
        Create entanglement between two qubits using CNOT.
        
        Args:
            qubit1: Control qubit index
            qubit2: Target qubit index
        """
        if qubit1 >= self.num_qubits or qubit2 >= self.num_qubits:
            raise ValueError("Qubit indices out of range")
        
        new_amplitudes = self.state.amplitudes.copy()
        
        for i in range(self.dimension):
            if (i >> qubit1) & 1:  # Control qubit is 1
                # Flip target qubit
                i_flipped = i ^ (1 << qubit2)
                new_amplitudes[i], new_amplitudes[i_flipped] = \
                    self.state.amplitudes[i_flipped], self.state.amplitudes[i]
        
        self.state.amplitudes = new_amplitudes
    
    def measure(self, qubit_index: Optional[int] = None) -> int:
        """
        Measure the quantum state.
        
        Args:
            qubit_index: Specific qubit to measure, or None for full state
            
        Returns:
            Measurement result
        """
        if qubit_index is None:
            return self.state.measure()
        
        # Measure specific qubit
        prob_0 = sum(
            self.state.get_probability(i)
            for i in range(self.dimension)
            if not ((i >> qubit_index) & 1)
        )
        
        return 0 if np.random.random() < prob_0 else 1
    
    def get_entanglement_entropy(self, subsystem_qubits: List[int]) -> float:
        """
        Calculate entanglement entropy of a subsystem.
        
        Args:
            subsystem_qubits: List of qubit indices for the subsystem
            
        Returns:
            Von Neumann entropy
        """
        # Simplified calculation - trace over complement qubits
        # This is a placeholder for full density matrix calculation
        probabilities = np.abs(self.state.amplitudes) ** 2
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return float(entropy)
