"""Retraction Primitives — core math for manifold projection experiments.

Consolidates the three retraction methods discussed in the numerical fidelity
design sketches:

* **``svd_polar``** — exact polar-factor via full SVD (ground-truth baseline).
* **``newton_schulz``** — heuristic quintic polynomial approximation (fast,
  fixed coefficients).
* **``controlled_spectrum_matrix``** — constructs a matrix with a precisely
  specified condition number for controlled experimental sweeps.
* **``check_orthogonality``** — measures the Stiefel projection error
  ``‖WᵀW − I‖_F``.

Intended use
------------
These helpers are imported by the fidelity and stability sweep experiments::

    from experiments.minimal_testbed.retraction_primitives import (
        controlled_spectrum_matrix,
        svd_polar,
        newton_schulz,
        check_orthogonality,
    )

They may also be run directly::

    python experiments/minimal_testbed/retraction_primitives.py

which prints a self-test comparing SVD vs Newton-Schulz projection errors.

References
----------
* "Accelerating Newton-Schulz Iteration for Orthogonalization via
  Chebyshev-type Polynomials" — arXiv 2506.10935.
* "Beyond the Ideal: Analyzing the Inexact Muon Update" — arXiv 2510.19933.
"""

import time
from typing import Literal

import torch
import torch.linalg as linalg

# ---------------------------------------------------------------------------
# 1. Controlled Spectrum Matrix Generator
# ---------------------------------------------------------------------------


def controlled_spectrum_matrix(
    rows: int,
    cols: int,
    kappa: float = 100.0,
    seed: int = 0,
) -> torch.Tensor:
    """Construct a matrix with a precisely controlled condition number κ.

    The singular values are log-spaced from ``1/κ`` (smallest) to ``1``
    (largest), giving an exact condition number of ``κ``.  A random
    orthonormal basis is applied so the principal directions are generic.

    Parameters
    ----------
    rows, cols:
        Matrix dimensions.
    kappa:
        Target condition number ``σ_max / σ_min``.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    torch.Tensor
        Matrix ``A = U Σ Vᵀ`` of shape ``(rows, cols)`` with condition
        number ≈ ``kappa``.

    Examples
    --------
    >>> A = controlled_spectrum_matrix(20, 10, kappa=100.0)
    >>> A.shape
    torch.Size([20, 10])
    """
    generator = torch.Generator()
    generator.manual_seed(seed)

    n = min(rows, cols)

    # Random orthonormal columns via QR decomposition
    U, _ = linalg.qr(torch.randn(rows, n, generator=generator))
    V, _ = linalg.qr(torch.randn(cols, n, generator=generator))

    # Log-spaced singular values: σ_i decreasing from 1 to 1/κ
    exponents = torch.linspace(0, 1, n)
    sigma = kappa ** (-exponents)  # σ_0 = 1, σ_{n-1} = 1/kappa

    # A = U diag(σ) Vᵀ
    return U @ torch.diag(sigma) @ V.T


# ---------------------------------------------------------------------------
# 2. Exact Polar-Factor Retraction (SVD)
# ---------------------------------------------------------------------------


def svd_polar(W: torch.Tensor) -> torch.Tensor:
    """Compute the exact orthogonal polar factor via SVD.

    For ``W = U Σ Vᵀ``, returns ``Q = U Vᵀ``, the closest orthogonal
    matrix to ``W`` in the Frobenius norm.

    This is the ground-truth retraction onto the Stiefel manifold and
    serves as the numerical gold standard against which approximate methods
    are measured.  Computationally intractable for large matrices at every
    training step, hence the need for the Newton-Schulz approximation.

    Parameters
    ----------
    W:
        Input matrix of shape ``(m, n)``.

    Returns
    -------
    torch.Tensor
        Orthogonal polar factor ``Q`` with shape ``(m, n)``,
        satisfying ``QᵀQ = I`` (for m ≥ n).
    """
    try:
        U, _S, Vh = linalg.svd(W, full_matrices=False)
    except RuntimeError:
        # Fallback for numerically degenerate inputs
        return W
    return U @ Vh


# ---------------------------------------------------------------------------
# 3. Heuristic Newton-Schulz Approximation
# ---------------------------------------------------------------------------


def newton_schulz(
    W: torch.Tensor,
    num_iters: int = 5,
    coefficients: Literal["quintic"] | tuple[float, float, float] = "quintic",
) -> torch.Tensor:
    """Approximate the orthogonal polar factor via Newton-Schulz iteration.

    Applies the following polynomial update ``num_iters`` times::

        A = X Xᵀ
        X ← a·X + b·A·X + c·A·A·X

    Default coefficients are the "cursed quintic" ``(3.4445, -4.7750, 2.0315)``
    widely used in the original Muon optimizer.

    Parameters
    ----------
    W:
        Input matrix of shape ``(m, n)``.
    num_iters:
        Number of Newton-Schulz iterations.  More iterations → smaller
        approximation error ``δ = ‖WᵀW − I‖_F``.
    coefficients:
        Either ``"quintic"`` (the default hand-tuned polynomial) or a
        3-tuple ``(a, b, c)`` supplying custom coefficients.

    Returns
    -------
    torch.Tensor
        Approximate orthogonal polar factor, same shape as ``W``.

    Notes
    -----
    The Frobenius norm of ``W`` is used for pre-normalisation (standard
    heuristic).  CANS uses the spectral norm (``σ_max``) instead for
    tighter spectral control — see the manuscript references.
    """
    assert W.ndim == 2, "newton_schulz expects a 2-D matrix"

    if coefficients == "quintic":
        a, b, c = 3.4445, -4.7750, 2.0315
    else:
        a, b, c = coefficients

    # Pre-normalise by Frobenius norm
    X = W / (linalg.norm(W, "fro").clamp(min=1e-7))

    # Handle tall matrices by transposing (iteration assumes m ≤ n)
    transposed = X.shape[0] > X.shape[1]
    if transposed:
        X = X.T

    for _ in range(num_iters):
        A = X @ X.T
        X = a * X + (b * A + c * (A @ A)) @ X

    if transposed:
        X = X.T

    return X


# ---------------------------------------------------------------------------
# 4. Orthogonality Checker
# ---------------------------------------------------------------------------


def check_orthogonality(W: torch.Tensor, silent: bool = False) -> float:
    """Measure the Stiefel projection error ``‖WᵀW − I‖_F``.

    Parameters
    ----------
    W:
        Matrix to check.  For a perfectly orthogonal matrix the result
        is exactly ``0``.
    silent:
        If ``False`` (default), prints the error.

    Returns
    -------
    float
        Projection error ``δ = ‖WᵀW − I‖_F``.
    """
    WTW = W.T @ W
    I = torch.eye(WTW.shape[0], dtype=W.dtype, device=W.device)
    error = linalg.norm(WTW - I, "fro").item()
    if not silent:
        print(f"  Projection Error ‖WᵀW − I‖_F : {error:.5e}")
    return error


# ---------------------------------------------------------------------------
# 5. Self-test
# ---------------------------------------------------------------------------


def _self_test() -> None:
    print("=" * 65)
    print("Retraction Primitives — self-test")
    print("=" * 65)

    ROWS, COLS, KAPPA = 20, 10, 1000
    SEED = 42

    W = controlled_spectrum_matrix(ROWS, COLS, kappa=KAPPA, seed=SEED)
    print(f"\nMatrix: {ROWS}×{COLS}, κ={KAPPA}")

    # --- SVD baseline ---
    t0 = time.perf_counter()
    W_svd = svd_polar(W)
    t_svd = time.perf_counter() - t0
    print(f"\nsvd_polar ({t_svd*1e6:.1f} µs):")
    check_orthogonality(W_svd)

    # --- Newton-Schulz at varying iteration counts ---
    for k in [1, 3, 5, 7, 10]:
        t0 = time.perf_counter()
        W_ns = newton_schulz(W, num_iters=k)
        t_ns = time.perf_counter() - t0
        err = check_orthogonality(W_ns, silent=True)
        print(
            f"  newton_schulz(k={k:2d})  δ={err:.5e}   "
            f"time={t_ns*1e6:6.1f} µs"
        )

    print("\nSelf-test complete.")
    print("=" * 65)


if __name__ == "__main__":
    _self_test()
