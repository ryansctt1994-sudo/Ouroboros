"""
Phase 5 Main Pipeline — Falsifying the Geometric Thesis of Forgetting
=======================================================================
Orchestrates Task A → Task B sequential experiments with three optimizers:
  - MuonCANS (geometric, CANS-accelerated)
  - AdamW    (standard deep-learning baseline)
  - SGD      (momentum baseline)

Logs PR_bc, EGP, and λ₁ diagnostics and prints a comparison table.

Usage (from repository root)::

    python main.py
    python main.py --seed 123 --epochs 100 --n-samples 2000

"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from typing import Any, Dict, List

import numpy as np

from ecs.systems.experiment_pipeline import ExperimentPipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Synthetic dataset generation
# ---------------------------------------------------------------------------

_DEFAULT_SEED = 42
_DEFAULT_N_SAMPLES = 1_000
_DEFAULT_N_FEATURES = 32
_DEFAULT_N_CLASSES = 2
_DEFAULT_EPOCHS = 50
_DEFAULT_LOG_INTERVAL = 10


def _generate_task(
    n_samples: int,
    n_features: int,
    n_classes: int,
    rng: np.random.Generator,
    train_ratio: float = 0.8,
) -> tuple:
    """Generate a synthetic classification task.

    Returns:
        (X_train, y_train, X_test, y_test)
    """
    W_true = rng.standard_normal((n_features, n_classes))
    X = rng.standard_normal((n_samples, n_features))
    logits = X @ W_true
    y = logits.argmax(axis=1)

    split = int(n_samples * train_ratio)
    return X[:split], y[:split], X[split:], y[split:]


# ---------------------------------------------------------------------------
# Results formatting
# ---------------------------------------------------------------------------


def _print_table(results: List[Dict[str, Any]]) -> None:
    """Print a formatted comparison table."""
    header = f"{'Optimizer':<14} {'Task A Acc':>10} {'Task B Acc':>10} {'Time (s)':>10}"
    print("\n" + "=" * len(header))
    print("Optimizer Performance Table")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['optimizer']:<14} "
            f"{r['task_a_final_acc']:>10.4f} "
            f"{r['task_b_final_acc']:>10.4f} "
            f"{r['elapsed_seconds']:>10.3f}"
        )
    print("=" * len(header))


def _print_diagnostics_summary(results: List[Dict[str, Any]]) -> None:
    """Print mean PR_bc, EGP, and λ₁ per optimizer."""
    print("\n" + "=" * 65)
    print("Diagnostics Summary (means over logged epochs)")
    print("=" * 65)
    print(f"{'Optimizer':<14} {'PR_bc (mean)':>14} {'EGP (mean)':>12} {'λ₁ (mean)':>12}")
    print("-" * 65)
    for r in results:
        log = r.get("log", [])
        pr_vals = [e["pr_bc"] for e in log if e.get("pr_bc") is not None]
        egp_vals = [e["egp"] for e in log if e.get("egp") is not None]
        lam_vals = [e["lambda1"] for e in log if e.get("lambda1") is not None]
        pr_mean = float(np.mean(pr_vals)) if pr_vals else float("nan")
        egp_mean = float(np.mean(egp_vals)) if egp_vals else float("nan")
        lam_mean = float(np.mean(lam_vals)) if lam_vals else float("nan")
        print(
            f"{r['optimizer']:<14} {pr_mean:>14.4f} {egp_mean:>12.4f} {lam_mean:>12.6f}"
        )
    print("=" * 65)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_pipeline(
    seed: int = _DEFAULT_SEED,
    n_samples: int = _DEFAULT_N_SAMPLES,
    n_features: int = _DEFAULT_N_FEATURES,
    n_classes: int = _DEFAULT_N_CLASSES,
    epochs: int = _DEFAULT_EPOCHS,
    log_interval: int = _DEFAULT_LOG_INTERVAL,
    output_path: str | None = None,
) -> Dict[str, Any]:
    """Execute the full Phase 5 pipeline.

    Args:
        seed:          Global random seed.
        n_samples:     Samples per task.
        n_features:    Input feature dimension.
        n_classes:     Number of output classes.
        epochs:        Training epochs per task per optimizer.
        log_interval:  Diagnostic logging interval.
        output_path:   Optional JSON path to write results.

    Returns:
        Dictionary containing all optimizer results and a summary.
    """
    t_total = time.perf_counter()
    rng = np.random.default_rng(seed)

    logger.info("Generating synthetic Task A …")
    X_a_tr, y_a_tr, X_a_te, y_a_te = _generate_task(
        n_samples, n_features, n_classes, rng
    )

    logger.info("Generating synthetic Task B …")
    X_b_tr, y_b_tr, X_b_te, y_b_te = _generate_task(
        n_samples, n_features, n_classes, rng
    )

    optimizers = ["muon_cans", "adamw", "sgd"]
    all_results: List[Dict[str, Any]] = []

    for opt_name in optimizers:
        logger.info("Running experiment with optimizer: %s", opt_name)
        pipeline = ExperimentPipeline(
            optimizer_name=opt_name,
            n_features=n_features,
            n_classes=n_classes,
            lr=0.02,
            epochs_per_task=epochs,
            log_interval=log_interval,
            seed=seed,
        )
        result = pipeline.run(
            X_a_tr, y_a_tr, X_b_tr, y_b_tr,
            X_a_te, y_a_te, X_b_te, y_b_te,
        )
        all_results.append(result)

    _print_table(all_results)
    _print_diagnostics_summary(all_results)

    total_elapsed = time.perf_counter() - t_total
    report: Dict[str, Any] = {
        "schema_version": "phase5.1",
        "seed": seed,
        "n_samples": n_samples,
        "n_features": n_features,
        "n_classes": n_classes,
        "epochs_per_task": epochs,
        "results": all_results,
        "total_elapsed_seconds": round(total_elapsed, 3),
    }

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        logger.info("Results written to %s", output_path)

    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Phase 5 pipeline — Geometric Thesis of Forgetting",
    )
    parser.add_argument("--seed", type=int, default=_DEFAULT_SEED)
    parser.add_argument("--n-samples", type=int, default=_DEFAULT_N_SAMPLES)
    parser.add_argument("--n-features", type=int, default=_DEFAULT_N_FEATURES)
    parser.add_argument("--n-classes", type=int, default=_DEFAULT_N_CLASSES)
    parser.add_argument("--epochs", type=int, default=_DEFAULT_EPOCHS)
    parser.add_argument("--log-interval", type=int, default=_DEFAULT_LOG_INTERVAL)
    parser.add_argument("--output", type=str, default=None,
                        help="Optional path to write JSON results.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress diagnostic output.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    run_pipeline(
        seed=args.seed,
        n_samples=args.n_samples,
        n_features=args.n_features,
        n_classes=args.n_classes,
        epochs=args.epochs,
        log_interval=args.log_interval,
        output_path=args.output,
    )
