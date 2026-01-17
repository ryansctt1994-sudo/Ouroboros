"""Coupling Interface: Static/Dynamic Impedance Matching.

Ensures seamless interfacing between GGCC (static) and GGCCD (dynamic) 
operational layers. Manages high-frequency oscillation suppression through 
exponential filtering techniques.

Features:
    - Static/Dynamic impedance matching
    - Exponential filtering for oscillation suppression
    - Adaptive coupling strength adjustment
    - Frequency analysis and spectral monitoring
    - AMUSED-tagged diagnostic logging
"""

import math
from collections import deque
from typing import List, Tuple, Dict, Any, Optional
import time

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class CouplingInterface:
    """Static/Dynamic impedance matching interface.
    
    Provides coupling between GGCC (static Guardian Gate Constellation Control)
    and GGCCD (dynamic GGCC) operational layers with adaptive impedance matching.
    
    Uses exponential filtering to suppress high-frequency oscillations while
    preserving low-frequency signal dynamics.
    
    Attributes:
        filter_alpha: Exponential filter coefficient [0, 1]
        coupling_strength: Base coupling strength [0, 1]
        oscillation_threshold: Maximum allowed oscillation amplitude
        static_state: Current static layer state
        dynamic_state: Current dynamic layer state
    """
    
    def __init__(self, filter_alpha: float = 0.3, 
                 coupling_strength: float = 0.7,
                 oscillation_threshold: float = 0.1,
                 enable_amused_logging: bool = True):
        """Initialize the coupling interface.
        
        Args:
            filter_alpha: Exponential filter coefficient (default: 0.3)
            coupling_strength: Coupling strength [0, 1] (default: 0.7)
            oscillation_threshold: Oscillation suppression threshold (default: 0.1)
            enable_amused_logging: Enable AMUSED-tagged logging
        """
        self.filter_alpha = filter_alpha
        self.coupling_strength = coupling_strength
        self.oscillation_threshold = oscillation_threshold
        self.amused_logging = enable_amused_logging
        
        # Layer states
        self.static_state: float = 0.0
        self.dynamic_state: float = 0.0
        self.filtered_state: float = 0.0
        
        # History for oscillation detection - use deque for O(1) eviction
        self.state_history: deque = deque(maxlen=100)
        self.oscillation_history: List[float] = []
        
        # Adaptive coupling parameters
        self.adaptive_coupling = coupling_strength
        self.coupling_adjustment_rate = 0.05
        
        # Metrics
        self.coupling_events = 0
        self.oscillation_suppressions = 0
        self.total_impedance_mismatch = 0.0
        
        if self.amused_logging:
            self._log_amused(
                f"CouplingInterface initialized: alpha={filter_alpha:.2f}, "
                f"strength={coupling_strength:.2f}, "
                f"threshold={oscillation_threshold:.2f}"
            )
    
    def _log_amused(self, message: str, level: str = "INFO"):
        """Log with AMUSED tag for human-readable resonant feedback."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[AMUSED:{level}] {timestamp} | CouplingInterface | {message}")
    
    def _exponential_filter(self, new_value: float, prev_filtered: float) -> float:
        """Apply exponential low-pass filter.
        
        Suppresses high-frequency oscillations while tracking low-frequency trends.
        
        Filter equation: y[n] = α * x[n] + (1 - α) * y[n-1]
        
        Args:
            new_value: New input value
            prev_filtered: Previous filtered value
            
        Returns:
            Filtered output
        """
        return self.filter_alpha * new_value + (1 - self.filter_alpha) * prev_filtered
    
    def _detect_oscillation(self) -> Tuple[bool, float]:
        """Detect high-frequency oscillations in state history.
        
        Returns:
            Tuple (oscillation_detected, oscillation_amplitude)
        """
        if len(self.state_history) < 3:
            return False, 0.0
        
        # Check for rapid sign changes (oscillation indicator)
        recent_states = self.state_history[-5:]
        if len(recent_states) < 3:
            return False, 0.0
        
        # Compute differences
        diffs = [recent_states[i+1] - recent_states[i] 
                for i in range(len(recent_states) - 1)]
        
        # Check for sign alternation
        sign_changes = sum(1 for i in range(len(diffs) - 1) 
                          if diffs[i] * diffs[i+1] < 0)
        
        # Compute oscillation amplitude
        amplitude = max(abs(d) for d in diffs) if diffs else 0.0
        
        # Oscillation detected if frequent sign changes and high amplitude
        oscillation_detected = (sign_changes >= 2 and 
                               amplitude > self.oscillation_threshold)
        
        return oscillation_detected, amplitude
    
    def couple_static_to_dynamic(self, static_value: float) -> float:
        """Couple static layer value to dynamic layer.
        
        Applies impedance matching and filtering to ensure smooth coupling.
        
        Args:
            static_value: Value from static GGCC layer
            
        Returns:
            Coupled value for dynamic GGCCD layer
        """
        self.coupling_events += 1
        self.static_state = static_value
        
        # Apply exponential filtering for oscillation suppression
        self.filtered_state = self._exponential_filter(
            static_value, 
            self.filtered_state
        )
        
        # Update state history (deque auto-evicts when maxlen reached)
        self.state_history.append(self.filtered_state)
        
        # Detect oscillations
        oscillation_detected, amplitude = self._detect_oscillation()
        
        if oscillation_detected:
            self.oscillation_suppressions += 1
            self.oscillation_history.append(amplitude)
            
            # Reduce coupling strength temporarily to suppress oscillation
            self.adaptive_coupling = max(
                0.1,
                self.adaptive_coupling - self.coupling_adjustment_rate
            )
            
            if self.amused_logging:
                self._log_amused(
                    f"Oscillation detected (amplitude={amplitude:.4f}), "
                    f"reduced coupling to {self.adaptive_coupling:.2f}",
                    "WARN"
                )
        else:
            # Gradually restore coupling strength
            self.adaptive_coupling = min(
                self.coupling_strength,
                self.adaptive_coupling + self.coupling_adjustment_rate / 2
            )
        
        # Apply adaptive coupling
        coupled_value = self.filtered_state * self.adaptive_coupling
        self.dynamic_state = coupled_value
        
        return coupled_value
    
    def couple_dynamic_to_static(self, dynamic_value: float) -> float:
        """Couple dynamic layer value to static layer.
        
        Applies reverse impedance matching with heavier filtering
        to prevent dynamic instabilities from affecting static layer.
        
        Args:
            dynamic_value: Value from dynamic GGCCD layer
            
        Returns:
            Coupled value for static GGCC layer
        """
        self.coupling_events += 1
        self.dynamic_state = dynamic_value
        
        # Use stronger filtering for dynamic-to-static coupling
        # (static layer should be more stable)
        heavy_alpha = self.filter_alpha * 0.5
        filtered = heavy_alpha * dynamic_value + (1 - heavy_alpha) * self.static_state
        
        # Apply conservative coupling
        coupled_value = filtered * (self.adaptive_coupling * 0.8)
        self.static_state = coupled_value
        
        return coupled_value
    
    def measure_impedance_mismatch(self) -> float:
        """Measure impedance mismatch between layers.
        
        Returns:
            Impedance mismatch value (lower is better)
        """
        # Impedance mismatch is the normalized difference between layers
        mismatch = abs(self.static_state - self.dynamic_state)
        self.total_impedance_mismatch += mismatch
        
        return mismatch
    
    def analyze_frequency_spectrum(self) -> Dict[str, float]:
        """Analyze frequency content of coupled signal.
        
        Provides spectral analysis to identify dominant frequencies
        and potential oscillation sources.
        
        Returns:
            Dictionary with frequency analysis results
        """
        if len(self.state_history) < 4:
            return {
                "low_freq_power": 0.0,
                "high_freq_power": 0.0,
                "dominant_freq": 0.0
            }
        
        if HAS_NUMPY:
            # Use FFT for spectral analysis
            signal = np.array(self.state_history[-64:])  # Last 64 samples
            if len(signal) < 4:
                return {
                    "low_freq_power": 0.0,
                    "high_freq_power": 0.0,
                    "dominant_freq": 0.0
                }
            
            # Compute FFT
            fft = np.fft.fft(signal)
            power_spectrum = np.abs(fft) ** 2
            
            # Split into low and high frequency bands
            mid_point = len(power_spectrum) // 4
            low_freq_power = float(np.sum(power_spectrum[:mid_point]))
            high_freq_power = float(np.sum(power_spectrum[mid_point:len(power_spectrum)//2]))
            
            # Find dominant frequency
            dominant_idx = np.argmax(power_spectrum[:len(power_spectrum)//2])
            dominant_freq = float(dominant_idx) / len(signal)
            
        else:
            # Simplified analysis without numpy
            signal = self.state_history[-32:]
            
            # Estimate low-frequency power (mean absolute value)
            low_freq_power = sum(abs(s) for s in signal) / len(signal)
            
            # Estimate high-frequency power (variance of differences)
            diffs = [signal[i+1] - signal[i] for i in range(len(signal) - 1)]
            high_freq_power = sum(d**2 for d in diffs) / len(diffs) if diffs else 0.0
            
            dominant_freq = 0.0
        
        return {
            "low_freq_power": low_freq_power,
            "high_freq_power": high_freq_power,
            "dominant_freq": dominant_freq
        }
    
    def adjust_coupling_strength(self, target_strength: float) -> None:
        """Manually adjust coupling strength.
        
        Args:
            target_strength: New coupling strength [0, 1]
        """
        old_strength = self.coupling_strength
        self.coupling_strength = max(0.0, min(1.0, target_strength))
        
        if self.amused_logging:
            self._log_amused(
                f"Coupling strength adjusted: {old_strength:.2f} → "
                f"{self.coupling_strength:.2f}"
            )
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about coupling interface.
        
        Returns:
            Dictionary with coupling metrics
        """
        avg_mismatch = (self.total_impedance_mismatch / self.coupling_events 
                       if self.coupling_events > 0 else 0.0)
        
        spectrum = self.analyze_frequency_spectrum()
        
        return {
            "filter_alpha": self.filter_alpha,
            "coupling_strength": self.coupling_strength,
            "adaptive_coupling": self.adaptive_coupling,
            "oscillation_threshold": self.oscillation_threshold,
            "static_state": self.static_state,
            "dynamic_state": self.dynamic_state,
            "filtered_state": self.filtered_state,
            "coupling_events": self.coupling_events,
            "oscillation_suppressions": self.oscillation_suppressions,
            "current_mismatch": self.measure_impedance_mismatch(),
            "avg_mismatch": avg_mismatch,
            "low_freq_power": spectrum["low_freq_power"],
            "high_freq_power": spectrum["high_freq_power"],
            "dominant_freq": spectrum["dominant_freq"]
        }
    
    def reset(self) -> None:
        """Reset interface state and clear history."""
        self.static_state = 0.0
        self.dynamic_state = 0.0
        self.filtered_state = 0.0
        self.state_history.clear()
        self.oscillation_history.clear()
        self.adaptive_coupling = self.coupling_strength
        
        if self.amused_logging:
            self._log_amused("Interface state reset")


if __name__ == "__main__":
    # Demonstration of CouplingInterface
    print("=" * 70)
    print("CouplingInterface: Static/Dynamic Impedance Matching Demo")
    print("=" * 70)
    print()
    
    interface = CouplingInterface(filter_alpha=0.3, coupling_strength=0.7)
    
    # Simulate coupling with oscillatory signal
    print("Simulating static-to-dynamic coupling...")
    import math
    for i in range(20):
        # Static value with high-frequency oscillation
        static_value = math.sin(i * 0.5) + 0.3 * math.sin(i * 3.0)
        
        coupled = interface.couple_static_to_dynamic(static_value)
        
        if i % 5 == 0:
            mismatch = interface.measure_impedance_mismatch()
            print(f"  Step {i}: static={static_value:.4f}, "
                  f"coupled={coupled:.4f}, mismatch={mismatch:.4f}")
    
    # Frequency analysis
    print("\nFrequency spectrum analysis:")
    spectrum = interface.analyze_frequency_spectrum()
    for key, value in spectrum.items():
        print(f"  {key}: {value:.6f}")
    
    # Show diagnostics
    print("\nDiagnostics:")
    diagnostics = interface.get_diagnostics()
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
