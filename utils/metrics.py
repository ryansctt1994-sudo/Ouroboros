"""
Diagnostic Metrics for the Geometric Thesis of Forgetting
==========================================================
Utility functions to compute the core diagnostics used in Phase 5:

  - ``participation_ratio_bc``  — Bias-Corrected Participation Ratio (PR_bc):
      monitors rank utilisation stability across tasks.

  - ``early_gradient_projection`` (EGP) — measures alignment between
      Task A and Task B gradients to quantify gradient interference.

  - ``lyapunov_exponent``  — finite-time Lyapunov exponent (λ₁) that
      quantifies attractor stability in the model's phase space under
      small perturbations.

All functions operate on plain NumPy arrays and have no framework-specific
dependencies.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Bias-Corrected Participation Ratio (PR_bc)
# ---------------------------------------------------------------------------


def participation_ratio_bc(weight_matrix: np.ndarray) -> float:
    """Compute the Bias-Corrected Participation Ratio of a weight matrix.

    The Participation Ratio quantifies the effective number of dimensions
    used by the singular-value spectrum of *weight_matrix*.  The bias
    correction (Nadler 2009) subtracts the expected PR of a random
    Marchenko-Pastur matrix of the same shape, making the metric more
    sensitive to genuine rank utilisation.

    Args:
        weight_matrix: 2-D array of shape (m, n).  If a higher-dimensional
            array is passed it is reshaped to (weight_matrix.shape[0], -1).

    Returns:
        Bias-corrected participation ratio in the range (0, min(m, n)].
        Higher values indicate richer rank utilisation.

    Raises:
        ValueError: If *weight_matrix* has fewer than 2 elements or is 1-D.
    """
    W = np.asarray(weight_matrix, dtype=float)
    if W.ndim == 1:
        raise ValueError("weight_matrix must be at least 2-D.")
    if W.ndim > 2:
        W = W.reshape(W.shape[0], -1)

    m, n = W.shape
    if m == 0 or n == 0:
        raise ValueError("weight_matrix must have non-zero dimensions.")

    singular_values = np.linalg.svd(W, compute_uv=False)
    lambdas = singular_values ** 2  # squared singular values ≡ eigenvalues of W^T W

    total = lambdas.sum()
    if total < 1e-12:
        return 0.0

    # Raw PR = (Σ λ_i)^2 / Σ λ_i^2
    pr_raw = (total ** 2) / (np.sum(lambdas ** 2) + 1e-12)

    # Marchenko-Pastur bias correction:
    # Expected PR of an (m × n) random matrix ≈ (1 + γ)^2 / (1 + γ^2)
    # where γ = n / m (aspect ratio, γ ≤ 1 by convention)
    gamma = min(m, n) / max(m, n)
    pr_mp = (1.0 + gamma) ** 2 / (1.0 + gamma ** 2 + 1e-12)

    return float(pr_raw - pr_mp)


# ---------------------------------------------------------------------------
# Early Gradient Projection (EGP)
# ---------------------------------------------------------------------------


def early_gradient_projection(
    grads_task_a: Sequence[np.ndarray],
    grads_task_b: Sequence[np.ndarray],
) -> float:
    """Compute the Early Gradient Projection (EGP) between two tasks.

    EGP measures the cosine alignment between the flattened Task A gradient
    vector and the flattened Task B gradient vector.  A value close to +1
    indicates aligned gradients (cooperative learning), near 0 indicates
    orthogonal gradients (independent), and negative values indicate
    conflicting gradients that cause catastrophic forgetting.

    Args:
        grads_task_a: List of gradient arrays for Task A (one per parameter).
        grads_task_b: List of gradient arrays for Task B (one per parameter).
            Must have the same shapes as ``grads_task_a``.

    Returns:
        Cosine similarity in [-1, 1].

    Raises:
        ValueError: If the gradient lists are empty or have incompatible shapes.
    """
    if len(grads_task_a) == 0 or len(grads_task_b) == 0:
        raise ValueError("Gradient lists must be non-empty.")
    if len(grads_task_a) != len(grads_task_b):
        raise ValueError(
            f"Gradient lists have different lengths: "
            f"{len(grads_task_a)} vs {len(grads_task_b)}"
        )

    flat_a = np.concatenate([g.ravel() for g in grads_task_a]).astype(float)
    flat_b = np.concatenate([g.ravel() for g in grads_task_b]).astype(float)

    if flat_a.shape != flat_b.shape:
        raise ValueError(
            f"Flattened gradient shapes do not match: "
            f"{flat_a.shape} vs {flat_b.shape}"
        )

    norm_a = np.linalg.norm(flat_a)
    norm_b = np.linalg.norm(flat_b)
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0

    return float(np.dot(flat_a, flat_b) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Finite-Time Lyapunov Exponent (λ₁)
# ---------------------------------------------------------------------------


def lyapunov_exponent(
    weight_matrices: List[np.ndarray],
    perturbation_scale: float = 1e-4,
    rng: np.random.Generator | None = None,
) -> float:
    """Estimate the largest finite-time Lyapunov exponent (λ₁).

    Approximates λ₁ by tracking how a small perturbation propagates through
    a sequence of linear maps (the weight matrices of each layer or snapshot).
    The exponent is estimated via the mean log-growth rate of the perturbation
    norm, using QR re-orthogonalisation (Ginelli et al. 2007).

    A negative λ₁ indicates a contracting (stable) attractor; a positive λ₁
    indicates exponential divergence (chaotic / unstable dynamics).

    Args:
        weight_matrices:   Ordered list of 2-D weight matrices W_1, …, W_T.
            Each must have consistent inner dimensions so that
            W_{t+1} @ v is defined for the output dimension of W_t.
        perturbation_scale: Initial perturbation magnitude.
        rng:               Optional seeded random generator for reproducibility.

    Returns:
        Estimated largest Lyapunov exponent λ₁.

    Raises:
        ValueError: If ``weight_matrices`` is empty or contains non-2-D arrays.
    """
    if len(weight_matrices) == 0:
        raise ValueError("weight_matrices must be non-empty.")

    if rng is None:
        rng = np.random.default_rng(0)

    # Initialise a random unit perturbation vector in the input space of W_1
    n_in = weight_matrices[0].shape[1]
    v = rng.standard_normal(n_in)
    v = v / (np.linalg.norm(v) + 1e-12) * perturbation_scale

    log_growth_sum = 0.0
    T = len(weight_matrices)

    for W in weight_matrices:
        if W.ndim != 2:
            raise ValueError(
                f"All weight matrices must be 2-D, got shape {W.shape}."
            )
        # Map the perturbation through this layer
        v_new = W @ v
        new_norm = np.linalg.norm(v_new)
        if new_norm < 1e-20:
            break
        log_growth_sum += np.log(new_norm / (np.linalg.norm(v) + 1e-12))
        # Re-normalise to prevent overflow
        v = v_new / new_norm * perturbation_scale

    return float(log_growth_sum / T)
