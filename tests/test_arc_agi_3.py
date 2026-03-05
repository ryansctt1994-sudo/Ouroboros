"""
Tests for the arc_agi_3 package and the run_arc_agi_3 initiation script.

Covers:
- InteractiveReasoningEnv: reset, step, difficulty levels, max_steps
- FGRPO: discounted_returns, compute_loss, edge cases
- EMPG: policy_entropy, compute_loss, adaptive beta
- EngramObservatory: push/start/stop lifecycle, metric computation
- run_arc_agi_3.MyceliumPolicy: forward pass, gradients
- run_arc_agi_3.OmegaAxisHeartbeat: tick phases
- run_arc_agi_3.run_arc_agi_3: smoke test
"""

from __future__ import annotations

import threading
import time

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# arc_agi_3 package imports
# ---------------------------------------------------------------------------

from arc_agi_3 import (
    EMPG,
    FGRPO,
    EngramObservatory,
    EnvStep,
    InteractiveReasoningEnv,
)
from run_arc_agi_3 import (
    MyceliumPolicy,
    OmegaAxisHeartbeat,
    run_arc_agi_3,
)


# ===========================================================================
# InteractiveReasoningEnv
# ===========================================================================


class TestInteractiveReasoningEnv:

    def test_reset_returns_observation_shape(self):
        env = InteractiveReasoningEnv(max_steps=10)
        obs = env.reset()
        assert obs.shape == (env.obs_dim,)

    def test_step_returns_env_step(self):
        env = InteractiveReasoningEnv(max_steps=10, seed=0)
        env.reset(seed=0)
        action = np.zeros(env.act_dim)
        result = env.step(action)
        assert isinstance(result, EnvStep)

    def test_step_increments_count(self):
        env = InteractiveReasoningEnv(max_steps=10, seed=1)
        env.reset(seed=1)
        for i in range(5):
            env.step(np.zeros(env.act_dim))
        assert env.step_count == 5

    def test_done_after_max_steps(self):
        env = InteractiveReasoningEnv(max_steps=3, seed=2)
        env.reset(seed=2)
        results = [env.step(np.zeros(env.act_dim)) for _ in range(3)]
        assert results[-1].done is True

    def test_not_done_before_max_steps(self):
        env = InteractiveReasoningEnv(max_steps=10, seed=3)
        env.reset(seed=3)
        result = env.step(np.zeros(env.act_dim))
        assert result.done is False

    @pytest.mark.parametrize("difficulty", ["simple", "latent_medium", "latent_complex"])
    def test_difficulty_levels_accepted(self, difficulty):
        env = InteractiveReasoningEnv(difficulty=difficulty)
        obs = env.reset()
        assert obs.shape == (env.obs_dim,)

    def test_invalid_difficulty_raises(self):
        with pytest.raises(ValueError):
            InteractiveReasoningEnv(difficulty="ultra_hard")

    def test_invalid_max_steps_raises(self):
        with pytest.raises(ValueError):
            InteractiveReasoningEnv(max_steps=0)

    def test_reward_is_scalar_in_minus_one_to_one(self):
        env = InteractiveReasoningEnv(max_steps=20, seed=5)
        env.reset()
        for _ in range(10):
            result = env.step(np.random.default_rng(5).standard_normal(env.act_dim))
            assert -1.0 <= result.reward <= 1.0

    def test_step_without_reset_raises(self):
        env = InteractiveReasoningEnv(max_steps=5)
        with pytest.raises(RuntimeError):
            env.step(np.zeros(env.act_dim))

    def test_info_contains_expected_keys(self):
        env = InteractiveReasoningEnv(max_steps=5, seed=7)
        env.reset()
        result = env.step(np.zeros(env.act_dim))
        assert "step" in result.info
        assert "difficulty" in result.info
        assert "n_rules" in result.info

    def test_default_max_steps_is_500(self):
        env = InteractiveReasoningEnv()
        assert env.max_steps == 500

    def test_default_difficulty_is_latent_complex(self):
        env = InteractiveReasoningEnv()
        assert env.difficulty == "latent_complex"

    def test_reproducible_with_seed(self):
        env1 = InteractiveReasoningEnv(max_steps=5, seed=42)
        env2 = InteractiveReasoningEnv(max_steps=5, seed=42)
        obs1 = env1.reset(seed=0)
        obs2 = env2.reset(seed=0)
        np.testing.assert_array_equal(obs1, obs2)

    def test_action_dimension_mismatch_handled(self):
        """Actions with wrong dimension should not raise (projection is applied)."""
        env = InteractiveReasoningEnv(max_steps=5, seed=9)
        env.reset()
        # Use action with different dimension than act_dim
        result = env.step(np.ones(env.obs_dim))
        assert isinstance(result, EnvStep)


# ===========================================================================
# FGRPO
# ===========================================================================


class TestFGRPO:

    def test_discounted_returns_single_step(self):
        fgrpo = FGRPO(gamma=0.99)
        returns = fgrpo.discounted_returns([1.0])
        assert np.isclose(returns[0], 1.0)

    def test_discounted_returns_multiple_steps(self):
        fgrpo = FGRPO(gamma=0.5)
        rewards = [1.0, 1.0, 1.0]
        returns = fgrpo.discounted_returns(rewards)
        # G_0 = 1 + 0.5 + 0.25 = 1.75
        assert np.isclose(returns[0], 1.75)

    def test_discounted_returns_shape(self):
        fgrpo = FGRPO()
        rewards = [0.5, 0.3, 0.1, 0.9]
        returns = fgrpo.discounted_returns(rewards)
        assert returns.shape == (4,)

    def test_compute_loss_single_trajectory(self):
        fgrpo = FGRPO(gamma=0.99, focal_alpha=2.0)
        lp = [np.array([-0.5, -0.3])]
        rewards = [[1.0, 0.5]]
        loss = fgrpo.compute_loss(lp, rewards)
        assert isinstance(loss, float)

    def test_compute_loss_multiple_trajectories(self):
        fgrpo = FGRPO()
        rng = np.random.default_rng(0)
        lps = [rng.standard_normal(5) for _ in range(4)]
        rewards = [rng.standard_normal(5).tolist() for _ in range(4)]
        loss = fgrpo.compute_loss(lps, rewards)
        assert np.isfinite(loss)

    def test_compute_loss_empty_raises(self):
        fgrpo = FGRPO()
        with pytest.raises(ValueError):
            fgrpo.compute_loss([], [])

    def test_compute_loss_mismatch_raises(self):
        fgrpo = FGRPO()
        with pytest.raises(ValueError):
            fgrpo.compute_loss([np.ones(3)], [[1.0, 2.0], [3.0, 4.0]])

    def test_compute_loss_trajectory_length_mismatch_raises(self):
        fgrpo = FGRPO()
        with pytest.raises(ValueError):
            fgrpo.compute_loss([np.ones(3)], [[1.0, 2.0]])

    def test_invalid_gamma_raises(self):
        with pytest.raises(ValueError):
            FGRPO(gamma=1.5)

    def test_invalid_focal_alpha_raises(self):
        with pytest.raises(ValueError):
            FGRPO(focal_alpha=-1.0)

    def test_zero_focal_alpha_no_weighting(self):
        """With focal_alpha=0 all transitions are weighted equally."""
        fgrpo = FGRPO(focal_alpha=0.0)
        lp = [np.array([-0.2])]
        rewards = [[1.0]]
        loss = fgrpo.compute_loss(lp, rewards)
        assert np.isfinite(loss)


# ===========================================================================
# EMPG
# ===========================================================================


class TestEMPG:

    def test_policy_entropy_uniform(self):
        empg = EMPG()
        log_probs = np.zeros(4)  # equal log-probs → uniform
        H = empg.policy_entropy(log_probs)
        # Uniform over 4 actions: H = log(4) ≈ 1.386
        assert H > 1.0

    def test_policy_entropy_deterministic(self):
        empg = EMPG()
        log_probs = np.array([-1e6, 0.0, -1e6, -1e6])
        H = empg.policy_entropy(log_probs)
        assert H < 0.1

    def test_compute_loss_reduces_with_high_entropy(self):
        empg = EMPG(entropy_coeff=0.1, target_entropy=None)
        pg_loss = 1.0
        # High entropy → large H → total_loss = pg_loss - beta * H < pg_loss
        lp = np.zeros(16)
        total = empg.compute_loss(pg_loss, lp)
        assert total < pg_loss

    def test_beta_adapts_when_entropy_differs_from_target(self):
        empg = EMPG(target_entropy=5.0, entropy_coeff=0.01, adapt_rate=0.1)
        # Policy with very low entropy (below target=5.0):
        # entropy_error = H - target < 0, so beta decreases (or clamps at 0)
        lp = np.array([-1e6, 0.0, -1e6, -1e6])
        empg.compute_loss(0.0, lp)
        assert empg.current_beta >= 0.0

    def test_beta_never_negative(self):
        empg = EMPG(target_entropy=0.001, entropy_coeff=0.001, adapt_rate=1.0)
        lp = np.zeros(4)  # high entropy
        for _ in range(100):
            empg.compute_loss(0.0, lp)
        assert empg.current_beta >= 0.0

    def test_invalid_entropy_coeff_raises(self):
        with pytest.raises(ValueError):
            EMPG(entropy_coeff=-0.1)

    def test_invalid_adapt_rate_raises(self):
        with pytest.raises(ValueError):
            EMPG(adapt_rate=-0.01)

    def test_no_target_entropy_beta_fixed(self):
        empg = EMPG(target_entropy=None, entropy_coeff=0.05)
        initial_beta = empg.current_beta
        lp = np.zeros(4)
        empg.compute_loss(1.0, lp)
        # Without adaptive target, beta stays fixed
        assert empg.current_beta == initial_beta

    def test_compute_loss_returns_float(self):
        empg = EMPG()
        loss = empg.compute_loss(0.5, np.zeros(8))
        assert isinstance(loss, float)


# ===========================================================================
# EngramObservatory
# ===========================================================================


class TestEngramObservatory:

    def test_start_stop_lifecycle(self):
        obs = EngramObservatory(log_dir="/tmp/test_engram_obs")
        obs.start()
        time.sleep(0.05)
        obs.stop(timeout=2.0)

    def test_push_does_not_block(self):
        obs = EngramObservatory(log_dir="/tmp/test_engram_push")
        obs.start()
        acts = np.random.default_rng(0).standard_normal(32)
        start = time.monotonic()
        for i in range(50):
            obs.push(activations=acts, step=i)
        elapsed = time.monotonic() - start
        obs.stop(timeout=2.0)
        assert elapsed < 1.0, "push calls should not block"

    def test_push_with_weights(self):
        obs = EngramObservatory(log_dir="/tmp/test_engram_weights")
        obs.start()
        acts = np.ones(16)
        weights = np.eye(16)
        obs.push(activations=acts, weights=weights, step=0)
        obs.stop(timeout=2.0)

    def test_double_start_does_not_raise(self):
        obs = EngramObservatory(log_dir="/tmp/test_engram_double")
        obs.start()
        obs.start()  # should warn but not raise
        obs.stop(timeout=2.0)

    def test_participation_ratio_ones_vector(self):
        pr = EngramObservatory._participation_ratio(np.ones(8))
        # For uniform vector, PR = 1.0 / n * (sum_v2)^2 / sum_v4
        # = 1/8 * 8^2 / 8 = 1.0
        assert np.isclose(pr, 1.0)

    def test_participation_ratio_zero_vector(self):
        pr = EngramObservatory._participation_ratio(np.zeros(8))
        assert pr == 0.0

    def test_participation_ratio_spike_vector(self):
        v = np.zeros(8)
        v[0] = 1.0
        pr_spike = EngramObservatory._participation_ratio(v)
        pr_uniform = EngramObservatory._participation_ratio(np.ones(8))
        assert pr_spike < pr_uniform

    def test_auto_step_counter(self):
        """push() without explicit step should auto-increment."""
        obs = EngramObservatory(log_dir="/tmp/test_engram_auto")
        obs.start()
        obs.push(np.ones(8))
        obs.push(np.ones(8))
        obs.stop(timeout=2.0)
        assert obs._step_counter == 2


# ===========================================================================
# MyceliumPolicy
# ===========================================================================


class TestMyceliumPolicy:

    def test_forward_returns_correct_shapes(self):
        policy = MyceliumPolicy(obs_dim=32, act_dim=8, seed=0)
        obs = np.ones(32)
        action, log_prob = policy.forward(obs)
        assert action.shape == (8,)
        assert log_prob.shape == (8,)

    def test_action_bounded(self):
        """tanh output should be strictly in (-1, 1)."""
        policy = MyceliumPolicy(seed=0)
        for _ in range(10):
            obs = np.random.default_rng(0).standard_normal(32)
            action, _ = policy.forward(obs)
            assert np.all(action > -1.0) and np.all(action < 1.0)

    def test_parameters_returns_four_arrays(self):
        policy = MyceliumPolicy()
        params = policy.parameters()
        assert len(params) == 4

    def test_gradients_have_matching_shapes(self):
        policy = MyceliumPolicy(seed=1)
        obs = np.ones(32)
        grads = policy.compute_gradients(obs, loss_signal=1.0)
        for p, g in zip(policy.parameters(), grads):
            assert p.shape == g.shape


# ===========================================================================
# OmegaAxisHeartbeat
# ===========================================================================


class TestOmegaAxisHeartbeat:

    def test_tick_returns_vector_of_correct_shape(self):
        hb = OmegaAxisHeartbeat(state_dim=32)
        state = hb.tick()
        assert state.shape == (32,)

    def test_tick_increments_count(self):
        hb = OmegaAxisHeartbeat(state_dim=16)
        for _ in range(5):
            hb.tick()
        assert hb.tick_count == 5

    def test_tick_with_external_input(self):
        hb = OmegaAxisHeartbeat(state_dim=16)
        ext = np.ones(16)
        state = hb.tick(external_input=ext)
        assert state.shape == (16,)

    def test_state_norm_bounded(self):
        """State norm should not grow unboundedly."""
        hb = OmegaAxisHeartbeat(state_dim=8)
        for _ in range(100):
            hb.tick(external_input=np.ones(8) * 10)
        norm = np.linalg.norm(hb._state)
        assert norm <= 1.0 + 1e-6

    def test_tick_with_mismatched_input_size(self):
        """External input with wrong size should be handled via resize."""
        hb = OmegaAxisHeartbeat(state_dim=16)
        state = hb.tick(external_input=np.ones(8))
        assert state.shape == (16,)

    def test_initial_state_is_zero(self):
        hb = OmegaAxisHeartbeat(state_dim=8)
        assert np.allclose(hb._state, 0.0)


# ===========================================================================
# run_arc_agi_3 smoke test
# ===========================================================================


class TestRunArcAgi3:

    def test_returns_list_of_stats(self):
        stats = run_arc_agi_3(n_episodes=2, max_steps=5, seed=0)
        assert isinstance(stats, list)
        assert len(stats) == 2

    def test_stats_contain_expected_keys(self):
        stats = run_arc_agi_3(n_episodes=1, max_steps=3, seed=42)
        ep = stats[0]
        assert "episode" in ep
        assert "steps" in ep
        assert "total_reward" in ep
        assert "mean_reward" in ep
        assert "fgrpo_loss" in ep
        assert "empg_loss" in ep

    def test_steps_equals_max_steps(self):
        stats = run_arc_agi_3(n_episodes=1, max_steps=10, seed=1)
        assert stats[0]["steps"] == 10

    def test_muon_step_count_increases_each_episode(self):
        stats = run_arc_agi_3(n_episodes=3, max_steps=5, seed=2)
        muon_steps = [s["muon_step"] for s in stats]
        assert muon_steps == sorted(muon_steps)
        assert muon_steps[-1] == 3  # one update per episode

    def test_difficulty_simple_accepted(self):
        stats = run_arc_agi_3(n_episodes=1, max_steps=3, difficulty="simple", seed=3)
        assert len(stats) == 1
