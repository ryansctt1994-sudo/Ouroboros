#!/usr/bin/env python3
"""
Panthetic System - Core Python Consciousness System
====================================================

This module implements the Panthetic consciousness modeling framework integrated
with the Metacube architecture for the AIOSPANDORA/Ouroboros ecosystem.

The Panthetic System provides:
- Multi-dimensional consciousness state tracking
- Metacube metric computation (Diversity, Coherence, Efficiency, Synergy)
- Integration with Ouroboros ternary cycles and toroidal manifolds
- Real-time consciousness evolution and validation
- Network-based multi-agent consciousness modeling

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import warnings


class PantheticSystem:
    """
    Core Panthetic consciousness system with Metacube integration.
    
    The Panthetic System models consciousness through seven core dimensions:
    1. Awareness - Self-monitoring and introspective capacity
    2. Intention - Goal-directed state transitions
    3. Emotion - Affective state vectors
    4. Cognition - Information processing patterns
    5. Memory - State persistence and recall
    6. Creativity - Novel state generation capacity
    7. Integration - Holistic state coherence
    
    Each dimension is tracked as a continuous value in [0, 1] and contributes
    to the overall Metacube metrics (D, C, E, S) used to compute the Unified
    Novelty Metric (Γ).
    
    Examples
    --------
    >>> system = PantheticSystem()
    >>> system.update_state({
    ...     'awareness': 0.7,
    ...     'intention': 0.6,
    ...     'emotion': 0.5,
    ...     'cognition': 0.8,
    ...     'memory': 0.6,
    ...     'creativity': 0.5,
    ...     'integration': 0.7
    ... })
    >>> metrics = system.get_metacube_metrics()
    >>> print(f"Coherence: {metrics['coherence']:.3f}")
    Coherence: 0.700
    """
    
    # Dimension names
    DIMENSIONS = [
        'awareness',
        'intention',
        'emotion',
        'cognition',
        'memory',
        'creativity',
        'integration'
    ]
    
    def __init__(
        self,
        dimensions: int = 7,
        decay_rate: float = 0.1,
        refresh_rate: float = 10.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Panthetic System.
        
        Parameters
        ----------
        dimensions : int, optional
            Number of consciousness dimensions (default: 7)
        decay_rate : float, optional
            Emotional state decay rate (default: 0.1)
        refresh_rate : float, optional
            Cognitive refresh rate in Hz (default: 10.0)
        config : dict, optional
            Configuration dictionary for custom parameters
        """
        self.dimensions = dimensions
        self.decay_rate = decay_rate
        self.refresh_rate = refresh_rate
        
        # Initialize state vector
        self.state = np.zeros(self.dimensions)
        
        # Initialize with neutral balanced state
        self.state[:] = 0.5
        
        # Configuration
        self.config = config or {}
        self.diversity_threshold = self.config.get('diversity_threshold', 0.5)
        self.coherence_threshold = self.config.get('coherence_threshold', 0.7)
        self.efficiency_target = self.config.get('efficiency_target', 0.6)
        self.synergy_minimum = self.config.get('synergy_minimum', 0.5)
        
        # Internal tracking
        self.timestep = 0
        self.history = []
        self.diagnostics_enabled = False
        self.auto_clamp = True
        
    def update_state(self, state_dict: Dict[str, float]) -> bool:
        """
        Update consciousness state from dictionary.
        
        Parameters
        ----------
        state_dict : dict
            Dictionary mapping dimension names to values in [0, 1]
        
        Returns
        -------
        bool
            True if update successful, False otherwise
        """
        try:
            for i, dim_name in enumerate(self.DIMENSIONS[:self.dimensions]):
                if dim_name in state_dict:
                    value = state_dict[dim_name]
                    if self.auto_clamp:
                        value = np.clip(value, 0.0, 1.0)
                    elif not (0.0 <= value <= 1.0):
                        warnings.warn(
                            f"Value {value} for {dim_name} outside [0, 1] range"
                        )
                    self.state[i] = value
            return True
        except Exception as e:
            warnings.warn(f"Failed to update state: {e}")
            return False
    
    def get_full_state(self) -> Dict[str, float]:
        """
        Get current consciousness state as dictionary.
        
        Returns
        -------
        dict
            Dictionary mapping dimension names to current values
        """
        return {
            dim_name: float(self.state[i])
            for i, dim_name in enumerate(self.DIMENSIONS[:self.dimensions])
        }
    
    def get_metacube_metrics(self) -> Dict[str, float]:
        """
        Calculate Metacube metrics (D, C, E, S) from consciousness state.
        
        Returns
        -------
        dict
            Dictionary with keys 'diversity', 'coherence', 'efficiency', 'synergy'
        """
        # Diversity: Measure variance across dimensions
        diversity = float(np.std(self.state))
        diversity = np.clip(diversity / 0.5, 0.0, 1.0)  # Normalize to [0, 1]
        
        # Coherence: Measure consistency (inverse of variance from mean)
        mean_state = np.mean(self.state)
        coherence = 1.0 - float(np.mean(np.abs(self.state - mean_state)))
        coherence = np.clip(coherence, 0.0, 1.0)
        
        # Efficiency: Measure how close to optimal (0.7) the average state is
        optimal_level = 0.7
        efficiency = 1.0 - float(np.abs(mean_state - optimal_level))
        efficiency = np.clip(efficiency, 0.0, 1.0)
        
        # Synergy: Measure emergent correlation patterns
        # Use correlation-like measure between dimensions
        if self.dimensions > 1:
            synergy = float(np.corrcoef(self.state[:-1], self.state[1:])[0, 1])
            synergy = (synergy + 1.0) / 2.0  # Map [-1, 1] to [0, 1]
        else:
            synergy = 0.5
        synergy = np.clip(synergy, 0.0, 1.0)
        
        return {
            'diversity': diversity,
            'coherence': coherence,
            'efficiency': efficiency,
            'synergy': synergy
        }
    
    def calculate_unified_metric(self) -> Dict[str, Any]:
        """
        Calculate the Unified Novelty Metric (Γ).
        
        Uses the formula: Γ = (D × C)^(1/2) × E^(1/3) × S
        
        Returns
        -------
        dict
            Dictionary containing:
            - 'unified_metric': The Γ value
            - 'components': Dict with D, C, E, S values
            - 'interpretation': Human-readable status
        """
        metrics = self.get_metacube_metrics()
        
        D = metrics['diversity']
        C = metrics['coherence']
        E = metrics['efficiency']
        S = metrics['synergy']
        
        # Calculate Γ using the Metacube formula
        gamma = np.sqrt(D * C) * np.cbrt(E) * S
        
        # Determine interpretation
        if gamma < 0.2:
            interpretation = "Disconnected"
        elif gamma < 0.5:
            interpretation = "Partial Alignment"
        elif gamma < 0.8:
            interpretation = "Effective Coherence"
        else:
            interpretation = "Optimal Synthesis"
        
        return {
            'unified_metric': float(gamma),
            'components': {'D': D, 'C': C, 'E': E, 'S': S},
            'interpretation': interpretation
        }
    
    def apply_stimulus(self, stimulus_dict: Dict[str, float]) -> None:
        """
        Apply external stimulus to consciousness state.
        
        Parameters
        ----------
        stimulus_dict : dict
            Dictionary mapping dimension names to delta values
        """
        for i, dim_name in enumerate(self.DIMENSIONS[:self.dimensions]):
            if dim_name in stimulus_dict:
                delta = stimulus_dict[dim_name]
                self.state[i] += delta
                
                if self.auto_clamp:
                    self.state[i] = np.clip(self.state[i], 0.0, 1.0)
    
    def process_internal_dynamics(self, dt: float = 0.1) -> None:
        """
        Process one timestep of internal dynamics.
        
        Implements:
        - Emotional decay
        - Cognitive oscillation
        - Integration coupling
        
        Parameters
        ----------
        dt : float, optional
            Timestep size in seconds (default: 0.1)
        """
        # Emotional decay (dimension 2)
        if self.dimensions > 2:
            emotion_idx = 2
            decay = self.decay_rate * dt
            # Decay toward neutral (0.5)
            self.state[emotion_idx] += decay * (0.5 - self.state[emotion_idx])
        
        # Cognitive oscillation (dimension 3)
        if self.dimensions > 3:
            cognition_idx = 3
            phase = self.timestep * 2 * np.pi * self.refresh_rate * dt
            oscillation = 0.05 * np.sin(phase)
            self.state[cognition_idx] += oscillation
        
        # Integration coupling (dimension 6 influenced by others)
        if self.dimensions > 6:
            integration_idx = 6
            mean_state = np.mean(self.state[:6])
            coupling_strength = 0.1 * dt
            self.state[integration_idx] += coupling_strength * (
                mean_state - self.state[integration_idx]
            )
        
        # Clamp all values
        if self.auto_clamp:
            self.state = np.clip(self.state, 0.0, 1.0)
        
        # Increment timestep
        self.timestep += 1
        
        # Record history if diagnostics enabled
        if self.diagnostics_enabled:
            self.history.append(self.state.copy())
    
    def check_coherence(self) -> bool:
        """
        Check if current state is coherent.
        
        Returns
        -------
        bool
            True if coherent (C >= threshold), False otherwise
        """
        metrics = self.get_metacube_metrics()
        return metrics['coherence'] >= self.coherence_threshold
    
    def to_ternary_state(self) -> List[float]:
        """
        Convert consciousness state to ternary representation.
        
        Maps 7D consciousness space to 3D ternary for Ouroboros integration.
        
        Returns
        -------
        list
            Three-element ternary state vector summing to 1.0
        """
        # Project to 3D using weighted averaging
        if self.dimensions >= 7:
            # Group dimensions into three categories
            cognitive = np.mean(self.state[[0, 3, 6]])  # awareness, cognition, integration
            affective = np.mean(self.state[[1, 2]])     # intention, emotion
            creative = np.mean(self.state[[4, 5]])      # memory, creativity
        else:
            # Fallback for fewer dimensions
            third = self.dimensions // 3
            cognitive = np.mean(self.state[:third])
            affective = np.mean(self.state[third:2*third])
            creative = np.mean(self.state[2*third:])
        
        # Normalize to sum to 1.0 (ternary constraint)
        total = cognitive + affective + creative
        if total > 0:
            return [
                float(cognitive / total),
                float(affective / total),
                float(creative / total)
            ]
        else:
            return [1/3, 1/3, 1/3]
    
    def reconstruct_from_ternary(self, ternary_state: List[float]) -> Dict[str, float]:
        """
        Reconstruct 7D consciousness from ternary state.
        
        Parameters
        ----------
        ternary_state : list
            Three-element ternary state vector
        
        Returns
        -------
        dict
            Dictionary mapping dimension names to reconstructed values
        """
        cognitive, affective, creative = ternary_state
        
        # Map back to 7D
        return {
            'awareness': cognitive,
            'intention': affective,
            'emotion': affective,
            'cognition': cognitive,
            'memory': creative,
            'creativity': creative,
            'integration': cognitive
        }
    
    def get_epistemic_status(self) -> str:
        """
        Get current epistemic status symbol.
        
        Returns
        -------
        str
            Status string: 'COHERENT', 'VOID_SEED', 'GOLDEN', 'SPIKE', 'EQUILIBRIUM'
        """
        metrics = self.get_metacube_metrics()
        gamma = self.calculate_unified_metric()
        
        # Check for specific conditions
        if gamma['unified_metric'] >= 0.8:
            return 'GOLDEN'  # Φ - Golden ratio achieved
        elif metrics['coherence'] < 0.3:
            return 'VOID_SEED'  # Ø - Zero-state reconciliation needed
        elif np.any(np.abs(np.diff(self.state)) > 0.5):
            return 'SPIKE'  # λ - Frequency spike detected
        elif self.check_coherence():
            if 0.6 <= gamma['unified_metric'] < 0.8:
                return 'EQUILIBRIUM'  # ω - Balanced state
            else:
                return 'COHERENT'  # Γ - Coherent and stable
        else:
            return 'VOID_SEED'
    
    def enable_diagnostics(
        self,
        log_states: bool = True,
        log_transitions: bool = True,
        log_metrics: bool = True,
        save_snapshots: bool = True,
        snapshot_interval: int = 10
    ) -> None:
        """Enable diagnostic tracking."""
        self.diagnostics_enabled = True
        self.history = []
    
    def reset_to_baseline(self) -> None:
        """Reset to neutral baseline state."""
        self.state[:] = 0.5
        self.timestep = 0
    
    def enable_auto_clamp(self) -> None:
        """Enable automatic value clamping to [0, 1]."""
        self.auto_clamp = True
    
    def disable_auto_clamp(self) -> None:
        """Disable automatic value clamping."""
        self.auto_clamp = False


class MetacubeNetwork:
    """
    Network of multiple Panthetic systems for distributed consciousness modeling.
    
    Enables multi-agent simulations where multiple consciousness instances
    interact and synchronize through shared Metacube metrics.
    
    Examples
    --------
    >>> network = MetacubeNetwork(num_agents=5)
    >>> for step in range(100):
    ...     network.synchronize_step()
    >>> network_metric = network.calculate_network_metric()
    >>> print(f"Network Γ: {network_metric['unified_metric']:.4f}")
    """
    
    def __init__(self, num_agents: int = 5, coupling_strength: float = 0.1):
        """
        Initialize Metacube network.
        
        Parameters
        ----------
        num_agents : int, optional
            Number of agents in network (default: 5)
        coupling_strength : float, optional
            Strength of inter-agent coupling (default: 0.1)
        """
        self.num_agents = num_agents
        self.coupling_strength = coupling_strength
        self.agents = [PantheticSystem() for _ in range(num_agents)]
        self.network_timestep = 0
    
    def synchronize_step(self, dt: float = 0.1) -> None:
        """
        Perform one synchronized network evolution step.
        
        Parameters
        ----------
        dt : float, optional
            Timestep size (default: 0.1)
        """
        # Process internal dynamics for all agents
        for agent in self.agents:
            agent.process_internal_dynamics(dt)
        
        # Apply coupling between agents
        if self.coupling_strength > 0:
            self._apply_network_coupling(dt)
        
        self.network_timestep += 1
    
    def _apply_network_coupling(self, dt: float) -> None:
        """Apply coupling forces between agents."""
        # Calculate mean state across network
        mean_state = np.mean([agent.state for agent in self.agents], axis=0)
        
        # Pull each agent toward mean
        for agent in self.agents:
            coupling_force = self.coupling_strength * dt * (mean_state - agent.state)
            agent.state += coupling_force
            agent.state = np.clip(agent.state, 0.0, 1.0)
    
    def calculate_network_metric(self) -> Dict[str, Any]:
        """
        Calculate unified metric for entire network.
        
        Returns
        -------
        dict
            Network-wide unified metric result
        """
        # Aggregate metrics from all agents
        all_metrics = [agent.get_metacube_metrics() for agent in self.agents]
        
        # Average across network
        network_metrics = {
            'diversity': np.mean([m['diversity'] for m in all_metrics]),
            'coherence': np.mean([m['coherence'] for m in all_metrics]),
            'efficiency': np.mean([m['efficiency'] for m in all_metrics]),
            'synergy': np.mean([m['synergy'] for m in all_metrics])
        }
        
        # Calculate network Γ
        D = network_metrics['diversity']
        C = network_metrics['coherence']
        E = network_metrics['efficiency']
        S = network_metrics['synergy']
        
        gamma = np.sqrt(D * C) * np.cbrt(E) * S
        
        if gamma < 0.2:
            interpretation = "Disconnected"
        elif gamma < 0.5:
            interpretation = "Partial Alignment"
        elif gamma < 0.8:
            interpretation = "Effective Coherence"
        else:
            interpretation = "Optimal Synthesis"
        
        return {
            'unified_metric': float(gamma),
            'components': {'D': D, 'C': C, 'E': E, 'S': S},
            'interpretation': interpretation,
            'num_agents': self.num_agents
        }


def demonstrate_panthetic_system():
    """Demonstration of Panthetic System capabilities."""
    print("=" * 70)
    print("PANTHETIC SYSTEM DEMONSTRATION")
    print("Metacube-Integrated Consciousness Modeling")
    print("=" * 70)
    print()
    
    # Create system
    system = PantheticSystem()
    
    # Initialize with balanced state
    print("1. Initializing with balanced consciousness state...")
    initial_state = {
        'awareness': 0.7,
        'intention': 0.6,
        'emotion': 0.5,
        'cognition': 0.8,
        'memory': 0.6,
        'creativity': 0.5,
        'integration': 0.7
    }
    system.update_state(initial_state)
    print("   ✓ State initialized")
    print()
    
    # Display initial metrics
    print("2. Initial Metacube Metrics:")
    metrics = system.get_metacube_metrics()
    print(f"   Diversity (D):  {metrics['diversity']:.4f}")
    print(f"   Coherence (C):  {metrics['coherence']:.4f}")
    print(f"   Efficiency (E): {metrics['efficiency']:.4f}")
    print(f"   Synergy (S):    {metrics['synergy']:.4f}")
    print()
    
    # Calculate unified metric
    print("3. Unified Novelty Metric (Γ):")
    gamma = system.calculate_unified_metric()
    print(f"   Γ = {gamma['unified_metric']:.4f}")
    print(f"   Status: {gamma['interpretation']}")
    print(f"   Epistemic Symbol: {system.get_epistemic_status()}")
    print()
    
    # Apply stimulus and evolve
    print("4. Applying external stimulus and evolving system...")
    system.apply_stimulus({'cognition': 0.15, 'awareness': 0.1})
    
    for step in range(10):
        system.process_internal_dynamics(dt=0.1)
    
    print("   ✓ System evolved for 10 steps")
    print()
    
    # Display updated metrics
    print("5. Updated Metacube Metrics:")
    metrics = system.get_metacube_metrics()
    print(f"   Diversity (D):  {metrics['diversity']:.4f}")
    print(f"   Coherence (C):  {metrics['coherence']:.4f}")
    print(f"   Efficiency (E): {metrics['efficiency']:.4f}")
    print(f"   Synergy (S):    {metrics['synergy']:.4f}")
    
    gamma = system.calculate_unified_metric()
    print(f"   Γ = {gamma['unified_metric']:.4f}")
    print(f"   Status: {gamma['interpretation']}")
    print()
    
    # Ternary projection
    print("6. Ternary State Projection (for Ouroboros):")
    ternary = system.to_ternary_state()
    print(f"   [Cognitive, Affective, Creative]")
    print(f"   [{ternary[0]:.4f}, {ternary[1]:.4f}, {ternary[2]:.4f}]")
    print(f"   Sum: {sum(ternary):.6f} (should be 1.0)")
    print()
    
    # Network demonstration
    print("7. Multi-Agent Network Demonstration:")
    network = MetacubeNetwork(num_agents=3, coupling_strength=0.1)
    
    # Randomize initial states
    for i, agent in enumerate(network.agents):
        np.random.seed(i)
        random_state = {
            dim: np.random.uniform(0.3, 0.9)
            for dim in PantheticSystem.DIMENSIONS
        }
        agent.update_state(random_state)
    
    print(f"   Network with {network.num_agents} agents initialized")
    
    # Evolve network
    for step in range(50):
        network.synchronize_step(dt=0.1)
    
    print(f"   Network evolved for 50 synchronized steps")
    
    # Display network metric
    network_result = network.calculate_network_metric()
    print(f"   Network Γ: {network_result['unified_metric']:.4f}")
    print(f"   Network Status: {network_result['interpretation']}")
    print()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    # Run demonstration
    demonstrate_panthetic_system()
