"""
vΩ.7 Decisive Test 2: Depth Extrapolation
==========================================
Evaluates a recursive / loop-based model block at depths up to 10× the
training depth and measures latent-state stability and performance decay.

Success Metric: A flat or slowly-decaying accuracy curve across depths.

Architecture: A "Loop-Block" MLP that applies the same weight matrix
repeatedly (analogous to a Loop-ViT or parameter-shared recurrent cell).
The number of forward passes (depth) is varied from 1× to 10× the
training depth.

Interfaces with existing Ouroboros primitives:
  - src.training.convergence_detector.EnhancedConvergenceV2
  - src.dna_helix_magnetar.PHI_GOLDEN_RATIO
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List

import numpy as np

from src.dna_helix_magnetar import PHI_GOLDEN_RATIO as PHI
from src.training.convergence_detector import EnhancedConvergenceV2

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED: int = 42
N_SAMPLES: int = 2_000
N_FEATURES: int = 16
N_CLASSES: int = 2
TRAIN_DEPTH: int = 4          # number of recursive applications during training
MAX_DEPTH_MULTIPLIER: int = 10
HIDDEN_DIM: int = 32
TRAIN_EPOCHS: int = 300
LR: float = 0.05


# ---------------------------------------------------------------------------
# Synthetic dataset
# ---------------------------------------------------------------------------

def _generate_dataset(
    n_samples: int,
    n_features: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    X = rng.standard_normal((n_samples, n_features))
    w = rng.standard_normal(n_features)
    y = (X @ w > 0).astype(int)
    return X, y


# ---------------------------------------------------------------------------
# Loop-Block model
# ---------------------------------------------------------------------------

class LoopBlock:
    """A single weight-shared MLP block applied recursively.

    Architecture:
      - ``proj``: one-time linear projection  in_dim → hidden_dim
      - ``W_rec``, ``b_rec``: shared recurrent layer  hidden_dim → hidden_dim
      - ``W2``, ``b2``: output head  hidden_dim → 1

    Only the recurrent (W_rec) weights are applied *depth* times; this
    keeps the hidden state shape constant across all depths.
    """

    def __init__(self, in_dim: int, hidden_dim: int, seed: int = SEED) -> None:
        rng = np.random.default_rng(seed)
        # Input projection (applied once)
        self.W_proj = rng.standard_normal((in_dim, hidden_dim)) / np.sqrt(in_dim)
        self.b_proj = np.zeros(hidden_dim)
        # Shared recurrent layer (applied *depth* times)
        self.W_rec = rng.standard_normal((hidden_dim, hidden_dim)) / np.sqrt(hidden_dim)
        self.b_rec = np.zeros(hidden_dim)
        # Output head
        self.W2 = rng.standard_normal((hidden_dim, 1)) / np.sqrt(hidden_dim)
        self.b2 = np.zeros(1)
        # PHI-scaled learning rate
        self.lr = LR / PHI

    # ------------------------------------------------------------------
    # Activation and helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _relu(z: np.ndarray) -> np.ndarray:
        return np.maximum(0, z)

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def _apply_rec(self, h: np.ndarray) -> np.ndarray:
        """One application of the shared recurrent layer."""
        return self._relu(h @ self.W_rec + self.b_rec)

    def forward(self, X: np.ndarray, depth: int) -> np.ndarray:
        """Project input, apply recurrent block *depth* times, return logits."""
        h = self._relu(X @ self.W_proj + self.b_proj)
        for _ in range(depth):
            h = self._apply_rec(h)
        return (h @ self.W2 + self.b2).squeeze(-1)

    def predict(self, X: np.ndarray, depth: int) -> np.ndarray:
        return (self._sigmoid(self.forward(X, depth)) >= 0.5).astype(int)

    # ------------------------------------------------------------------
    # Training (at fixed TRAIN_DEPTH)
    # ------------------------------------------------------------------

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        depth: int,
        epochs: int,
        convergence_detector: EnhancedConvergenceV2,
    ) -> None:
        n = len(y)
        for epoch in range(epochs):
            # Forward — store all intermediate hidden states
            h0 = self._relu(X @ self.W_proj + self.b_proj)
            hiddens = [h0]
            h = h0
            for _ in range(depth):
                h = self._apply_rec(h)
                hiddens.append(h)

            logits = (hiddens[-1] @ self.W2 + self.b2).squeeze(-1)
            p = self._sigmoid(logits)
            loss = -np.mean(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))

            # Convergence check
            metrics = convergence_detector.watch(epoch=epoch, loss=float(loss))
            if metrics.recommended_action == "EARLY_STOP":
                logger.info(f"Early stop at epoch {epoch} (loss={loss:.4f})")
                break

            # Backward through output head
            err = p - y
            grad_W2 = hiddens[-1].T @ err[:, np.newaxis] / n
            grad_b2 = err.mean()

            # Gradient into final hidden state
            delta = (err[:, np.newaxis] @ self.W2.T) * (hiddens[-1] > 0)

            # Accumulate gradient for shared recurrent weights in reverse order
            grad_W_rec = np.zeros_like(self.W_rec)
            grad_b_rec = np.zeros_like(self.b_rec)
            for step in range(depth - 1, -1, -1):
                h_in  = hiddens[step]       # input to this recurrent application
                h_out = hiddens[step + 1]   # output of this recurrent application
                mask = (h_out > 0).astype(float)
                grad_W_rec += h_in.T @ (delta * mask) / n
                grad_b_rec += (delta * mask).mean(axis=0)
                delta = (delta * mask) @ self.W_rec.T

            # Gradient for input projection
            mask0 = (h0 > 0).astype(float)
            grad_W_proj = X.T @ (delta * mask0) / n
            grad_b_proj = (delta * mask0).mean(axis=0)

            # Update parameters
            self.W2     -= self.lr * grad_W2
            self.b2     -= self.lr * grad_b2
            self.W_rec  -= self.lr * grad_W_rec
            self.b_rec  -= self.lr * grad_b_rec
            self.W_proj -= self.lr * grad_W_proj
            self.b_proj -= self.lr * grad_b_proj


# ---------------------------------------------------------------------------
# Latent stability metric
# ---------------------------------------------------------------------------

def _latent_stability(model: LoopBlock, X: np.ndarray, depth: int) -> float:
    """Measure the mean L2 norm of hidden activations at a given depth.

    A stable model keeps activation norms bounded even at large depths.
    """
    h = model._relu(X @ model.W_proj + model.b_proj)
    norms: List[float] = [float(np.mean(np.linalg.norm(h, axis=1)))]
    for _ in range(depth):
        h = model._apply_rec(h)
        norms.append(float(np.mean(np.linalg.norm(h, axis=1))))
    if len(norms) < 2:
        return 1.0
    # Stability = ratio of last to first norm; <=1 means contracting (stable)
    return norms[-1] / (norms[0] + 1e-12)


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def run(seed: int = SEED, verbose: bool = True) -> Dict[str, Any]:
    """Execute the depth extrapolation test.

    Returns a dictionary with per-depth accuracy, latent stability ratio,
    and a verdict on whether the decay curve is flat/slow.
    """
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)

    X_train, y_train = _generate_dataset(N_SAMPLES, N_FEATURES, rng)
    X_test,  y_test  = _generate_dataset(N_SAMPLES // 4, N_FEATURES, rng)

    # Train at TRAIN_DEPTH
    model = LoopBlock(in_dim=N_FEATURES, hidden_dim=HIDDEN_DIM, seed=seed)
    detector = EnhancedConvergenceV2(initial_patience=20, warmup_epochs=10)

    logger.info(f"Training Loop-Block at depth={TRAIN_DEPTH} …")
    model.fit(X_train, y_train, depth=TRAIN_DEPTH,
              epochs=TRAIN_EPOCHS, convergence_detector=detector)

    # Evaluate at depths 1× … 10×
    max_depth = TRAIN_DEPTH * MAX_DEPTH_MULTIPLIER
    depth_results: List[Dict[str, Any]] = []

    for multiplier in range(1, MAX_DEPTH_MULTIPLIER + 1):
        depth = TRAIN_DEPTH * multiplier
        acc = float(np.mean(y_test == model.predict(X_test, depth=depth)))
        stability = _latent_stability(model, X_test[:100], depth=depth)
        depth_results.append({
            "depth":              depth,
            "depth_multiplier":   multiplier,
            "accuracy":           round(acc, 4),
            "latent_stability":   round(stability, 4),
        })

    elapsed = time.perf_counter() - t0

    # Verdict: check that accuracy at 10× is within 10 pp of 1×
    acc_1x  = depth_results[0]["accuracy"]
    acc_10x = depth_results[-1]["accuracy"]
    decay = acc_1x - acc_10x
    verdict = "FLAT_OR_SLOW" if decay <= 0.10 else "RAPID_DECAY"

    results: Dict[str, Any] = {
        "test":            "depth_extrapolation",
        "seed":            seed,
        "train_depth":     TRAIN_DEPTH,
        "max_depth":       max_depth,
        "depth_curve":     depth_results,
        "accuracy_decay":  round(decay, 4),
        "verdict":         verdict,
        "elapsed_seconds": round(elapsed, 3),
    }

    if verbose:
        print("\n=== Depth Extrapolation Results ===")
        print(f"  Accuracy at 1× depth ({TRAIN_DEPTH}):  {acc_1x:.3f}")
        print(f"  Accuracy at 10× depth ({max_depth}): {acc_10x:.3f}")
        print(f"  Decay: {decay:+.3f}  [{verdict}]")
        print(f"  Elapsed: {elapsed:.3f}s")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
