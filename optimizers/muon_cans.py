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

    Args:
        params:            List of parameter arrays (numpy arrays, modified in place).
        lr:                Learning rate.
        momentum:          Momentum coefficient (default 0.95).
        ns_steps:          Newton-Schulz iterations per step (default 5).
        weight_decay:      L2 regularisation coefficient (default 0.0).
        scalar_decay_mult: Extra L2 anchoring multiplier for 1-D parameters
                           (default 10.0, must be >= 1.0).  The effective weight
                           decay applied to 1-D params is
                           ``scalar_decay_mult * weight_decay``.
    """

    def __init__(
        self,
        params: List[np.ndarray],
        lr: float = 0.02,
        momentum: float = 0.95,
        ns_steps: int = 5,
        weight_decay: float = 0.0,
        scalar_decay_mult: float = 10.0,
    ) -> None:
        if lr <= 0:
            raise ValueError(f"lr must be positive, got {lr}")
        if not (0.0 <= momentum < 1.0):
            raise ValueError(f"momentum must be in [0, 1), got {momentum}")
        if scalar_decay_mult < 1.0:
            raise ValueError(f"scalar_decay_mult must be >= 1.0, got {scalar_decay_mult}")

        self.params = params
        self.lr = lr
        self.momentum = momentum
        self.ns_steps = ns_steps
        self.weight_decay = weight_decay
        self.scalar_decay_mult = scalar_decay_mult

        # Momentum buffers (initialised lazily on first step)
        self._buffers: List[Optional[np.ndarray]] = [None] * len(params)
        self.step_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(self, grads: List[np.ndarray]) -> None:
        """Apply one optimisation step.

        Args:
            grads: List of gradient arrays, one per parameter in ``self.params``.
                   Must have the same shapes as the corresponding parameters.

        Raises:
            ValueError: If the number of gradients does not match parameters.
        """
        if len(grads) != len(self.params):
            raise ValueError(
                f"Expected {len(self.params)} gradients, got {len(grads)}"
            )

        self.step_count += 1

        for i, (param, grad) in enumerate(zip(self.params, grads)):
            if grad is None:
                continue

            g = grad.copy().astype(float)

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

            # Orthogonalise 2-D parameters; fall back to sign-normalised SGD for 1-D
            if effective_grad.ndim >= 2:
                orig_shape = effective_grad.shape
                mat = effective_grad.reshape(orig_shape[0], -1)
                update = _orthogonalise(mat, num_steps=self.ns_steps)
                update = update.reshape(orig_shape)
            else:
                # Scalar or 1-D: normalise by RMS for stable scale
                rms = np.sqrt(np.mean(effective_grad ** 2)) + 1e-8
                update = effective_grad / rms

            param -= self.lr * update

    def zero_grad(self) -> None:
        """No-op: gradient storage is managed externally by the caller."""

    def reset_momentum(self) -> None:
        """Zero all initialised momentum buffers in-place.

        Buffers that have not yet been initialised (``None``) are left as-is.
        This is useful for resetting optimiser state between tasks without
        reallocating memory (the "ghost-breaker" pattern).
        """
        for buf in self._buffers:
            if buf is not None:
                buf[:] = 0.0

    def state_dict(self) -> Dict:
        """Return serialisable optimiser state."""
        return {
            "step_count": self.step_count,
            "lr": self.lr,
            "momentum": self.momentum,
            "ns_steps": self.ns_steps,
            "weight_decay": self.weight_decay,
            "buffers": [b.tolist() if b is not None else None for b in self._buffers],
        }

    def load_state_dict(self, state: Dict) -> None:
        """Restore optimiser state from a dictionary produced by :meth:`state_dict`."""
        self.step_count = state["step_count"]
        self.lr = state["lr"]
        self.momentum = state["momentum"]
        self.ns_steps = state["ns_steps"]
        self.weight_decay = state["weight_decay"]
        self._buffers = [
            np.array(b) if b is not None else None for b in state["buffers"]
        ]
