"""
Ouroboros Virtual Processor - Mathematical/Epistemic Processor

This module provides the core mathematical operations for the Ouroboros system:
- Ternary cycle normalization
- Delta-check with entropy penalties
- Möbius kernel discretization
- Ramanujan tau function approximations
- Geodesic flow on torus manifolds
- Modular symmetry operations
- Zeta-seeded ergotropy calculations
"""

import math
import threading
import time
import heapq
import uuid
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Callable

# Check for extended features (numpy/scipy availability)
np = None
scipy_zeta = None
EXTENDED_FEATURES = False

try:
    import numpy as np
    from scipy.special import zeta as scipy_zeta
    EXTENDED_FEATURES = True
except ImportError:
    pass


def _py_scalar(x: Any) -> Any:
    """Normalize NumPy scalar values to native Python scalar types."""
    try:
        if np is not None and isinstance(x, np.generic):
        if EXTENDED_FEATURES and isinstance(x, np.generic):
            return x.item()
    except Exception:
        pass
    return x


TAU = 2.0 * math.pi

# Rollback-friendly signature for operational torus geometry patches
GEOMETRY_RUNTIME_PATCH_SIGNATURE = {
    "id": "torus-runtime-v1-stability",
    "description": "Operational torus decision modulation with normalized penalties",
    "commits": [
        "c7144c0",  # initial runtime hook integration
        "3044ce7",  # stability/normalization upgrades
    ],
}


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _frac(x: float) -> float:
    return x - math.floor(x)


def _wrap_angle_rad(a: float) -> float:
    return a % TAU


def _angle_delta(a: float, b: float) -> float:
    """Smallest signed circular difference (a-b) in (-pi, pi]."""
    d = (a - b) % TAU
    if d > math.pi:
        d -= TAU
    return d


def _safe_float(x: Any) -> float:
    return float(_py_scalar(x))


def _finite_or(x: Any, fallback: float = 0.0) -> float:
    """Return finite float value or fallback when NaN/Inf is encountered."""
    value = _safe_float(x)
    return value if math.isfinite(value) else fallback


@dataclass(frozen=True)
class TorusParams:
    """Major/minor torus radii container with validation and type classification."""

    R: float
    r: Optional[float] = None

    def minor(self) -> float:
        return self.R if self.r is None else self.r

    def validate(self) -> None:
        if self.R <= 0:
            raise ValueError("Major radius R must be > 0.")
        if self.minor() <= 0:
            raise ValueError("Minor radius r must be > 0.")

    def torus_type(self, eps: float = 1e-12) -> str:
        r = self.minor()
        if abs(self.R - r) <= eps:
            return "horn"
        if self.R > r:
            return "ring"
        return "spindle"


def torus_point(phi: float, theta: float, tp: TorusParams) -> Tuple[float, float, float]:
    """Surface parameterization of a torus (surface point, not geodesic integration)."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    cphi = math.cos(phi)
    sphi = math.sin(phi)
    cth = math.cos(theta)
    sth = math.sin(theta)

    rho = R + r * cphi
    return (rho * cth, rho * sth, r * sphi)


def torus_metric(phi: float, tp: TorusParams) -> Tuple[float, float, float]:
    """Return first fundamental form coefficients (E, F, G)."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    return (r * r, 0.0, (R + r * math.cos(phi)) ** 2)


def torus_area_element(phi: float, tp: TorusParams) -> float:
    """Return area element sqrt(det(g)) = r * (R + r*cos(phi))."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    return r * (R + r * math.cos(phi))


def torus_gaussian_curvature(phi: float, tp: TorusParams, eps: float = 1e-12) -> float:
    """Return Gaussian curvature K(phi) = cos(phi)/(r*(R+r*cos(phi)))."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    denom = r * (R + r * math.cos(phi))
    if abs(denom) < eps:
        return 0.0
    return math.cos(phi) / denom


def map_state_to_torus_angles(u: float, v: float) -> Tuple[float, float]:
    """Deterministically map scalar state values to torus angles in [0, 2π)."""
    return (_wrap_angle_rad(TAU * _frac(_safe_float(u))), _wrap_angle_rad(TAU * _frac(_safe_float(v))))


def geometry_patch_signature() -> Dict[str, Any]:
    """Return immutable signature metadata for runtime torus geometry patches."""
    return {
        "id": GEOMETRY_RUNTIME_PATCH_SIGNATURE["id"],
        "description": GEOMETRY_RUNTIME_PATCH_SIGNATURE["description"],
        "commits": list(GEOMETRY_RUNTIME_PATCH_SIGNATURE["commits"]),
    }


def geometry_features(
    tp: TorusParams,
    phi: float,
    theta: float,
    prev_phi: Optional[float] = None,
    prev_theta: Optional[float] = None,
    curvature_gain: float = 1.0,
    use_curvature: bool = True,
    ds_cap: Optional[float] = None,
    normalize_ds: bool = True,
) -> Dict[str, Any]:
    """Compute runtime torus geometry features for control and telemetry."""
    tp.validate()
    R = tp.R
    r = tp.minor()

    phi = _wrap_angle_rad(phi)
    theta = _wrap_angle_rad(theta)

    x, y, z = torus_point(phi, theta, tp)
    E, F, G = torus_metric(phi, tp)
    dA = torus_area_element(phi, tp)

    dA_max = r * (R + r)
    w_area = 0.0 if dA_max <= 0 else _clamp(_finite_or(dA / dA_max, 0.0), 0.0, 1.0)

    K = 0.0
    w_curv = 0.5
    if use_curvature:
        K = _finite_or(torus_gaussian_curvature(phi, tp), 0.0)
        gain = _finite_or(curvature_gain, 1.0)
        w_curv = 0.5 * (1.0 + math.tanh(gain * K))

    ds = None
    ds_norm = None
    if prev_phi is not None and prev_theta is not None:
        dphi = _angle_delta(phi, prev_phi)
        dtheta = _angle_delta(theta, prev_theta)
        ds2 = (E * dphi * dphi) + (G * dtheta * dtheta)
        ds = math.sqrt(max(_finite_or(ds2, 0.0), 0.0))

        if normalize_ds:
            g_max = (R + r) ** 2
            ds_char = math.sqrt((r * r) * (math.pi ** 2) + g_max * (math.pi ** 2))
            ds_char = max(ds_char, 1e-12)
            ds_norm = _clamp(ds / ds_char, 0.0, 1.0)

        if ds_cap is not None:
            cap = max(_finite_or(ds_cap, 0.0), 0.0)
            ds = min(ds, cap)

    return {
        "phi": float(phi),
        "theta": float(theta),
        "xyz": (float(x), float(y), float(z)),
        "metric": (float(E), float(F), float(G)),
        "dA": float(dA),
        "w_area": float(w_area),
        "K": float(K),
        "w_curv": float(w_curv),
        "ds": None if ds is None else float(ds),
        "ds_norm": None if ds_norm is None else float(ds_norm),
        "torus_type": tp.torus_type(),
    }


def _py_scalar(x: Any) -> Any:
    """Normalize NumPy scalar values to native Python scalar types."""
    try:
        if np is not None and isinstance(x, np.generic):
            return x.item()
    except Exception:
        pass
    return x


TAU = 2.0 * math.pi
PHASE_LOCK_RATE_LIMIT_SECONDS = 0.01

# Rollback-friendly signature for operational torus geometry patches
GEOMETRY_RUNTIME_PATCH_SIGNATURE = {
    "id": "torus-runtime-v1-stability",
    "description": "Operational torus decision modulation with normalized penalties",
    "commits": [
        "c7144c0",  # initial runtime hook integration
        "3044ce7",  # stability/normalization upgrades
    ],
}


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _frac(x: float) -> float:
    return x - math.floor(x)


def _wrap_angle_rad(a: float) -> float:
    return a % TAU


def _angle_delta(a: float, b: float) -> float:
    """Smallest signed circular difference (a-b) in (-pi, pi]."""
    d = (a - b) % TAU
    if d > math.pi:
        d -= TAU
    return d


def _safe_float(x: Any) -> float:
    return float(_py_scalar(x))


def _finite_or(x: Any, fallback: float = 0.0) -> float:
    """Return finite float value or fallback when NaN/Inf is encountered."""
    value = _safe_float(x)
    return value if math.isfinite(value) else fallback


@dataclass(frozen=True)
class TorusParams:
    """Major/minor torus radii container with validation and type classification."""

    R: float
    r: Optional[float] = None

    def minor(self) -> float:
        return self.R if self.r is None else self.r

    def validate(self) -> None:
        if self.R <= 0:
            raise ValueError("Major radius R must be > 0.")
        if self.minor() <= 0:
            raise ValueError("Minor radius r must be > 0.")

    def torus_type(self, eps: float = 1e-12) -> str:
        r = self.minor()
        if abs(self.R - r) <= eps:
            return "horn"
        if self.R > r:
            return "ring"
        return "spindle"


def torus_point(phi: float, theta: float, tp: TorusParams) -> Tuple[float, float, float]:
    """Surface parameterization of a torus (surface point, not geodesic integration)."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    rho = R + r * math.cos(phi)
    return (
        rho * math.cos(theta),
        rho * math.sin(theta),
        r * math.sin(phi),
    )


def torus_metric(phi: float, tp: TorusParams) -> Tuple[float, float, float]:
    """Return first fundamental form coefficients (E, F, G)."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    return (r * r, 0.0, (R + r * math.cos(phi)) ** 2)


def torus_area_element(phi: float, tp: TorusParams) -> float:
    """Return area element sqrt(det(g)) = r * (R + r*cos(phi))."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    return r * (R + r * math.cos(phi))


def torus_gaussian_curvature(phi: float, tp: TorusParams, eps: float = 1e-12) -> float:
    """Return Gaussian curvature K(phi) = cos(phi)/(r*(R+r*cos(phi)))."""
    tp.validate()
    R = tp.R
    r = tp.minor()
    denom = r * (R + r * math.cos(phi))
    if abs(denom) < eps:
        return 0.0
    return math.cos(phi) / denom


def map_state_to_torus_angles(u: float, v: float) -> Tuple[float, float]:
    """Deterministically map scalar state values to torus angles in [0, 2π)."""
    return (
        _wrap_angle_rad(TAU * _frac(_safe_float(u))),
        _wrap_angle_rad(TAU * _frac(_safe_float(v))),
    )


def geometry_patch_signature() -> Dict[str, Any]:
    """Return immutable signature metadata for runtime torus geometry patches."""
    return {
        "id": GEOMETRY_RUNTIME_PATCH_SIGNATURE["id"],
        "description": GEOMETRY_RUNTIME_PATCH_SIGNATURE["description"],
        "commits": list(GEOMETRY_RUNTIME_PATCH_SIGNATURE["commits"]),
    }


def geometry_features(
    tp: TorusParams,
    phi: float,
    theta: float,
    prev_phi: Optional[float] = None,
    prev_theta: Optional[float] = None,
    curvature_gain: float = 1.0,
    use_curvature: bool = True,
    ds_cap: Optional[float] = None,
    normalize_ds: bool = True,
) -> Dict[str, Any]:
    """Compute runtime torus geometry features for control and telemetry."""
    tp.validate()
    R = tp.R
    r = tp.minor()

    phi = _wrap_angle_rad(phi)
    theta = _wrap_angle_rad(theta)

    x, y, z = torus_point(phi, theta, tp)
    E, F, G = torus_metric(phi, tp)
    dA = torus_area_element(phi, tp)

    dA_max = r * (R + r)
    w_area = 0.0 if dA_max <= 0 else _clamp(_finite_or(dA / dA_max, 0.0), 0.0, 1.0)

    K = 0.0
    w_curv = 0.5
    if use_curvature:
        K = _finite_or(torus_gaussian_curvature(phi, tp), 0.0)
        gain = _finite_or(curvature_gain, 1.0)
        w_curv = 0.5 * (1.0 + math.tanh(gain * K))

    ds = None
    ds_norm = None
    if prev_phi is not None and prev_theta is not None:
        dphi = _angle_delta(phi, prev_phi)
        dtheta = _angle_delta(theta, prev_theta)
        ds2 = (E * dphi * dphi) + (G * dtheta * dtheta)
        ds = math.sqrt(max(_finite_or(ds2, 0.0), 0.0))

        if normalize_ds:
            g_max = (R + r) ** 2
            ds_char = math.sqrt((r * r) * (math.pi ** 2) + g_max * (math.pi ** 2))
            ds_char = max(ds_char, 1e-12)
            ds_norm = _clamp(ds / ds_char, 0.0, 1.0)

        if ds_cap is not None:
            cap = max(_finite_or(ds_cap, 0.0), 0.0)
            ds = min(ds, cap)

    return {
        "phi": float(phi),
        "theta": float(theta),
        "xyz": (float(x), float(y), float(z)),
        "metric": (float(E), float(F), float(G)),
        "dA": float(dA),
        "w_area": float(w_area),
        "K": float(K),
        "w_curv": float(w_curv),
        "ds": None if ds is None else float(ds),
        "ds_norm": None if ds_norm is None else float(ds_norm),
        "torus_type": tp.torus_type(),
    }


# ----------------------------------------------------------------------------
# Task Scheduler (Preserved from original implementation)
# ----------------------------------------------------------------------------


class Task:
    """Represents a scheduled task with priority and optional interval execution."""
    
    def __init__(
        self,
        task_id: str,
        fn: Callable,
        priority: int,
        next_run: float,
        args: Optional[Tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
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
        self._last_phase_lock_time = 0.0
    
    def schedule_task(
        self,
        fn: Callable,
        *,
        priority: int = 10,
        delay: float = 0.0,
        interval: Optional[float] = None,
        args: Optional[Tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
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

    def monitor_phase_lock(self, phi: float, theta: float, rate_limit: bool = True) -> Dict[str, Any]:
        """Record a phase-lock monitoring sample with optional lightweight rate limiting."""
        now = time.time()
        with self._lock:
            if rate_limit and (now - self._last_phase_lock_time) < PHASE_LOCK_RATE_LIMIT_SECONDS:
                return {"status": "rate_limited", "timestamp": now}
            self._last_phase_lock_time = now

        quaternion = self.quaternion_state(phi, theta)
        sample = {
            "timestamp": now,
            "phi": float(phi),
            "theta": float(theta),
            "phase_locked": True,
            "gradient_magnitude": 0.0,
            "quaternion": quaternion,
        }
        with self._lock:
            self._monitoring_data.append(sample)
        return sample

    def quaternion_state(self, phi: float, theta: float) -> Tuple[float, float, float, float]:
        """Return a normalized quaternion state from angular coordinates with identity fallback."""
        half_phi = 0.5 * phi
        half_theta = 0.5 * theta

        w = math.cos(half_phi) * math.cos(half_theta)
        x = math.sin(half_phi) * math.cos(half_theta)
        y = math.cos(half_phi) * math.sin(half_theta)
        z = math.sin(half_phi) * math.sin(half_theta)

        norm = math.sqrt(w * w + x * x + y * y + z * z)
        if norm <= 1e-12 or not math.isfinite(norm):
            return (1.0, 0.0, 0.0, 0.0)

        return (w / norm, x / norm, y / norm, z / norm)


# ----------------------------------------------------------------------------
# Mathematical/Epistemic OuroborosVirtualProcessor
# ----------------------------------------------------------------------------

class OuroborosVirtualProcessor:
    """
    Mathematical/Epistemic Virtual Processor for Ouroboros.
    
    Provides core mathematical operations:
    - Ternary cycle normalization on probability simplices
    - Delta-check with entropy penalties
    - Möbius kernel discretization for number-theoretic grounding
    - Ramanujan tau function approximations
    - Geodesic flow on torus manifolds
    - Modular symmetry operations
    - Zeta-seeded ergotropy calculations
    """
    
    def __init__(
        self, 
        radius: float = 1.0,
        minor_radius: Optional[float] = None,
        lambda_: float = 0.3, 
        threshold: float = 0.4, 
        zeta_seed: float = 0.0
    ):
        """
        Initialize the OuroborosVirtualProcessor.
        
        Args:
            radius: Major torus radius R (default: 1.0)
            minor_radius: Minor torus radius r (default: None -> horn torus, r=R)
            lambda_: Lambda parameter (default: 0.3)
            threshold: Delta-check threshold (default: 0.4)
            zeta_seed: Zeta seed for extended features (default: 0.0)
        """
        self.R = radius
        self.r = radius if minor_radius is None else minor_radius
        self.radius = self.R
        self.minor_radius = self.r
        self._tp = TorusParams(R=self.R, r=self.r)
        self._tp.validate()
        self.lambda_ = lambda_
        self.threshold = threshold
        self.zeta_seed = zeta_seed
        # Persistent non-orientable memory bucket for Möbius states
        self._quaternion_cache: Dict[str, Dict[str, Any]] = {}
        self._geom_prev: Optional[Tuple[float, float]] = None
        self.geom_score_mix = 0.35
        self.geom_switch_lambda = 0.15
        self.geom_curv_gain = 1.25
        self.use_curvature = True
        self.geom_normalize_ds = True
        self.geom_ds_cap: Optional[float] = None
        self.geom_use_ds_norm = True
        self.geom_score_mode = "magnitude"
    
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
        Compute torus parametric flow using major radius R and minor radius r.

        General torus equations:
        x = (R + r cos(φ)) cos(θ)
        y = (R + r cos(φ)) sin(θ)
        z = r sin(φ)

        Defaults preserve historical horn torus behavior when r = R.

        Args:
            phi: Poloidal angle
            theta: Toroidal angle

        Returns:
            Tuple of (x, y, z) coordinates as floats
        """
        return torus_point(phi, theta, self._tp)

    def torus_metric(self, phi: float) -> Tuple[float, float, float]:
        """Return first fundamental form coefficients (E, F, G) for the torus."""
        return torus_metric(phi, self._tp)

    def torus_area_element(self, phi: float) -> float:
        """Return sqrt(det(g)) = r * (R + r cos(phi))."""
        return torus_area_element(phi, self._tp)
    
    def torus_type(self) -> str:
        """Return torus classification: ring, horn, or spindle."""
        return self._tp.torus_type()

    def _geometry_uv(self, metrics: Dict[str, float]) -> Tuple[float, float]:
        """Derive deterministic torus mapping scalars from runtime metrics."""
        u = _finite_or(metrics.get("u", 0.0), 0.0)
        v = _finite_or(metrics.get("v", 0.0), 0.0)
        u = u + 0.17 * self.zeta_seed
        v = v + 0.31 * self.zeta_seed
        return (u, v)

    def apply_geometry_to_decision(
        self,
        base_score: float,
        switch_penalty: float,
        metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """Apply torus geometry features to runtime score and switch penalty."""
        base_score = _finite_or(base_score, 0.0)
        switch_penalty = _finite_or(switch_penalty, 0.0)

        u, v = self._geometry_uv(metrics)
        phi, theta = map_state_to_torus_angles(u, v)

        prev_phi, prev_theta = (
            self._geom_prev if self._geom_prev is not None else (None, None)
        )
        gf = geometry_features(
            self._tp,
            phi=phi,
            theta=theta,
            prev_phi=prev_phi,
            prev_theta=prev_theta,
            curvature_gain=self.geom_curv_gain,
            use_curvature=self.use_curvature,
            ds_cap=self.geom_ds_cap,
            normalize_ds=self.geom_normalize_ds,
        )
        self._geom_prev = (gf["phi"], gf["theta"])

        w_area = _finite_or(gf["w_area"], 0.5)
        w_curv = _finite_or(gf["w_curv"], 0.5) if self.use_curvature else 0.5
        geometry_gain = _clamp(0.5 * w_area + 0.5 * w_curv, 0.0, 1.0)

        scale = 0.7 + 0.6 * geometry_gain
        mix = _clamp(_finite_or(self.geom_score_mix, 0.0), 0.0, 1.0)

        if self.geom_score_mode == "magnitude":
            sign = -1.0 if base_score < 0 else 1.0
            score_scaled = sign * (abs(base_score) * scale)
        else:
            score_scaled = base_score * scale

        score = _finite_or((1.0 - mix) * base_score + mix * score_scaled, base_score)

        ds_for_penalty = None
        if self.geom_use_ds_norm and gf["ds_norm"] is not None:
            ds_for_penalty = _finite_or(gf["ds_norm"], 0.0)
        elif gf["ds"] is not None:
            ds_for_penalty = _finite_or(gf["ds"], 0.0)

        if ds_for_penalty is not None:
            lam = _finite_or(self.geom_switch_lambda, 0.0)
            switch_penalty = _finite_or(switch_penalty + lam * ds_for_penalty, switch_penalty)

        return {
            "score": float(score),
            "switch_penalty": float(switch_penalty),
            "geometry": gf,
        }

    def modular_symmetry(self, n: int) -> int:
        """
        Compute modular symmetry (mod 9).
        
        Args:
            n: Integer input
            
        Returns:
            n mod 9 (value in range [0, 8])
        """
        return n % 9

    def mobius_handshake(
        self,
        elpis_state: List[float],
        pandora_state: List[float]
    ) -> Dict[str, Any]:
        """Perform a Möbius-style state exchange while preserving simplex invariants."""
        eps = 1e-9

        elpis_norm = self.ternary_cycle(elpis_state)
        pandora_norm = self.ternary_cycle(pandora_state)

        if not elpis_norm or not pandora_norm:
            return {
                "handshake_valid": False,
                "elpis_state_transformed": elpis_norm,
                "pandora_state_transformed": pandora_norm,
                "invariants": {
                    "sum_preserved_elpis": False,
                    "sum_preserved_pandora": False,
                    "nonnegativity_elpis": False,
                    "nonnegativity_pandora": False,
                },
                "metrics": {"delta_elpis": 0.0, "delta_pandora": 0.0},
            }

        mix_ratio = 1.0 / (1.0 + self.R)

        # Non-orientable exchange: each side gets a wrapped contribution from the other.
        elpis_tx = [
            (1.0 - mix_ratio) * a + mix_ratio * pandora_norm[(i + 1) % len(pandora_norm)]
            for i, a in enumerate(elpis_norm)
        ]
        pandora_tx = [
            (1.0 - mix_ratio) * b + mix_ratio * elpis_norm[(i - 1) % len(elpis_norm)]
            for i, b in enumerate(pandora_norm)
        ]

        elpis_tx = self.ternary_cycle(elpis_tx)
        pandora_tx = self.ternary_cycle(pandora_tx)

        invariants = {
            "sum_preserved_elpis": abs(sum(elpis_tx) - 1.0) <= 1e-6,
            "sum_preserved_pandora": abs(sum(pandora_tx) - 1.0) <= 1e-6,
            "nonnegativity_elpis": all(v >= -eps for v in elpis_tx),
            "nonnegativity_pandora": all(v >= -eps for v in pandora_tx),
        }

        delta_elpis = sum(abs(a - b) for a, b in zip(elpis_norm, elpis_tx))
        delta_pandora = sum(abs(a - b) for a, b in zip(pandora_norm, pandora_tx))

        return {
            "handshake_valid": all(invariants.values()),
            "elpis_state_transformed": elpis_tx,
            "pandora_state_transformed": pandora_tx,
            "invariants": invariants,
            "metrics": {
                "delta_elpis": float(delta_elpis),
                "delta_pandora": float(delta_pandora),
            },
        }

    def persistent_mobius_store(self, state_id: str, state: List[float]) -> bool:
        """Store normalized state and its Möbius transform in the persistent cache."""
        if not state_id:
            return False

        normalized = self.ternary_cycle(state)
        if not normalized:
            return False

        n = max(1, int(round(sum((i + 1) * v for i, v in enumerate(normalized)) * 10)))
        transformed = self.ternary_cycle([
            v + 0.01 * k for v, k in zip(normalized, self.mobius_kernel(n, discretization=len(normalized)))
        ])

        self._quaternion_cache[state_id] = {
            "original": normalized,
            "transformed": transformed,
            "mobius_n": n,
        }
        return True

    def persistent_mobius_retrieve(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a previously stored Möbius state from the persistent cache."""
        return self._quaternion_cache.get(state_id)
    
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
                zeta_s = scipy_zeta(s) if scipy_zeta is not None else (math.pi ** 2 / 6.0 if s == 2.0 else 1.0)
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
        
        return float(self.zeta_seed * zeta_s * self.R)
    
    def snapshot_state(self) -> Dict[str, Any]:
        """
        Return snapshot of current processor state.
        
        Returns:
            Dictionary with processor configuration and state
        """
        snapshot = {
            "radius": self.R,
            "minor_radius": self.r,
            "torus_type": self.torus_type(),
            "lambda": self.lambda_,
            "threshold": self.threshold,
            "zeta_seed": self.zeta_seed,
            "geometry_prev": self._geom_prev,
            "geometry_patch_signature": geometry_patch_signature(),
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

        return {k: _py_scalar(v) for k, v in snapshot.items()}
    
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


# ----------------------------------------------------------------------------
# Factory Function
# ----------------------------------------------------------------------------

def create_elpis_processor(config: Optional[Dict[str, Any]] = None) -> OuroborosVirtualProcessor:
    """
    Factory function to create an OuroborosVirtualProcessor from configuration.
    
    Args:
        config: Optional configuration dictionary with keys:
            - radius (default: 1.0)
            - minor_radius (default: None -> uses radius)
            - lambda (default: 0.3)
            - threshold (default: 0.4)
            - zeta_seed (default: 0.0)
    
    Returns:
        Configured OuroborosVirtualProcessor instance
    """
    if config is None:
        config = {}
    
    radius = config.get("radius", 1.0)
    minor_radius = config.get("minor_radius")
    lambda_ = config.get("lambda", 0.3)
    threshold = config.get("threshold", 0.4)
    zeta_seed = config.get("zeta_seed", 0.0)
    
    return OuroborosVirtualProcessor(
        radius=radius,
        minor_radius=minor_radius,
        lambda_=lambda_,
        threshold=threshold,
        zeta_seed=zeta_seed
    )
