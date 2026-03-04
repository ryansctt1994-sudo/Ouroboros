"""
ExperimentPipeline ECS System
==============================
Orchestrates sequential Task A → Task B experiments within the ECS framework,
integrating the MuonCANS optimizer and Phase 5 diagnostic metrics.

The pipeline:
  1. Trains a model on Task A using the specified optimizer.
  2. Continues training on Task B without resetting parameters (sequential /
     continual-learning setup).
  3. Logs PR_bc, EGP, and λ₁ diagnostics at configurable intervals so that
     downstream analysis can correlate geometric stability with accuracy
     retention.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np

from optimizers.muon_cans import MuonCANS
from utils.metrics import (
    early_gradient_projection,
    lyapunov_exponent,
    participation_ratio_bc,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tiny linear model used inside the pipeline
# ---------------------------------------------------------------------------


class _LinearModel:
    """Minimal linear classifier (logistic regression) — no framework deps."""

    def __init__(self, n_features: int, n_classes: int, seed: int = 0) -> None:
        rng = np.random.default_rng(seed)
        # Single weight matrix W: (n_features, n_classes)
        self.W = rng.standard_normal((n_features, n_classes)) * 0.01
        self.b = np.zeros(n_classes)

    @property
    def params(self) -> List[np.ndarray]:
        return [self.W, self.b]

    def forward(self, X: np.ndarray) -> np.ndarray:
        """Compute softmax probabilities. Returns (n_samples, n_classes)."""
        logits = X @ self.W + self.b
        # Numerically stable softmax
        logits -= logits.max(axis=1, keepdims=True)
        exp_l = np.exp(logits)
        return exp_l / exp_l.sum(axis=1, keepdims=True)

    def compute_grads(
        self, X: np.ndarray, y: np.ndarray
    ) -> List[np.ndarray]:
        """Cross-entropy gradients w.r.t. W and b."""
        probs = self.forward(X)
        n = len(y)
        # One-hot delta
        delta = probs.copy()
        delta[np.arange(n), y] -= 1.0
        delta /= n
        grad_W = X.T @ delta
        grad_b = delta.sum(axis=0)
        return [grad_W, grad_b]

    def accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        preds = self.forward(X).argmax(axis=1)
        return float(np.mean(preds == y))


# ---------------------------------------------------------------------------
# ExperimentPipeline
# ---------------------------------------------------------------------------


class ExperimentPipeline:
    """ECS system that orchestrates Task A → Task B sequential training.

    Attributes:
        optimizer_name: One of ``"muon_cans"``, ``"adamw"``, ``"sgd"``.
        n_features:     Number of input features.
        n_classes:      Number of output classes.
        lr:             Learning rate.
        epochs_per_task: Training epochs for each task.
        log_interval:   Log diagnostics every *n* epochs.
        seed:           Random seed for reproducibility.
    """

    SUPPORTED_OPTIMIZERS = ("muon_cans", "adamw", "sgd")

    def __init__(
        self,
        optimizer_name: str = "muon_cans",
        n_features: int = 32,
        n_classes: int = 2,
        lr: float = 0.02,
        epochs_per_task: int = 50,
        log_interval: int = 10,
        seed: int = 42,
    ) -> None:
        if optimizer_name not in self.SUPPORTED_OPTIMIZERS:
            raise ValueError(
                f"optimizer_name must be one of {self.SUPPORTED_OPTIMIZERS}, "
                f"got '{optimizer_name}'"
            )

        self.optimizer_name = optimizer_name
        self.n_features = n_features
        self.n_classes = n_classes
        self.lr = lr
        self.epochs_per_task = epochs_per_task
        self.log_interval = log_interval
        self.seed = seed

        self._model: Optional[_LinearModel] = None
        self._optimizer: Any = None
        self._log: List[Dict[str, Any]] = []
        self._grads_task_a: Optional[List[np.ndarray]] = None
        self._rng: np.random.Generator = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Optimizer factory
    # ------------------------------------------------------------------

    def _build_optimizer(self, params: List[np.ndarray]) -> Any:
        if self.optimizer_name == "muon_cans":
            return MuonCANS(params, lr=self.lr, momentum=0.95, ns_steps=5)
        if self.optimizer_name == "adamw":
            return _AdamW(params, lr=self.lr, weight_decay=1e-2)
        # sgd fallback
        return _SGDMomentum(params, lr=self.lr, momentum=0.9)

    # ------------------------------------------------------------------
    # Training helpers
    # ------------------------------------------------------------------

    def _train_epoch(
        self,
        X: np.ndarray,
        y: np.ndarray,
        batch_size: int = 64,
    ) -> float:
        """Train for one epoch; returns mean cross-entropy loss."""
        n = len(y)
        indices = self._rng.permutation(n)
        self._epoch_counter += 1
        total_loss = 0.0
        batches = 0
        for start in range(0, n, batch_size):
            idx = indices[start : start + batch_size]
            X_b, y_b = X[idx], y[idx]
            grads = self._model.compute_grads(X_b, y_b)
            # Cross-entropy loss
            probs = self._model.forward(X_b)
            eps = 1e-12
            loss = -np.log(probs[np.arange(len(y_b)), y_b] + eps).mean()
            total_loss += loss
            batches += 1
            self._optimizer.step(grads)
        return total_loss / max(batches, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        X_a: np.ndarray,
        y_a: np.ndarray,
        X_b: np.ndarray,
        y_b: np.ndarray,
        X_a_test: Optional[np.ndarray] = None,
        y_a_test: Optional[np.ndarray] = None,
        X_b_test: Optional[np.ndarray] = None,
        y_b_test: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Run the full Task A → Task B experiment.

        Args:
            X_a / y_a:           Task A training data.
            X_b / y_b:           Task B training data.
            X_a_test / y_a_test: Optional Task A held-out test data.
            X_b_test / y_b_test: Optional Task B held-out test data.

        Returns:
            Results dictionary containing:
              - ``log``               — per-epoch diagnostic records.
              - ``task_a_final_acc``  — Task A accuracy after Task B training.
              - ``task_b_final_acc``  — Task B accuracy after Task B training.
              - ``optimizer``         — optimizer name used.
              - ``elapsed_seconds``   — wall-clock time.
        """
        t0 = time.perf_counter()

        self._model = _LinearModel(
            n_features=self.n_features,
            n_classes=self.n_classes,
            seed=self.seed,
        )
        self._optimizer = self._build_optimizer(self._model.params)
        self._log = []
        self._epoch_counter = 0
        self._rng = np.random.default_rng(self.seed)

        # ---- Task A training ----------------------------------------
        logger.info("[%s] Training on Task A …", self.optimizer_name)
        for epoch in range(self.epochs_per_task):
            loss = self._train_epoch(X_a, y_a)
            if epoch % self.log_interval == 0 or epoch == self.epochs_per_task - 1:
                entry = self._make_log_entry("task_a", epoch, loss, X_a, y_a)
                self._log.append(entry)
                logger.debug("  Task A epoch %d  loss=%.4f  pr_bc=%.4f",
                             epoch, loss, entry["pr_bc"])

        # Capture Task A gradients for EGP computation
        self._grads_task_a = self._model.compute_grads(X_a, y_a)

        # ---- Task B training ----------------------------------------
        logger.info("[%s] Training on Task B …", self.optimizer_name)
        for epoch in range(self.epochs_per_task):
            loss = self._train_epoch(X_b, y_b)
            if epoch % self.log_interval == 0 or epoch == self.epochs_per_task - 1:
                entry = self._make_log_entry("task_b", epoch, loss, X_b, y_b)
                # EGP: alignment of Task B grads with stored Task A grads
                grads_b = self._model.compute_grads(X_b, y_b)
                entry["egp"] = early_gradient_projection(
                    self._grads_task_a, grads_b
                )
                self._log.append(entry)
                logger.debug("  Task B epoch %d  loss=%.4f  egp=%.4f",
                             epoch, loss, entry["egp"])

        # ---- Final evaluation ---------------------------------------
        test_X_a = X_a_test if X_a_test is not None else X_a
        test_y_a = y_a_test if y_a_test is not None else y_a
        test_X_b = X_b_test if X_b_test is not None else X_b
        test_y_b = y_b_test if y_b_test is not None else y_b

        acc_a = self._model.accuracy(test_X_a, test_y_a)
        acc_b = self._model.accuracy(test_X_b, test_y_b)

        elapsed = time.perf_counter() - t0
        logger.info(
            "[%s] Done. Task A acc=%.3f  Task B acc=%.3f  (%.2fs)",
            self.optimizer_name, acc_a, acc_b, elapsed,
        )

        return {
            "optimizer": self.optimizer_name,
            "task_a_final_acc": round(acc_a, 4),
            "task_b_final_acc": round(acc_b, 4),
            "log": self._log,
            "elapsed_seconds": round(elapsed, 3),
        }

    # ------------------------------------------------------------------
    # Diagnostics helper
    # ------------------------------------------------------------------

    def _make_log_entry(
        self,
        task: str,
        epoch: int,
        loss: float,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Dict[str, Any]:
        pr = participation_ratio_bc(self._model.W)
        lam = lyapunov_exponent([self._model.W], rng=np.random.default_rng(self.seed))
        acc = self._model.accuracy(X, y)
        return {
            "task": task,
            "epoch": epoch,
            "loss": round(float(loss), 6),
            "accuracy": round(acc, 4),
            "pr_bc": round(pr, 4),
            "lambda1": round(lam, 6),
            "egp": None,  # filled in for task_b entries
        }


# ---------------------------------------------------------------------------
# Minimal AdamW and SGD-Momentum fallbacks (no framework dependencies)
# ---------------------------------------------------------------------------


class _AdamW:
    """Minimal AdamW implementation for baseline comparisons."""

    def __init__(
        self,
        params: List[np.ndarray],
        lr: float = 1e-3,
        betas: tuple = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 1e-2,
    ) -> None:
        self.params = params
        self.lr = lr
        self.beta1, self.beta2 = betas
        self.eps = eps
        self.weight_decay = weight_decay
        self._m = [np.zeros_like(p) for p in params]
        self._v = [np.zeros_like(p) for p in params]
        self._t = 0

    def step(self, grads: List[np.ndarray]) -> None:
        self._t += 1
        for i, (p, g) in enumerate(zip(self.params, grads)):
            if g is None:
                continue
            g = g.astype(float)
            # Decoupled weight decay
            p *= 1.0 - self.lr * self.weight_decay
            self._m[i] = self.beta1 * self._m[i] + (1.0 - self.beta1) * g
            self._v[i] = self.beta2 * self._v[i] + (1.0 - self.beta2) * g ** 2
            m_hat = self._m[i] / (1.0 - self.beta1 ** self._t)
            v_hat = self._v[i] / (1.0 - self.beta2 ** self._t)
            p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class _SGDMomentum:
    """Minimal SGD with momentum for baseline comparisons."""

    def __init__(
        self,
        params: List[np.ndarray],
        lr: float = 0.01,
        momentum: float = 0.9,
    ) -> None:
        self.params = params
        self.lr = lr
        self.momentum = momentum
        self._buf = [np.zeros_like(p) for p in params]

    def step(self, grads: List[np.ndarray]) -> None:
        for i, (p, g) in enumerate(zip(self.params, grads)):
            if g is None:
                continue
            self._buf[i] = self.momentum * self._buf[i] + g.astype(float)
            p -= self.lr * self._buf[i]
