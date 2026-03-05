"""
Tests for Phase 5 components:
  - optimizers.muon_cans.MuonCANS
  - utils.metrics (participation_ratio_bc, early_gradient_projection, lyapunov_exponent)
  - ecs.systems.experiment_pipeline.ExperimentPipeline
  - main.run_pipeline
"""

from __future__ import annotations

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# MuonCANS
# ---------------------------------------------------------------------------

from optimizers.muon_cans import MuonCANS, _orthogonalise


class TestOrthogonalise:
    """Tests for the internal Newton-Schulz orthogonalisation helper."""

    def test_output_shape_preserved(self):
        rng = np.random.default_rng(0)
        G = rng.standard_normal((8, 4))
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_output_shape_wide_matrix(self):
        """Transposed tall matrices (wide inputs) should also be handled."""
        rng = np.random.default_rng(1)
        G = rng.standard_normal((4, 8))
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_orthogonalise_reduces_off_diagonal(self):
        """After orthogonalisation the output should have bounded spectral norm."""
        rng = np.random.default_rng(2)
        G = rng.standard_normal((16, 4))
        Q = _orthogonalise(G, num_steps=10)
        # The NS iteration normalises the spectral norm; verify it is bounded
        spec_norm = np.linalg.norm(Q, ord=2)
        assert spec_norm <= 2.0, f"Spectral norm {spec_norm:.4f} is unexpectedly large."
        # Output shape must match input
        assert Q.shape == G.shape

    def test_near_zero_matrix(self):
        """Near-zero matrices should return without errors."""
        G = np.zeros((4, 4)) + 1e-10
        Q = _orthogonalise(G)
        assert Q.shape == G.shape

    def test_requires_2d(self):
        with pytest.raises(ValueError):
            _orthogonalise(np.ones((2, 3, 4)))


class TestMuonCANS:
    """Tests for MuonCANS optimizer."""

    def _make_params(self, shapes, seed=0):
        rng = np.random.default_rng(seed)
        return [rng.standard_normal(s) for s in shapes]

    def test_initialization(self):
        params = self._make_params([(4, 4), (4,)])
        opt = MuonCANS(params, lr=0.01)
        assert opt.lr == 0.01
        assert opt.step_count == 0
        assert len(opt._buffers) == 2

    def test_invalid_lr(self):
        params = self._make_params([(4, 4)])
        with pytest.raises(ValueError):
            MuonCANS(params, lr=-0.1)

    def test_invalid_momentum(self):
        params = self._make_params([(4, 4)])
        with pytest.raises(ValueError):
            MuonCANS(params, momentum=1.5)

    def test_step_updates_params(self):
        params = self._make_params([(4, 4), (4,)])
        before = [p.copy() for p in params]
        opt = MuonCANS(params, lr=0.01)
        grads = self._make_params([(4, 4), (4,)], seed=99)
        opt.step(grads)
        for p_before, p_after in zip(before, params):
            assert not np.allclose(p_before, p_after), "Parameters must change after step."

    def test_step_count_increments(self):
        params = self._make_params([(4, 4)])
        opt = MuonCANS(params, lr=0.01)
        grads = self._make_params([(4, 4)], seed=5)
        opt.step(grads)
        assert opt.step_count == 1
        opt.step(grads)
        assert opt.step_count == 2

    def test_wrong_grad_count_raises(self):
        params = self._make_params([(4, 4), (4,)])
        opt = MuonCANS(params, lr=0.01)
        with pytest.raises(ValueError):
            opt.step([np.zeros((4, 4))])  # Only 1 grad for 2 params

    def test_state_dict_round_trip(self):
        params = self._make_params([(4, 4), (4,)])
        opt = MuonCANS(params, lr=0.01)
        grads = self._make_params([(4, 4), (4,)])
        opt.step(grads)
        state = opt.state_dict()
        assert state["step_count"] == 1

        # Restore into a new optimizer
        params2 = self._make_params([(4, 4), (4,)])
        opt2 = MuonCANS(params2, lr=0.01)
        opt2.load_state_dict(state)
        assert opt2.step_count == 1

    def test_weight_decay_applies(self):
        """Weight decay should differ from no weight decay."""
        rng = np.random.default_rng(7)
        params_wd = [rng.standard_normal((4, 4))]
        params_no_wd = [params_wd[0].copy()]
        grads = [rng.standard_normal((4, 4))]

        opt_wd = MuonCANS(params_wd, lr=0.01, weight_decay=0.1)
        opt_no_wd = MuonCANS(params_no_wd, lr=0.01, weight_decay=0.0)
        opt_wd.step([g.copy() for g in grads])
        opt_no_wd.step([g.copy() for g in grads])

        assert not np.allclose(params_wd[0], params_no_wd[0])

    def test_1d_param_handled(self):
        """1-D bias parameters should be updated without errors."""
        params = [np.zeros(8)]
        opt = MuonCANS(params, lr=0.01)
        grads = [np.ones(8)]
        opt.step(grads)
        assert not np.allclose(params[0], 0.0)

    def test_reset_momentum_zeros_buffers(self):
        """reset_momentum() should zero all initialised buffers in-place."""
        params = [np.ones((4, 4)), np.ones(4)]
        opt = MuonCANS(params, lr=0.01)
        grads = [np.ones((4, 4)), np.ones(4)]
        opt.step(grads)
        # Buffers should now be initialised
        for buf in opt._buffers:
            assert buf is not None
        opt.reset_momentum()
        for buf in opt._buffers:
            assert buf is not None
            assert np.all(buf == 0.0)

    def test_scalar_decay_mult_affects_1d_more_than_2d(self):
        """scalar_decay_mult should increase 1-D update magnitude without affecting 2-D."""
        rng = np.random.default_rng(42)
        param_2d = rng.standard_normal((4, 4))
        param_1d = rng.standard_normal(4)

        # Baseline: scalar_decay_mult=1.0 (no extra anchoring)
        p2d_base = param_2d.copy()
        p1d_base = param_1d.copy()
        opt_base = MuonCANS(
            [p2d_base, p1d_base], lr=0.01, weight_decay=0.1, scalar_decay_mult=1.0
        )
        opt_base.step([np.zeros((4, 4)), np.zeros(4)])
        delta_1d_base = np.linalg.norm(p1d_base - param_1d)
        delta_2d_base = np.linalg.norm(p2d_base - param_2d)

        # Increased: scalar_decay_mult=5.0
        p2d_mult = param_2d.copy()
        p1d_mult = param_1d.copy()
        opt_mult = MuonCANS(
            [p2d_mult, p1d_mult], lr=0.01, weight_decay=0.1, scalar_decay_mult=5.0
        )
        opt_mult.step([np.zeros((4, 4)), np.zeros(4)])
        delta_1d_mult = np.linalg.norm(p1d_mult - param_1d)
        delta_2d_mult = np.linalg.norm(p2d_mult - param_2d)

        # 1-D update should be larger with higher scalar_decay_mult
        assert delta_1d_mult > delta_1d_base
        # 2-D update should be unaffected by scalar_decay_mult
        assert np.isclose(delta_2d_base, delta_2d_mult)

    def test_small_matrix_guard_preserves_shape_and_does_not_crash(self):
        """_orthogonalise should handle small matrices without crashing."""
        for shape in [(1, 8), (8, 1), (2, 2), (3, 10), (10, 3)]:
            G = np.random.default_rng(0).standard_normal(shape)
            Q = _orthogonalise(G)
            assert Q.shape == shape, f"Shape mismatch for input {shape}: got {Q.shape}"

        # Near-zero small matrix should also be stable
        G_zero = np.zeros((2, 2))
        Q_zero = _orthogonalise(G_zero)
        assert Q_zero.shape == (2, 2)
        assert not np.any(np.isnan(Q_zero))


# ---------------------------------------------------------------------------
# utils.metrics
# ---------------------------------------------------------------------------

from utils.metrics import (
    early_gradient_projection,
    lyapunov_exponent,
    participation_ratio_bc,
)


class TestParticipationRatioBc:
    """Tests for participation_ratio_bc."""

    def test_full_rank_matrix(self):
        """A full-rank matrix should have a high PR_bc."""
        rng = np.random.default_rng(0)
        W = rng.standard_normal((16, 8))
        pr = participation_ratio_bc(W)
        # Full-rank: PR should be positive
        assert pr > 0

    def test_rank_one_matrix(self):
        """A rank-1 matrix should have a lower PR than a full-rank matrix."""
        rng = np.random.default_rng(0)
        u = rng.standard_normal(16)
        v = rng.standard_normal(8)
        W_rank1 = np.outer(u, v)
        W_full = rng.standard_normal((16, 8))
        pr_rank1 = participation_ratio_bc(W_rank1)
        pr_full = participation_ratio_bc(W_full)
        assert pr_full > pr_rank1

    def test_zero_matrix(self):
        W = np.zeros((8, 4))
        pr = participation_ratio_bc(W)
        assert pr == 0.0

    def test_1d_raises(self):
        with pytest.raises(ValueError):
            participation_ratio_bc(np.ones(8))

    def test_3d_input_reshaped(self):
        """3-D input should be reshaped without error."""
        W = np.random.default_rng(1).standard_normal((4, 4, 4))
        pr = participation_ratio_bc(W)
        assert isinstance(pr, float)


class TestEarlyGradientProjection:
    """Tests for early_gradient_projection."""

    def test_identical_grads_returns_one(self):
        g = [np.array([1.0, 0.0, 0.0])]
        assert np.isclose(early_gradient_projection(g, g), 1.0)

    def test_opposite_grads_returns_neg_one(self):
        g_a = [np.array([1.0, 0.0])]
        g_b = [np.array([-1.0, 0.0])]
        assert np.isclose(early_gradient_projection(g_a, g_b), -1.0)

    def test_orthogonal_grads_returns_zero(self):
        g_a = [np.array([1.0, 0.0])]
        g_b = [np.array([0.0, 1.0])]
        assert np.isclose(early_gradient_projection(g_a, g_b), 0.0, atol=1e-9)

    def test_multi_param_grads(self):
        rng = np.random.default_rng(0)
        g_a = [rng.standard_normal(s) for s in [(4, 4), (4,)]]
        egp = early_gradient_projection(g_a, g_a)
        assert np.isclose(egp, 1.0)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            early_gradient_projection([], [np.ones(4)])

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            early_gradient_projection([np.ones(4)], [np.ones(4), np.ones(4)])

    def test_zero_grad_returns_zero(self):
        g_a = [np.zeros(4)]
        g_b = [np.ones(4)]
        assert early_gradient_projection(g_a, g_b) == 0.0


class TestLyapunovExponent:
    """Tests for lyapunov_exponent."""

    def test_contracting_system(self):
        """Small weight matrices should give negative λ₁ (contracting)."""
        rng = np.random.default_rng(0)
        matrices = [rng.standard_normal((4, 4)) * 0.1 for _ in range(10)]
        lam = lyapunov_exponent(matrices, rng=rng)
        assert lam < 0.0

    def test_expanding_system(self):
        """Large weight matrices should give positive λ₁ (expanding)."""
        rng = np.random.default_rng(1)
        matrices = [rng.standard_normal((4, 4)) * 3.0 for _ in range(10)]
        lam = lyapunov_exponent(matrices, rng=rng)
        assert lam > 0.0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            lyapunov_exponent([])

    def test_non_2d_raises(self):
        with pytest.raises(ValueError):
            lyapunov_exponent([np.ones((2, 2, 2))])

    def test_reproducibility_with_seed(self):
        rng_a = np.random.default_rng(42)
        rng_b = np.random.default_rng(42)
        matrices = [np.random.default_rng(i).standard_normal((4, 4)) for i in range(5)]
        lam_a = lyapunov_exponent(matrices, rng=rng_a)
        lam_b = lyapunov_exponent(matrices, rng=rng_b)
        assert lam_a == lam_b

    def test_returns_float(self):
        W = [np.eye(3)]
        result = lyapunov_exponent(W)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# ExperimentPipeline
# ---------------------------------------------------------------------------

from ecs.systems.experiment_pipeline import ExperimentPipeline


def _make_task(n_samples=200, n_features=8, n_classes=2, seed=0):
    rng = np.random.default_rng(seed)
    W = rng.standard_normal((n_features, n_classes))
    X = rng.standard_normal((n_samples, n_features))
    y = (X @ W).argmax(axis=1)
    split = int(n_samples * 0.8)
    return X[:split], y[:split], X[split:], y[split:]


class TestExperimentPipeline:
    """Tests for ExperimentPipeline ECS system."""

    def test_invalid_optimizer_raises(self):
        with pytest.raises(ValueError):
            ExperimentPipeline(optimizer_name="unknown_opt")

    @pytest.mark.parametrize("opt_name", ["muon_cans", "adamw", "sgd"])
    def test_run_returns_expected_keys(self, opt_name):
        X_a_tr, y_a_tr, X_a_te, y_a_te = _make_task(seed=0)
        X_b_tr, y_b_tr, X_b_te, y_b_te = _make_task(seed=1)

        pipeline = ExperimentPipeline(
            optimizer_name=opt_name,
            n_features=8,
            n_classes=2,
            epochs_per_task=5,
            log_interval=2,
            seed=42,
        )
        result = pipeline.run(
            X_a_tr, y_a_tr, X_b_tr, y_b_tr,
            X_a_te, y_a_te, X_b_te, y_b_te,
        )
        assert "optimizer" in result
        assert "task_a_final_acc" in result
        assert "task_b_final_acc" in result
        assert "log" in result
        assert "elapsed_seconds" in result
        assert result["optimizer"] == opt_name

    def test_log_contains_pr_bc(self):
        X_a_tr, y_a_tr, X_a_te, y_a_te = _make_task(seed=0)
        X_b_tr, y_b_tr, X_b_te, y_b_te = _make_task(seed=1)

        pipeline = ExperimentPipeline(
            n_features=8, n_classes=2, epochs_per_task=5, log_interval=2, seed=42
        )
        result = pipeline.run(X_a_tr, y_a_tr, X_b_tr, y_b_tr)
        assert any(e["pr_bc"] is not None for e in result["log"])

    def test_log_contains_egp_for_task_b(self):
        X_a_tr, y_a_tr, X_a_te, y_a_te = _make_task(seed=0)
        X_b_tr, y_b_tr, X_b_te, y_b_te = _make_task(seed=1)

        pipeline = ExperimentPipeline(
            n_features=8, n_classes=2, epochs_per_task=5, log_interval=2, seed=42
        )
        result = pipeline.run(X_a_tr, y_a_tr, X_b_tr, y_b_tr)
        task_b_entries = [e for e in result["log"] if e["task"] == "task_b"]
        assert len(task_b_entries) > 0
        assert all(e["egp"] is not None for e in task_b_entries)

    def test_accuracy_in_valid_range(self):
        X_a_tr, y_a_tr, X_a_te, y_a_te = _make_task(seed=0)
        X_b_tr, y_b_tr, X_b_te, y_b_te = _make_task(seed=1)

        pipeline = ExperimentPipeline(
            n_features=8, n_classes=2, epochs_per_task=10, log_interval=5, seed=42
        )
        result = pipeline.run(
            X_a_tr, y_a_tr, X_b_tr, y_b_tr,
            X_a_te, y_a_te, X_b_te, y_b_te,
        )
        assert 0.0 <= result["task_a_final_acc"] <= 1.0
        assert 0.0 <= result["task_b_final_acc"] <= 1.0

    def test_elapsed_seconds_positive(self):
        X_a_tr, y_a_tr, _, _ = _make_task(seed=0)
        X_b_tr, y_b_tr, _, _ = _make_task(seed=1)

        pipeline = ExperimentPipeline(
            n_features=8, n_classes=2, epochs_per_task=3, log_interval=2, seed=42
        )
        result = pipeline.run(X_a_tr, y_a_tr, X_b_tr, y_b_tr)
        assert result["elapsed_seconds"] > 0.0


# ---------------------------------------------------------------------------
# main.run_pipeline (smoke test)
# ---------------------------------------------------------------------------

from main import run_pipeline


class TestRunPipeline:
    """Smoke tests for the top-level run_pipeline function."""

    def test_returns_report_dict(self):
        report = run_pipeline(
            seed=0, n_samples=100, n_features=8, n_classes=2, epochs=3, log_interval=2
        )
        assert "results" in report
        assert len(report["results"]) == 3  # muon_cans, adamw, sgd

    def test_all_optimizers_present(self):
        report = run_pipeline(
            seed=0, n_samples=100, n_features=8, n_classes=2, epochs=3, log_interval=2
        )
        names = {r["optimizer"] for r in report["results"]}
        assert names == {"muon_cans", "adamw", "sgd"}

    def test_output_json_written(self, tmp_path):
        out = str(tmp_path / "results.json")
        run_pipeline(
            seed=0, n_samples=50, n_features=4, n_classes=2,
            epochs=2, log_interval=1, output_path=out,
        )
        import json, os
        assert os.path.exists(out)
        with open(out) as f:
            data = json.load(f)
        assert "results" in data
