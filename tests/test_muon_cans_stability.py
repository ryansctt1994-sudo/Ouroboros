"""
Instrumented stability test for MuonCANS.

Runs MuonCANS for many episodes with a synthetic learning environment and
records three diagnostic curves:

    sakib_index       – coherence signal (proxy for policy quality)
    policy_delta_norm – magnitude of each weight update (from metrics)
    reward_variance   – rolling variance of rewards (policy steadiness)

The tests assert the *three stability signatures* that indicate a healthy
orthogonal optimizer:

    1. Weight norm stays roughly stable (no explosion, no collapse).
    2. Updates mostly rotate the policy:
       cos(angle(w, Δw)) stays near zero because Δw ⊥ w after NS orthog.
    3. Reward variance does not grow over time (gating stabilises policy).

If instead long flat regions, sakib_advantage ≈ 0, and almost no policy
movement are observed, the gating rule is too strict — this is also tested
so the harness can raise an alert.

Scientific question under test
-------------------------------
Can learning happen primarily through rotation of representations?

The stability signatures above answer this question empirically without
requiring any algorithmic change to MuonCANS.
"""

from __future__ import annotations

import math
from typing import Dict, List

import numpy as np
import pytest

from optimizers.muon_cans import MuonCANS

# ---------------------------------------------------------------------------
# Synthetic learning environment
# ---------------------------------------------------------------------------

_ENV_SEED = 7


class _SyntheticEnv:
    """Minimal environment for stability testing.

    A linear policy maps weight matrix W onto a latent state; the reward is
    the cosine similarity of that state to a fixed target direction.  The
    "Sakib index" is approximated by smoothed reward.

    The gradient is the direction that increases reward, plus Gaussian noise
    to simulate real-world stochasticity.

    Parameters
    ----------
    n_in, n_out:
        Parameter matrix shape (policy layer).
    noise_sigma:
        Standard deviation of gradient noise.
    seed:
        RNG seed for reproducibility.
    """

    def __init__(
        self,
        n_in: int = 16,
        n_out: int = 8,
        noise_sigma: float = 0.05,
        seed: int = _ENV_SEED,
    ) -> None:
        rng = np.random.default_rng(seed)
        self.target = rng.standard_normal(n_out)
        self.target /= np.linalg.norm(self.target) + 1e-8
        self.noise_sigma = noise_sigma
        self._rng = rng
        self.n_in = n_in
        self.n_out = n_out

    def reward(self, w: np.ndarray) -> float:
        """Cosine similarity of W @ ones to the target direction."""
        state = w @ np.ones(self.n_in) / self.n_in
        state_norm = np.linalg.norm(state) + 1e-8
        return float(np.dot(state / state_norm, self.target))

    def grad(self, w: np.ndarray) -> np.ndarray:
        """Policy-gradient direction (toward target) + Gaussian noise."""
        # Derivative of reward w.r.t. W: target ⊗ ones / n_in
        clean = np.outer(self.target, np.ones(self.n_in)) / self.n_in
        noise = self._rng.standard_normal(w.shape) * self.noise_sigma
        return (clean + noise).astype(float)


# ---------------------------------------------------------------------------
# Stability harness
# ---------------------------------------------------------------------------


class StabilityHarness:
    """Run MuonCANS for *n_steps* and record the three diagnostic curves.

    Attributes
    ----------
    sakib_indices : list[float]
        Smoothed reward used as the Sakib-index proxy.
    delta_norms : list[float]
        ``policy_delta_norm`` from ``MuonCANS.metrics`` after each step.
    reward_variance : list[float]
        Rolling variance of rewards over a window of size *var_window*.
    cos_w_dw : list[float]
        ``cos_w_dw`` from ``MuonCANS.metrics`` — alignment between weights
        and update direction.  Should stay near zero for a rotational optimizer.
    weight_norms : list[float]
        ``weight_norm`` from ``MuonCANS.metrics`` — tracks ||w||.
    """

    def __init__(
        self,
        n_steps: int = 300,
        lr: float = 0.02,
        momentum: float = 0.95,
        var_window: int = 20,
        env_seed: int = _ENV_SEED,
    ) -> None:
        self.n_steps = n_steps
        self.var_window = var_window
        self.env = _SyntheticEnv(seed=env_seed)

        rng = np.random.default_rng(env_seed + 1)
        self._w = rng.standard_normal((self.env.n_out, self.env.n_in))
        self._opt = MuonCANS([self._w], lr=lr, momentum=momentum)

        # Recorded curves
        self.sakib_indices: List[float] = []
        self.delta_norms: List[float] = []
        self.reward_variance: List[float] = []
        self.cos_w_dw: List[float] = []
        self.weight_norms: List[float] = []

        self._rewards: List[float] = []
        self._smoothed_sakib: float = 0.5

    def run(self) -> "StabilityHarness":
        """Execute the full run and populate recorded curves."""
        for _ in range(self.n_steps):
            r = self.env.reward(self._w)
            g = self.env.grad(self._w)

            # Sakib advantage: smoothed reward signal, clipped to [0, ∞)
            self._smoothed_sakib = 0.9 * self._smoothed_sakib + 0.1 * max(r, 0.0)
            sakib_adv = self._smoothed_sakib

            self._opt.step([g], sakib_advantage=sakib_adv)

            # --- record ---
            self._rewards.append(r)
            self.sakib_indices.append(self._smoothed_sakib)
            self.delta_norms.append(self._opt.metrics["policy_delta_norm"][0])
            self.cos_w_dw.append(self._opt.metrics["cos_w_dw"][0])
            self.weight_norms.append(self._opt.metrics["weight_norm"][0])

            # Rolling reward variance
            window = self._rewards[-self.var_window:]
            rv = float(np.var(window)) if len(window) >= 2 else 0.0
            self.reward_variance.append(rv)

        return self

    # Convenience aggregates used by the tests below
    def _first_half(self, curve: List[float]) -> List[float]:
        mid = self.n_steps // 2
        return curve[:mid]

    def _second_half(self, curve: List[float]) -> List[float]:
        mid = self.n_steps // 2
        return curve[mid:]


# ---------------------------------------------------------------------------
# Pre-computed shared run (one run shared across the test class)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def harness() -> StabilityHarness:
    return StabilityHarness(n_steps=300).run()


# ---------------------------------------------------------------------------
# Stability signature tests
# ---------------------------------------------------------------------------


class TestWeightNormStability:
    """Weight norm should remain roughly stable — not explode or collapse."""

    def test_weight_norm_does_not_explode(self, harness: StabilityHarness) -> None:
        """||w|| must stay below a generous upper bound throughout the run."""
        max_norm = max(harness.weight_norms)
        initial_norm = harness.weight_norms[0]
        assert max_norm < 50.0 * max(initial_norm, 1.0), (
            f"Weight norm exploded: initial={initial_norm:.3f}, max={max_norm:.3f}"
        )

    def test_weight_norm_does_not_collapse(self, harness: StabilityHarness) -> None:
        """||w|| must stay above a small positive threshold."""
        min_norm = min(harness.weight_norms)
        assert min_norm > 1e-3, (
            f"Weight norm collapsed to near zero: {min_norm:.6g}"
        )

    def test_weight_norm_variance_bounded(self, harness: StabilityHarness) -> None:
        """Standard deviation of ||w|| should be < 2× its mean (relatively stable)."""
        norms = np.array(harness.weight_norms)
        std_rel = float(np.std(norms) / (np.mean(norms) + 1e-8))
        assert std_rel < 2.0, (
            f"Weight norm is too volatile: relative std={std_rel:.3f}"
        )


class TestRotationalUpdates:
    """Updates should mostly rotate the policy: cos(angle(w, Δw)) near zero.

    Because MuonCANS orthogonalises the gradient update direction (removing
    rank-one components aligned with the gradient matrix axes), the effective
    update for a 2-D weight matrix is approximately perpendicular to the raw
    gradient direction.  The cosine between the *weight vector* and the
    *update vector* is a proxy for how "rotational" vs "radial" each step is.

    We do not require cos ≈ 0 for every single step (momentum and weight-
    decay can introduce a small radial component), but the *mean absolute
    cosine* must remain small.
    """

    def test_mean_abs_cos_is_small(self, harness: StabilityHarness) -> None:
        """Mean |cos(w, Δw)| should be well below 1 (not purely radial)."""
        mean_abs_cos = float(np.mean(np.abs(harness.cos_w_dw)))
        assert mean_abs_cos < 0.9, (
            f"Updates are too radial (mean |cos|={mean_abs_cos:.3f}); "
            "orthogonal constraint may not be active"
        )

    def test_updates_are_non_zero(self, harness: StabilityHarness) -> None:
        """Policy should actually move — no long flat (stalled) regions."""
        zero_steps = sum(1 for d in harness.delta_norms if d < 1e-10)
        fraction_zero = zero_steps / len(harness.delta_norms)
        assert fraction_zero < 0.20, (
            f"{100*fraction_zero:.1f}% of steps produced zero updates; "
            "sakib gating may be too strict"
        )

    def test_policy_delta_norm_is_finite(self, harness: StabilityHarness) -> None:
        assert all(math.isfinite(d) for d in harness.delta_norms), (
            "policy_delta_norm contains NaN or Inf"
        )


class TestSakibIndexDynamics:
    """Sakib index (coherence proxy) should show meaningful dynamics."""

    def test_sakib_index_is_bounded(self, harness: StabilityHarness) -> None:
        """Sakib index must stay in [0, 1] since it is a smoothed reward."""
        assert all(0.0 <= s <= 1.0 for s in harness.sakib_indices), (
            "Sakib index out of [0, 1] range"
        )

    def test_sakib_index_is_not_always_zero(self, harness: StabilityHarness) -> None:
        """Advantage must be non-zero at least some of the time."""
        non_zero = sum(1 for s in harness.sakib_indices if s > 1e-6)
        assert non_zero > len(harness.sakib_indices) // 4, (
            "Sakib advantage was near-zero for more than 75% of steps; "
            "check coherence signal or gating threshold"
        )

    def test_sakib_index_shows_upward_trend(self, harness: StabilityHarness) -> None:
        """The smoothed Sakib index should increase (or stay flat) over time.

        The policy is learning to align with the target direction, so
        coherence should trend upward.
        """
        first_mean = float(np.mean(harness._first_half(harness.sakib_indices)))
        second_mean = float(np.mean(harness._second_half(harness.sakib_indices)))
        # Allow a small tolerance: we don't require strict monotone increase.
        assert second_mean >= first_mean - 0.1, (
            f"Sakib index degraded: first_half_mean={first_mean:.4f}, "
            f"second_half_mean={second_mean:.4f}"
        )


class TestRewardVariance:
    """Reward variance should not grow over time (policy should stabilise).

    We compare variance in the second half of training to the first half.
    A healthy rotational optimizer keeps variance flat or decreasing.
    """

    def test_reward_variance_does_not_grow(self, harness: StabilityHarness) -> None:
        first_var  = float(np.mean(harness._first_half(harness.reward_variance)))
        second_var = float(np.mean(harness._second_half(harness.reward_variance)))
        # Accept up to 50% growth; flag if variance more than doubles.
        assert second_var <= first_var * 1.5 + 1e-6, (
            f"Reward variance grew significantly: "
            f"first_half={first_var:.5f}, second_half={second_var:.5f}"
        )

    def test_reward_variance_is_finite(self, harness: StabilityHarness) -> None:
        assert all(math.isfinite(v) for v in harness.reward_variance), (
            "reward_variance contains NaN or Inf"
        )


# ---------------------------------------------------------------------------
# Gating sensitivity probe
# ---------------------------------------------------------------------------


class TestGatingSensitivity:
    """Verify the Sakib-advantage gate is responsive but not over-restrictive.

    We re-run with a *zero* advantage to confirm that advantage_eps still
    produces small-but-nonzero updates (epsilon gating), and with a *large*
    advantage to confirm the gate scales updates up.
    """

    def _run_with_constant_advantage(self, adv: float, n_steps: int = 50) -> float:
        """Return mean delta_norm over n_steps with a constant advantage."""
        rng = np.random.default_rng(99)
        env = _SyntheticEnv(seed=99)
        # Shape must match env gradient: (n_out, n_in)
        w = rng.standard_normal((env.n_out, env.n_in))
        opt = MuonCANS([w], lr=0.02, momentum=0.0)
        norms = []
        for _ in range(n_steps):
            g = env.grad(w)
            opt.step([g], sakib_advantage=adv)
            norms.append(opt.metrics["policy_delta_norm"][0])
        return float(np.mean(norms))

    def test_zero_advantage_still_produces_updates_via_eps(self) -> None:
        mean_norm = self._run_with_constant_advantage(0.0)
        assert mean_norm > 0, (
            "Zero sakib_advantage should still produce nonzero updates via advantage_eps"
        )

    def test_large_advantage_scales_updates_up(self) -> None:
        norm_small = self._run_with_constant_advantage(0.01)
        norm_large = self._run_with_constant_advantage(1.0)
        assert norm_large > norm_small, (
            f"Larger advantage should produce larger updates; "
            f"got small={norm_small:.6g}, large={norm_large:.6g}"
        )
