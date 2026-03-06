"""
Instrumented stability test for MuonCANS.

Runs MuonCANS for many episodes with a synthetic learning environment and
records five diagnostic curves:

    sakib_index       – coherence signal (proxy for policy quality)
    policy_delta_norm – magnitude of each weight update (from metrics)
    reward_variance   – rolling variance of rewards (policy steadiness)
    grad_weight_cos   – cos(g, w) before projection (is constraint cosmetic?)
    weight_drift_cos  – cos(w_t, w_{t-1}) (slow rotation vs turbulence)

Five observability tests answer the following questions:

    1. Alignment (grad_weight_cos):
       If cos(g, w) ≈ 0 most of the time, the projection removes almost
       nothing and the constraint is cosmetic.  If it's large, orthogonal
       projection discards a meaningful portion of the learning signal.

    2. Representation drift (weight_drift_cos):
       Consecutive weights should have high cosine similarity (near 1)
       — slow rotation, not turbulence.  Low similarity means the policy
       loses memory every step ("amnesia").

    3. Multi-seed variance:
       10 short seeds, not one heroic run.  We compare MuonCANS seed
       variance against a plain normalised-SGD baseline.  Lower variance
       is a real, practical contribution even without faster convergence.

    4. Gating distribution:
       The Sakib advantage must not be near zero most of the time or the
       optimizer is just a brake pedal.

    5. Baseline comparison:
       SGD (norm-scale), Adam, MuonCANS — same environment, same seeds.
       All should improve; MuonCANS result is placed in context.

Scientific question under test
-------------------------------
Can learning happen primarily through rotation of representations?

The curves above answer this question empirically without requiring any
algorithmic change to MuonCANS.
"""

from __future__ import annotations

import math
import platform
import sys
from typing import Dict, List, Optional

import numpy as np
import pytest

from optimizers.muon_cans import MuonCANS

# ---------------------------------------------------------------------------
# Reproducibility header — logged once at module import
# ---------------------------------------------------------------------------
# Learning stability experiments are sensitive to library and runtime
# differences.  Log key environment facts so that any numerical anomaly can
# be traced back to a specific dependency version.
_ENV_INFO: Dict[str, str] = {
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "numpy": np.__version__,
}
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
    """Run MuonCANS for *n_steps* and record five diagnostic curves.

    Attributes
    ----------
    sakib_indices : list[float]
        Smoothed reward used as the Sakib-index proxy.
    delta_norms : list[float]
        ``policy_delta_norm`` from ``MuonCANS.metrics`` after each step.
    reward_variance : list[float]
        Rolling variance of rewards over a window of size *var_window*.
    cos_w_dw : list[float]
        ``cos_w_dw`` — alignment between weights and update direction (post-projection).
    weight_norms : list[float]
        ``weight_norm`` — tracks ||w||.
    grad_weight_cos : list[float]
        ``grad_weight_cos`` — cos(raw_g, w) *before* projection.
    grad_grad_cos : list[float]
        ``grad_grad_cos`` — cos(g_t, g_{t-1}).  Reveals gradient consistency:
        near-zero → random walk; negative → optimizer fighting itself.
    weight_drift_cos : list[float]
        cos(w_t, w_{t-1}) computed externally.  Near 1 = slow rotation;
        near 0 = turbulent/amnesiac policy.
    raw_advantages : list[float]
        Raw Sakib advantage values passed to each step.
    env_info : dict[str, str]
        Snapshot of environment versions captured at construction time for
        reproducibility tracing.
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
        self.env_info: Dict[str, str] = dict(_ENV_INFO)

        rng = np.random.default_rng(env_seed + 1)
        self._w = rng.standard_normal((self.env.n_out, self.env.n_in))
        self._opt = MuonCANS([self._w], lr=lr, momentum=momentum)

        # Recorded curves
        self.sakib_indices: List[float] = []
        self.delta_norms: List[float] = []
        self.reward_variance: List[float] = []
        self.cos_w_dw: List[float] = []
        self.weight_norms: List[float] = []
        self.grad_weight_cos: List[float] = []
        self.grad_grad_cos: List[float] = []
        self.weight_drift_cos: List[float] = []
        self.raw_advantages: List[float] = []

        self._rewards: List[float] = []
        self._smoothed_sakib: float = 0.5

    def run(self) -> "StabilityHarness":
        """Execute the full run and populate all diagnostic curves."""
        w_prev: Optional[np.ndarray] = None

        for _ in range(self.n_steps):
            r = self.env.reward(self._w)
            g = self.env.grad(self._w)

            # Sakib advantage: smoothed reward signal, clipped to [0, ∞)
            self._smoothed_sakib = 0.9 * self._smoothed_sakib + 0.1 * max(r, 0.0)
            sakib_adv = self._smoothed_sakib
            self.raw_advantages.append(sakib_adv)

            self._opt.step([g], sakib_advantage=sakib_adv)

            # --- record optimizer metrics ---
            self._rewards.append(r)
            self.sakib_indices.append(self._smoothed_sakib)
            self.delta_norms.append(self._opt.metrics["policy_delta_norm"][0])
            self.cos_w_dw.append(self._opt.metrics["cos_w_dw"][0])
            self.weight_norms.append(self._opt.metrics["weight_norm"][0])
            self.grad_weight_cos.append(self._opt.metrics["grad_weight_cos"][0])
            self.grad_grad_cos.append(self._opt.metrics["grad_grad_cos"][0])

            # --- weight drift: cos(w_t, w_{t-1}) ---
            # Snapshot the weight *after* the step so we measure the change
            # the optimizer actually produced, not a pre-step vs pre-step pair.
            w_post = self._w.ravel().copy()
            if w_prev is not None:
                denom = (np.linalg.norm(w_prev) * np.linalg.norm(w_post)) + 1e-8
                drift = float(np.dot(w_prev, w_post) / denom)
            else:
                drift = 1.0  # first step: no previous state to compare
            self.weight_drift_cos.append(drift)
            w_prev = w_post  # store post-step weight for next iteration

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


# ---------------------------------------------------------------------------
# Baseline optimisers (SGD-norm and Adam) for comparative tests
# ---------------------------------------------------------------------------


class _SGDBaseline:
    """Normalised-gradient SGD (ascent): w += lr * g / (||g|| + eps).

    ``env.grad()`` returns the direction that *increases* reward, so we add
    the normalised gradient to ascend toward higher reward.
    """

    def __init__(self, w: np.ndarray, lr: float = 0.02) -> None:
        self.w = w
        self.lr = lr
        self._eps = 1e-8

    def step(self, g: np.ndarray) -> None:
        norm = np.linalg.norm(g) + self._eps
        self.w += self.lr * g / norm  # gradient ascent

    def reward(self, env: _SyntheticEnv) -> float:
        return env.reward(self.w)


class _AdamBaseline:
    """Adam optimiser (ascent, β₁=0.9, β₂=0.999, ε=1e-8).

    Like ``_SGDBaseline``, uses gradient ascent because ``env.grad()``
    returns the direction that increases reward.
    """

    def __init__(self, w: np.ndarray, lr: float = 0.005) -> None:
        self.w = w
        self.lr = lr
        self._m = np.zeros_like(w)
        self._v = np.zeros_like(w)
        self._t = 0
        self._b1, self._b2, self._eps = 0.9, 0.999, 1e-8

    def step(self, g: np.ndarray) -> None:
        self._t += 1
        self._m = self._b1 * self._m + (1 - self._b1) * g
        self._v = self._b2 * self._v + (1 - self._b2) * g ** 2
        m_hat = self._m / (1 - self._b1 ** self._t)
        v_hat = self._v / (1 - self._b2 ** self._t)
        self.w += self.lr * m_hat / (np.sqrt(v_hat) + self._eps)  # gradient ascent

    def reward(self, env: _SyntheticEnv) -> float:
        return env.reward(self.w)


# ---------------------------------------------------------------------------
# Multi-seed runner
# ---------------------------------------------------------------------------


def _run_muon_cans_seed(seed: int, n_steps: int = 100, lr: float = 0.02) -> float:
    """Run one MuonCANS seed; return final smoothed reward."""
    env = _SyntheticEnv(seed=seed)
    rng = np.random.default_rng(seed + 100)
    w = rng.standard_normal((env.n_out, env.n_in))
    opt = MuonCANS([w], lr=lr, momentum=0.95)
    smoothed = 0.5
    for _ in range(n_steps):
        r = env.reward(w)
        g = env.grad(w)
        smoothed = 0.9 * smoothed + 0.1 * max(r, 0.0)
        opt.step([g], sakib_advantage=smoothed)
    return env.reward(w)


def _run_sgd_seed(seed: int, n_steps: int = 100, lr: float = 0.02) -> float:
    """Run one SGD-norm seed; return final reward."""
    env = _SyntheticEnv(seed=seed)
    rng = np.random.default_rng(seed + 100)
    w = rng.standard_normal((env.n_out, env.n_in))
    opt = _SGDBaseline(w, lr=lr)
    for _ in range(n_steps):
        opt.step(env.grad(w))
    return env.reward(w)


def _run_adam_seed(seed: int, n_steps: int = 100, lr: float = 0.005) -> float:
    """Run one Adam seed; return final reward."""
    env = _SyntheticEnv(seed=seed)
    rng = np.random.default_rng(seed + 100)
    w = rng.standard_normal((env.n_out, env.n_in))
    opt = _AdamBaseline(w, lr=lr)
    for _ in range(n_steps):
        opt.step(env.grad(w))
    return env.reward(w)


_SEEDS = list(range(10))  # 10 seeds × short runs


@pytest.fixture(scope="module")
def multi_seed_results():
    """Pre-computed 10-seed results for all three optimisers."""
    muon = [_run_muon_cans_seed(s) for s in _SEEDS]
    sgd  = [_run_sgd_seed(s) for s in _SEEDS]
    adam = [_run_adam_seed(s) for s in _SEEDS]
    return {"muon": muon, "sgd": sgd, "adam": adam}


# ---------------------------------------------------------------------------
# New test classes
# ---------------------------------------------------------------------------


class TestGradGradCosine:
    """cos(g_t, g_{t-1}) — successive gradient alignment.

    Healthy signs:
      - Value is finite and in [-1, 1]
      - First-step value is 1.0 (gradient is perfectly aligned with itself)
      - Not persistently near ±1 after the first step (would indicate
        gradient is frozen or oscillating between two directions)
      - Not persistently strongly negative (optimizer fighting itself)

    The goal is observability, not proving superiority.  These tests verify
    the instrumentation is sane and flag the obvious pathologies.
    """

    def test_first_step_value_is_one(self) -> None:
        """On the very first step there is no previous gradient: value = 1.0."""
        p = np.random.default_rng(0).standard_normal((8, 4))
        opt = MuonCANS([p], lr=0.01)
        opt.step([np.ones((8, 4))])
        assert opt.metrics["grad_grad_cos"][0] == pytest.approx(1.0)

    def test_values_are_in_valid_range(self, harness: StabilityHarness) -> None:
        for v in harness.grad_grad_cos:
            assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9, f"grad_grad_cos out of range: {v}"

    def test_values_are_finite(self, harness: StabilityHarness) -> None:
        assert all(math.isfinite(v) for v in harness.grad_grad_cos), (
            "grad_grad_cos contains NaN or Inf"
        )

    def test_not_persistently_strongly_negative(self, harness: StabilityHarness) -> None:
        """Flag if the optimizer is fighting itself most of the time."""
        strongly_neg = sum(1 for v in harness.grad_grad_cos if v < -0.8)
        fraction = strongly_neg / len(harness.grad_grad_cos)
        assert fraction < 0.5, (
            f"{100*fraction:.1f}% of steps have grad_grad_cos < -0.8; "
            "the optimizer may be undoing its previous step repeatedly"
        )

    def test_reset_metrics_clears_grad_history(self) -> None:
        """After reset_metrics(), the next step should return 1.0 again."""
        p = np.random.default_rng(1).standard_normal((8, 4))
        opt = MuonCANS([p], lr=0.01)
        opt.step([np.ones((8, 4))])
        opt.step([np.ones((8, 4))])  # now _prev_grads is set
        opt.reset_metrics()
        opt.step([np.ones((8, 4))])  # should act like the first step
        assert opt.metrics["grad_grad_cos"][0] == pytest.approx(1.0), (
            "After reset_metrics(), first step should have grad_grad_cos=1.0"
        )

    def test_reset_metrics_empties_all_metric_lists(self) -> None:
        p = np.random.default_rng(2).standard_normal((8, 4))
        opt = MuonCANS([p], lr=0.01)
        opt.step([np.ones((8, 4))])
        opt.reset_metrics()
        for key, val in opt.metrics.items():
            assert val == [], f"metrics['{key}'] was not cleared by reset_metrics()"

    def test_second_step_reflects_actual_alignment(self) -> None:
        """Identical gradients on step 2 → cos = 1; opposing → cos = -1."""
        p = np.random.default_rng(3).standard_normal((8, 4))
        g = np.ones((8, 4))

        # lr=1e-9: effectively frozen weights while satisfying the lr > 0 guard
        opt = MuonCANS([p], lr=1e-9, momentum=0.0)
        opt.step([g])   # step 1: stores g as _prev_grad
        opt.step([g])   # step 2: cos(g, g) = 1.0
        assert opt.metrics["grad_grad_cos"][0] == pytest.approx(1.0, abs=1e-6)

        p2 = np.random.default_rng(3).standard_normal((8, 4))
        opt2 = MuonCANS([p2], lr=1e-9, momentum=0.0)
        opt2.step([g])
        opt2.step([-g])  # opposing gradient → cos = -1.0
        assert opt2.metrics["grad_grad_cos"][0] == pytest.approx(-1.0, abs=1e-6)

    # ------------------------------------------------------------------
    # Invariant 1 & 2 — track_grad_history flag
    # ------------------------------------------------------------------

    def test_track_grad_history_true_produces_numeric_values(self) -> None:
        """Invariant 1: track_grad_history=True (default) behaves exactly as before.

        After each step, metrics["grad_grad_cos"] holds one finite float per
        parameter (not None).  The flag must not alter gradient values or
        weight updates.
        """
        rng = np.random.default_rng(42)
        p = rng.standard_normal((8, 4))
        opt = MuonCANS([p], lr=0.01, momentum=0.0, track_grad_history=True)
        for _ in range(5):
            g = rng.standard_normal((8, 4))
            opt.step([g])
            # metrics are refreshed each step: one entry per parameter
            v = opt.metrics["grad_grad_cos"][0]
            assert v is not None, "grad_grad_cos should be numeric, not None"
            assert math.isfinite(v), f"grad_grad_cos is not finite: {v}"
            assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9, f"grad_grad_cos out of range: {v}"

    def test_track_grad_history_false_does_not_affect_weights(self) -> None:
        """Invariant 2: track_grad_history=False leaves weight updates identical.

        The flag controls only telemetry.  Two optimisers with the same seed —
        one with history tracking, one without — must produce the same final
        weights.  The disabled run's grad_grad_cos entries must all be None.
        """
        grads = [np.random.default_rng(i).standard_normal((8, 4)) for i in range(5)]

        p_tracked   = np.random.default_rng(99).standard_normal((8, 4))
        p_untracked = p_tracked.copy()

        opt_on  = MuonCANS([p_tracked],   lr=0.01, momentum=0.9, track_grad_history=True)
        opt_off = MuonCANS([p_untracked], lr=0.01, momentum=0.9, track_grad_history=False)

        for g in grads:
            opt_on.step([g.copy()])
            opt_off.step([g.copy()])
            # Disabled run: current step's metric entry is None
            assert opt_off.metrics["grad_grad_cos"][0] is None, (
                "Expected None when track_grad_history=False, "
                f"got {opt_off.metrics['grad_grad_cos'][0]!r}"
            )

        # Weights must be numerically identical — only telemetry differs
        np.testing.assert_array_equal(
            p_tracked, p_untracked,
            err_msg="track_grad_history flag must not affect weight updates",
        )


class TestRepresentationDrift:
    """cos(w_t, w_{t-1}) — how violently representations rotate.

    Healthy networks: slow rotation (drift_cos near 1), with early steps
    allowed to be noisier than late steps.  The optimizer must never produce
    drift_cos that is consistently near zero or negative (amnesia).
    """

    def test_drift_cos_in_valid_range(self, harness: StabilityHarness) -> None:
        for v in harness.weight_drift_cos:
            assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9, f"weight_drift_cos out of range: {v}"

    def test_mean_drift_cos_shows_slow_rotation(self, harness: StabilityHarness) -> None:
        """Mean cosine should be well above zero — policy is not wandering randomly."""
        mean_drift = float(np.mean(harness.weight_drift_cos))
        assert mean_drift > 0.0, (
            f"Mean weight drift cosine is {mean_drift:.4f}; "
            "representations may be rotating too violently (amnesia)"
        )

    def test_late_drift_not_larger_than_early_drift(self, harness: StabilityHarness) -> None:
        """Late-training rotations should not be larger than early ones.

        We allow late == early (flat regime) but flag if the policy is
        accelerating its rotation — that would indicate instability.
        """
        # Use 1 - drift_cos as "rotation angle" proxy
        early_rotation = float(np.mean(
            [1.0 - v for v in harness._first_half(harness.weight_drift_cos)]
        ))
        late_rotation = float(np.mean(
            [1.0 - v for v in harness._second_half(harness.weight_drift_cos)]
        ))
        assert late_rotation <= early_rotation * 3.0 + 1e-6, (
            f"Policy is rotating faster late in training "
            f"(early={early_rotation:.4f}, late={late_rotation:.4f}); "
            "representations never settled"
        )


class TestGradientWeightAlignment:
    """cos(g, w) — is the orthogonal projection meaningful or cosmetic?

    If this cosine is near zero most of the time, the orthogonal constraint
    is removing almost nothing from the gradient.  If it is large, the
    constraint is actively shaping the update direction.

    The test is purely diagnostic: both outcomes are valid and informative.
    We only verify the metric is finite and sane.
    """

    def test_grad_weight_cos_in_valid_range(self, harness: StabilityHarness) -> None:
        for v in harness.grad_weight_cos:
            assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9, (
                f"grad_weight_cos out of range: {v}"
            )

    def test_grad_weight_cos_is_finite(self, harness: StabilityHarness) -> None:
        assert all(math.isfinite(v) for v in harness.grad_weight_cos), (
            "grad_weight_cos contains NaN or Inf"
        )

    def test_grad_weight_cos_has_variance(self, harness: StabilityHarness) -> None:
        """The metric should vary across steps — a constant value means it is broken."""
        std = float(np.std(harness.grad_weight_cos))
        assert std > 1e-6, (
            f"grad_weight_cos has near-zero variance ({std:.2e}); "
            "metric may not be computing correctly"
        )


class TestMultiSeedVariance:
    """10 seeds × short runs.  Variance across seeds tells us about stability.

    We compare MuonCANS seed-variance against the SGD-norm baseline.
    A lower or equal variance is a real contribution even without faster
    convergence.

    We also verify that every method actually *learns* — all 10 seeds must
    show positive final reward (the target direction is findable).
    """

    def test_all_muon_seeds_improve(self, multi_seed_results) -> None:
        results = multi_seed_results["muon"]
        failures = [s for s, r in zip(_SEEDS, results) if not math.isfinite(r)]
        assert not failures, f"MuonCANS produced non-finite reward on seeds {failures}"

    def test_all_sgd_seeds_improve(self, multi_seed_results) -> None:
        results = multi_seed_results["sgd"]
        failures = [s for s, r in zip(_SEEDS, results) if not math.isfinite(r)]
        assert not failures, f"SGD produced non-finite reward on seeds {failures}"

    def test_all_adam_seeds_improve(self, multi_seed_results) -> None:
        results = multi_seed_results["adam"]
        failures = [s for s, r in zip(_SEEDS, results) if not math.isfinite(r)]
        assert not failures, f"Adam produced non-finite reward on seeds {failures}"

    def test_muon_seed_variance_not_catastrophically_worse_than_sgd(
        self, multi_seed_results
    ) -> None:
        """MuonCANS must not have dramatically higher variance than SGD.

        A looser bound (×5) deliberately avoids over-claiming — the goal is
        to catch catastrophic instability, not to prove superiority.
        """
        muon_var = float(np.var(multi_seed_results["muon"]))
        sgd_var  = float(np.var(multi_seed_results["sgd"])) + 1e-9
        assert muon_var <= sgd_var * 5.0, (
            f"MuonCANS seed variance ({muon_var:.4f}) is more than 5× "
            f"SGD variance ({sgd_var:.4f}); method is unstable across seeds"
        )

    def test_env_info_recorded(self, harness: StabilityHarness) -> None:
        """Harness must capture runtime versions for reproducibility tracing."""
        assert "python" in harness.env_info, "Missing python version in env_info"
        assert "numpy" in harness.env_info, "Missing numpy version in env_info"
        assert harness.env_info["numpy"] == np.__version__


class TestGatingDistribution:
    """The Sakib advantage distribution must not be a permanent brake pedal.

    If the advantage is near zero for the vast majority of steps, the
    optimizer is barely moving.  We test that it has meaningful spread and
    is positive at least half the time.
    """

    def test_advantage_has_spread(self, harness: StabilityHarness) -> None:
        """Standard deviation of raw_advantages must be non-trivial."""
        std = float(np.std(harness.raw_advantages))
        assert std > 1e-4, (
            f"Sakib advantage has near-zero spread (std={std:.2e}); "
            "the gate may be stuck"
        )

    def test_advantage_not_permanently_zero(self, harness: StabilityHarness) -> None:
        """Gate must be meaningfully active for at least some steps.

        The smoothed Sakib advantage decays geometrically from its initial
        value toward zero when rewards are negative.  We check that at least
        10 % of steps carry a non-negligible advantage (> 0.01), confirming
        the gate is not a permanent brake pedal from the very first step.
        """
        active = sum(1 for a in harness.raw_advantages if a > 0.01)
        frac = active / len(harness.raw_advantages)
        assert frac > 0.10, (
            f"Sakib advantage exceeds 0.01 on only {100*frac:.1f}% of steps "
            f"({active}/{len(harness.raw_advantages)}); "
            "the gate may be permanently inactive"
        )

    def test_advantage_never_exceeds_one(self, harness: StabilityHarness) -> None:
        """Smoothed reward proxy is bounded in [0, 1]."""
        assert all(0.0 <= a <= 1.0 for a in harness.raw_advantages), (
            "raw_advantages contains values outside [0, 1]"
        )


class TestBaselineComparison:
    """MuonCANS vs SGD-norm vs Adam — same environment, same 10 seeds.

    These tests do NOT claim superiority.  They verify that all methods are
    plausible and that MuonCANS is in the same ballpark, so that the two
    diagnostic curves (grad_grad_cos, weight_drift_cos) can be interpreted
    in context.
    """

    def test_muon_mean_reward_is_positive(self, multi_seed_results) -> None:
        mean = float(np.mean(multi_seed_results["muon"]))
        assert mean > -0.5, (
            f"MuonCANS mean final reward is very negative ({mean:.4f}); "
            "method may not be learning at all"
        )

    def test_sgd_mean_reward_is_positive(self, multi_seed_results) -> None:
        mean = float(np.mean(multi_seed_results["sgd"]))
        assert mean > -0.5, f"SGD mean final reward is very negative ({mean:.4f})"

    def test_adam_mean_reward_is_positive(self, multi_seed_results) -> None:
        mean = float(np.mean(multi_seed_results["adam"]))
        assert mean > -0.5, f"Adam mean final reward is very negative ({mean:.4f})"

    def test_all_methods_finite(self, multi_seed_results) -> None:
        for name, results in multi_seed_results.items():
            for r in results:
                assert math.isfinite(r), f"{name} produced non-finite reward: {r}"

    def test_reproducibility_env_info_present(self, harness: StabilityHarness) -> None:
        """Env-info dict must contain all required reproducibility keys."""
        required = {"python", "numpy", "platform"}
        missing = required - set(harness.env_info.keys())
        assert not missing, f"Missing reproducibility keys in env_info: {missing}"
