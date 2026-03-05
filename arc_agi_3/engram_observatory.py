"""
EngramObservatory
=================
Asynchronous telemetry daemon for the ARC-AGI-3 Mycelium training loop.

Streams three categories of real-time metrics to TensorBoard (or stdout when
TensorBoard is unavailable):

* **Activation metrics** — mean activation magnitude and L2 norm.
* **Sparsity metrics**   — fraction of near-zero activations (dead units).
* **Structural metrics** — bias-corrected participation ratio (PR_bc),
  measuring effective dimensionality of the representation.

The observatory runs in a background :class:`threading.Thread` and consumes
state snapshots pushed by the main training loop via :meth:`push`.  The
daemon accumulates samples in a bounded queue so that the training loop is
never blocked by slow TensorBoard writes.

Usage
-----
Typical integration::

    observatory = EngramObservatory(log_dir="runs/arc_agi_3")
    observatory.start()
    try:
        for step, (obs, act, rew) in enumerate(rollout):
            observatory.push(activations=obs, weights=model_weights, step=step)
    finally:
        observatory.stop()
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional TensorBoard import
# ---------------------------------------------------------------------------

_SummaryWriter = None
_HAS_TB = False

try:
    from torch.utils.tensorboard import SummaryWriter as _TorchSW  # type: ignore

    _SummaryWriter = _TorchSW
    _HAS_TB = True
    logger.debug("Using torch.utils.tensorboard.SummaryWriter")
except ImportError:
    pass

if not _HAS_TB:
    try:
        from tensorboard.summary.writer.event_file_writer import (  # type: ignore
            EventFileWriter,
        )
        from tensorboardX import SummaryWriter as _TBXWriter  # type: ignore

        _SummaryWriter = _TBXWriter
        _HAS_TB = True
        logger.debug("Using tensorboardX.SummaryWriter")
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Internal TensorBoard wrapper with no-op fallback
# ---------------------------------------------------------------------------


class _TBLogger:
    """Thin TensorBoard writer with a graceful no-op fallback."""

    def __init__(self, log_dir: str) -> None:
        self._writer = None
        if _HAS_TB and _SummaryWriter is not None:
            try:
                self._writer = _SummaryWriter(log_dir=log_dir)
                logger.info("TensorBoard writer opened at %s", log_dir)
            except Exception as exc:
                logger.warning("Could not open TensorBoard writer: %s", exc)
        else:
            logger.info(
                "TensorBoard not available — metrics will be logged to stdout only"
            )

    def add_scalar(self, tag: str, value: float, step: int) -> None:
        if self._writer is not None:
            try:
                self._writer.add_scalar(tag, value, global_step=step)
            except Exception as exc:
                logger.debug("TensorBoard write error (%s): %s", tag, exc)

    def close(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# EngramObservatory
# ---------------------------------------------------------------------------

_QUEUE_MAXSIZE = 1024  # bounded buffer prevents unbounded memory growth


class EngramObservatory:
    """Asynchronous real-time telemetry for Mycelium training.

    Parameters
    ----------
    log_dir:
        TensorBoard log directory (default: ``"runs/arc_agi_3"``).
    sparsity_threshold:
        Activations with absolute value below this threshold are considered
        *dead* for the sparsity metric (default: 1e-3).
    poll_interval:
        Seconds between telemetry polls when the queue is empty (default: 0.05).
    """

    def __init__(
        self,
        log_dir: str = "runs/arc_agi_3",
        sparsity_threshold: float = 1e-3,
        poll_interval: float = 0.05,
    ) -> None:
        self._tb = _TBLogger(log_dir=log_dir)
        self._sparsity_threshold = sparsity_threshold
        self._poll_interval = poll_interval

        self._q: queue.Queue = queue.Queue(maxsize=_QUEUE_MAXSIZE)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._step_counter: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Launch the background telemetry daemon thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("EngramObservatory is already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="EngramObservatory",
            daemon=True,
        )
        self._thread.start()
        logger.info("EngramObservatory daemon started.")

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the daemon to stop and wait for it to finish.

        Parameters
        ----------
        timeout:
            Maximum seconds to wait for the daemon to drain and exit.
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(
                    "EngramObservatory daemon did not exit within %.1fs.", timeout
                )
        self._tb.close()
        logger.info("EngramObservatory daemon stopped.")

    def push(
        self,
        activations: np.ndarray,
        weights: Optional[np.ndarray] = None,
        step: Optional[int] = None,
    ) -> None:
        """Submit a state snapshot to the telemetry queue.

        This method is non-blocking — if the queue is full the snapshot is
        silently dropped to avoid stalling the training loop.

        Parameters
        ----------
        activations:
            1-D (or higher-D, will be flattened) activation vector.
        weights:
            Optional weight matrix for structural metrics.  When ``None``
            the participation ratio is computed from ``activations`` alone.
        step:
            Global training step.  When ``None`` an internal counter is used.
        """
        if step is None:
            step = self._step_counter
            self._step_counter += 1
        try:
            self._q.put_nowait((activations, weights, step))
        except queue.Full:
            logger.warning("EngramObservatory queue full — dropping snapshot at step %d", step)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Background daemon loop: drain queue and write metrics."""
        while not self._stop_event.is_set() or not self._q.empty():
            try:
                activations, weights, step = self._q.get(timeout=self._poll_interval)
            except queue.Empty:
                continue
            try:
                self._process(activations, weights, step)
            except Exception as exc:
                logger.error("EngramObservatory processing error at step %d: %s", step, exc)

    def _process(
        self,
        activations: np.ndarray,
        weights: Optional[np.ndarray],
        step: int,
    ) -> None:
        """Compute and log metrics for one snapshot."""
        acts = np.asarray(activations, dtype=float).ravel()

        # --- Activation metrics ---
        act_mean = float(np.mean(np.abs(acts)))
        act_norm = float(np.linalg.norm(acts))

        # --- Sparsity metrics ---
        sparsity = float(np.mean(np.abs(acts) < self._sparsity_threshold))

        # --- Structural metrics (Participation Ratio) ---
        pr_bc = self._participation_ratio(acts)

        # Write to TensorBoard
        self._tb.add_scalar("engram/activation_mean", act_mean, step)
        self._tb.add_scalar("engram/activation_norm", act_norm, step)
        self._tb.add_scalar("engram/sparsity", sparsity, step)
        self._tb.add_scalar("engram/pr_bc", pr_bc, step)

        if weights is not None:
            W = np.asarray(weights, dtype=float)
            if W.ndim >= 2:
                pr_w = self._participation_ratio(W.ravel())
                self._tb.add_scalar("engram/weight_pr_bc", pr_w, step)

        logger.debug(
            "step=%d  act_mean=%.4f  norm=%.4f  sparsity=%.4f  pr_bc=%.4f",
            step,
            act_mean,
            act_norm,
            sparsity,
            pr_bc,
        )

    @staticmethod
    def _participation_ratio(v: np.ndarray, eps: float = 1e-8) -> float:
        """Bias-corrected participation ratio of a 1-D vector.

        Computes :math:`PR_{bc} = (\\sum_i v_i^2)^2 / \\sum_i v_i^4`,
        normalised to [0, 1] by the vector length.
        """
        v2 = v ** 2
        sum2 = float(np.sum(v2))
        sum4 = float(np.sum(v2 ** 2))
        if sum4 < eps:
            return 0.0
        n = len(v)
        raw = (sum2 ** 2) / sum4
        return float(raw / n) if n > 0 else 0.0
