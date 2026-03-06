"""
MuonCANS Optimizer
==================
Muon optimizer with Chebyshev-Accelerated Newton-Schulz (CANS) iterations
to enforce geometric stability during optimization.

The Newton-Schulz iteration orthogonalises the gradient matrix so that
parameter updates lie on the Stiefel manifold, preventing rank collapse and
stabilising attractor dynamics across sequential tasks (Task A → Task B).

Chebyshev acceleration reduces the number of NS iterations needed to
converge to the orthogonal factor, lowering per-step cost while maintaining
geometric guarantees.

Reference implementation is pure-NumPy so it runs without JAX/PyTorch.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Newton-Schulz iteration (Chebyshev-accelerated)
# ---------------------------------------------------------------------------

# Chebyshev coefficients for a degree-5 NS polynomial approximation.
# These coefficients satisfy the minimax polynomial for the orthogonalisation
# map on the interval [0, 1] (singular values normalised to lie in [0, 1]).
_CHEBY_COEFFS: Tuple[float, ...] = (
    3.4445,   # a
    -4.7750,  # b
    2.0315,   # c
)


def _newton_schulz_step(
    G: np.ndarray,
    coeffs: Tuple[float, ...] = _CHEBY_COEFFS,
) -> np.ndarray:
    """One Chebyshev-accelerated Newton-Schulz iteration.

    Given a matrix G with singular values in (0, 1], returns an improved
    approximation to the orthogonal factor U from G = U Σ V^T.

    Args:
        G:      Input matrix of shape (m, n) with m >= n.
        coeffs: Chebyshev polynomial coefficients (a, b, c).

    Returns:
        Updated matrix of the same shape.
    """
    a, b, c = coeffs
    GtG = G.T @ G
    # Degree-3 Chebyshev-NS polynomial: G_new = a*G + b*G*G^T*G + c*G*(G^T*G)^2
    return a * G + b * G @ GtG + c * G @ (GtG @ GtG)


def _orthogonalise(
    G: np.ndarray,
    num_steps: int = 5,
    eps: float = 1e-7,
) -> np.ndarray:
    """Orthogonalise matrix G via Chebyshev-accelerated Newton-Schulz.

    For small matrices (min dimension < 4), Newton-Schulz iterations are
    bypassed and a stable spectral normalisation is returned instead.

    Args:
        G:         Input matrix of shape (m, n).
        num_steps: Number of NS iterations (default 5 is sufficient for fp32).
        eps:       Numerical stabilisation for the spectral norm estimate.

    Returns:
        Orthogonalised matrix of the same shape.
    """
    if G.ndim != 2:
        raise ValueError(f"_orthogonalise expects a 2-D matrix, got shape {G.shape}")

    m, n = G.shape

    # Small-matrix guard: skip NS iterations for tiny matrices
    if min(m, n) < 4:
        spec_norm = np.linalg.norm(G, ord=2)
        if spec_norm < eps:
            return G
        return G / (spec_norm + eps)

    # Transpose so that m >= n (tall matrix)
    transposed = m < n
    if transposed:
        G = G.T

    # Normalise so that the largest singular value is ≤ 1
    spec_norm = np.linalg.norm(G, ord=2)
    if spec_norm < eps:
        return (G.T if transposed else G)
    G = G / (spec_norm + eps)

    for _ in range(num_steps):
        G = _newton_schulz_step(G)

    if transposed:
        G = G.T
    return G


# ---------------------------------------------------------------------------
# MuonCANS optimiser
# ---------------------------------------------------------------------------


class MuonCANS:
    """Muon optimizer with Chebyshev-Accelerated Newton-Schulz orthogonalisation.

    Maintains a momentum buffer (Nesterov-style) and orthogonalises the
    effective gradient before applying the weight update.  For 1-D parameters
    (biases, layer-norms) it falls back to standard SGD with momentum so that
    all parameter shapes are handled uniformly.

    Optionally accepts a **Sakib advantage** signal in :meth:`step` to scale
    the effective learning rate dynamically.  The scaling formula is::

        effective_lr = lr * (sakib_advantage + advantage_eps)

    where ``advantage_eps`` is a small positive offset that prevents stalling
    when the advantage signal is exactly zero.

    After every call to :meth:`step`, per-parameter telemetry is written to
    :attr:`metrics` (a plain dict).  The following keys are always populated:

    * ``policy_delta_norm``  – list of ||Δw|| per parameter.
    * ``cos_w_dw``           – list of cos(∠(w, Δw)) per parameter.
    * ``weight_norm``        – list of ||w|| per parameter.
    * ``grad_weight_cos``    – list of cos(g, w) per parameter (pre-projection).

    When ``track_grad_history=True`` (default), the additional key is populated:

    * ``grad_grad_cos``      – list of cos(g_t, g_{t-1}) per parameter.
      Set to 1.0 on the first step (no previous gradient exists yet).
      Disable with ``track_grad_history=False`` to avoid the per-step
      gradient copy cost for large parameter arrays.

    Args:
        params:             List of parameter arrays (numpy arrays, modified in place).
        lr:                 Learning rate.
        momentum:           Momentum coefficient (default 0.95).
        ns_steps:           Newton-Schulz iterations per step (default 5).
        weight_decay:       L2 regularisation coefficient (default 0.0).
        scalar_decay_mult:  Extra L2 anchoring multiplier for 1-D parameters
                            (default 10.0, must be >= 1.0).
        eps:                Numerical stabilisation constant (default 1e-7).
        advantage_eps:      Small offset added to the Sakib advantage before
                            multiplying by ``lr``, preventing zero-stall
                            (default 1e-4).
        track_grad_history: If ``True`` (default), store a copy of each raw
                            gradient for the next step's ``grad_grad_cos``
                            computation.  Set to ``False`` for large models
                            where the extra allocation is undesirable.
    """

    def __init__(
        self,
        params: List[np.ndarray],
        lr: float = 0.02,
        momentum: float = 0.95,
        ns_steps: int = 5,
        weight_decay: float = 0.0,
        scalar_decay_mult: float = 10.0,
        eps: float = 1e-7,
        advantage_eps: float = 1e-4,
        track_grad_history: bool = True,
    ) -> None:
        if lr <= 0:
            raise ValueError(f"lr must be positive, got {lr}")
        if not (0.0 <= momentum < 1.0):
            raise ValueError(f"momentum must be in [0, 1), got {momentum}")
        if scalar_decay_mult < 1.0:
            raise ValueError(f"scalar_decay_mult must be >= 1.0, got {scalar_decay_mult}")
        if advantage_eps < 0:
            raise ValueError(f"advantage_eps must be non-negative, got {advantage_eps}")

        self.params = params
        self.lr = lr
        self.momentum = momentum
        self.ns_steps = ns_steps
        self.weight_decay = weight_decay
        self.scalar_decay_mult = scalar_decay_mult
        self.eps = eps
        self.advantage_eps = advantage_eps
        self.track_grad_history = track_grad_history

        # Momentum buffers (initialised lazily on first step)
        self._buffers: List[Optional[np.ndarray]] = [None] * len(params)
        # Previous raw-gradient snapshots for grad_grad_cos (only when enabled)
        self._prev_grads: List[Optional[np.ndarray]] = [None] * len(params)
        self.step_count: int = 0

        # Telemetry populated after every call to step()
        self.metrics: Dict[str, List[float]] = {
            "policy_delta_norm": [],
            "cos_w_dw": [],
            "weight_norm": [],
            "grad_weight_cos": [],
            "grad_grad_cos": [],
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _orthogonalise(self, G: np.ndarray) -> np.ndarray:
        """Orthogonalise a matrix using the module-level implementation.

        Convenience instance method so callers can use ``opt._orthogonalise(G)``
        without importing the module-level helper directly.

        Args:
            G: Input matrix of shape (m, n).

        Returns:
            Orthogonalised matrix of the same shape.
        """
        return _orthogonalise(G, num_steps=self.ns_steps, eps=self.eps)

    def step(
        self,
        grads: List[np.ndarray],
        sakib_advantage: Optional[float] = None,
    ) -> None:
        """Apply one optimisation step.

        Args:
            grads:            List of gradient arrays, one per parameter in
                              ``self.params``.  Must match parameter shapes.
            sakib_advantage:  Optional scalar advantage signal (e.g. from the
                              Sakib index).  When provided the effective learning
                              rate for this step becomes::

                                  effective_lr = lr * (sakib_advantage + advantage_eps)

                              Pass ``None`` (default) to use ``lr`` unmodified.

        Raises:
            ValueError: If the number of gradients does not match parameters.
        """
        if len(grads) != len(self.params):
            raise ValueError(
                f"Expected {len(self.params)} gradients, got {len(grads)}"
            )

        # Compute effective learning rate (Sakib advantage scaling)
        if sakib_advantage is not None:
            effective_lr = self.lr * (float(sakib_advantage) + self.advantage_eps)
        else:
            effective_lr = self.lr

        self.step_count += 1

        # Reset per-step telemetry lists
        delta_norms: List[float] = []
        cos_alignments: List[float] = []
        w_norms: List[float] = []
        grad_weight_cosines: List[float] = []
        grad_grad_cosines: List[float] = []

        for i, (param, grad) in enumerate(zip(self.params, grads)):
            if grad is None:
                continue

            g = grad.copy().astype(float)

            # --- Pre-step diagnostics (raw gradient, before any modification) ---
            g_flat = g.ravel()
            g_norm_raw = float(np.linalg.norm(g_flat))
            w_norm_raw = float(np.linalg.norm(param))

            # cos(g_t, w) — is the orthogonal constraint meaningful or cosmetic?
            denom_gw = g_norm_raw * w_norm_raw + self.eps
            cos_gw = float(np.dot(g_flat, param.ravel()) / denom_gw)
            grad_weight_cosines.append(cos_gw)

            # cos(g_t, g_{t-1}) — successive gradient alignment.
            # Healthy learning: cosine trends from weakly positive → more positive.
            # Warning signs: persistently near 0 (random walk), or negative
            # (optimizer undoing its previous step).
            # Only computed (and gradient history only stored) when
            # track_grad_history=True to avoid the per-step allocation cost
            # for large parameter arrays.
            if self.track_grad_history:
                prev_g = self._prev_grads[i]
                if prev_g is not None:
                    prev_norm = float(np.linalg.norm(prev_g))
                    denom_gg = g_norm_raw * prev_norm + self.eps
                    cos_gg = float(np.dot(g_flat, prev_g) / denom_gg)
                else:
                    # First step: no previous gradient — defined as 1.0 by convention.
                    cos_gg = 1.0
                grad_grad_cosines.append(cos_gg)
                self._prev_grads[i] = g_flat.copy()
            else:
                grad_grad_cosines.append(float("nan"))

            # Weight-decay as gradient regularisation
            if self.weight_decay != 0.0:
                g += self.weight_decay * param
                # Extra L2 anchoring for 1-D parameters (biases, layer-norm scales)
                if param.ndim == 1 and self.scalar_decay_mult != 1.0:
                    g += (self.scalar_decay_mult - 1.0) * self.weight_decay * param

            # Momentum update
            if self._buffers[i] is None:
                self._buffers[i] = g.copy()
            else:
                self._buffers[i] = (
                    self.momentum * self._buffers[i] + (1.0 - self.momentum) * g
                )
            effective_grad = self._buffers[i]

            # Orthogonalise 2-D parameters; fall back to RMS-normalised SGD for 1-D
            if effective_grad.ndim >= 2:
                orig_shape = effective_grad.shape
                mat = effective_grad.reshape(orig_shape[0], -1)
                update = _orthogonalise(mat, num_steps=self.ns_steps, eps=self.eps)
                update = update.reshape(orig_shape)
            else:
                # Scalar or 1-D: normalise by RMS for stable scale
                rms = np.sqrt(np.mean(effective_grad ** 2)) + 1e-8
                update = effective_grad / rms

            # --- Post-update telemetry ---
            delta = effective_lr * update
            delta_norm = float(np.linalg.norm(delta))
            w_norm = float(np.linalg.norm(param))
            # Cosine alignment between current weight and update direction
            denom = (w_norm * delta_norm) + self.eps
            cos_val = float(np.dot(param.ravel(), delta.ravel()) / denom)

            delta_norms.append(delta_norm)
            cos_alignments.append(cos_val)
            w_norms.append(w_norm)

            logger.debug(
                "step=%d param=%d policy_delta_norm=%.6g cos_w_dw=%.6g "
                "weight_norm=%.6g grad_weight_cos=%.6g grad_grad_cos=%.6g",
                self.step_count, i, delta_norm, cos_val, w_norm, cos_gw, cos_gg,
            )

            param -= delta

        # Persist telemetry for external inspection
        self.metrics["policy_delta_norm"] = delta_norms
        self.metrics["cos_w_dw"] = cos_alignments
        self.metrics["weight_norm"] = w_norms
        self.metrics["grad_weight_cos"] = grad_weight_cosines
        self.metrics["grad_grad_cos"] = grad_grad_cosines

    def zero_grad(self) -> None:
        """No-op: gradient storage is managed externally by the caller."""

    def reset_metrics(self) -> None:
        """Clear all accumulated telemetry and gradient history.

        Resets ``_prev_grads`` so that ``grad_grad_cos`` starts fresh at 1.0
        on the next call to :meth:`step`, and empties every list inside
        :attr:`metrics`.

        Call this between independent experiments to prevent contamination
        across runs — especially important when sharing a single
        ``MuonCANS`` instance across multiple training phases.
        """
        self._prev_grads = [None] * len(self.params)
        for key in self.metrics:
            self.metrics[key] = []

    def reset_momentum(self) -> None:
        """Zero all initialised momentum buffers in-place and clear gradient history.

        Buffers that have not yet been initialised (``None``) are left as-is.
        Gradient history (used for ``grad_grad_cos``) is also cleared so that
        ``grad_grad_cos`` resets to 1.0 on the first step after the boundary.
        This is useful for resetting optimiser state between tasks without
        reallocating memory (the "ghost-breaker" pattern).
        """
        for buf in self._buffers:
            if buf is not None:
                buf.fill(0.0)
        self._prev_grads = [None] * len(self.params)

    def state_dict(self) -> Dict:
        """Return serialisable optimiser state."""
        return {
            "step_count": self.step_count,
            "lr": self.lr,
            "momentum": self.momentum,
            "ns_steps": self.ns_steps,
            "weight_decay": self.weight_decay,
            "scalar_decay_mult": self.scalar_decay_mult,
            "eps": self.eps,
            "advantage_eps": self.advantage_eps,
            "track_grad_history": self.track_grad_history,
            "buffers": [b.tolist() if b is not None else None for b in self._buffers],
            "metrics": {k: list(v) for k, v in self.metrics.items()},
        }

    def load_state_dict(self, state: Dict) -> None:
        """Restore optimiser state from a dictionary produced by :meth:`state_dict`."""
        self.step_count = state["step_count"]
        self.lr = state["lr"]
        self.momentum = state["momentum"]
        self.ns_steps = state["ns_steps"]
        self.weight_decay = state["weight_decay"]
        self.scalar_decay_mult = state.get("scalar_decay_mult", 10.0)
        self.eps = state.get("eps", 1e-7)
        self.advantage_eps = state.get("advantage_eps", 1e-4)
        self.track_grad_history = state.get("track_grad_history", True)
        self._buffers = [
            np.array(b) if b is not None else None for b in state["buffers"]
        ]
        if "metrics" in state:
            self.metrics = {k: list(v) for k, v in state["metrics"].items()}
