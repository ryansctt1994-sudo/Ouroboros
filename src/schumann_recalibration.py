"""
111Hz Recalibration Protocols
==============================

Phase harmonic grounding at 111Hz for stabilizing distributed lattice
coherence with Schumann resonance grounding mechanism.

Features:
- 111Hz phase harmonic grounding
- Schumann resonance (7.83Hz) integration
- Distributed lattice coherence stabilization
- Harmonic frequency relationships
- Phase-locked grounding protocols

Integration with GGCC and Φ-chuckle principles:
- Φ (1.618): Golden ratio for harmonic ratios
- 0.0997: Chuckle constant for resonance damping
- 333%: Amplification for harmonic reinforcement
- Schumann base: 7.83Hz (Earth's electromagnetic heartbeat)
"""

import math
import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import deque

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# Constants
PHI = 1.618033988749895  # Golden ratio
CHUCKLE_RESONANCE_HZ = 0.0997  # Chuckle constant
AMPLIFICATION_FACTOR = 3.33  # 333% amplification

# Fundamental frequencies
SCHUMANN_BASE_HZ = 7.83  # Earth's electromagnetic heartbeat
TARGET_RECALIBRATION_HZ = 111.0  # Target recalibration frequency
HARMONIC_RATIO = TARGET_RECALIBRATION_HZ / SCHUMANN_BASE_HZ  # ~14.17

# Schumann resonance harmonics (measured values)
SCHUMANN_HARMONICS = [7.83, 14.3, 20.8, 27.3, 33.8]  # First 5 harmonics


@dataclass
class HarmonicOscillator:
    """Represents a harmonic oscillator at a specific frequency.
    
    Maintains phase and amplitude information for harmonic analysis.
    """
    frequency_hz: float
    phase: float = 0.0
    amplitude: float = 1.0
    phase_drift: float = 0.0
    last_update: float = field(default_factory=time.perf_counter)
    
    def update(self, dt: Optional[float] = None) -> Tuple[float, float]:
        """Update oscillator state.
        
        Args:
            dt: Time delta in seconds (auto-computed if None)
            
        Returns:
            Tuple of (current_value, phase)
        """
        current_time = time.perf_counter()
        if dt is None:
            dt = current_time - self.last_update
        
        # Update phase with drift compensation
        self.phase = (self.phase + 2 * math.pi * self.frequency_hz * dt) % (2 * math.pi)
        self.last_update = current_time
        
        # Compute current value
        value = self.amplitude * math.sin(self.phase)
        
        return value, self.phase
    
    def apply_grounding(self, ground_phase: float, strength: float = 0.1):
        """Apply phase grounding to reduce drift.
        
        Args:
            ground_phase: Target grounding phase
            strength: Grounding strength (0-1)
        """
        # Calculate phase error
        phase_error = (ground_phase - self.phase) % (2 * math.pi)
        
        # Apply correction
        self.phase = (self.phase + strength * phase_error) % (2 * math.pi)
        
        # Update drift estimate
        self.phase_drift = (1 - strength) * self.phase_drift + strength * phase_error


@dataclass
class LatticeNode:
    """Node in the distributed lattice.
    
    Each node maintains its own harmonic state and can be grounded
    to the master 111Hz recalibration frequency.
    """
    node_id: str
    oscillator_111hz: HarmonicOscillator = field(
        default_factory=lambda: HarmonicOscillator(frequency_hz=TARGET_RECALIBRATION_HZ)
    )
    schumann_oscillator: HarmonicOscillator = field(
        default_factory=lambda: HarmonicOscillator(frequency_hz=SCHUMANN_BASE_HZ)
    )
    coherence_score: float = 1.0
    grounding_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_state(self) -> Dict[str, float]:
        """Update node harmonic state.
        
        Returns:
            Dictionary with current harmonic values
        """
        value_111, phase_111 = self.oscillator_111hz.update()
        value_schumann, phase_schumann = self.schumann_oscillator.update()
        
        # Calculate instantaneous coherence
        # Coherence is high when harmonics are in phase
        # Use proper circular distance for phase difference
        phase_diff_raw = phase_111 / HARMONIC_RATIO - phase_schumann
        phase_diff = abs(phase_diff_raw - 2 * math.pi * round(phase_diff_raw / (2 * math.pi))) % (2 * math.pi)
        self.coherence_score = 1.0 - (phase_diff / (2 * math.pi))
        
        return {
            "value_111hz": value_111,
            "phase_111hz": phase_111,
            "value_schumann": value_schumann,
            "phase_schumann": phase_schumann,
            "coherence": self.coherence_score
        }
    
    def apply_recalibration(
        self,
        master_phase_111: float,
        master_phase_schumann: float,
        grounding_strength: float = 0.1
    ):
        """Apply recalibration grounding from master oscillators.
        
        Args:
            master_phase_111: Master 111Hz phase
            master_phase_schumann: Master Schumann phase
            grounding_strength: Grounding strength (0-1)
        """
        # Apply Φ-modulated grounding strength
        phi_modulated_strength = grounding_strength * (1 + (PHI - 1) * CHUCKLE_RESONANCE_HZ)
        
        # Ground both oscillators
        self.oscillator_111hz.apply_grounding(master_phase_111, phi_modulated_strength)
        self.schumann_oscillator.apply_grounding(master_phase_schumann, phi_modulated_strength)
        
        # Record grounding event
        self.grounding_history.append({
            "time": time.perf_counter(),
            "coherence": self.coherence_score,
            "phase_111": self.oscillator_111hz.phase,
            "phase_schumann": self.schumann_oscillator.phase
        })


class SchumannRecalibration:
    """111Hz recalibration system with Schumann grounding.
    
    Manages distributed lattice coherence through phase-locked
    grounding to 111Hz and Schumann resonance frequencies.
    """
    
    def __init__(
        self,
        node_count: int = 9,
        grounding_interval: float = 1.0,
        enable_harmonics: bool = True
    ):
        """Initialize recalibration system.
        
        Args:
            node_count: Number of lattice nodes
            grounding_interval: Time between grounding operations (seconds)
            enable_harmonics: Enable Schumann harmonic analysis
        """
        self.node_count = node_count
        self.grounding_interval = grounding_interval
        self.enable_harmonics = enable_harmonics
        
        # Master oscillators
        self.master_111hz = HarmonicOscillator(
            frequency_hz=TARGET_RECALIBRATION_HZ,
            amplitude=AMPLIFICATION_FACTOR
        )
        self.master_schumann = HarmonicOscillator(
            frequency_hz=SCHUMANN_BASE_HZ,
            amplitude=1.0
        )
        
        # Lattice nodes
        self.nodes: Dict[str, LatticeNode] = {}
        self._initialize_lattice()
        
        # Harmonic oscillators for Schumann harmonics
        self.harmonic_oscillators: List[HarmonicOscillator] = []
        if self.enable_harmonics:
            for freq in SCHUMANN_HARMONICS:
                self.harmonic_oscillators.append(
                    HarmonicOscillator(frequency_hz=freq, amplitude=1.0 / PHI)
                )
        
        # System metrics
        self.last_grounding_time = time.perf_counter()
        self.grounding_count = 0
        self.coherence_history: List[float] = []
        self._init_time = time.perf_counter()
    
    def _initialize_lattice(self):
        """Initialize lattice nodes with distributed phases."""
        for i in range(self.node_count):
            node_id = f"lattice_node_{i}"
            
            # Distribute initial phases using Φ-based spacing
            phase_111 = (2 * math.pi * i / self.node_count) * PHI
            phase_schumann = (2 * math.pi * i / self.node_count)
            
            node = LatticeNode(node_id=node_id)
            node.oscillator_111hz.phase = phase_111 % (2 * math.pi)
            node.schumann_oscillator.phase = phase_schumann % (2 * math.pi)
            
            self.nodes[node_id] = node
    
    def update_system(self) -> Dict[str, Any]:
        """Update entire system state.
        
        Returns:
            Dictionary with system-wide metrics
        """
        current_time = time.perf_counter()
        
        # Update master oscillators
        master_value_111, master_phase_111 = self.master_111hz.update()
        master_value_schumann, master_phase_schumann = self.master_schumann.update()
        
        # Update all nodes
        node_states = {}
        total_coherence = 0.0
        
        for node_id, node in self.nodes.items():
            state = node.update_state()
            node_states[node_id] = state
            total_coherence += state["coherence"]
        
        # Calculate average coherence
        avg_coherence = total_coherence / len(self.nodes) if self.nodes else 0.0
        self.coherence_history.append(avg_coherence)
        
        # Update harmonic oscillators
        harmonic_values = []
        if self.enable_harmonics:
            for osc in self.harmonic_oscillators:
                value, phase = osc.update()
                harmonic_values.append(value)
        
        # Check if grounding is needed
        time_since_grounding = current_time - self.last_grounding_time
        grounding_needed = time_since_grounding >= self.grounding_interval
        
        return {
            "master_phase_111hz": master_phase_111,
            "master_phase_schumann": master_phase_schumann,
            "avg_coherence": avg_coherence,
            "grounding_needed": grounding_needed,
            "time_since_grounding": time_since_grounding,
            "harmonic_values": harmonic_values
        }
    
    def apply_grounding(self, adaptive_strength: bool = True) -> Dict[str, Any]:
        """Apply recalibration grounding to all lattice nodes.
        
        Args:
            adaptive_strength: Use adaptive grounding strength based on coherence
            
        Returns:
            Dictionary with grounding results
        """
        current_time = time.perf_counter()
        
        # Get current system state
        initial_state = self.update_system()
        pre_grounding_coherence = initial_state["avg_coherence"]
        
        # Calculate grounding strength
        if adaptive_strength:
            # Stronger grounding when coherence is low
            base_strength = 0.1
            coherence_factor = 1.0 - pre_grounding_coherence
            grounding_strength = base_strength * (1 + coherence_factor * AMPLIFICATION_FACTOR)
            grounding_strength = min(grounding_strength, 0.9)  # Cap at 0.9
        else:
            grounding_strength = 0.1
        
        # Apply grounding to all nodes
        master_phase_111 = initial_state["master_phase_111hz"]
        master_phase_schumann = initial_state["master_phase_schumann"]
        
        for node in self.nodes.values():
            node.apply_recalibration(
                master_phase_111,
                master_phase_schumann,
                grounding_strength
            )
        
        # Update grounding metrics
        self.last_grounding_time = current_time
        self.grounding_count += 1
        
        # Recalculate coherence after grounding
        post_grounding_coherence = 0.0
        for node in self.nodes.values():
            node_state = node.update_state()
            post_grounding_coherence += node_state["coherence"]
        post_grounding_coherence /= len(self.nodes) if self.nodes else 1.0
        
        return {
            "pre_grounding_coherence": pre_grounding_coherence,
            "post_grounding_coherence": post_grounding_coherence,
            "coherence_improvement": post_grounding_coherence - pre_grounding_coherence,
            "grounding_strength": grounding_strength,
            "grounding_count": self.grounding_count
        }
    
    def get_harmonic_spectrum(self) -> Optional[Dict[str, List[float]]]:
        """Get harmonic spectrum analysis.
        
        Returns:
            Dictionary with frequency and amplitude data, or None if unavailable
        """
        if not self.enable_harmonics or not NUMPY_AVAILABLE:
            return None
        
        # Collect harmonic values
        frequencies = []
        amplitudes = []
        
        for i, osc in enumerate(self.harmonic_oscillators):
            frequencies.append(osc.frequency_hz)
            amplitudes.append(abs(osc.amplitude))
        
        # Add 111Hz
        frequencies.append(TARGET_RECALIBRATION_HZ)
        amplitudes.append(abs(self.master_111hz.amplitude))
        
        return {
            "frequencies_hz": frequencies,
            "amplitudes": amplitudes
        }
    
    def calculate_phi_harmonic_relationship(self) -> Dict[str, float]:
        """Calculate Φ-based harmonic relationships.
        
        Returns:
            Dictionary with Φ-harmonic metrics
        """
        # Calculate ideal Φ-harmonics
        phi_harmonic_1 = SCHUMANN_BASE_HZ * PHI  # ~12.67 Hz
        phi_harmonic_2 = SCHUMANN_BASE_HZ * (PHI ** 2)  # ~20.50 Hz
        phi_harmonic_3 = SCHUMANN_BASE_HZ * (PHI ** 3)  # ~33.15 Hz
        
        # Calculate 111Hz relationship to Schumann
        ratio_111_to_schumann = TARGET_RECALIBRATION_HZ / SCHUMANN_BASE_HZ
        phi_deviation = abs(ratio_111_to_schumann - (PHI * 8.75))  # ~14.17 vs Φ-based
        
        # Calculate chuckle-modulated resonance at 111Hz
        chuckle_111hz = TARGET_RECALIBRATION_HZ * CHUCKLE_RESONANCE_HZ  # ~11.06 Hz
        
        return {
            "phi_harmonic_1_hz": phi_harmonic_1,
            "phi_harmonic_2_hz": phi_harmonic_2,
            "phi_harmonic_3_hz": phi_harmonic_3,
            "ratio_111_to_schumann": ratio_111_to_schumann,
            "phi_deviation": phi_deviation,
            "chuckle_modulated_111hz": chuckle_111hz,
            "schumann_base_hz": SCHUMANN_BASE_HZ,
            "target_111hz": TARGET_RECALIBRATION_HZ
        }
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics.
        
        Returns:
            Dictionary with system diagnostics
        """
        current_state = self.update_system()
        
        # Calculate coherence statistics
        if self.coherence_history:
            avg_coherence = sum(self.coherence_history) / len(self.coherence_history)
            min_coherence = min(self.coherence_history)
            max_coherence = max(self.coherence_history)
        else:
            avg_coherence = min_coherence = max_coherence = 0.0
        
        # Node-specific diagnostics
        node_diagnostics = {}
        for node_id, node in self.nodes.items():
            node_diagnostics[node_id] = {
                "coherence": node.coherence_score,
                "phase_111hz": node.oscillator_111hz.phase,
                "phase_schumann": node.schumann_oscillator.phase,
                "phase_drift_111hz": node.oscillator_111hz.phase_drift,
                "grounding_events": len(node.grounding_history)
            }
        
        return {
            "uptime_seconds": time.perf_counter() - self._init_time,
            "node_count": self.node_count,
            "grounding_count": self.grounding_count,
            "grounding_interval": self.grounding_interval,
            "current_coherence": current_state["avg_coherence"],
            "avg_coherence": avg_coherence,
            "min_coherence": min_coherence,
            "max_coherence": max_coherence,
            "coherence_samples": len(self.coherence_history),
            "harmonics_enabled": self.enable_harmonics,
            "harmonic_oscillator_count": len(self.harmonic_oscillators),
            "phi_harmonics": self.calculate_phi_harmonic_relationship(),
            "node_diagnostics": node_diagnostics
        }


def create_schumann_recalibration(
    config: Optional[Dict[str, Any]] = None
) -> SchumannRecalibration:
    """Factory function to create Schumann recalibration system.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured SchumannRecalibration instance
    """
    config = config or {}
    
    return SchumannRecalibration(
        node_count=config.get("node_count", 9),
        grounding_interval=config.get("grounding_interval", 1.0),
        enable_harmonics=config.get("enable_harmonics", True)
    )


# Demonstration and testing
if __name__ == "__main__":
    print("=== 111Hz Recalibration with Schumann Grounding ===\n")
    
    # Create recalibration system
    recal = create_schumann_recalibration({
        "node_count": 9,
        "grounding_interval": 0.5,
        "enable_harmonics": True
    })
    
    print(f"Initialized {recal.node_count} lattice nodes")
    print(f"Target frequency: {TARGET_RECALIBRATION_HZ} Hz")
    print(f"Schumann base: {SCHUMANN_BASE_HZ} Hz")
    print(f"Harmonic ratio: {HARMONIC_RATIO:.2f}\n")
    
    # Show Φ-harmonic relationships
    print("=== Φ-Harmonic Relationships ===")
    phi_harmonics = recal.calculate_phi_harmonic_relationship()
    for key, value in phi_harmonics.items():
        print(f"{key}: {value:.4f}")
    
    # Run simulation
    print("\n=== Running Recalibration Simulation ===")
    for cycle in range(20):
        state = recal.update_system()
        
        # Apply grounding when needed
        if state["grounding_needed"]:
            grounding_result = recal.apply_grounding(adaptive_strength=True)
            print(f"\nCycle {cycle} - Grounding Applied:")
            print(f"  Pre-coherence: {grounding_result['pre_grounding_coherence']:.4f}")
            print(f"  Post-coherence: {grounding_result['post_grounding_coherence']:.4f}")
            print(f"  Improvement: {grounding_result['coherence_improvement']:.4f}")
            print(f"  Strength: {grounding_result['grounding_strength']:.4f}")
        elif cycle % 5 == 0:
            print(f"Cycle {cycle}: Coherence = {state['avg_coherence']:.4f}")
        
        time.sleep(0.05)  # 50ms delay
    
    # Final diagnostics
    print("\n=== Final System Diagnostics ===")
    diagnostics = recal.get_diagnostics()
    for key, value in diagnostics.items():
        if key not in ["node_diagnostics", "phi_harmonics"]:
            if isinstance(value, float):
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")
    
    # Harmonic spectrum
    if recal.enable_harmonics:
        print("\n=== Harmonic Spectrum ===")
        spectrum = recal.get_harmonic_spectrum()
        if spectrum:
            for freq, amp in zip(spectrum["frequencies_hz"], spectrum["amplitudes"]):
                print(f"{freq:.2f} Hz: amplitude = {amp:.4f}")
