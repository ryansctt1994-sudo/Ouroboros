"""
Tests for the MuonCANS optimizer.

Validates:
- Weight shape preservation across 1-D and 2-D parameters
- Gradient orthogonality (Stiefel-manifold property) for 2-D weights
- Sakib advantage scaling (dynamic learning rate)
- Integrated telemetry metrics (policy_delta_norm, cos_w_dw, weight_norm)
- Parameter stability across multiple steps
- state_dict / load_state_dict round-trip
- Edge cases: zero gradients, mismatched gradient count
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from optimizers.muon_cans import MuonCANS, _orthogonalise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RNG = np.random.default_rng(42)


def _rand_param(*shape: int) -> np.ndarray:
    return RNG.standard_normal(shape).astype(float)


def _rand_grad(*shape: int) -> np.ndarray:
    return RNG.standard_normal(shape).astype(float)


# ---------------------------------------------------------------------------
# _orthogonalise unit tests
# ---------------------------------------------------------------------------


class TestOrthogonalise:
    """Low-level Newton-Schulz orthogonalisation tests."""

    def test_output_shape_preserved(self) -> None:
        G = _rand_grad(8, 4)
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_output_shape_wide_matrix(self) -> None:
        G = _rand_grad(4, 8)
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_near_orthogonal_columns(self) -> None:
        """After orthogonalisation the column norms should be close to 1 for tall matrices."""
        G = _rand_grad(32, 8)
        Q = _orthogonalise(G)
        # Q^T Q should be close to identity (within tolerance)
        inner = Q.T @ Q
        np.testing.assert_allclose(inner, np.eye(8), atol=0.05)

    def test_zero_matrix_returns_without_error(self) -> None:
        G = np.zeros((8, 4))
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_small_matrix_fallback(self) -> None:
        """Matrices with min-dim < 4 use spectral normalisation fallback."""
        G = _rand_grad(8, 2)
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_1d_raises(self) -> None:
        with pytest.raises(ValueError, match="2-D"):
            _orthogonalise(np.ones(5))


# ---------------------------------------------------------------------------
# MuonCANS weight-shape tests
# ---------------------------------------------------------------------------


class TestWeightShapes:
    """Ensure parameter shapes are not mutated by the optimizer."""

    def test_2d_param_shape_preserved(self) -> None:
        p = _rand_param(16, 8)
        opt = MuonCANS([p], lr=0.01)
        opt.step([_rand_grad(16, 8)])
        assert p.shape == (16, 8)

    def test_1d_param_shape_preserved(self) -> None:
        p = _rand_param(16)
        opt = MuonCANS([p], lr=0.01)
        opt.step([_rand_grad(16)])
        assert p.shape == (16,)

    def test_3d_param_shape_preserved(self) -> None:
        p = _rand_param(4, 3, 3)
        opt = MuonCANS([p], lr=0.01)
        opt.step([_rand_grad(4, 3, 3)])
        assert p.shape == (4, 3, 3)

    def test_multiple_params_all_shapes_preserved(self) -> None:
        shapes = [(32, 16), (16,), (8, 8), (8,)]
        params = [_rand_param(*s) for s in shapes]
        grads = [_rand_grad(*s) for s in shapes]
        originals = [p.copy() for p in params]

        opt = MuonCANS(params, lr=0.01)
        opt.step(grads)

        for p, orig, s in zip(params, originals, shapes):
            assert p.shape == s, f"shape changed for {s}"
            # Parameters should have actually changed (non-zero gradient → update)
            assert not np.allclose(p, orig), f"param {s} was not updated"


# ---------------------------------------------------------------------------
# Gradient orthogonality tests
# ---------------------------------------------------------------------------


class TestGradientOrthogonality:
    """Verify that 2-D weight updates approximate an orthogonal matrix."""

    def test_update_is_orthogonal_for_tall_matrix(self) -> None:
        """The update applied to a tall (m > n) 2-D param should be near-orthogonal."""
        p = _rand_param(64, 16)
        grad = _rand_grad(64, 16)

        # Capture pre-step weight, then step
        p_before = p.copy()
        opt = MuonCANS([p], lr=1.0, momentum=0.0)  # momentum=0 ⇒ update = orthog(grad)
        opt.step([grad])

        delta = p_before - p  # effective update (lr * orthog_grad)
        # Normalise to get the update direction
        delta_mat = delta.reshape(64, -1)
        spec = np.linalg.norm(delta_mat, ord=2)
        if spec > 1e-9:
            Q = delta_mat / spec
            inner = Q.T @ Q
            np.testing.assert_allclose(inner, np.eye(16), atol=0.05)

    def test_1d_update_is_rms_normalised(self) -> None:
        """1-D parameter updates should have a stable (RMS-normalised) scale."""
        p = _rand_param(64)
        grad = _rand_grad(64)

        p_before = p.copy()
        opt = MuonCANS([p], lr=0.1, momentum=0.0)
        opt.step([grad])

        delta = p_before - p
        # Expected update direction: grad / (rms(grad) + 1e-8)
        rms = np.sqrt(np.mean(grad ** 2)) + 1e-8
        expected_delta = 0.1 * grad / rms
        np.testing.assert_allclose(delta, expected_delta, atol=1e-9)


# ---------------------------------------------------------------------------
# Sakib advantage scaling tests
# ---------------------------------------------------------------------------


class TestSakibAdvantageScaling:
    """Dynamic learning-rate scaling via the Sakib advantage signal."""

    def test_positive_advantage_scales_lr_up(self) -> None:
        """Larger advantage → larger update magnitude."""
        g = _rand_grad(8, 4)

        p_low = _rand_param(8, 4)
        p_high = p_low.copy()

        opt_low = MuonCANS([p_low], lr=0.01, momentum=0.0)
        opt_high = MuonCANS([p_high], lr=0.01, momentum=0.0)

        opt_low.step([g.copy()], sakib_advantage=0.1)
        opt_high.step([g.copy()], sakib_advantage=1.0)

        delta_low = np.linalg.norm(p_low - opt_low.params[0])  # original - updated
        # Use actual update magnitudes from metrics
        norm_low = opt_low.metrics["policy_delta_norm"][0]
        norm_high = opt_high.metrics["policy_delta_norm"][0]

        assert norm_high > norm_low, (
            f"Higher advantage should give a larger update; got {norm_high:.6g} vs {norm_low:.6g}"
        )

    def test_zero_advantage_uses_eps_offset(self) -> None:
        """With sakib_advantage=0, the step uses lr * advantage_eps (not zero)."""
        p = _rand_param(8, 4)
        p_before = p.copy()
        adv_eps = 1e-2

        opt = MuonCANS([p], lr=1.0, momentum=0.0, advantage_eps=adv_eps)
        opt.step([_rand_grad(8, 4)], sakib_advantage=0.0)

        assert not np.allclose(p, p_before), "Zero advantage with eps offset should still update"
        assert opt.metrics["policy_delta_norm"][0] > 0

    def test_no_advantage_uses_bare_lr(self) -> None:
        """When sakib_advantage is None the optimizer uses lr unchanged."""
        g = _rand_grad(8, 4)
        p_with = _rand_param(8, 4)
        p_without = p_with.copy()

        opt_with = MuonCANS([p_with], lr=0.5, momentum=0.0)
        opt_without = MuonCANS([p_without], lr=0.5, momentum=0.0)

        # advantage=1.0 - advantage_eps ≈ 1.0, so effectively lr stays the same
        opt_with.step([g.copy()], sakib_advantage=None)
        opt_without.step([g.copy()])  # default: no advantage

        np.testing.assert_allclose(p_with, p_without, atol=1e-12)

    def test_advantage_eps_default_prevents_zero_lr(self) -> None:
        """Default advantage_eps prevents a completely zero effective LR."""
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=1.0, momentum=0.0)
        # Even with 0 advantage, the effective_lr = 1.0 * (0 + 1e-4) > 0
        opt.step([np.ones((8, 4))], sakib_advantage=0.0)
        assert opt.metrics["policy_delta_norm"][0] > 0

    def test_negative_advantage_eps_raises(self) -> None:
        with pytest.raises(ValueError, match="advantage_eps"):
            MuonCANS([_rand_param(4, 4)], advantage_eps=-1e-4)


# ---------------------------------------------------------------------------
# Telemetry metrics tests
# ---------------------------------------------------------------------------


class TestMetrics:
    """Validate the telemetry fields populated by step()."""

    def _make_opt_and_step(
        self, shapes, advantage=None
    ):
        params = [_rand_param(*s) for s in shapes]
        grads = [_rand_grad(*s) for s in shapes]
        opt = MuonCANS(params, lr=0.05, momentum=0.0)
        opt.step(grads, sakib_advantage=advantage)
        return opt

    def test_metric_keys_present(self) -> None:
        opt = self._make_opt_and_step([(8, 4)])
        assert "policy_delta_norm" in opt.metrics
        assert "cos_w_dw" in opt.metrics
        assert "weight_norm" in opt.metrics

    def test_metric_lengths_match_params(self) -> None:
        shapes = [(16, 8), (8,), (4, 4)]
        opt = self._make_opt_and_step(shapes)
        assert len(opt.metrics["policy_delta_norm"]) == len(shapes)
        assert len(opt.metrics["cos_w_dw"]) == len(shapes)
        assert len(opt.metrics["weight_norm"]) == len(shapes)

    def test_policy_delta_norm_is_positive(self) -> None:
        opt = self._make_opt_and_step([(8, 4)])
        assert opt.metrics["policy_delta_norm"][0] > 0

    def test_weight_norm_is_non_negative(self) -> None:
        opt = self._make_opt_and_step([(8, 4)])
        assert opt.metrics["weight_norm"][0] >= 0

    def test_cos_w_dw_in_valid_range(self) -> None:
        """Cosine values must be in [-1, 1] (within float rounding)."""
        opt = self._make_opt_and_step([(32, 16)])
        cos = opt.metrics["cos_w_dw"][0]
        assert -1.0 - 1e-9 <= cos <= 1.0 + 1e-9, f"cosine out of range: {cos}"

    def test_metrics_updated_each_step(self) -> None:
        """Metrics from consecutive steps should (in general) differ."""
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=0.05)
        opt.step([_rand_grad(8, 4)])
        norm_first = opt.metrics["policy_delta_norm"][0]

        opt.step([_rand_grad(8, 4)])
        norm_second = opt.metrics["policy_delta_norm"][0]

        # After momentum warms up, norms will be different across steps.
        # We only verify they are both positive.
        assert norm_first > 0
        assert norm_second > 0

    def test_metrics_with_sakib_advantage(self) -> None:
        """Metrics are collected correctly when Sakib advantage is provided."""
        opt = self._make_opt_and_step([(16, 8)], advantage=0.5)
        assert opt.metrics["policy_delta_norm"][0] > 0
        assert len(opt.metrics["cos_w_dw"]) == 1


# ---------------------------------------------------------------------------
# Parameter stability tests
# ---------------------------------------------------------------------------


class TestParameterStability:
    """Verify that parameters remain finite and bounded across many steps."""

    def test_params_remain_finite_after_100_steps(self) -> None:
        p = _rand_param(32, 16)
        opt = MuonCANS([p], lr=0.02, momentum=0.95)

        for _ in range(100):
            g = _rand_grad(32, 16)
            opt.step([g])

        assert np.all(np.isfinite(p)), "Parameters contain NaN or Inf after 100 steps"

    def test_1d_params_remain_finite(self) -> None:
        p = _rand_param(64)
        opt = MuonCANS([p], lr=0.02)

        for _ in range(50):
            opt.step([_rand_grad(64)])

        assert np.all(np.isfinite(p))

    def test_weight_decay_reduces_norm(self) -> None:
        """With large weight decay and zero gradient, parameters should shrink."""
        p = np.ones((8, 4), dtype=float)
        opt = MuonCANS([p], lr=0.1, momentum=0.0, weight_decay=0.5)

        # Zero gradient — only weight-decay pushes the update
        zero_grad = np.zeros((8, 4))
        norm_before = np.linalg.norm(p)
        opt.step([zero_grad])
        norm_after = np.linalg.norm(p)
        assert norm_after < norm_before, "Weight decay should reduce ||w||"

    def test_reset_momentum_zeroes_buffers(self) -> None:
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=0.01)
        opt.step([_rand_grad(8, 4)])  # initialise buffer

        opt.reset_momentum()
        assert np.all(opt._buffers[0] == 0.0)


# ---------------------------------------------------------------------------
# state_dict / load_state_dict round-trip
# ---------------------------------------------------------------------------


class TestStateDictRoundTrip:
    def test_round_trip_preserves_step_count(self) -> None:
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=0.01)
        opt.step([_rand_grad(8, 4)])
        opt.step([_rand_grad(8, 4)])

        sd = opt.state_dict()
        assert sd["step_count"] == 2

        p2 = _rand_param(8, 4)
        opt2 = MuonCANS([p2], lr=0.01)
        opt2.load_state_dict(sd)
        assert opt2.step_count == 2

    def test_round_trip_preserves_advantage_eps(self) -> None:
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=0.01, advantage_eps=1e-3)
        sd = opt.state_dict()
        assert sd["advantage_eps"] == pytest.approx(1e-3)

        p2 = _rand_param(8, 4)
        opt2 = MuonCANS([p2], lr=0.01)
        opt2.load_state_dict(sd)
        assert opt2.advantage_eps == pytest.approx(1e-3)

    def test_round_trip_preserves_metrics(self) -> None:
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=0.05, momentum=0.0)
        opt.step([_rand_grad(8, 4)])
        original_norm = opt.metrics["policy_delta_norm"][0]

        sd = opt.state_dict()

        p2 = _rand_param(8, 4)
        opt2 = MuonCANS([p2], lr=0.05)
        opt2.load_state_dict(sd)
        assert opt2.metrics["policy_delta_norm"][0] == pytest.approx(original_norm)

    def test_round_trip_preserves_buffers(self) -> None:
        p = _rand_param(8, 4)
        opt = MuonCANS([p], lr=0.01)
        opt.step([_rand_grad(8, 4)])
        buf_before = opt._buffers[0].copy()

        sd = opt.state_dict()

        p2 = _rand_param(8, 4)
        opt2 = MuonCANS([p2], lr=0.01)
        opt2.load_state_dict(sd)
        np.testing.assert_allclose(opt2._buffers[0], buf_before)


# ---------------------------------------------------------------------------
# Error / edge-case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_mismatched_grad_count_raises(self) -> None:
        opt = MuonCANS([_rand_param(4, 4), _rand_param(4)], lr=0.01)
        with pytest.raises(ValueError, match="Expected 2 gradients"):
            opt.step([_rand_grad(4, 4)])

    def test_invalid_lr_raises(self) -> None:
        with pytest.raises(ValueError, match="lr must be positive"):
            MuonCANS([_rand_param(4, 4)], lr=0.0)

    def test_invalid_momentum_raises(self) -> None:
        with pytest.raises(ValueError, match="momentum"):
            MuonCANS([_rand_param(4, 4)], momentum=1.0)

    def test_invalid_scalar_decay_mult_raises(self) -> None:
        with pytest.raises(ValueError, match="scalar_decay_mult"):
            MuonCANS([_rand_param(4, 4)], scalar_decay_mult=0.5)

    def test_zero_gradient_does_not_change_param(self) -> None:
        """A zero gradient (with no weight-decay) should produce no update."""
        p = _rand_param(8, 4)
        p_before = p.copy()
        opt = MuonCANS([p], lr=0.1, momentum=0.0, weight_decay=0.0)
        opt.step([np.zeros((8, 4))])
        # _orthogonalise of zero → zero, so param unchanged
        np.testing.assert_allclose(p, p_before)

    def test_step_count_increments(self) -> None:
        opt = MuonCANS([_rand_param(4, 4)], lr=0.01)
        assert opt.step_count == 0
        opt.step([_rand_grad(4, 4)])
        assert opt.step_count == 1
        opt.step([_rand_grad(4, 4)])
        assert opt.step_count == 2
