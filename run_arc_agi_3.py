"""
run_arc_agi_3.py — ARC-AGI-3 Interactive Reasoning Environment Initiation Script
==================================================================================
Launches the Mycelium agent into a procedurally generated ARC-AGI-3 environment
and evaluates its adaptive reasoning capabilities.

Architecture
------------
1. **Environment**  — ``InteractiveReasoningEnv`` with max_steps=500 and
   difficulty=``latent_complex``.
2. **Mycelium agent** — lightweight policy network trained with:
   - ``MuonCANS`` optimizer (geometric gradient projection via Newton-Schulz).
   - ``FGRPO`` (Focal Group Relative Policy Optimisation) for exploration.
   - ``EMPG`` (Entropy-Modulated Policy Gradients) for uncertainty calibration.
3. **ECS Heartbeat** — Ω-Axis Kernel ticking loop:
   Spread Activation → Decay → Consolidation.
4. **Telemetry** — ``EngramObservatory`` streams activation, sparsity, and
   structural metrics to TensorBoard asynchronously.

Usage::

    python run_arc_agi_3.py
    python run_arc_agi_3.py --episodes 10 --seed 42 --log-dir runs/arc_agi_3

"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import List, Optional, Tuple

import numpy as np

from arc_agi_3 import EMPG, FGRPO, EngramObservatory, InteractiveReasoningEnv
from optimizers.muon_cans import MuonCANS

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arc_agi_3.run")

# ---------------------------------------------------------------------------
# Mycelium policy network (pure-NumPy two-layer MLP)
# ---------------------------------------------------------------------------

_OBS_DIM = 32  # must match InteractiveReasoningEnv.obs_dim
_ACT_DIM = 8   # must match InteractiveReasoningEnv.act_dim
_HIDDEN_DIM = 64


class MyceliumPolicy:
    """Minimal two-layer MLP policy for the Mycelium agent.

    Parameters are stored as a flat list of NumPy arrays so they can be
    passed directly to ``MuonCANS``.

    Parameters
    ----------
    obs_dim:  Observation dimensionality.
    act_dim:  Action dimensionality.
    hidden:   Hidden layer width.
    seed:     Optional RNG seed.
    """

    def __init__(
        self,
        obs_dim: int = _OBS_DIM,
        act_dim: int = _ACT_DIM,
        hidden: int = _HIDDEN_DIM,
        seed: Optional[int] = None,
    ) -> None:
        rng = np.random.default_rng(seed)
        scale = 0.1

        # Layer 1
        self.W1: np.ndarray = rng.standard_normal((hidden, obs_dim)) * scale
        self.b1: np.ndarray = np.zeros(hidden)

        # Layer 2
        self.W2: np.ndarray = rng.standard_normal((act_dim, hidden)) * scale
        self.b2: np.ndarray = np.zeros(act_dim)

    def parameters(self) -> List[np.ndarray]:
        """Return all trainable parameters as a list."""
        return [self.W1, self.b1, self.W2, self.b2]

    def forward(self, obs: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Forward pass.

        Returns
        -------
        action : np.ndarray  — mean action vector.
        log_prob : np.ndarray — per-dimension log-probabilities (Gaussian).
        """
        h = np.tanh(self.W1 @ obs + self.b1)
        logits = self.W2 @ h + self.b2

        # Treat logits as Gaussian means; sample action
        action = np.tanh(logits)  # bounded to (-1, 1)

        # Log-probability of a unit-variance Gaussian evaluated at logits
        log_prob = -0.5 * logits ** 2 - 0.5 * np.log(2 * np.pi)
        return action, log_prob

    def compute_gradients(
        self,
        obs: np.ndarray,
        loss_signal: float,
    ) -> List[np.ndarray]:
        """Estimate parameter gradients via a finite-difference REINFORCE step.

        Uses a simple perturbation estimate proportional to ``loss_signal``
        so the whole stack remains pure-NumPy without autograd.

        Parameters
        ----------
        obs:         Observation vector.
        loss_signal: Scalar loss value to backpropagate.

        Returns
        -------
        List of gradient arrays matching ``parameters()``.
        """
        h = np.tanh(self.W1 @ obs + self.b1)
        logits = self.W2 @ h + self.b2

        # dL/d_logits (Gaussian log-prob gradient)
        d_logits = logits * loss_signal

        # Gradients for W2, b2
        dW2 = np.outer(d_logits, h)
        db2 = d_logits

        # Gradients for W1, b1
        d_h = self.W2.T @ d_logits
        d_tanh = (1.0 - h ** 2) * d_h
        dW1 = np.outer(d_tanh, obs)
        db1 = d_tanh

        return [dW1, db1, dW2, db2]


# ---------------------------------------------------------------------------
# Ω-Axis ECS Heartbeat
# ---------------------------------------------------------------------------


class OmegaAxisHeartbeat:
    """Ω-Axis Kernel ticking loop: Spread Activation → Decay → Consolidation.

    Maintains an activation state vector that evolves each tick through three
    phases mirroring the ECS (Entity-Component-System) lifecycle used
    throughout the Ouroboros framework.

    Parameters
    ----------
    state_dim: Dimensionality of the kernel state vector.
    spread:    Fraction of activation spread to neighbours each tick (0–1).
    decay:     Decay coefficient applied after spreading (0–1).
    """

    def __init__(
        self,
        state_dim: int = _OBS_DIM,
        spread: float = 0.1,
        decay: float = 0.95,
    ) -> None:
        self.state_dim = state_dim
        self.spread = spread
        self.decay = decay
        self._state: np.ndarray = np.zeros(state_dim)
        self._tick_count: int = 0

    @property
    def tick_count(self) -> int:
        return self._tick_count

    def tick(self, external_input: Optional[np.ndarray] = None) -> np.ndarray:
        """Advance the kernel by one tick.

        Phases
        ------
        1. **Spread Activation** — diffuse current state to adjacent dimensions.
        2. **Decay**             — attenuate state by the decay coefficient.
        3. **Consolidation**     — merge external input (agent action feedback).

        Parameters
        ----------
        external_input:
            Optional vector injected at the Consolidation phase (e.g., the
            agent's last action projected back into kernel space).

        Returns
        -------
        np.ndarray
            Updated kernel state after all three phases.
        """
        # Phase 1 — Spread Activation (circular convolution with spread kernel)
        spread_state = (
            (1.0 - self.spread) * self._state
            + 0.5 * self.spread * np.roll(self._state, 1)
            + 0.5 * self.spread * np.roll(self._state, -1)
        )

        # Phase 2 — Decay
        decayed = spread_state * self.decay

        # Phase 3 — Consolidation (inject external input)
        if external_input is not None:
            ext = np.asarray(external_input, dtype=float)
            if ext.shape[0] != self.state_dim:
                # Resize via zero-padding or truncation
                resized = np.zeros(self.state_dim)
                n = min(ext.shape[0], self.state_dim)
                resized[:n] = ext[:n]
                ext = resized
            decayed = decayed + ext * (1.0 - self.decay)

        # Normalise to unit norm to prevent unbounded growth
        norm = np.linalg.norm(decayed)
        if norm > 1.0:
            decayed = decayed / norm

        self._state = decayed
        self._tick_count += 1
        return self._state.copy()


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------


def _run_episode(
    env: InteractiveReasoningEnv,
    policy: MyceliumPolicy,
    optimizer: MuonCANS,
    fgrpo: FGRPO,
    empg: EMPG,
    heartbeat: OmegaAxisHeartbeat,
    observatory: EngramObservatory,
    episode_idx: int,
    seed: Optional[int] = None,
) -> dict:
    """Run one full episode and update the policy.

    Returns a dict with episode statistics.
    """
    obs = env.reset(seed=seed)
    trajectory_log_probs: List[np.ndarray] = []
    trajectory_rewards: List[float] = []

    step_t = 0
    total_reward = 0.0

    while True:
        # ECS Heartbeat tick — Spread → Decay → Consolidation
        kernel_state = heartbeat.tick(external_input=obs)

        # Policy forward pass on heartbeat-modulated observation
        modulated_obs = obs * 0.8 + kernel_state * 0.2
        action, log_prob = policy.forward(modulated_obs)

        # Environment step
        env_step = env.step(action)
        obs = env_step.observation
        reward = env_step.reward

        trajectory_log_probs.append(np.atleast_1d(log_prob.sum()))
        trajectory_rewards.append(reward)
        total_reward += reward
        step_t += 1

        # Push telemetry asynchronously
        observatory.push(
            activations=modulated_obs,
            weights=policy.W1,
            step=episode_idx * env.max_steps + step_t,
        )

        if env_step.done:
            break

    # Policy update using FGRPO + EMPG
    fgrpo_loss = fgrpo.compute_loss(
        log_probs=[np.concatenate(trajectory_log_probs)],
        rewards=[trajectory_rewards],
    )
    lp_flat = np.concatenate(trajectory_log_probs)
    total_loss = empg.compute_loss(pg_loss=fgrpo_loss, log_probs_flat=lp_flat)

    # Gradient update via MuonCANS
    grads = policy.compute_gradients(obs, total_loss)
    optimizer.step(grads)

    stats = {
        "episode": episode_idx,
        "steps": step_t,
        "total_reward": total_reward,
        "mean_reward": total_reward / max(step_t, 1),
        "fgrpo_loss": fgrpo_loss,
        "empg_loss": total_loss,
        "empg_beta": empg.current_beta,
        "muon_step": optimizer.step_count,
    }

    logger.info(
        "episode=%03d  steps=%d  reward_sum=%.4f  reward_mean=%.4f  "
        "fgrpo=%.4f  empg_β=%.5f",
        episode_idx,
        step_t,
        total_reward,
        stats["mean_reward"],
        fgrpo_loss,
        empg.current_beta,
    )

    return stats


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_arc_agi_3(
    n_episodes: int = 5,
    max_steps: int = 500,
    difficulty: str = "latent_complex",
    log_dir: str = "runs/arc_agi_3",
    seed: Optional[int] = None,
    lr: float = 0.02,
    momentum: float = 0.95,
    target_entropy: float = 1.0,
) -> List[dict]:
    """Run the ARC-AGI-3 Mycelium initiation sequence.

    Parameters
    ----------
    n_episodes:      Number of training episodes.
    max_steps:       Maximum steps per episode (default: 500).
    difficulty:      Environment difficulty level (default: ``latent_complex``).
    log_dir:         TensorBoard log directory.
    seed:            Optional global seed.
    lr:              MuonCANS learning rate.
    momentum:        MuonCANS momentum coefficient.
    target_entropy:  EMPG target entropy in nats.

    Returns
    -------
    List[dict]
        Per-episode statistics dictionaries.
    """
    logger.info(
        "=== ARC-AGI-3 Mycelium Initiation ===  episodes=%d  difficulty=%s",
        n_episodes,
        difficulty,
    )

    # 1. Environment Setup
    env = InteractiveReasoningEnv(
        max_steps=max_steps,
        difficulty=difficulty,
    )

    # 2. Mycelium agent components
    policy = MyceliumPolicy(obs_dim=env.obs_dim, act_dim=env.act_dim, seed=seed)
    optimizer = MuonCANS(policy.parameters(), lr=lr, momentum=momentum)
    fgrpo = FGRPO(gamma=0.99, focal_alpha=2.0)
    empg = EMPG(target_entropy=target_entropy, entropy_coeff=0.01)

    # 3. ECS Heartbeat (Ω-Axis Kernel)
    heartbeat = OmegaAxisHeartbeat(state_dim=env.obs_dim)

    # 4. Live observability — EngramObservatory (async, non-blocking)
    observatory = EngramObservatory(log_dir=log_dir)
    observatory.start()

    # 5. Training loop with robust error capture
    all_stats: List[dict] = []
    try:
        for episode in range(n_episodes):
            ep_seed = (seed + episode) if seed is not None else None
            stats = _run_episode(
                env=env,
                policy=policy,
                optimizer=optimizer,
                fgrpo=fgrpo,
                empg=empg,
                heartbeat=heartbeat,
                observatory=observatory,
                episode_idx=episode,
                seed=ep_seed,
            )
            all_stats.append(stats)

        logger.info(
            "=== Initiation complete ===  episodes_run=%d  "
            "total_reward=%.4f  final_beta=%.5f",
            len(all_stats),
            sum(s["total_reward"] for s in all_stats),
            empg.current_beta,
        )

    except Exception:
        logger.exception("Simulation failed — shutting down telemetry daemon cleanly.")
        raise
    finally:
        # Ensure clean telemetry daemon shutdown to avoid memory leaks
        observatory.stop()

    return all_stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ARC-AGI-3 Mycelium Initiation Script"
    )
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes")
    parser.add_argument(
        "--max-steps", type=int, default=500, help="Max steps per episode"
    )
    parser.add_argument(
        "--difficulty",
        default="latent_complex",
        choices=["simple", "latent_medium", "latent_complex"],
        help="Environment difficulty",
    )
    parser.add_argument(
        "--log-dir", default="runs/arc_agi_3", help="TensorBoard log directory"
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--lr", type=float, default=0.02, help="MuonCANS learning rate")
    parser.add_argument(
        "--momentum", type=float, default=0.95, help="MuonCANS momentum"
    )
    parser.add_argument(
        "--target-entropy",
        type=float,
        default=1.0,
        help="EMPG target entropy (nats)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    start_time = time.time()
    try:
        stats = run_arc_agi_3(
            n_episodes=args.episodes,
            max_steps=args.max_steps,
            difficulty=args.difficulty,
            log_dir=args.log_dir,
            seed=args.seed,
            lr=args.lr,
            momentum=args.momentum,
            target_entropy=args.target_entropy,
        )
    except Exception:
        logger.error("run_arc_agi_3 exited with an error.")
        return 1

    elapsed = time.time() - start_time
    logger.info("Wall-clock time: %.2fs", elapsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
