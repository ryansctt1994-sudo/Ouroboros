"""SymmetryMonitor v2: Auto-drift Detection and Kalman-backed Filters.

Automated phase-lock drift corrections with negligible operational overhead.
Reinforces Guardian Clause dynamics through sparse correction system.

Features:
    - Automatic phase-lock drift detection
    - Kalman filter-based state estimation
    - Guardian Clause dynamics reinforcement
    - Sparse correction system for minimal overhead
    - AMUSED-tagged diagnostic logging
"""

import math
from typing import List, Tuple, Dict, Any, Optional
import time


class SymmetryMonitorV2:
    """Auto-drift detection with Kalman-backed filtering.
    
    Monitors symmetry in dynamic systems and applies Kalman filtering
    to detect and correct phase-lock drift with minimal overhead.
    
    The Kalman filter provides optimal state estimation in the presence
    of noise, making it ideal for detecting subtle symmetry violations.
    
    Attributes:
        drift_threshold: Maximum allowed phase drift (radians)
        kalman_gain: Kalman filter gain parameter
        correction_sparsity: Correction application frequency (0-1)
        state_estimate: Current symmetry state estimate
        error_covariance: Kalman filter error covariance
    """
    
    def __init__(self, drift_threshold: float = 0.01, kalman_gain: float = 0.5,
                 correction_sparsity: float = 0.1, enable_amused_logging: bool = True):
        """Initialize the symmetry monitor.
        
        Args:
            drift_threshold: Phase drift threshold in radians (default: 0.01)
            kalman_gain: Kalman filter gain [0, 1] (default: 0.5)
            correction_sparsity: Correction frequency [0, 1] (default: 0.1)
            enable_amused_logging: Enable AMUSED-tagged logging
        """
        self.drift_threshold = drift_threshold
        self.kalman_gain = kalman_gain
        self.correction_sparsity = correction_sparsity
        self.amused_logging = enable_amused_logging
        
        # Kalman filter state
        self.state_estimate: float = 0.0  # Phase estimate
        self.error_covariance: float = 1.0  # Initial uncertainty
        
        # Measurement and process noise (tunable parameters)
        self.measurement_noise: float = 0.01
        self.process_noise: float = 0.001
        
        # Guardian Clause state
        self.guardian_active = False
        self.guardian_corrections = 0
        
        # Drift tracking
        self.drift_history: List[float] = []
        self.correction_count = 0
        self.measurement_count = 0
        
        # Performance metrics
        self.total_drift = 0.0
        self.max_drift = 0.0
        
        if self.amused_logging:
            self._log_amused(
                f"SymmetryMonitor v2 initialized: threshold={drift_threshold:.4f}, "
                f"kalman_gain={kalman_gain:.2f}, sparsity={correction_sparsity:.2f}"
            )
    
    def _log_amused(self, message: str, level: str = "INFO"):
        """Log with AMUSED tag for human-readable resonant feedback."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[AMUSED:{level}] {timestamp} | SymmetryMonitor | {message}")
    
    def _kalman_predict(self) -> None:
        """Kalman filter prediction step.
        
        Projects state estimate forward with process noise.
        """
        # State prediction (assume constant phase model)
        # state_estimate remains the same (no control input)
        
        # Covariance prediction
        self.error_covariance += self.process_noise
    
    def _kalman_update(self, measurement: float) -> None:
        """Kalman filter update step.
        
        Updates state estimate based on new measurement.
        
        Args:
            measurement: Observed phase value
        """
        # Kalman gain
        K = self.error_covariance / (self.error_covariance + self.measurement_noise)
        
        # Update estimate
        innovation = measurement - self.state_estimate
        self.state_estimate += K * innovation
        
        # Update error covariance
        self.error_covariance = (1 - K) * self.error_covariance
    
    def measure_phase(self, observed_phase: float) -> Dict[str, Any]:
        """Measure and track phase symmetry.
        
        Applies Kalman filtering to estimate true phase and detect drift.
        
        Args:
            observed_phase: Observed phase value in radians
            
        Returns:
            Dictionary with measurement results and drift information
        """
        self.measurement_count += 1
        
        # Kalman prediction
        self._kalman_predict()
        
        # Kalman update with measurement
        self._kalman_update(observed_phase)
        
        # Compute drift (deviation from expected symmetry)
        # For symmetry, expected phase should be 0 (modulo 2π)
        normalized_phase = self.state_estimate % (2 * math.pi)
        if normalized_phase > math.pi:
            normalized_phase -= 2 * math.pi
        
        drift = abs(normalized_phase)
        self.drift_history.append(drift)
        self.total_drift += drift
        self.max_drift = max(self.max_drift, drift)
        
        # Check if drift exceeds threshold
        drift_detected = drift > self.drift_threshold
        
        result = {
            "observed_phase": observed_phase,
            "estimated_phase": self.state_estimate,
            "drift": drift,
            "drift_detected": drift_detected,
            "error_covariance": self.error_covariance,
            "measurement_count": self.measurement_count
        }
        
        if drift_detected and self.amused_logging:
            self._log_amused(
                f"Phase drift detected: {drift:.6f} rad (threshold={self.drift_threshold:.6f})",
                "WARN"
            )
        
        return result
    
    def apply_correction(self, force_correction: bool = False) -> Optional[float]:
        """Apply sparse correction to phase drift.
        
        Corrections are applied sparsely to minimize operational overhead.
        
        Args:
            force_correction: Force correction regardless of sparsity
            
        Returns:
            Correction value applied, or None if no correction
        """
        # Determine if correction should be applied
        import random
        should_correct = force_correction or (random.random() < self.correction_sparsity)
        
        if not should_correct:
            return None
        
        # Compute correction based on current drift
        if len(self.drift_history) == 0:
            return None
        
        current_drift = self.drift_history[-1]
        
        if current_drift <= self.drift_threshold:
            return None  # No correction needed
        
        # Correction magnitude proportional to drift
        correction = -current_drift * self.kalman_gain
        
        # Apply correction to state estimate
        self.state_estimate += correction
        self.correction_count += 1
        
        if self.amused_logging:
            self._log_amused(
                f"Applied phase correction: {correction:.6f} rad "
                f"(drift={current_drift:.6f})",
                "INFO"
            )
        
        return correction
    
    def activate_guardian_clause(self, threshold_multiplier: float = 2.0) -> bool:
        """Activate Guardian Clause for enhanced drift protection.
        
        Guardian Clause provides additional protection layer when
        drift exceeds critical thresholds.
        
        Args:
            threshold_multiplier: Multiplier for activation threshold
            
        Returns:
            True if Guardian Clause was activated
        """
        if len(self.drift_history) == 0:
            return False
        
        recent_drift = sum(self.drift_history[-10:]) / min(10, len(self.drift_history))
        critical_threshold = self.drift_threshold * threshold_multiplier
        
        if recent_drift > critical_threshold and not self.guardian_active:
            self.guardian_active = True
            self.guardian_corrections = 0
            
            if self.amused_logging:
                self._log_amused(
                    f"Guardian Clause ACTIVATED: recent_drift={recent_drift:.6f} "
                    f"(critical={critical_threshold:.6f})",
                    "WARN"
                )
            
            return True
        
        return False
    
    def guardian_correct(self) -> Optional[float]:
        """Apply Guardian Clause correction.
        
        More aggressive correction when Guardian Clause is active.
        
        Returns:
            Correction value or None
        """
        if not self.guardian_active:
            return None
        
        if len(self.drift_history) == 0:
            return None
        
        # Apply stronger correction
        current_drift = self.drift_history[-1]
        correction = -current_drift * 0.9  # High gain for Guardian mode
        
        self.state_estimate += correction
        self.guardian_corrections += 1
        
        if self.amused_logging:
            self._log_amused(
                f"Guardian correction applied: {correction:.6f} rad "
                f"(total_guardian={self.guardian_corrections})"
            )
        
        # Deactivate Guardian if drift is controlled
        if current_drift < self.drift_threshold * 0.5:
            self.guardian_active = False
            if self.amused_logging:
                self._log_amused(
                    f"Guardian Clause DEACTIVATED after {self.guardian_corrections} corrections"
                )
        
        return correction
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about symmetry monitoring.
        
        Returns:
            Dictionary with monitoring metrics
        """
        avg_drift = self.total_drift / self.measurement_count if self.measurement_count > 0 else 0.0
        correction_rate = self.correction_count / self.measurement_count if self.measurement_count > 0 else 0.0
        
        return {
            "drift_threshold": self.drift_threshold,
            "kalman_gain": self.kalman_gain,
            "correction_sparsity": self.correction_sparsity,
            "state_estimate": self.state_estimate,
            "error_covariance": self.error_covariance,
            "measurement_count": self.measurement_count,
            "correction_count": self.correction_count,
            "correction_rate": correction_rate,
            "avg_drift": avg_drift,
            "max_drift": self.max_drift,
            "guardian_active": self.guardian_active,
            "guardian_corrections": self.guardian_corrections
        }
    
    def reset(self) -> None:
        """Reset monitor state and clear history."""
        self.state_estimate = 0.0
        self.error_covariance = 1.0
        self.drift_history.clear()
        self.correction_count = 0
        self.measurement_count = 0
        self.total_drift = 0.0
        self.max_drift = 0.0
        self.guardian_active = False
        self.guardian_corrections = 0
        
        if self.amused_logging:
            self._log_amused("Monitor state reset")


if __name__ == "__main__":
    # Demonstration of SymmetryMonitor v2
    print("=" * 70)
    print("SymmetryMonitor v2: Auto-drift Detection Demo")
    print("=" * 70)
    print()
    
    import random
    monitor = SymmetryMonitorV2(drift_threshold=0.05)
    
    # Simulate phase measurements with drift
    print("Simulating phase measurements with gradual drift...")
    for i in range(20):
        # Simulated phase with increasing drift
        true_phase = 0.0
        noise = random.gauss(0, 0.01)
        drift = 0.003 * i  # Gradual drift
        observed = true_phase + noise + drift
        
        result = monitor.measure_phase(observed)
        
        if i % 5 == 0:
            print(f"  Measurement {i}: drift={result['drift']:.6f}, "
                  f"detected={result['drift_detected']}")
        
        # Apply corrections
        if result['drift_detected']:
            correction = monitor.apply_correction()
            if correction:
                print(f"    → Correction applied: {correction:.6f}")
        
        # Check Guardian Clause
        if monitor.activate_guardian_clause():
            print(f"    → Guardian Clause activated!")
            monitor.guardian_correct()
    
    # Show diagnostics
    print("\nDiagnostics:")
    diagnostics = monitor.get_diagnostics()
    for key, value in diagnostics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
