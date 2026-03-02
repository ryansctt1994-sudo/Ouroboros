"""
vΩ.7 Decisive Test 1: Adversarial Inversion
============================================
Inverts spurious correlations (colour-label mapping) at test time and
measures the delta between baseline performance and vΩ performance.

Success Metric: Graceful degradation (small Δ) vs. catastrophic collapse
               (large Δ).

The test uses a synthetic 2-D classification dataset where a "colour"
feature is perfectly correlated with the label during training but is
*inverted* at test time.  A causal model that has learnt the true
decision boundary (based on shape features) degrades gracefully; one
that memorised the spurious colour correlation collapses.

Interfaces with existing Ouroboros primitives:
  - src.lexicon_gigas.topological_manifold_subspace_optimization
  - src.dna_helix_magnetar.PHI_GOLDEN_RATIO
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, Tuple

import numpy as np

from src.dna_helix_magnetar import PHI_GOLDEN_RATIO as PHI
from src.lexicon_gigas import topological_manifold_subspace_optimization

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED: int = 42
N_SAMPLES: int = 1_000
N_FEATURES: int = 8          # "shape" features
N_CLASSES: int = 2
SPURIOUS_WEIGHT: float = 2.0  # how strongly spurious feature influences label
CAUSAL_WEIGHT: float = 1.0    # how strongly causal features influence label
TRAIN_RATIO: float = 0.8
RANK: int = 4                 # HOSVD rank for latent projection


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def _generate_dataset(
    n_samples: int,
    rng: np.random.Generator,
    invert_spurious: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """Create a synthetic dataset with one spurious and several causal features.

    The label is determined by the sign of a linear combination of causal
    features.  A "colour" (spurious) feature is appended and is correlated
    with the label during normal generation but optionally inverted.

    Args:
        n_samples: Number of samples.
        rng: Seeded random generator.
        invert_spurious: When True the colour feature is negated (inverted).

    Returns:
        X: Feature matrix of shape (n_samples, N_FEATURES + 1).
        y: Binary label array of shape (n_samples,).
    """
    # Causal features
    X_causal = rng.standard_normal((n_samples, N_FEATURES))
    weights = rng.standard_normal(N_FEATURES)
    logits = X_causal @ weights
    y = (logits > 0).astype(int)

    # Spurious colour feature: +1 when label=1, -1 when label=0
    spurious = np.where(y == 1, 1.0, -1.0)
    if invert_spurious:
        spurious = -spurious
    spurious += rng.standard_normal(n_samples) * 0.1  # small noise

    X = np.column_stack([X_causal, spurious])
    return X, y


# ---------------------------------------------------------------------------
# Minimal linear classifier
# ---------------------------------------------------------------------------

class LinearClassifier:
    """Logistic regression via gradient descent with PHI-scaled learning rate."""

    def __init__(self, n_features: int, seed: int = SEED) -> None:
        rng = np.random.default_rng(seed)
        self.w = rng.standard_normal(n_features) * 0.01
        self.b = 0.0
        # PHI-scaled initial learning rate for harmonic convergence
        self.lr = 0.1 / PHI

    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._sigmoid(X @ self.w + self.b)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.predict_proba(X) >= 0.5).astype(int)

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 200) -> None:
        n = len(y)
        for _ in range(epochs):
            p = self.predict_proba(X)
            err = p - y
            grad_w = X.T @ err / n
            grad_b = err.mean()
            self.w -= self.lr * grad_w
            self.b -= self.lr * grad_b


def _accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_true == y_pred))


# ---------------------------------------------------------------------------
# Latent projection via HOSVD (causal abstraction layer)
# ---------------------------------------------------------------------------

def _project_latent(X: np.ndarray, rank: int = RANK) -> np.ndarray:
    """Project X into a lower-rank latent space using HOSVD.

    Uses topological_manifold_subspace_optimization from lexicon_gigas.
    The per-sample factor matrix (mode-0) provides the latent representation.
    """
    # Reshape to 3-D tensor: (n_samples, n_features, 1)
    tensor = X[:, :, np.newaxis].astype(float)
    _, factors = topological_manifold_subspace_optimization(tensor, target_rank=rank)
    # factors[0] is the per-sample factor matrix: shape (n_samples, rank)
    return factors[0]


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def run(seed: int = SEED, verbose: bool = True) -> Dict[str, Any]:
    """Execute the adversarial inversion test.

    Returns a dictionary suitable for JSON serialisation with:
      - baseline_accuracy
      - inverted_accuracy (both models)
      - delta_baseline (Δ for raw model)
      - delta_vo (Δ for vΩ latent-projected model)
      - verdict (GRACEFUL or CATASTROPHIC for each)
      - elapsed_seconds
    """
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)

    logger.info("Generating training data …")
    X_train_full, y_train = _generate_dataset(N_SAMPLES, rng, invert_spurious=False)
    X_test_full,  y_test  = _generate_dataset(N_SAMPLES, rng, invert_spurious=False)
    X_inv_full,   y_inv   = _generate_dataset(N_SAMPLES, rng, invert_spurious=True)

    # ------------------------------------------------------------------ #
    # Baseline model: raw features (memorises spurious correlation)
    # ------------------------------------------------------------------ #
    logger.info("Training baseline model …")
    clf_base = LinearClassifier(n_features=X_train_full.shape[1], seed=seed)
    clf_base.fit(X_train_full, y_train)
    acc_base_normal   = _accuracy(y_test, clf_base.predict(X_test_full))
    acc_base_inverted = _accuracy(y_inv,  clf_base.predict(X_inv_full))
    delta_base = acc_base_normal - acc_base_inverted

    # ------------------------------------------------------------------ #
    # vΩ model: latent-projected features (causal abstraction)
    # ------------------------------------------------------------------ #
    logger.info("Building vΩ latent space via HOSVD …")
    X_train_lat = _project_latent(X_train_full)
    X_test_lat  = _project_latent(X_test_full)
    X_inv_lat   = _project_latent(X_inv_full)

    logger.info("Training vΩ model …")
    clf_vo = LinearClassifier(n_features=X_train_lat.shape[1], seed=seed)
    clf_vo.fit(X_train_lat, y_train)
    acc_vo_normal   = _accuracy(y_test, clf_vo.predict(X_test_lat))
    acc_vo_inverted = _accuracy(y_inv,  clf_vo.predict(X_inv_lat))
    delta_vo = acc_vo_normal - acc_vo_inverted

    elapsed = time.perf_counter() - t0

    # Verdict: degradation <= 5 pp is graceful
    GRACEFUL_THRESHOLD = 0.05
    verdict_base = "GRACEFUL" if delta_base <= GRACEFUL_THRESHOLD else "CATASTROPHIC"
    verdict_vo   = "GRACEFUL" if delta_vo   <= GRACEFUL_THRESHOLD else "CATASTROPHIC"

    results: Dict[str, Any] = {
        "test": "adversarial_inversion",
        "seed": seed,
        "n_samples": N_SAMPLES,
        "baseline": {
            "normal_accuracy":   round(acc_base_normal,   4),
            "inverted_accuracy": round(acc_base_inverted, 4),
            "delta":             round(delta_base,        4),
            "verdict":           verdict_base,
        },
        "vo": {
            "normal_accuracy":   round(acc_vo_normal,   4),
            "inverted_accuracy": round(acc_vo_inverted, 4),
            "delta":             round(delta_vo,        4),
            "verdict":           verdict_vo,
        },
        "elapsed_seconds": round(elapsed, 3),
    }

    if verbose:
        print("\n=== Adversarial Inversion Results ===")
        print(f"  Baseline  normal={acc_base_normal:.3f}  inverted={acc_base_inverted:.3f}"
              f"  Δ={delta_base:+.3f}  [{verdict_base}]")
        print(f"  vΩ        normal={acc_vo_normal:.3f}  inverted={acc_vo_inverted:.3f}"
              f"  Δ={delta_vo:+.3f}  [{verdict_vo}]")
        print(f"  Elapsed: {elapsed:.3f}s")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
