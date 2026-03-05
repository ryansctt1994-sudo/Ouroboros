"""
Policy Gradient Modules for ARC-AGI-3 Mycelium Training
=========================================================

Implements two complementary policy-gradient algorithms used to guide the
Mycelium agent during ARC-AGI-3 evaluation:

**FGRPO — Focal Group Relative Policy Optimisation**
    Computes advantage estimates by comparing each trajectory's return
    against the mean return of a *group* of contemporaneous rollouts
    (group-relative baseline).  A focal weighting term down-weights
    near-zero advantages, concentrating gradient signal on the most
    informative transitions.

**EMPG — Entropy-Modulated Policy Gradients**
    Augments the standard policy-gradient loss with an entropy bonus
    (or penalty) whose coefficient is dynamically adjusted based on the
    current policy entropy relative to a target value.  This prevents
    premature collapse to deterministic policies in partially-observable
    environments.

Both classes are pure-NumPy for portability and operate on pre-computed
log-probabilities supplied by the caller.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FGRPO — Focal Group Relative Policy Optimisation
# ---------------------------------------------------------------------------


class FGRPO:
    """Focal Group Relative Policy Optimisation.

    Computes the FGRPO policy-gradient loss for a *group* of trajectories.
    The advantage for each trajectory is estimated relative to the group mean
    (a control-variate baseline), then re-weighted by a focal factor that
    suppresses transitions with near-zero advantage.

    Parameters
    ----------
    gamma:
        Discount factor for cumulative returns (default: 0.99).
    focal_alpha:
        Focal weighting exponent.  Higher values concentrate gradient
        signal on high-advantage transitions (default: 2.0).
    eps:
        Numerical stability constant (default: 1e-8).
    """

    def __init__(
        self,
        gamma: float = 0.99,
        focal_alpha: float = 2.0,
        eps: float = 1e-8,
    ) -> None:
        if not (0.0 < gamma <= 1.0):
            raise ValueError(f"gamma must be in (0, 1], got {gamma}")
        if focal_alpha < 0.0:
            raise ValueError(f"focal_alpha must be >= 0, got {focal_alpha}")

        self.gamma = gamma
        self.focal_alpha = focal_alpha
        self.eps = eps

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discounted_returns(self, rewards: Sequence[float]) -> np.ndarray:
        """Compute discounted cumulative returns for a single trajectory.

        Parameters
        ----------
        rewards:
            Sequence of scalar rewards for one episode.

        Returns
        -------
        np.ndarray
            Array of discounted returns :math:`G_t = \\sum_{k=0}^{T-t-1} \\gamma^k r_{t+k}`.
        """
        rewards = np.asarray(rewards, dtype=float)
        T = len(rewards)
        returns = np.zeros(T, dtype=float)
        running = 0.0
        for t in reversed(range(T)):
            running = rewards[t] + self.gamma * running
            returns[t] = running
        return returns

    def compute_loss(
        self,
        log_probs: Sequence[np.ndarray],
        rewards: Sequence[Sequence[float]],
    ) -> float:
        """Compute the FGRPO loss over a group of trajectories.

        Parameters
        ----------
        log_probs:
            List of per-trajectory log-probability arrays, one entry per step.
            Each element has shape ``(T_i,)`` where ``T_i`` is the episode length.
        rewards:
            List of per-trajectory reward sequences.  Must align with
            ``log_probs`` (same number of trajectories and steps).

        Returns
        -------
        float
            Scalar FGRPO loss (negated for gradient ascent via descent).

        Raises
        ------
        ValueError
            If ``log_probs`` and ``rewards`` have incompatible lengths.
        """
        if len(log_probs) != len(rewards):
            raise ValueError(
                f"log_probs and rewards must have the same number of trajectories, "
                f"got {len(log_probs)} vs {len(rewards)}"
            )
        if len(log_probs) == 0:
            raise ValueError("log_probs must contain at least one trajectory.")

        # Compute discounted returns for every trajectory
        all_returns: List[np.ndarray] = [
            self.discounted_returns(r) for r in rewards
        ]

        # Group-relative baseline: mean return across all transitions in the group
        group_mean = float(np.mean(np.concatenate(all_returns)))
        group_std = float(np.std(np.concatenate(all_returns))) + self.eps

        total_loss = 0.0
        total_steps = 0

        for lp, G in zip(log_probs, all_returns):
            lp = np.asarray(lp, dtype=float)
            if lp.shape[0] != G.shape[0]:
                raise ValueError(
                    f"Trajectory length mismatch: log_probs has {lp.shape[0]} steps "
                    f"but rewards has {G.shape[0]} steps."
                )

            # Normalised advantage
            advantage = (G - group_mean) / group_std

            # Focal weight: w = |A|^alpha (suppresses near-zero advantages)
            focal_weight = (np.abs(advantage) + self.eps) ** self.focal_alpha

            # Focal GRPO loss: -E[w * A * log π(a)]
            total_loss += float(np.sum(-focal_weight * advantage * lp))
            total_steps += len(lp)

        loss = total_loss / max(total_steps, 1)
        logger.debug(
            "FGRPO loss=%.6f  group_mean=%.4f  group_std=%.4f  n_trajectories=%d",
            loss,
            group_mean,
            group_std,
            len(log_probs),
        )
        return loss


# ---------------------------------------------------------------------------
# EMPG — Entropy-Modulated Policy Gradients
# ---------------------------------------------------------------------------


class EMPG:
    """Entropy-Modulated Policy Gradients.

    Augments the standard policy-gradient loss with an adaptive entropy
    bonus whose coefficient :math:`\\beta` is adjusted towards a target
    entropy value.  This prevents the policy from collapsing to a
    deterministic mapping when the environment contains significant
    aleatoric uncertainty.

    Parameters
    ----------
    target_entropy:
        Desired policy entropy in nats.  Set to ``None`` to disable
        adaptive scaling (uses fixed ``entropy_coeff``).
    entropy_coeff:
        Initial entropy regularisation coefficient :math:`\\beta`
        (default: 0.01).
    adapt_rate:
        Rate at which :math:`\\beta` adapts toward the target entropy
        (default: 0.005).
    eps:
        Numerical stability constant (default: 1e-8).
    """

    def __init__(
        self,
        target_entropy: Optional[float] = None,
        entropy_coeff: float = 0.01,
        adapt_rate: float = 0.005,
        eps: float = 1e-8,
    ) -> None:
        if entropy_coeff < 0.0:
            raise ValueError(f"entropy_coeff must be >= 0, got {entropy_coeff}")
        if adapt_rate < 0.0:
            raise ValueError(f"adapt_rate must be >= 0, got {adapt_rate}")

        self.target_entropy = target_entropy
        self.entropy_coeff = entropy_coeff
        self.adapt_rate = adapt_rate
        self.eps = eps

        self._current_beta: float = entropy_coeff

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_beta(self) -> float:
        """Current entropy regularisation coefficient :math:`\\beta`."""
        return self._current_beta

    def policy_entropy(self, log_probs: np.ndarray) -> float:
        """Estimate policy entropy from a batch of log-probabilities.

        Treats ``log_probs`` as unnormalised log-weights and computes the
        soft-max entropy :math:`H = -\\sum_i p_i \\log p_i`.

        Parameters
        ----------
        log_probs:
            1-D array of per-action log-probabilities for a single step.

        Returns
        -------
        float
            Entropy in nats.
        """
        log_probs = np.asarray(log_probs, dtype=float)
        # Numerically stable soft-max
        lp = log_probs - np.max(log_probs)
        probs = np.exp(lp)
        probs /= probs.sum() + self.eps
        entropy = -float(np.sum(probs * np.log(probs + self.eps)))
        return entropy

    def compute_loss(
        self,
        pg_loss: float,
        log_probs_flat: np.ndarray,
    ) -> float:
        """Compute the EMPG total loss.

        Combines a pre-computed policy-gradient loss with the entropy bonus,
        and (optionally) updates :math:`\\beta` toward the target entropy.

        Parameters
        ----------
        pg_loss:
            Scalar policy-gradient loss (e.g., from FGRPO).
        log_probs_flat:
            Flattened array of all per-step log-probabilities in the batch,
            used to estimate the current policy entropy.

        Returns
        -------
        float
            Total EMPG loss: ``pg_loss - beta * H``.
        """
        log_probs_flat = np.asarray(log_probs_flat, dtype=float)
        H = self.policy_entropy(log_probs_flat)

        # Adapt beta toward the target entropy
        if self.target_entropy is not None:
            entropy_error = H - self.target_entropy
            self._current_beta = max(
                0.0, self._current_beta + self.adapt_rate * entropy_error
            )

        total_loss = pg_loss - self._current_beta * H
        logger.debug(
            "EMPG total_loss=%.6f  pg_loss=%.6f  entropy=%.4f  beta=%.6f",
            total_loss,
            pg_loss,
            H,
            self._current_beta,
        )
        return total_loss
