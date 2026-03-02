"""
vΩ.7 Decisive Test 3: Width Sweep
===================================
Orchestrates training runs across model widths (128, 256, 512, 1024) and
compares baseline vs. vΩ (latent-projected) accuracy at each width.

Success Metric:
  - If vΩ advantage *grows* with width → Bias Shift (causal).
  - If vΩ advantage *shrinks* with width → Regulariser effect only.

Interfaces with existing Ouroboros primitives:
  - src.training.model_orchestrator.FairModelOrchestrator
  - src.training.convergence_detector.EnhancedConvergenceV2
  - src.lexicon_gigas.topological_manifold_subspace_optimization
  - src.dna_helix_magnetar.PHI_GOLDEN_RATIO
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List

import numpy as np

from src.dna_helix_magnetar import PHI_GOLDEN_RATIO as PHI
from src.lexicon_gigas import topological_manifold_subspace_optimization
from src.training.model_orchestrator import FairModelOrchestrator
from src.training.convergence_detector import EnhancedConvergenceV2

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED: int = 42
N_SAMPLES: int = 2_000
N_FEATURES: int = 32
WIDTHS: List[int] = [128, 256, 512, 1024]
TRAIN_EPOCHS: int = 300
LATENT_RANK: int = 8


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
# Width-parameterised MLP
# ---------------------------------------------------------------------------

class WidthMLP:
    """Two-layer MLP with a configurable hidden width.

    Uses a PHI-scaled learning rate for harmonic convergence.
    """

    def __init__(self, in_dim: int, width: int, seed: int = SEED) -> None:
        rng = np.random.default_rng(seed)
        self.W1 = rng.standard_normal((in_dim, width)) / np.sqrt(in_dim)
        self.b1 = np.zeros(width)
        self.W2 = rng.standard_normal((width, 1)) / np.sqrt(width)
        self.b2 = np.zeros(1)
        self.lr = 0.05 / PHI

    @staticmethod
    def _relu(z: np.ndarray) -> np.ndarray:
        return np.maximum(0.0, z)

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def _forward(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        h = self._relu(X @ self.W1 + self.b1)
        logits = (h @ self.W2 + self.b2).squeeze(-1)
        return h, logits

    def predict(self, X: np.ndarray) -> np.ndarray:
        _, logits = self._forward(X)
        return (self._sigmoid(logits) >= 0.5).astype(int)

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int,
        convergence_detector: EnhancedConvergenceV2,
    ) -> None:
        n = len(y)
        for epoch in range(epochs):
            h, logits = self._forward(X)
            p = self._sigmoid(logits)
            loss = -np.mean(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12))

            metrics = convergence_detector.watch(epoch=epoch, loss=float(loss))
            if metrics.recommended_action == "EARLY_STOP":
                logger.debug(f"  [width] early stop epoch {epoch}")
                break

            err = p - y
            grad_W2 = h.T @ err[:, np.newaxis] / n
            grad_b2 = err.mean()
            delta = (err[:, np.newaxis] @ self.W2.T) * (h > 0)
            grad_W1 = X.T @ delta / n
            grad_b1 = delta.mean(axis=0)

            self.W1 -= self.lr * grad_W1
            self.b1 -= self.lr * grad_b1
            self.W2 -= self.lr * grad_W2
            self.b2 -= self.lr * grad_b2


# ---------------------------------------------------------------------------
# Latent projection (vΩ layer)
# ---------------------------------------------------------------------------

def _project_latent(X: np.ndarray, rank: int = LATENT_RANK) -> np.ndarray:
    tensor = X[:, :, np.newaxis].astype(float)
    _, factors = topological_manifold_subspace_optimization(tensor, target_rank=rank)
    # factors[0] is the per-sample factor matrix: shape (n_samples, rank)
    return factors[0]


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def run(seed: int = SEED, verbose: bool = True) -> Dict[str, Any]:
    """Execute the width sweep test.

    Returns a dictionary with per-width baseline and vΩ accuracies, the
    advantage at each width, and whether the advantage grows or shrinks.
    """
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)

    X_train_raw, y_train = _generate_dataset(N_SAMPLES, N_FEATURES, rng)
    X_test_raw,  y_test  = _generate_dataset(N_SAMPLES // 4, N_FEATURES, rng)

    # Pre-compute latent projections once (same for all widths)
    logger.info("Computing vΩ latent projections …")
    X_train_lat = _project_latent(X_train_raw)
    X_test_lat  = _project_latent(X_test_raw)

    # Set up orchestrator
    orchestrator = FairModelOrchestrator(aging_factor=0.05, decay_factor=0.98)

    width_results: List[Dict[str, Any]] = []

    for width in WIDTHS:
        for variant, (X_tr, X_te, label) in enumerate([
            (X_train_raw, X_test_raw, "baseline"),
            (X_train_lat, X_test_lat, "vo"),
        ]):
            model_id = f"width_{width}_{label}"
            orchestrator.register_model(model_id, base_priority=float(width) / 1024)
            orchestrator.submit_request(model_id, estimated_duration=5.0)

        # Schedule and train both variants for this width
        row: Dict[str, Any] = {"width": width}
        for _ in range(2):
            scheduled = orchestrator.schedule_next()
            if scheduled is None:
                continue
            req_id, request = scheduled
            model_id = request.model_id
            is_vo = model_id.endswith("_vo")

            X_tr = X_train_lat if is_vo else X_train_raw
            X_te = X_test_lat  if is_vo else X_test_raw
            in_dim = X_tr.shape[1]

            logger.info(f"Training {model_id} (width={width}, in_dim={in_dim}) …")
            detector = EnhancedConvergenceV2(initial_patience=20, warmup_epochs=10)
            mlp = WidthMLP(in_dim=in_dim, width=width, seed=seed)
            mlp.fit(X_tr, y_train, epochs=TRAIN_EPOCHS, convergence_detector=detector)

            acc = float(np.mean(y_test == mlp.predict(X_te)))
            key = "vo_accuracy" if is_vo else "baseline_accuracy"
            row[key] = round(acc, 4)

            orchestrator.complete_request(req_id, actual_duration=5.0)

        row["advantage"] = round(row.get("vo_accuracy", 0.0) - row.get("baseline_accuracy", 0.0), 4)
        width_results.append(row)

        if verbose:
            print(f"  width={width:4d}  baseline={row.get('baseline_accuracy', '?'):.3f}"
                  f"  vΩ={row.get('vo_accuracy', '?'):.3f}"
                  f"  advantage={row['advantage']:+.3f}")

    elapsed = time.perf_counter() - t0

    # Verdict: does advantage grow with width?
    advantages = [r["advantage"] for r in width_results]
    trend = advantages[-1] - advantages[0]
    verdict = "BIAS_SHIFT" if trend > 0 else "REGULARISER"

    results: Dict[str, Any] = {
        "test":            "width_sweep",
        "seed":            seed,
        "widths":          WIDTHS,
        "width_results":   width_results,
        "advantage_trend": round(trend, 4),
        "verdict":         verdict,
        "elapsed_seconds": round(elapsed, 3),
    }

    if verbose:
        print(f"\n=== Width Sweep Results ===")
        print(f"  Advantage trend (128→1024): {trend:+.4f}  [{verdict}]")
        print(f"  Elapsed: {elapsed:.3f}s")

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
