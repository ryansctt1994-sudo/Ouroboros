"""
InteractiveReasoningEnv
=======================
Procedurally generated Interactive Reasoning Environment for ARC-AGI-3.

The environment generates latent-rule tasks of configurable difficulty and
exposes a standard RL step/reset interface.  Each episode consists of a
sequence of (observation, action, reward) transitions governed by hidden
compositional rules that the agent must discover through interaction.

Difficulty levels
-----------------
``simple``         — single-rule tasks with explicit cues.
``latent_medium``  — two-rule compositions with partial cues.
``latent_complex`` — three-or-more-rule compositions with no explicit cues
                     (the setting used for ARC-AGI-3 evaluation).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DIFFICULTY_LEVELS: Tuple[str, ...] = ("simple", "latent_medium", "latent_complex")

_RULE_COMPLEXITY: Dict[str, int] = {
    "simple": 1,
    "latent_medium": 2,
    "latent_complex": 3,
}

# Observation and action space dimensionality
OBS_DIM: int = 32
ACT_DIM: int = 8


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class EnvStep:
    """Single environment transition."""

    observation: np.ndarray
    reward: float
    done: bool
    info: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Latent rule primitives
# ---------------------------------------------------------------------------


def _rotation_rule(obs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Apply a cyclic rotation to the observation vector."""
    shift = int(rng.integers(1, obs.shape[0]))
    return np.roll(obs, shift)


def _scaling_rule(obs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Scale the observation by a random factor drawn from (0.5, 2.0)."""
    factor = rng.uniform(0.5, 2.0)
    return obs * factor


def _projection_rule(obs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Project the observation onto a random subspace."""
    dim = obs.shape[0]
    proj = rng.standard_normal((dim, dim))
    proj /= np.linalg.norm(proj, axis=0, keepdims=True) + 1e-8
    return proj @ obs


_ALL_RULES = [_rotation_rule, _scaling_rule, _projection_rule]


# ---------------------------------------------------------------------------
# InteractiveReasoningEnv
# ---------------------------------------------------------------------------


class InteractiveReasoningEnv:
    """Procedurally generated Interactive Reasoning Environment.

    Each episode is governed by a latent compositional rule randomly sampled
    at ``reset`` time.  The agent receives a noisy observation of the current
    hidden state and must submit an action vector; reward is the cosine
    similarity between the action and the *target* direction implied by the
    latent rule.

    Parameters
    ----------
    max_steps:
        Maximum number of steps per episode (default: 500).
    difficulty:
        One of ``"simple"``, ``"latent_medium"``, or ``"latent_complex"``
        (default: ``"latent_complex"``).
    obs_dim:
        Dimensionality of the observation vector (default: 32).
    act_dim:
        Dimensionality of the action vector (default: 8).
    noise_scale:
        Standard deviation of Gaussian observation noise (default: 0.1).
    seed:
        Optional seed for reproducibility.
    """

    def __init__(
        self,
        max_steps: int = 500,
        difficulty: str = "latent_complex",
        obs_dim: int = OBS_DIM,
        act_dim: int = ACT_DIM,
        noise_scale: float = 0.1,
        seed: Optional[int] = None,
    ) -> None:
        if difficulty not in DIFFICULTY_LEVELS:
            raise ValueError(
                f"difficulty must be one of {DIFFICULTY_LEVELS}, got {difficulty!r}"
            )
        if max_steps <= 0:
            raise ValueError(f"max_steps must be positive, got {max_steps}")

        self.max_steps = max_steps
        self.difficulty = difficulty
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        self.noise_scale = noise_scale

        self._rng = np.random.default_rng(seed)
        self._step_count: int = 0
        self._hidden_state: Optional[np.ndarray] = None
        self._active_rules: List[Any] = []
        self._episode_seed: Optional[int] = None

        logger.info(
            "InteractiveReasoningEnv initialised — difficulty=%s  max_steps=%d",
            difficulty,
            max_steps,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def step_count(self) -> int:
        """Current step within the active episode."""
        return self._step_count

    def reset(self, seed: Optional[int] = None) -> np.ndarray:
        """Begin a new episode.

        Procedurally samples a fresh latent rule composition and returns the
        initial observation.

        Parameters
        ----------
        seed:
            Optional per-episode seed (overrides instance RNG for this episode).

        Returns
        -------
        np.ndarray
            Initial observation vector of shape ``(obs_dim,)``.
        """
        if seed is not None:
            self._rng = np.random.default_rng(seed)
            self._episode_seed = seed

        self._step_count = 0

        # Sample a fresh hidden state
        self._hidden_state = self._rng.standard_normal(self.obs_dim)
        self._hidden_state /= np.linalg.norm(self._hidden_state) + 1e-8

        # Sample latent rules according to difficulty
        n_rules = _RULE_COMPLEXITY[self.difficulty]
        rule_indices = self._rng.choice(len(_ALL_RULES), size=n_rules, replace=True)
        self._active_rules = [_ALL_RULES[i] for i in rule_indices]

        obs = self._get_observation()
        logger.debug(
            "reset — episode_seed=%s  n_rules=%d  obs_norm=%.4f",
            self._episode_seed,
            n_rules,
            float(np.linalg.norm(obs)),
        )
        return obs

    def step(self, action: np.ndarray) -> EnvStep:
        """Advance the environment by one step.

        Parameters
        ----------
        action:
            Agent action vector of shape ``(act_dim,)``.  The action is
            projected into the observation space to compute the reward.

        Returns
        -------
        EnvStep
            Named tuple containing the next observation, scalar reward,
            done flag, and an info dict.

        Raises
        ------
        RuntimeError
            If ``reset`` has not been called before the first ``step``.
        """
        if self._hidden_state is None:
            raise RuntimeError("Call reset() before step().")

        action = np.asarray(action, dtype=float)

        # Project action into observation space if shapes differ
        if action.shape[0] != self.obs_dim:
            proj_matrix = self._rng.standard_normal((self.obs_dim, action.shape[0]))
            proj_matrix /= np.linalg.norm(proj_matrix, axis=0, keepdims=True) + 1e-8
            action_proj = proj_matrix @ action
        else:
            action_proj = action

        # Evolve hidden state through active rules
        new_state = self._hidden_state.copy()
        for rule in self._active_rules:
            new_state = rule(new_state, self._rng)
        new_state /= np.linalg.norm(new_state) + 1e-8
        self._hidden_state = new_state

        # Reward = cosine similarity between action projection and new hidden state
        act_norm = np.linalg.norm(action_proj) + 1e-8
        state_norm = np.linalg.norm(self._hidden_state) + 1e-8
        reward = float(
            np.dot(action_proj / act_norm, self._hidden_state / state_norm)
        )

        self._step_count += 1
        done = self._step_count >= self.max_steps

        obs = self._get_observation()
        info: Dict[str, Any] = {
            "step": self._step_count,
            "difficulty": self.difficulty,
            "n_rules": len(self._active_rules),
        }

        return EnvStep(observation=obs, reward=reward, done=done, info=info)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_observation(self) -> np.ndarray:
        """Return a noisy observation of the current hidden state."""
        noise = self._rng.standard_normal(self.obs_dim) * self.noise_scale
        return (self._hidden_state + noise).astype(np.float64)
