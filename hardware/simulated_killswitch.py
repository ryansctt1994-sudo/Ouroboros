"""
Simulated Kill-Switch Model

Provides a software simulation of the MachXO2 FPGA kill-switch
for testing and development without physical hardware.
"""

import time
import secrets
import hmac
import hashlib
from typing import Dict, Any, Optional
from enum import Enum


class KillSwitchState(Enum):
    """Kill-switch states."""
    INIT = "init"
    ARMED = "armed"
    TRIGGERED = "triggered"
    TAMPER = "tamper"
    FAULT = "fault"


class SimulatedKillSwitch:
    """
    Simulates the MachXO2 FPGA kill-switch.
    
    Provides the same interface as hardware kill-switch for testing.
    """
    
    def __init__(self, key: bytes = None, latency_ns: int = 449):
        """
        Initialize simulated kill-switch.
        
        Args:
            key: 32-byte HMAC key (generated if not provided)
            latency_ns: Simulated hardware latency in nanoseconds (default: 449)
        """
        self.key = key or secrets.token_bytes(32)
        self.latency_ns = latency_ns
        self.state = KillSwitchState.INIT
        self.nonce: Optional[bytes] = None
        self.trigger_count = 0
        self.tamper_count = 0
        self.start_time = time.time()
        self.last_heartbeat = time.time()
        self.watchdog_timeout = 60.0  # seconds
        
        # Auto-transition to ARMED after initialization
        time.sleep(0.01)  # Simulate startup delay
        self._self_test()
    
    def _self_test(self) -> bool:
        """Perform self-test."""
        # Simulated self-test always passes
        self.state = KillSwitchState.ARMED
        return True
    
    def generate_challenge(self) -> bytes:
        """
        Generate authentication challenge.
        
        Returns:
            32-byte random nonce
        """
        self.nonce = secrets.token_bytes(32)
        return self.nonce
    
    def verify_signature(self, command: bytes, signature: bytes) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            command: Command bytes
            signature: HMAC-SHA256 signature
            
        Returns:
            True if signature is valid
        """
        if self.nonce is None:
            return False
        
        expected = hmac.new(
            self.key,
            self.nonce + command,
            hashlib.sha256
        ).digest()
        
        # Constant-time comparison
        return hmac.compare_digest(expected, signature)
    
    def trigger(self, signature: bytes = None) -> bool:
        """
        Trigger the kill-switch.
        
        Args:
            signature: Optional HMAC signature for authentication
            
        Returns:
            True if trigger successful
        """
        if self.state != KillSwitchState.ARMED:
            return False
        
        # If signature provided, verify it
        if signature is not None:
            if not self.verify_signature(b'TRIGGER', signature):
                return False
        
        # Activate kill-switch
        self.state = KillSwitchState.TRIGGERED
        self.trigger_count += 1
        
        print(f"[KILLSWITCH] TRIGGERED at {time.time():.2f}")
        print("[KILLSWITCH] System power cut simulated")
        
        return True
    
    def detect_tamper(self) -> None:
        """Simulate tamper detection."""
        if self.state == KillSwitchState.ARMED:
            self.state = KillSwitchState.TAMPER
            self.tamper_count += 1
            print(f"[KILLSWITCH] TAMPER detected at {time.time():.2f}")
    
    def heartbeat(self) -> bool:
        """
        Receive watchdog heartbeat.
        
        Returns:
            True if heartbeat acknowledged
        """
        if self.state != KillSwitchState.ARMED:
            return False
        
        self.last_heartbeat = time.time()
        return True
    
    def check_watchdog(self) -> None:
        """Check watchdog timeout and trigger if expired."""
        if self.state == KillSwitchState.ARMED:
            elapsed = time.time() - self.last_heartbeat
            if elapsed > self.watchdog_timeout:
                print(f"[KILLSWITCH] Watchdog timeout ({elapsed:.1f}s)")
                self.trigger()
    
    def reset(self, authorized: bool = False) -> bool:
        """
        Reset the kill-switch.
        
        Args:
            authorized: Whether reset is authorized
            
        Returns:
            True if reset successful
        """
        if not authorized:
            return False
        
        if self.state == KillSwitchState.TRIGGERED:
            self.state = KillSwitchState.INIT
            time.sleep(0.01)  # Simulate reset delay
            self._self_test()
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get kill-switch status.
        
        Returns:
            Status dictionary
        """
        uptime = time.time() - self.start_time
        time_since_heartbeat = time.time() - self.last_heartbeat
        
        return {
            'state': self.state.value,
            'trigger_count': self.trigger_count,
            'tamper_count': self.tamper_count,
            'uptime': uptime,
            'last_heartbeat': time_since_heartbeat,
            'watchdog_timeout': self.watchdog_timeout
        }
    
    def get_led_color(self) -> str:
        """
        Get status LED color.
        
        Returns:
            LED color string
        """
        led_map = {
            KillSwitchState.INIT: "blinking",
            KillSwitchState.ARMED: "green",
            KillSwitchState.TRIGGERED: "red",
            KillSwitchState.TAMPER: "red_rapid",
            KillSwitchState.FAULT: "orange"
        }
        return led_map.get(self.state, "off")


class IcarusLatch:
    """
    Software boundary enforcement with simulated hardware kill-switch.
    """
    
    def __init__(self, killswitch: SimulatedKillSwitch = None):
        """
        Initialize Icarus Latch.
        
        Args:
            killswitch: Kill-switch instance (created if not provided)
        """
        self.killswitch = killswitch or SimulatedKillSwitch()
        
        # Define boundaries
        self.boundaries = {
            'max_entities': 10000,
            'max_memory_mb': 4096,
            'max_cpu_percent': 80,
            'max_iterations': 1000000,
            'max_depth': 100
        }
        
        self.violations = []
        self.violation_threshold_soft = 3
        self.violation_threshold_hard = 10
    
    def check_boundary(self, metric: str, value: float) -> bool:
        """
        Check if metric exceeds boundary.
        
        Args:
            metric: Metric name
            value: Current value
            
        Returns:
            True if within boundary
        """
        if metric in self.boundaries:
            if value > self.boundaries[metric]:
                self.violations.append({
                    'metric': metric,
                    'value': value,
                    'limit': self.boundaries[metric],
                    'timestamp': time.time()
                })
                return False
        return True
    
    def enforce(self) -> None:
        """Enforce boundaries with graduated response."""
        violation_count = len(self.violations)
        
        if violation_count == 0:
            return
        
        # Soft limit: warnings
        if violation_count < self.violation_threshold_soft:
            print(f"[LATCH] WARNING: {self.violations[-1]}")
            return
        
        # Hard limit: graceful shutdown
        if violation_count < self.violation_threshold_hard:
            print(f"[LATCH] ERROR: Multiple violations - graceful shutdown")
            # In real system, would initiate graceful shutdown
            return
        
        # Critical: hardware kill
        print(f"[LATCH] CRITICAL: {violation_count} violations - KILL SWITCH")
        self.killswitch.trigger()
    
    def reset_violations(self) -> None:
        """Reset violation history."""
        self.violations.clear()


# Example usage
if __name__ == '__main__':
    # Create simulated kill-switch
    killswitch = SimulatedKillSwitch()
    print(f"Kill-switch initialized: {killswitch.get_status()}")
    print(f"LED status: {killswitch.get_led_color()}")
    
    # Test heartbeat
    print("\n--- Testing Heartbeat ---")
    for i in range(3):
        ack = killswitch.heartbeat()
        print(f"Heartbeat {i+1}: {'ACK' if ack else 'NAK'}")
        time.sleep(0.1)
    
    # Test authentication
    print("\n--- Testing Authentication ---")
    nonce = killswitch.generate_challenge()
    command = b'TRIGGER'
    signature = hmac.new(
        killswitch.key,
        nonce + command,
        hashlib.sha256
    ).digest()
    
    # Test Icarus Latch
    print("\n--- Testing Icarus Latch ---")
    latch = IcarusLatch(killswitch)
    
    # Simulate boundary violations
    for i in range(15):
        # Simulate increasing entity count
        latch.check_boundary('max_entities', 9000 + i * 500)
        latch.enforce()
        time.sleep(0.05)
    
    # Final status
    print(f"\nFinal status: {killswitch.get_status()}")
