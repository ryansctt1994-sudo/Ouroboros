"""
OuroborosTelemetryDaemon — asynchronous zero-copy telemetry bridge.

Phase 2 of the EDEN telemetry system.  This daemon:

1. Maps shared memory exported by the Rust ``ECSStateBuffer`` via ctypes,
   wrapping the raw pointers into NumPy zero-copy arrays.
2. Asynchronously computes topological / spectral metrics:
   - **Persistent Entropy (PE)** using Gudhi's Rips complex.
   - **Betti-1 (b_1)** loop count from persistent homology.
   - **Bias-Corrected Participation Ratio (PR_bc)** of the activation vector.
3. Logs all metrics to TensorBoard via ``torch.utils.tensorboard`` (or the
   pure-Python ``tensorboard`` writer when PyTorch is absent).
4. Ships a ``SyntheticGraphSimulation`` that validates the full pipeline
   against a 100 000-node synthetic graph.

Usage
-----
Stand-alone daemon::

    python experiments/telemetry_observer.py

With a pre-built ``libeden_ecs`` shared library::

    EDEN_ECS_LIB=/path/to/libeden_ecs.so python experiments/telemetry_observer.py

Run the built-in self-test (no Rust library required)::

    python experiments/telemetry_observer.py --self-test

Dependencies (all optional — graceful degradation when absent)
--------------------------------------------------------------
- numpy          (required for zero-copy arrays)
- gudhi          (required for PE / Betti-1)
- torch          (optional, preferred TensorBoard backend)
- tensorboard    (optional, fallback TensorBoard backend)
- scipy          (optional, improves point-cloud sampling)
"""

from __future__ import annotations

import argparse
import asyncio
import ctypes
import logging
import math
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency guards
# ---------------------------------------------------------------------------

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]
    _HAS_NUMPY = False

try:
    import gudhi  # type: ignore[import]
    _HAS_GUDHI = True
except ImportError:
    gudhi = None  # type: ignore[assignment]
    _HAS_GUDHI = False

# TensorBoard: prefer PyTorch's bundled writer, fall back to standalone.
_SummaryWriter = None
try:
    from torch.utils.tensorboard import SummaryWriter as _SummaryWriter  # type: ignore[import]
    _HAS_TB = True
except ImportError:
    try:
        # PyTorch unavailable — use the pure-Python tensorboard package.
        from tensorboard.summary.writer.event_file_writer import EventFileWriter as _efw  # noqa: F401
        from tensorboard import SummaryWriter as _SummaryWriter  # type: ignore[import]
        _HAS_TB = True
    except ImportError:
        _HAS_TB = False

# ---------------------------------------------------------------------------
# Buffer constants (must match Rust side)
# ---------------------------------------------------------------------------

MAX_ENTITIES: int = 100_000
MAX_EDGES: int = 800_000


# ---------------------------------------------------------------------------
# ctypes FFI binding
# ---------------------------------------------------------------------------

class _ECSLib:
    """Thin ctypes wrapper around ``libeden_ecs``."""

    def __init__(self, lib_path: str) -> None:
        self._lib = ctypes.CDLL(lib_path)
        self._setup_signatures()

    def _setup_signatures(self) -> None:
        lib = self._lib

        lib.ecs_state_buffer_new.restype = ctypes.c_void_p
        lib.ecs_state_buffer_new.argtypes = []

        lib.ecs_state_buffer_free.restype = None
        lib.ecs_state_buffer_free.argtypes = [ctypes.c_void_p]

        lib.ecs_state_buffer_flush.restype = ctypes.c_int
        lib.ecs_state_buffer_flush.argtypes = [
            ctypes.c_void_p,          # buf
            ctypes.POINTER(ctypes.c_double),  # errors
            ctypes.c_size_t,          # n_entities
            ctypes.POINTER(ctypes.c_double),  # acts
            ctypes.POINTER(ctypes.c_double),  # weights
            ctypes.c_size_t,          # n_edges
        ]

        lib.ecs_state_buffer_prediction_errors_ptr.restype = ctypes.POINTER(ctypes.c_double)
        lib.ecs_state_buffer_prediction_errors_ptr.argtypes = [ctypes.c_void_p]

        lib.ecs_state_buffer_activations_ptr.restype = ctypes.POINTER(ctypes.c_double)
        lib.ecs_state_buffer_activations_ptr.argtypes = [ctypes.c_void_p]

        lib.ecs_state_buffer_connectivity_weights_ptr.restype = ctypes.POINTER(ctypes.c_double)
        lib.ecs_state_buffer_connectivity_weights_ptr.argtypes = [ctypes.c_void_p]

        lib.ecs_state_buffer_entity_count.restype = ctypes.c_uint32
        lib.ecs_state_buffer_entity_count.argtypes = [ctypes.c_void_p]

        lib.ecs_state_buffer_edge_count.restype = ctypes.c_uint32
        lib.ecs_state_buffer_edge_count.argtypes = [ctypes.c_void_p]

    # -- convenience wrappers -----------------------------------------------

    def new(self) -> ctypes.c_void_p:
        return self._lib.ecs_state_buffer_new()

    def free(self, buf: ctypes.c_void_p) -> None:
        self._lib.ecs_state_buffer_free(buf)

    def flush(
        self,
        buf: ctypes.c_void_p,
        errors: "np.ndarray",
        acts: "np.ndarray",
        weights: "np.ndarray",
    ) -> int:
        assert _HAS_NUMPY, "numpy is required for FFI flush"
        errors = np.ascontiguousarray(errors, dtype=np.float64)
        acts = np.ascontiguousarray(acts, dtype=np.float64)
        weights = np.ascontiguousarray(weights, dtype=np.float64)
        return self._lib.ecs_state_buffer_flush(
            buf,
            errors.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            len(errors),
            acts.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            weights.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            len(weights),
        )

    def zero_copy_errors(self, buf: ctypes.c_void_p, n: int) -> "np.ndarray":
        ptr = self._lib.ecs_state_buffer_prediction_errors_ptr(buf)
        return np.frombuffer(
            (ctypes.c_double * n).from_address(ctypes.addressof(ptr.contents)),
            dtype=np.float64,
            count=n,
        )

    def zero_copy_activations(self, buf: ctypes.c_void_p, n: int) -> "np.ndarray":
        ptr = self._lib.ecs_state_buffer_activations_ptr(buf)
        return np.frombuffer(
            (ctypes.c_double * n).from_address(ctypes.addressof(ptr.contents)),
            dtype=np.float64,
            count=n,
        )

    def zero_copy_weights(self, buf: ctypes.c_void_p, n_w: int) -> "np.ndarray":
        ptr = self._lib.ecs_state_buffer_connectivity_weights_ptr(buf)
        return np.frombuffer(
            (ctypes.c_double * n_w).from_address(ctypes.addressof(ptr.contents)),
            dtype=np.float64,
            count=n_w,
        )

    def entity_count(self, buf: ctypes.c_void_p) -> int:
        return int(self._lib.ecs_state_buffer_entity_count(buf))

    def edge_count(self, buf: ctypes.c_void_p) -> int:
        return int(self._lib.ecs_state_buffer_edge_count(buf))


# ---------------------------------------------------------------------------
# Geometric / topological metric computations
# ---------------------------------------------------------------------------

def compute_persistent_entropy(points: "np.ndarray", max_edge_length: float = 2.0) -> float:
    """Compute Persistent Entropy (PE) of a 2-D / n-D point cloud.

    PE is the Shannon entropy of the normalised persistence diagram lifetime
    distribution over all finite H_0 and H_1 bars.

    Requires Gudhi.  Returns ``float('nan')`` when Gudhi is absent or the
    diagram is trivial.
    """
    if not _HAS_GUDHI or not _HAS_NUMPY:
        return float("nan")

    if points.ndim != 2 or len(points) < 3:
        return float("nan")

    try:
        rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge_length)
        simplex_tree = rips.create_simplex_tree(max_dimension=2)
        simplex_tree.compute_persistence()
        persistence = simplex_tree.persistence()

        lifetimes = [
            death - birth
            for _, (birth, death) in persistence
            if math.isfinite(death)
        ]
        if not lifetimes:
            return 0.0

        total = sum(lifetimes)
        if total == 0.0:
            return 0.0

        entropy = -sum((l / total) * math.log(l / total) for l in lifetimes if l > 0)
        return float(entropy)
    except Exception as exc:  # pragma: no cover
        logger.warning("compute_persistent_entropy failed: %s", exc)
        return float("nan")


def compute_betti_1(points: "np.ndarray", max_edge_length: float = 2.0) -> int:
    """Compute Betti-1 (number of 1-cycles) from persistent homology.

    A bar in the H_1 persistence diagram whose lifetime exceeds 5 % of the
    maximum lifetime is counted as a significant loop.

    Requires Gudhi.  Returns ``0`` when Gudhi is absent.
    """
    if not _HAS_GUDHI or not _HAS_NUMPY:
        return 0

    if points.ndim != 2 or len(points) < 3:
        return 0

    try:
        rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge_length)
        simplex_tree = rips.create_simplex_tree(max_dimension=2)
        simplex_tree.compute_persistence()

        h1_bars = [
            (death - birth)
            for dim, (birth, death) in simplex_tree.persistence()
            if dim == 1 and math.isfinite(death)
        ]
        if not h1_bars:
            return 0

        threshold = 0.05 * max(h1_bars)
        return sum(1 for l in h1_bars if l > threshold)
    except Exception as exc:  # pragma: no cover
        logger.warning("compute_betti_1 failed: %s", exc)
        return 0


def compute_participation_ratio(activations: "np.ndarray") -> float:
    """Bias-Corrected Participation Ratio (PR_bc) of the activation vector.

    The standard PR is ``(sum x_i)^2 / (N * sum x_i^2)`` normalised to
    ``[0, 1]``.  The bias-corrected form subtracts the finite-sample baseline
    ``1/N``::

        PR_bc = PR - 1/N

    Values near 1 indicate uniform activation (high participation).
    Values near 0 indicate sparse / collapsed activity.

    Returns ``float('nan')`` for empty or all-zero inputs.
    """
    if not _HAS_NUMPY:
        return float("nan")

    a = np.asarray(activations, dtype=np.float64)
    if a.size == 0:
        return float("nan")

    sq_sum = float(np.dot(a, a))
    if sq_sum == 0.0:
        return float("nan")

    s = float(np.sum(a))
    n = a.size
    pr = (s * s) / (n * sq_sum)
    pr_bc = pr - 1.0 / n
    return float(pr_bc)


# ---------------------------------------------------------------------------
# TensorBoard logger
# ---------------------------------------------------------------------------

class _TBLogger:
    """Thin TensorBoard writer wrapper with graceful no-op fallback."""

    def __init__(self, log_dir: str = "runs/telemetry") -> None:
        self._writer = None
        if _HAS_TB and _SummaryWriter is not None:
            try:
                self._writer = _SummaryWriter(log_dir=log_dir)
                logger.info("TensorBoard writer opened at %s", log_dir)
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not open TensorBoard writer: %s", exc)
        else:
            logger.info("TensorBoard not available — metrics will be logged only to stdout")

    def add_scalar(self, tag: str, value: float, step: int) -> None:
        if self._writer is not None:
            try:
                self._writer.add_scalar(tag, value, global_step=step)
            except Exception as exc:  # pragma: no cover
                logger.debug("TensorBoard write error (%s): %s", tag, exc)

    def close(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
            except Exception:  # pragma: no cover
                pass


# ---------------------------------------------------------------------------
# OuroborosTelemetryDaemon
# ---------------------------------------------------------------------------

class OuroborosTelemetryDaemon:
    """Asynchronous zero-copy telemetry bridge between Rust ECS and Python.

    Parameters
    ----------
    lib_path:
        Path to the compiled ``libeden_ecs`` shared library.  When ``None``
        the daemon runs in *simulation mode* using Python-side buffers.
    poll_interval:
        Seconds between telemetry snapshots (default: 0.1 s = 10 Hz).
    log_dir:
        TensorBoard log directory.
    max_edge_length:
        Maximum edge length for Rips complex construction (passed to Gudhi).
    """

    def __init__(
        self,
        lib_path: Optional[str] = None,
        poll_interval: float = 0.1,
        log_dir: str = "runs/telemetry",
        max_edge_length: float = 2.0,
    ) -> None:
        self._poll_interval = poll_interval
        self._max_edge_length = max_edge_length
        self._tb = _TBLogger(log_dir=log_dir)
        self._step = 0
        self._running = False

        # FFI layer (optional)
        self._lib: Optional[_ECSLib] = None
        self._buf: Optional[ctypes.c_void_p] = None

        if lib_path is not None:
            try:
                self._lib = _ECSLib(lib_path)
                self._buf = self._lib.new()
                logger.info("Loaded Rust ECS library from %s", lib_path)
            except OSError as exc:
                logger.warning("Could not load Rust library (%s): %s — using simulation mode", lib_path, exc)

        # Simulation-mode buffers (used when Rust library is absent)
        if _HAS_NUMPY and self._lib is None:
            self._sim_errors: "np.ndarray" = np.zeros(MAX_ENTITIES, dtype=np.float64)
            self._sim_acts: "np.ndarray" = np.zeros(MAX_ENTITIES, dtype=np.float64)
            self._sim_weights: "np.ndarray" = np.zeros(MAX_EDGES, dtype=np.float64)
            self._sim_n_entities: int = 0
            self._sim_n_edges: int = 0

    # -- data ingestion -------------------------------------------------------

    def push_state(
        self,
        prediction_errors: "np.ndarray",
        activations: "np.ndarray",
        connectivity_weights: "np.ndarray",
    ) -> None:
        """Push new ECS state into the shared buffers.

        When the Rust library is loaded this calls ``ecs_state_buffer_flush``
        via ctypes.  In simulation mode the arrays are stored directly.
        """
        if not _HAS_NUMPY:
            return

        if self._lib is not None and self._buf is not None:
            self._lib.flush(self._buf, prediction_errors, activations, connectivity_weights)
        else:
            n_e = min(len(prediction_errors), MAX_ENTITIES)
            n_w = min(len(connectivity_weights), MAX_EDGES)
            self._sim_errors[:n_e] = prediction_errors[:n_e]
            self._sim_errors[n_e:] = 0.0
            self._sim_acts[:n_e] = activations[:n_e]
            self._sim_acts[n_e:] = 0.0
            self._sim_weights[:n_w] = connectivity_weights[:n_w]
            self._sim_weights[n_w:] = 0.0
            self._sim_n_entities = n_e
            self._sim_n_edges = n_w

    # -- zero-copy buffer access -----------------------------------------------

    def _read_buffers(self) -> Tuple["np.ndarray", "np.ndarray", "np.ndarray"]:
        """Return zero-copy (or local) NumPy views of the current state."""
        if not _HAS_NUMPY:
            raise RuntimeError("numpy is required")

        if self._lib is not None and self._buf is not None:
            n_e = self._lib.entity_count(self._buf)
            n_w = self._lib.edge_count(self._buf)
            if n_e == 0:
                return (
                    np.empty(0, dtype=np.float64),
                    np.empty(0, dtype=np.float64),
                    np.empty(0, dtype=np.float64),
                )
            errors = self._lib.zero_copy_errors(self._buf, n_e)
            acts = self._lib.zero_copy_activations(self._buf, n_e)
            weights = self._lib.zero_copy_weights(self._buf, n_w)
            return errors, acts, weights
        else:
            n_e = self._sim_n_entities
            n_w = self._sim_n_edges
            return (
                self._sim_errors[:n_e],
                self._sim_acts[:n_e],
                self._sim_weights[:n_w],
            )

    # -- metric computation --------------------------------------------------

    def compute_metrics(self) -> dict:
        """Compute PE, Betti-1, and PR_bc from the current buffer snapshot.

        Returns a dict with keys ``pe``, ``betti_1``, ``pr_bc``,
        ``entity_count``, and ``edge_count``.
        """
        errors, acts, weights = self._read_buffers()

        result = {
            "entity_count": len(errors),
            "edge_count": len(weights),
            "pe": float("nan"),
            "betti_1": 0,
            "pr_bc": float("nan"),
        }

        if not _HAS_NUMPY or len(acts) == 0:
            return result

        # Participation Ratio (cheap — no Gudhi needed)
        result["pr_bc"] = compute_participation_ratio(acts)

        # Topological metrics require a point cloud.
        # Represent each entity as a 2-D point (error, activation).
        if _HAS_GUDHI and len(errors) >= 3:
            points = np.column_stack([errors, acts])
            result["pe"] = compute_persistent_entropy(points, self._max_edge_length)
            result["betti_1"] = compute_betti_1(points, self._max_edge_length)

        return result

    # -- async event loop ----------------------------------------------------

    async def _observe_once(self) -> None:
        metrics = self.compute_metrics()
        self._step += 1
        step = self._step

        logger.info(
            "step=%d  entities=%d  edges=%d  PE=%.4f  b1=%d  PR_bc=%.4f",
            step,
            metrics["entity_count"],
            metrics["edge_count"],
            metrics["pe"],
            metrics["betti_1"],
            metrics["pr_bc"],
        )

        self._tb.add_scalar("telemetry/persistent_entropy", metrics["pe"], step)
        self._tb.add_scalar("telemetry/betti_1", float(metrics["betti_1"]), step)
        self._tb.add_scalar("telemetry/pr_bc", metrics["pr_bc"], step)
        self._tb.add_scalar("telemetry/entity_count", float(metrics["entity_count"]), step)
        self._tb.add_scalar("telemetry/edge_count", float(metrics["edge_count"]), step)

    async def run(self, max_steps: Optional[int] = None) -> None:
        """Run the telemetry loop indefinitely (or for ``max_steps`` steps)."""
        self._running = True
        logger.info("OuroborosTelemetryDaemon started (poll_interval=%.3fs)", self._poll_interval)
        try:
            while self._running:
                await self._observe_once()
                if max_steps is not None and self._step >= max_steps:
                    break
                await asyncio.sleep(self._poll_interval)
        finally:
            self._running = False
            self._tb.close()
            if self._lib is not None and self._buf is not None:
                self._lib.free(self._buf)
                self._buf = None
            logger.info("OuroborosTelemetryDaemon stopped after %d steps", self._step)

    def stop(self) -> None:
        """Signal the daemon to stop after the current observation."""
        self._running = False


# ---------------------------------------------------------------------------
# Synthetic graph simulation (100 000-node validation)
# ---------------------------------------------------------------------------

class SyntheticGraphSimulation:
    """Drive ``OuroborosTelemetryDaemon`` with a synthetic 100 000-node graph.

    The simulation generates:
    - Gaussian-perturbed prediction errors (mean 0, std 0.1).
    - Uniform-random activations in ``[0, 1]``.
    - Edge weights drawn from ``|N(0, 1)|``.

    It exercises the full pipeline (push → compute → log) for ``n_steps``
    telemetry frames.
    """

    def __init__(
        self,
        n_entities: int = MAX_ENTITIES,
        n_edges: int = MAX_EDGES,
        n_steps: int = 10,
        seed: int = 42,
    ) -> None:
        self.n_entities = n_entities
        self.n_edges = n_edges
        self.n_steps = n_steps
        self.seed = seed

    def run(self, daemon: OuroborosTelemetryDaemon) -> list:
        """Execute the simulation and return a list of per-step metric dicts."""
        if not _HAS_NUMPY:
            logger.error("numpy is required for SyntheticGraphSimulation")
            return []

        rng = np.random.default_rng(self.seed)
        results = []

        logger.info(
            "SyntheticGraphSimulation: %d entities, %d edges, %d steps",
            self.n_entities,
            self.n_edges,
            self.n_steps,
        )

        for step_idx in range(self.n_steps):
            errors = rng.normal(0.0, 0.1, size=self.n_entities)
            acts = rng.uniform(0.0, 1.0, size=self.n_entities)
            weights = np.abs(rng.standard_normal(size=self.n_edges))

            daemon.push_state(errors, acts, weights)
            metrics = daemon.compute_metrics()

            # Log via daemon's internal TensorBoard writer
            daemon._step += 1
            step = daemon._step
            daemon._tb.add_scalar("telemetry/persistent_entropy", metrics["pe"], step)
            daemon._tb.add_scalar("telemetry/betti_1", float(metrics["betti_1"]), step)
            daemon._tb.add_scalar("telemetry/pr_bc", metrics["pr_bc"], step)
            daemon._tb.add_scalar("telemetry/entity_count", float(metrics["entity_count"]), step)
            daemon._tb.add_scalar("telemetry/edge_count", float(metrics["edge_count"]), step)

            logger.info(
                "  [%d/%d] entities=%d  edges=%d  PE=%.4f  b1=%d  PR_bc=%.4f",
                step_idx + 1,
                self.n_steps,
                metrics["entity_count"],
                metrics["edge_count"],
                metrics["pe"],
                metrics["betti_1"],
                metrics["pr_bc"],
            )
            results.append(metrics)

        return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _find_lib() -> Optional[str]:
    """Search common locations for a compiled ``libeden_ecs`` shared library."""
    candidates = [
        os.environ.get("EDEN_ECS_LIB", ""),
        "target/release/libeden_ecs.so",
        "target/release/libeden_ecs.dylib",
        "target/release/eden_ecs.dll",
        "target/debug/libeden_ecs.so",
        "target/debug/libeden_ecs.dylib",
        "target/debug/eden_ecs.dll",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


def main(argv: Optional[list] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="OuroborosTelemetryDaemon — zero-copy ECS telemetry bridge"
    )
    parser.add_argument(
        "--lib",
        default=None,
        help="Path to libeden_ecs shared library (auto-detected when omitted)",
    )
    parser.add_argument(
        "--log-dir",
        default="runs/telemetry",
        help="TensorBoard log directory (default: runs/telemetry)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.1,
        help="Telemetry poll interval in seconds (default: 0.1)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in synthetic graph simulation and exit",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=10,
        help="Number of simulation steps for --self-test (default: 10)",
    )
    args = parser.parse_args(argv)

    lib_path = args.lib or _find_lib()

    daemon = OuroborosTelemetryDaemon(
        lib_path=lib_path,
        poll_interval=args.poll_interval,
        log_dir=args.log_dir,
    )

    if args.self_test:
        sim = SyntheticGraphSimulation(n_steps=args.steps)
        results = sim.run(daemon)
        daemon._tb.close()

        passed = all(
            math.isfinite(r["pr_bc"]) or r["entity_count"] == 0
            for r in results
        )
        if passed:
            logger.info("Self-test PASSED (%d steps)", len(results))
            return 0
        else:
            logger.error("Self-test FAILED — unexpected NaN in PR_bc")
            return 1

    asyncio.run(daemon.run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
