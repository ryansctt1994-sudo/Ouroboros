"""
Ouroboros Virtual Processor - Mathematical/Epistemic Processor

This module provides the core mathematical operations for the Ouroboros system:
- Ternary cycle normalization
- Delta-check with entropy penalties
- Möbius kernel discretization
- Ramanujan tau function approximations
- Geodesic flow on horn torus
- Modular symmetry operations
- Zeta-seeded ergotropy calculations
"""

import math
from typing import List, Dict, Any, Optional, Tuple, Callable

# Check for extended features (numpy/scipy availability)
try:
    import numpy as np
    from scipy.special import zeta as scipy_zeta
    EXTENDED_FEATURES = True
except ImportError:
    EXTENDED_FEATURES = False


# ============================================================================
# Task Scheduler (Preserved from original implementation)
# ============================================================================

import threading
import time
import heapq
import uuid
from collections import deque


class Task:
    """Represents a scheduled task with priority and optional interval execution."""
    
    def __init__(
        self,
        task_id: str,
        fn: Callable,
        priority: int,
        next_run: float,
        args: tuple = None,
        kwargs: dict = None,
        interval: Optional[float] = None,
        name: Optional[str] = None,
    ):
        self.task_id = task_id
        self.fn = fn
        self.priority = priority
        self.next_run = next_run
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.interval = interval
        self.name = name or f"task_{task_id[:8]}"
        self.cancelled = False
        self.execution_count = 0
    
    def __lt__(self, other):
        """Comparison for heapq: prioritize by next_run, then priority (lower is higher priority)."""
        if self.next_run != other.next_run:
            return self.next_run < other.next_run
        return self.priority < other.priority
    
    def execute(self):
        """Execute the task callable."""
        self.execution_count += 1
        return self.fn(*self.args, **self.kwargs)
    
    def should_repeat(self) -> bool:
        """Check if task should be rescheduled after execution."""
        return self.interval is not None and not self.cancelled
    
    def reschedule(self):
        """Update next_run time for interval tasks."""
        if self.interval:
            self.next_run = time.time() + self.interval


class TaskScheduler:
    """
    Virtual processor with event loop and priority task scheduler.
    
    This class manages a background thread that processes scheduled tasks with
    priority ordering, backpressure controls, and monitoring capabilities.
    
    NOTE: This was the original OuroborosVirtualProcessor, renamed to TaskScheduler
    to preserve the functionality while the main class is refactored for mathematical operations.
    """
    
    def __init__(self):
        self._state = {
            'running': False,
            'errors': [],
            'stats': {
                'tasks_executed': 0,
                'tasks_cancelled': 0,
                'ticks': 0,
            }
        }
        self._monitoring_data = deque(maxlen=1000)  # O(1) append/pop instead of O(n)
        self._task_queue: List[Task] = []  # Min heap for priority queue
        self._task_registry: Dict[str, Task] = {}  # Fast lookup by task_id
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._poll_interval = 0.1
        self._on_tick: Optional[Callable] = None
        self._max_tasks_per_tick = 50
        self._tick_time_budget_ms = 10
    
    def schedule_task(
        self,
        fn: Callable,
        *,
        priority: int = 10,
        delay: float = 0.0,
        interval: Optional[float] = None,
        args: tuple = None,
        kwargs: dict = None,
        name: Optional[str] = None,
    ) -> str:
        """
        Schedule a task for execution.
        
        Args:
            fn: Callable to execute
            priority: Task priority (lower number = higher priority, default 10)
            delay: Initial delay before first execution (seconds, default 0.0)
            interval: If set, task repeats every interval seconds (default None)
            args: Positional arguments for fn (default None)
            kwargs: Keyword arguments for fn (default None)
            name: Optional task name for debugging (default None)
        
        Returns:
            task_id: Unique identifier for the scheduled task
        """
        task_id = str(uuid.uuid4())
        next_run = time.time() + delay
        
        task = Task(
            task_id=task_id,
            fn=fn,
            priority=priority,
            next_run=next_run,
            args=args,
            kwargs=kwargs,
            interval=interval,
            name=name,
        )
        
        with self._lock:
            self._task_registry[task_id] = task
            heapq.heappush(self._task_queue, task)
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Unique identifier of the task to cancel
        
        Returns:
            True if task was found and cancelled, False otherwise
        """
        with self._lock:
            task = self._task_registry.get(task_id)
            if task and not task.cancelled:
                task.cancelled = True
                self._state['stats']['tasks_cancelled'] += 1
                return True
            return False
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all active (non-cancelled) tasks with safe metadata.
        
        Returns:
            List of task metadata dictionaries
        """
        with self._lock:
            tasks_info = []
            for task in self._task_registry.values():
                if not task.cancelled:
                    tasks_info.append({
                        'task_id': task.task_id,
                        'name': task.name,
                        'priority': task.priority,
                        'next_run': task.next_run,
                        'interval': task.interval,
                        'execution_count': task.execution_count,
                    })
            return tasks_info
    
    def start_event_loop(
        self,
        poll_interval: float = 0.1,
        on_tick: Optional[Callable] = None,
        max_tasks_per_tick: int = 50,
        tick_time_budget_ms: int = 10,
    ):
        """
        Start the background event loop.
        
        Args:
            poll_interval: Interval between event loop ticks (seconds, default 0.1)
            on_tick: Optional callback invoked each tick (default None)
            max_tasks_per_tick: Maximum tasks to execute per tick (default 50)
            tick_time_budget_ms: Maximum time budget for task execution per tick (ms, default 10)
        """
        if self._state['running']:
            return
        
        self._poll_interval = poll_interval
        self._on_tick = on_tick
        self._max_tasks_per_tick = max_tasks_per_tick
        self._tick_time_budget_ms = tick_time_budget_ms
        self._state['running'] = True
        
        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()
    
    def stop_event_loop(self):
        """Stop the background event loop."""
        self._state['running'] = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
    
    def _event_loop(self):
        """Main event loop running in background thread."""
        while self._state['running']:
            tick_start = time.time()
            
            try:
                # Execute scheduled tasks with backpressure controls
                self._execute_due_tasks()
                
                # Invoke user tick callback if provided
                if self._on_tick:
                    self._on_tick()
                
                self._state['stats']['ticks'] += 1
                
                # Record monitoring data
                self._monitoring_data.append({
                    'timestamp': time.time(),
                    'tick_duration': time.time() - tick_start,
                    'queue_size': len(self._task_queue),
                })
                
            except Exception as e:
                # Never crash the event loop
                self._state['errors'].append({
                    'timestamp': time.time(),
                    'error': str(e),
                    'type': type(e).__name__,
                })
            
            # Sleep for remaining poll interval
            elapsed = time.time() - tick_start
            sleep_time = max(0, self._poll_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _execute_due_tasks(self):
        """Execute tasks that are due, respecting backpressure controls."""
        current_time = time.time()
        tick_start = current_time
        tick_budget_seconds = self._tick_time_budget_ms / 1000.0
        tasks_executed = 0
        
        while tasks_executed < self._max_tasks_per_tick:
            # Check time budget
            if (time.time() - tick_start) >= tick_budget_seconds:
                break
            
            # Get next due task
            with self._lock:
                if not self._task_queue:
                    break
                
                # Peek at next task
                if self._task_queue[0].next_run > current_time:
                    break
                
                task = heapq.heappop(self._task_queue)
            
            # Skip cancelled tasks
            if task.cancelled:
                with self._lock:
                    self._task_registry.pop(task.task_id, None)
                continue
            
            # Execute task
            try:
                task.execute()
                self._state['stats']['tasks_executed'] += 1
                tasks_executed += 1
                
                # Reschedule interval tasks
                if task.should_repeat():
                    task.reschedule()
                    with self._lock:
                        heapq.heappush(self._task_queue, task)
                else:
                    with self._lock:
                        self._task_registry.pop(task.task_id, None)
                        
            except Exception as e:
                # Record error but continue execution
                self._state['errors'].append({
                    'timestamp': time.time(),
                    'error': str(e),
                    'type': type(e).__name__,
                    'task_id': task.task_id,
                    'task_name': task.name,
                })
                
                # Clean up failed task
                with self._lock:
                    self._task_registry.pop(task.task_id, None)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current processor state (thread-safe)."""
        with self._lock:
            return {
                'running': self._state['running'],
                'error_count': len(self._state['errors']),
                'stats': self._state['stats'].copy(),
                'queue_size': len(self._task_queue),
                'active_tasks': len([t for t in self._task_registry.values() if not t.cancelled]),
            }
    
    def get_monitoring_data(self) -> List[Dict[str, Any]]:
        """Get recent monitoring data (thread-safe)."""
        with self._lock:
            return list(self._monitoring_data)


# ============================================================================
# Mathematical/Epistemic OuroborosVirtualProcessor
# ============================================================================

class OuroborosVirtualProcessor:
    """
    Mathematical/Epistemic Virtual Processor for Ouroboros.
    
    Provides core mathematical operations:
    - Ternary cycle normalization on probability simplices
    - Delta-check with entropy penalties
    - Möbius kernel discretization for number-theoretic grounding
    - Ramanujan tau function approximations
    - Geodesic flow on horn torus
    - Modular symmetry operations
    - Zeta-seeded ergotropy calculations
    """
    
    def __init__(
        self, 
        radius: float = 1.0, 
        lambda_: float = 0.3, 
        threshold: float = 0.4, 
        zeta_seed: float = 0.0
    ):
        """
        Initialize the OuroborosVirtualProcessor.
        
        Args:
            radius: Torus radius (default: 1.0)
            lambda_: Lambda parameter (default: 0.3)
            threshold: Delta-check threshold (default: 0.4)
            zeta_seed: Zeta seed for extended features (default: 0.0)
        """
        self.R = radius
        self.lambda_ = lambda_
        self.threshold = threshold
        self.zeta_seed = zeta_seed
    
    def ternary_cycle(self, V: List[float]) -> List[float]:
        """
        Normalize input vector to non-negative, sum-to-1 (ternary cycle).
        
        Handles variable-length vectors, projects negatives to 0, normalizes to sum=1.
        
        Args:
            V: Input vector (any length)
            
        Returns:
            Normalized vector as a list
        """
        EPS = 1e-15
        
        # Handle empty vector
        if not V:
            return []
        
        # Project to non-negative
        V_nonneg = [max(0.0, v) for v in V]
        
        # Compute sum
        total = sum(V_nonneg)
        
        # Handle all-zero input with EPS fallback
        if total <= EPS:
            # Return uniform distribution
            n = len(V)
            return [1.0 / n] * n
        
        # Normalize to sum to 1
        return [v / total for v in V_nonneg]
    
    def delta_check(
        self, 
        V_expected: List[float], 
        V_observed: List[float]
    ) -> Dict[str, Any]:
        """
        Compute divergence between expected and observed vectors with entropy penalty.
        
        Args:
            V_expected: Expected vector
            V_observed: Observed vector
            
        Returns:
            Dictionary with keys "delta" (float) and "verdict" ("PASS" or "FAIL")
        """
        EPS = 1e-12
        
        # Normalize both vectors
        V_exp_norm = self.ternary_cycle(V_expected)
        V_obs_norm = self.ternary_cycle(V_observed)
        
        # Compute L1 distance
        l1_dist = sum(abs(e - o) for e, o in zip(V_exp_norm, V_obs_norm))
        
        # Compute entropy penalty for observed vector
        entropy_penalty = 0.0
        for p in V_obs_norm:
            if p > EPS:
                entropy_penalty -= p * math.log(p)
        
        # Combine with lambda weighting
        delta = l1_dist + self.lambda_ * entropy_penalty
        
        # Determine verdict
        verdict = "PASS" if delta <= self.threshold else "FAIL"
        
        return {
            "delta": delta,
            "verdict": verdict
        }
    
    def mobius_kernel(self, n: int, discretization: int = 100) -> List[float]:
        """
        Compute Möbius kernel discretization.
        
        Returns a list of N values based on the Möbius function μ(n):
        - μ(n) = 1 if n is square-free with even number of prime factors
        - μ(n) = -1 if n is square-free with odd number of prime factors  
        - μ(n) = 0 if n has a squared prime factor
        
        Args:
            n: Integer for Möbius function evaluation
            discretization: Number of discretization points (default: 100)
            
        Returns:
            List of kernel values with oscillation pattern μ(n) * cos(2πk/N) / (k+1)
        """
        if not EXTENDED_FEATURES:
            # Fallback: return zeros if extended features not available
            return [0.0] * discretization
        
        # Compute Möbius function value
        mu_n = self._mobius_mu(n)
        
        # Generate kernel with oscillation pattern
        kernel = []
        N = discretization
        for k in range(N):
            # μ(n) * cos(2πk/N) / (k+1)
            theta = 2 * math.pi * k / N
            value = mu_n * math.cos(theta) / (k + 1)
            kernel.append(value)
        
        return kernel
    
    def _mobius_mu(self, n: int) -> int:
        """
        Compute Möbius function μ(n).
        
        Args:
            n: Positive integer
            
        Returns:
            μ(n): 1, -1, or 0
        """
        if n <= 0:
            return 0
        if n == 1:
            return 1
        
        # Factor n and count prime factors
        prime_count = 0
        temp_n = n
        
        # Check for factor 2
        if temp_n % 2 == 0:
            prime_count += 1
            temp_n //= 2
            # Check for squared factor
            if temp_n % 2 == 0:
                return 0
        
        # Check odd factors
        p = 3
        while p * p <= temp_n:
            if temp_n % p == 0:
                prime_count += 1
                temp_n //= p
                # Check for squared factor
                if temp_n % p == 0:
                    return 0
            p += 2
        
        # If temp_n > 1, it's a prime factor
        if temp_n > 1:
            prime_count += 1
        
        # Return based on parity of prime count
        return -1 if prime_count % 2 == 1 else 1
    
    def ramanujan_tau(self, n: int) -> float:
        """
        Compute Ramanujan tau function τ(n) approximation.
        
        For n ≤ 0, returns 0.0.
        Extended mode (EXTENDED_FEATURES=True): Returns τ(1) = 1.0 (mathematically correct)
        Fallback mode: Uses formula n² - 24n (which gives -23 for n=1)
        
        Args:
            n: Integer argument
            
        Returns:
            τ(n) approximation as float
        """
        if n <= 0:
            return 0.0
        
        # Special case: τ(1) = 1 in extended mode
        if n == 1:
            if EXTENDED_FEATURES:
                return 1.0
            else:
                # Fallback uses formula n² - 24n which gives -23 for n=1
                return float(n * n - 24 * n)
        
        # Base approximation: n² - 24n
        base = n * n - 24 * n
        
        if EXTENDED_FEATURES and self.zeta_seed != 0.0:
            # Extended mode with correction
            correction = self.zeta_seed * math.log(n + 1)
            return float(base + correction)
        else:
            # Fallback mode
            return float(base)
    
    def geodesic_flow(self, phi: float, theta: float) -> Tuple[float, float, float]:
        """
        Compute parametric horn torus geodesic flow.
        
        Parametric equations:
        x = R(1 + cos(φ))cos(θ)
        y = R(1 + cos(φ))sin(θ)
        z = R sin(φ)
        
        Args:
            phi: Poloidal angle
            theta: Toroidal angle
            
        Returns:
            Tuple of (x, y, z) coordinates as floats
        """
        R = self.R
        
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        
        r_xy = R * (1 + cos_phi)
        
        x = r_xy * cos_theta
        y = r_xy * sin_theta
        z = R * sin_phi
        
        return (x, y, z)
    
    def modular_symmetry(self, n: int) -> int:
        """
        Compute modular symmetry (mod 9).
        
        Args:
            n: Integer input
            
        Returns:
            n mod 9 (value in range [0, 8])
        """
        return n % 9
    
    def zeta_ergotropy(self, s: float = 2.0) -> float:
        """
        Compute zeta-seeded ergotropy.
        
        Formula: zeta_seed * ζ(s) * R
        
        Uses scipy.special.zeta if available, otherwise fallback to π²/6 for s=2.
        
        Args:
            s: Riemann zeta function argument (default: 2.0)
            
        Returns:
            Ergotropy value
        """
        if EXTENDED_FEATURES:
            try:
                zeta_s = scipy_zeta(s)
            except (ValueError, RuntimeError, Exception):
                # Fallback to Basel problem solution for s=2
                if s == 2.0:
                    zeta_s = math.pi ** 2 / 6.0
                else:
                    zeta_s = 1.0
        else:
            # Fallback mode
            if s == 2.0:
                zeta_s = math.pi ** 2 / 6.0
            else:
                zeta_s = 1.0
        
        return self.zeta_seed * zeta_s * self.R
    
    def snapshot_state(self) -> Dict[str, Any]:
        """
        Return snapshot of current processor state.
        
        Returns:
            Dictionary with processor configuration and state
        """
        snapshot = {
            "radius": self.R,
            "lambda": self.lambda_,
            "threshold": self.threshold,
            "zeta_seed": self.zeta_seed,
            "extended_features": EXTENDED_FEATURES,
            "meta": {
                "version": "1.0",
                "type": "OuroborosVirtualProcessor"
            }
        }
        
        # Add extended features if available
        if EXTENDED_FEATURES:
            snapshot["ergotropy"] = self.zeta_ergotropy()
            snapshot["modular_class"] = self.modular_symmetry(int(self.R * 100))
        
        return snapshot
    
    def extended_delta_check(
        self,
        V_exp: List[float],
        V_obs: List[float],
        use_tau: bool = False
    ) -> Dict[str, Any]:
        """
        Extended delta check with optional tau correction.
        
        Args:
            V_exp: Expected vector
            V_obs: Observed vector
            use_tau: Whether to apply tau correction
            
        Returns:
            Dictionary with delta, tau_correction, delta_extended, verdict_extended
        """
        # Base delta check
        base_result = self.delta_check(V_exp, V_obs)
        delta = base_result["delta"]
        
        # Compute tau correction if requested
        tau_correction = 0.0
        if use_tau and EXTENDED_FEATURES:
            # Use tau(n) where n is derived from vector length
            n = len(V_exp)
            tau_correction = self.ramanujan_tau(n) * 1e-6  # Small correction factor
        
        # Extended delta
        delta_extended = delta + tau_correction
        
        # Extended verdict
        verdict_extended = "PASS" if delta_extended <= self.threshold else "FAIL"
        
        return {
            "delta": delta,
            "tau_correction": tau_correction,
            "delta_extended": delta_extended,
            "verdict_extended": verdict_extended
        }


# ============================================================================
# Factory Function
# ============================================================================

def create_elpis_processor(config: Optional[Dict[str, Any]] = None) -> OuroborosVirtualProcessor:
    """
    Factory function to create an OuroborosVirtualProcessor from configuration.
    
    Args:
        config: Optional configuration dictionary with keys:
            - radius (default: 1.0)
            - lambda (default: 0.3)
            - threshold (default: 0.4)
            - zeta_seed (default: 0.0)
    
    Returns:
        Configured OuroborosVirtualProcessor instance
    """
    if config is None:
        config = {}
    
    radius = config.get("radius", 1.0)
    lambda_ = config.get("lambda", 0.3)
    threshold = config.get("threshold", 0.4)
    zeta_seed = config.get("zeta_seed", 0.0)
    
    return OuroborosVirtualProcessor(
        radius=radius,
        lambda_=lambda_,
        threshold=threshold,
        zeta_seed=zeta_seed
    )

