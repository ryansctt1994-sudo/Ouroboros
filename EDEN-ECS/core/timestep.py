"""Hybrid Timestep System for EDEN-ECS v2.0.0"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import time


class TimestepMode(Enum):
    """Timestep execution modes"""
    FIXED = "fixed"           # Deterministic fixed timestep
    VARIABLE = "variable"     # Smooth variable timestep
    HYBRID = "hybrid"         # Combined fixed logic with variable rendering


@dataclass
class TimestepDiagnostics:
    """Performance diagnostics for timestep system"""
    fps: float = 0.0
    frame_time_ms: float = 0.0
    accumulator_ms: float = 0.0
    physics_steps: int = 0
    drift_percentage: float = 0.0
    spiral_warning: bool = False


class TimestepManager:
    """
    Manages hybrid timestep execution with drift detection.
    
    Features:
    - Three modes: FIXED (deterministic), VARIABLE (smooth), HYBRID (both)
    - Drift detection with automatic warnings
    - Performance diagnostics with FPS tracking
    - Accumulator management to prevent spiral-of-death scenarios
    """
    
    def __init__(
        self,
        mode: TimestepMode = TimestepMode.HYBRID,
        fixed_timestep: float = 1.0 / 60.0,  # 60 Hz
        max_accumulator: float = 0.25,        # Max 250ms accumulation
        drift_threshold: float = 0.001        # 0.1% drift warning threshold
    ):
        self.mode = mode
        self.fixed_timestep = fixed_timestep
        self.max_accumulator = max_accumulator
        self.drift_threshold = drift_threshold
        
        # Internal state
        self.accumulator = 0.0
        self.last_time = time.perf_counter()
        self.frame_count = 0
        self.fps_update_interval = 1.0
        self.fps_timer = 0.0
        
        # Diagnostics
        self.diagnostics = TimestepDiagnostics()
        self._frame_times: list[float] = []
        
    def update(self) -> tuple[list[float], float]:
        """
        Update timestep and return physics steps and interpolation alpha.
        
        Returns:
            (physics_deltas, alpha): List of fixed timesteps for physics and interpolation factor
        """
        current_time = time.perf_counter()
        frame_time = current_time - self.last_time
        self.last_time = current_time
        
        # Track frame times for FPS calculation
        self._frame_times.append(frame_time)
        if len(self._frame_times) > 100:
            self._frame_times.pop(0)
        
        # Update FPS counter
        self.fps_timer += frame_time
        self.frame_count += 1
        if self.fps_timer >= self.fps_update_interval:
            self.diagnostics.fps = self.frame_count / self.fps_timer
            self.frame_count = 0
            self.fps_timer = 0.0
        
        self.diagnostics.frame_time_ms = frame_time * 1000.0
        
        if self.mode == TimestepMode.FIXED:
            return self._update_fixed()
        elif self.mode == TimestepMode.VARIABLE:
            return self._update_variable(frame_time)
        else:  # HYBRID
            return self._update_hybrid(frame_time)
    
    def _update_fixed(self) -> tuple[list[float], float]:
        """Fixed timestep mode - deterministic but may skip frames"""
        return ([self.fixed_timestep], 1.0)
    
    def _update_variable(self, frame_time: float) -> tuple[list[float], float]:
        """Variable timestep mode - smooth but non-deterministic"""
        # Clamp frame time to prevent huge jumps
        clamped_time = min(frame_time, self.max_accumulator)
        return ([clamped_time], 1.0)
    
    def _update_hybrid(self, frame_time: float) -> tuple[list[float], float]:
        """
        Hybrid mode - fixed timestep physics with variable rendering.
        Uses accumulator pattern to decouple physics from rendering.
        """
        # Add frame time to accumulator
        self.accumulator += frame_time
        
        # Prevent spiral of death
        if self.accumulator > self.max_accumulator:
            drift = (self.accumulator - self.max_accumulator) / self.max_accumulator
            self.diagnostics.drift_percentage = drift * 100.0
            
            if drift > self.drift_threshold:
                self.diagnostics.spiral_warning = True
            
            # Clamp accumulator
            self.accumulator = self.max_accumulator
        else:
            self.diagnostics.spiral_warning = False
            self.diagnostics.drift_percentage = 0.0
        
        # Process fixed timesteps
        physics_steps = []
        step_count = 0
        while self.accumulator >= self.fixed_timestep:
            physics_steps.append(self.fixed_timestep)
            self.accumulator -= self.fixed_timestep
            step_count += 1
        
        # Calculate interpolation alpha for rendering
        alpha = self.accumulator / self.fixed_timestep
        
        # Update diagnostics
        self.diagnostics.physics_steps = step_count
        self.diagnostics.accumulator_ms = self.accumulator * 1000.0
        
        return (physics_steps, alpha)
    
    def get_diagnostics(self) -> TimestepDiagnostics:
        """Get current performance diagnostics"""
        return self.diagnostics
    
    def reset(self) -> None:
        """Reset timestep manager state"""
        self.accumulator = 0.0
        self.last_time = time.perf_counter()
        self.frame_count = 0
        self.fps_timer = 0.0
        self._frame_times.clear()
        self.diagnostics = TimestepDiagnostics()
