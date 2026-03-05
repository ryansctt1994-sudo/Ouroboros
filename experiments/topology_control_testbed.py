"""Topology Control Testbed — Phase-Space Governor prototype (Script 1).

Implements PR_bc + LLE-proxy telemetry driving a closed-loop
``TopologyScheduler`` that autonomously adjusts learning-rate and momentum
to maintain the system near the "edge of chaos" (λ₁ ≈ 0).

Run::

    python experiments/topology_control_testbed.py

The training loop runs for TOTAL_STEPS=500.  At step 200 the learning rate
is spiked 100× to simulate a catastrophic LMO-coupling violation; the
Governor should detect the chaos signal and clamp the LR back down.

References
----------
* "Empirical Analysis of Stochastic Dynamical Systems in Neural Network
  Optimization" — Geometry-Aware Optimizer Dynamics (internal manuscript).
"""

import math
from typing import Dict

import torch
import torch.nn as nn
import torch.optim as optim
import torch.linalg as linalg

# ---------------------------------------------------------------------------
# 1. Topological Telemetry Primitives
# ---------------------------------------------------------------------------


def compute_pr_bc(
    activations: torch.Tensor,
    noise_bias_correction: float = 1e-4,
) -> float:
    """Compute the Bias-Corrected Participation Ratio (PR_bc).

    Measures the effective dimensionality of the representation manifold,
    adjusting for finite-sample covariance bias.

    Parameters
    ----------
    activations:
        Activation matrix of shape ``(batch, features)``.
    noise_bias_correction:
        Scalar ``c`` subtracted from the Frobenius denominator to strip
        sampling-noise inflation: ``PR_bc ∝ Tr(Σ)² / (‖Σ‖_F² − c·Tr(Σ)²)``.

    Returns
    -------
    float
        PR_bc value.  Returns ``1.0`` on degenerate inputs.
    """
    if activations.size(0) <= 1:
        return 1.0

    centered_H = activations - activations.mean(dim=0, keepdim=True)
    covariance_matrix = (centered_H.T @ centered_H) / (activations.size(0) - 1)

    trace_cov = torch.trace(covariance_matrix)
    squared_frobenius = linalg.norm(covariance_matrix, "fro") ** 2

    corrected_denominator = squared_frobenius - (noise_bias_correction * trace_cov ** 2)

    if corrected_denominator <= 0 or trace_cov <= 0:
        return 1.0

    pr_bc = (trace_cov ** 2 / corrected_denominator).item()
    return pr_bc


def compute_lle_proxy(
    W_current: torch.Tensor,
    W_prev: torch.Tensor | None,
    delta_t: float = 1.0,
) -> float:
    """Compute a step-energy proxy for the Largest Lyapunov Exponent.

    Approximates λ₁ as ``(1/Δt) · ln(‖W_t − W_{t-1}‖_F)``.
    Positive values indicate large, potentially chaotic updates; strongly
    negative values indicate very small (frozen) updates.

    Parameters
    ----------
    W_current:
        Weight tensor at the current step.
    W_prev:
        Weight tensor at the previous step, or ``None`` on the first call.
    delta_t:
        Time-step size (default ``1.0``).

    Returns
    -------
    float
        LLE proxy value.  Returns ``-1.0`` for the first call or
        near-zero updates.
    """
    if W_prev is None:
        return -1.0

    divergence = linalg.norm(W_current - W_prev, "fro").item()

    if divergence < 1e-12:
        return -1.0

    return (1.0 / delta_t) * math.log(divergence)


# ---------------------------------------------------------------------------
# 2. The Dynamic Topology Scheduler (The Governor)
# ---------------------------------------------------------------------------


class TopologyScheduler:
    """Closed-loop dynamical controller using LLE + PR_bc telemetry.

    Observes the step-energy LLE proxy and PR_bc, then autonomously
    adjusts ``lr`` and ``momentum`` to keep the system near λ₁ ≈ 0.

    Parameters
    ----------
    optimizer:
        The PyTorch optimizer to govern.
    base_eta:
        Reference learning rate (used to set min/max clamps).
    base_beta:
        Reference momentum (used to set min/max clamps).
    lle_crit_high:
        LLE threshold above which the system is deemed chaotic.
        For the step-energy proxy ``ln(‖ΔW‖_F)``, a value of ``1.5``
        corresponds to ‖ΔW‖_F > e^1.5 ≈ 4.5.
    lle_crit_low:
        LLE threshold below which the system is deemed over-damped
        (risk of representation freeze).
    """

    def __init__(
        self,
        optimizer: optim.Optimizer,
        base_eta: float,
        base_beta: float,
        lle_crit_high: float = 1.5,
        lle_crit_low: float = -3.0,
    ) -> None:
        self.optimizer = optimizer
        self.base_eta = base_eta
        self.base_beta = base_beta
        self.W_prev: torch.Tensor | None = None
        self.lle_crit_high = lle_crit_high
        self.lle_crit_low = lle_crit_low

        # Safe operational bounds
        self.eta_min = base_eta * 0.1
        self.eta_max = base_eta * 5.0
        self.beta_min = 0.80
        self.beta_max = 0.99

    def step(
        self,
        W_current: torch.Tensor,
        activations: torch.Tensor,
    ) -> Dict[str, float]:
        """Perform one telemetry + intervention step.

        Parameters
        ----------
        W_current:
            Current weight tensor for the monitored layer.
        activations:
            Batch activations from the monitored layer,
            shape ``(batch, features)``.

        Returns
        -------
        dict
            Keys: ``lle``, ``pr_bc``, ``eta``, ``beta``.
        """
        # --- Telemetry ---
        pr_bc = compute_pr_bc(activations)
        lle = compute_lle_proxy(W_current, self.W_prev)
        self.W_prev = W_current.clone().detach()

        new_eta = self.base_eta
        new_beta = self.base_beta

        for param_group in self.optimizer.param_groups:
            current_eta = param_group["lr"]
            current_beta = param_group.get("momentum", self.base_beta)

            # STATE A — Systemic Chaos Imminent (λ₁ > lle_crit_high)
            # Action: slash η, increase inertial β to clamp onto manifold
            if lle > self.lle_crit_high:
                new_eta = max(self.eta_min, current_eta * 0.5)
                new_beta = min(self.beta_max, current_beta + 0.02)

            # STATE B — Over-Constrained / Representation Freezing
            # Action: nudge η upward, slightly reduce β to push toward edge
            elif lle < self.lle_crit_low:
                new_eta = min(self.eta_max, current_eta * 1.05)
                new_beta = max(self.beta_min, current_beta - 0.01)

            # STATE C — Edge of Chaos — maintain trajectory
            else:
                new_eta = current_eta
                new_beta = current_beta

            param_group["lr"] = new_eta
            if "momentum" in param_group:
                param_group["momentum"] = new_beta

            # Only govern the first param-group in this mock testbed
            break

        return {"lle": lle, "pr_bc": pr_bc, "eta": new_eta, "beta": new_beta}


# ---------------------------------------------------------------------------
# 3. Orthogonal MLP Testbed (Mock)
# ---------------------------------------------------------------------------


class OrthogonalMLP(nn.Module):
    """Minimal mock of a model with one orthogonal-constrained hidden layer.

    In a full Muon deployment the ``ortho_layer`` weights would be
    orthogonalised at every step.  Here the layer is unconstrained so that
    the Governor dynamics can be studied in isolation.
    """

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int) -> None:
        super().__init__()
        # The constrained layer whose weight matrix is monitored by the Governor
        self.ortho_layer = nn.Linear(in_dim, hidden_dim, bias=False)
        self.relu = nn.ReLU()
        self.final_layer = nn.Linear(hidden_dim, out_dim)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return ``(output, activations)``."""
        activations = self.relu(self.ortho_layer(x))
        out = self.final_layer(activations)
        return out, activations


# ---------------------------------------------------------------------------
# 4. Predictive Latency Test Loop
# ---------------------------------------------------------------------------


def main() -> None:
    BASE_LR = 1.0e-3
    BASE_MOMENTUM = 0.9
    TOTAL_STEPS = 500

    model = OrthogonalMLP(in_dim=128, hidden_dim=256, out_dim=10)
    optimizer = optim.SGD(model.parameters(), lr=BASE_LR, momentum=BASE_MOMENTUM)
    criterion = nn.MSELoss()

    scheduler = TopologyScheduler(optimizer, BASE_LR, BASE_MOMENTUM)

    # target_weight is a live view — always reflects the current parameter data
    target_weight = model.ortho_layer.weight.data

    print(f"--- Starting Predictive Latency Test (Total Steps: {TOTAL_STEPS}) ---")
    print(f"Initial LR: {BASE_LR}, Momentum: {BASE_MOMENTUM}")
    print()
    print("Step | Loss       | PR_bc     | LLE     | New LR   | New Beta | Action")
    print("-" * 78)

    for step in range(1, TOTAL_STEPS + 1):
        mock_input = torch.randn(64, 128)
        mock_target = torch.randn(64, 10)

        # --- Forward + Backward ---
        optimizer.zero_grad()
        output, activations = model(mock_input)
        loss = criterion(output, mock_target)
        loss.backward()

        # NOTE: In a full Muon deployment the orthogonalised update
        # (CANS / Newton-Schulz) would be applied here before optimizer.step().
        optimizer.step()

        # --- Governor Intervention ---
        telemetry = scheduler.step(target_weight, activations)

        # --- Classify action for display ---
        if telemetry["lle"] > scheduler.lle_crit_high:
            action = "Clamp Down (Chaos)"
        elif telemetry["lle"] < scheduler.lle_crit_low:
            action = "Push (Freeze)"
        else:
            action = "Hold"

        # Print every 25 steps plus the steps around the collapse event
        if step % 25 == 0 or step <= 3 or step in (199, 200, 201, 202, 203):
            print(
                f"{step:4d} | {loss.item():10.4f} | {telemetry['pr_bc']:9.3f} | "
                f"{telemetry['lle']:7.3f} | {telemetry['eta']:.2e} | "
                f"{telemetry['beta']:.3f} | {action}"
            )

        # --- Simulated collapse at step 200 ---
        # Spike the LR 100× above the stable threshold to simulate a
        # catastrophic violation of the LMO coupling.
        if step == 200:
            print()
            print("=" * 78)
            print("= COLLAPSE INDUCED: LR spiked 100× to simulate LMO-coupling violation =")
            print("=" * 78)
            print()
            optimizer.param_groups[0]["lr"] = 1.0e-1
            # The Governor will detect λ₁ > lle_crit_high on the next step
            # and begin clamping the LR back down.

    # --- Final summary ---
    final_lr = optimizer.param_groups[0]["lr"]
    final_beta = optimizer.param_groups[0].get("momentum", BASE_MOMENTUM)
    print()
    print("=" * 78)
    print("SIMULATION COMPLETE")
    print(f"  Final LR   : {final_lr:.4e}  (baseline: {BASE_LR:.4e})")
    print(f"  Final Beta : {final_beta:.3f}  (baseline: {BASE_MOMENTUM:.3f})")
    print("=" * 78)


if __name__ == "__main__":
    main()
