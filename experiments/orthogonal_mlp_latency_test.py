"""OrthogonalMLP Predictive Latency Test — Dual-Telemetry Governor (Script 3).

The final combined testbed that integrates both telemetry channels:

* **Twin-Trajectory LLE** (λ₁) — measures exponential separation of a
  shadow parameter trajectory, providing chaos / stability signals.
* **Bias-Corrected Participation Ratio** (PR_bc) — measures the effective
  dimensionality of the hidden-layer activation manifold.

The ``TopologyScheduler`` uses both signals together:

* High λ₁ alone → ``Chaos Clamp`` (slash η, raise β).
* Low λ₁ *and* low PR_bc → ``Push to Edge`` (raise η, lower β) to prevent
  representation bottleneck.
* Otherwise → ``Hold`` (edge-of-chaos regime).

Run::

    python experiments/orthogonal_mlp_latency_test.py

A catastrophic LR spike (50× baseline) is injected at step 250 to test
whether the telemetry predicts feature collapse *before* the loss degrades.

References
----------
* "Causal Regulation of Dynamical Phases in Stiefel Manifold Optimization"
  — Geometry-Aware Optimizer Dynamics (internal manuscript).
"""

import math
from typing import Dict

import torch
import torch.nn as nn
import torch.optim as optim
import torch.linalg as linalg

torch.set_default_dtype(torch.float64)

# ---------------------------------------------------------------------------
# 1. Topological Telemetry Primitives
# ---------------------------------------------------------------------------


def compute_pr_bc(
    activations: torch.Tensor,
    noise_bias_correction: float = 1e-4,
) -> float:
    """Bias-Corrected Participation Ratio.

    See ``experiments/topology_control_testbed.py`` for full docstring.
    """
    if activations.size(0) <= 1:
        return 1.0

    centered_H = activations - activations.mean(dim=0, keepdim=True)
    covariance_matrix = (centered_H.T @ centered_H) / (activations.size(0) - 1)

    trace_cov = torch.trace(covariance_matrix)
    squared_frobenius = linalg.norm(covariance_matrix, "fro") ** 2

    corrected_denominator = squared_frobenius - (noise_bias_correction * trace_cov ** 2)

    if corrected_denominator <= 0 or trace_cov <= 0:
        return 1e-6  # Representation-collapse fallback

    return (trace_cov ** 2 / corrected_denominator).item()


def compute_twin_trajectory_lle(
    current_distance: float,
    initial_distance: float,
    steps: int,
) -> float:
    """Finite-Time LLE via twin-trajectory separation.

    See ``experiments/minimal_testbed/quadratic_control_test.py`` for full docstring.
    """
    if steps <= 0 or initial_distance < 1e-12:
        return -1.0
    current_distance = max(current_distance, 1e-15)
    return (1.0 / steps) * math.log(current_distance / initial_distance)


class EMA:
    """Exponential Moving Average for telemetry hysteresis."""

    def __init__(self, initial_value: float, decay: float) -> None:
        self.value = initial_value
        self.decay = decay

    def update(self, new_value: float) -> float:
        """Update and return the smoothed EMA value."""
        self.value = self.decay * self.value + (1.0 - self.decay) * new_value
        return self.value


# ---------------------------------------------------------------------------
# 2. Integrated Dual-Telemetry Topology Scheduler
# ---------------------------------------------------------------------------


class TopologyScheduler:
    """Dynamical control system combining Twin-Trajectory LLE and PR_bc.

    Navigates the Stiefel manifold by balancing stability (LLE) and
    representational expressivity (PR_bc).

    Parameters
    ----------
    optimizer:
        PyTorch optimizer to govern.
    base_eta, base_beta:
        Baseline learning rate and momentum (set the operational bounds).
    lle_ema_decay:
        EMA smoothing decay for the LLE signal.
    lle_crit_high:
        Chaos threshold — LLE > this value triggers ``Chaos Clamp``.
    lle_crit_low:
        Freeze threshold — LLE < this value *and* PR_bc below
        ``pr_bc_bottleneck_thresh`` triggers ``Push to Edge``.
    pr_bc_bottleneck_thresh:
        PR_bc threshold below which the representation is deemed bottlenecked.
    """

    def __init__(
        self,
        optimizer: optim.Optimizer,
        base_eta: float,
        base_beta: float,
        lle_ema_decay: float = 0.95,
        lle_crit_high: float = 0.01,
        lle_crit_low: float = -0.05,
        pr_bc_bottleneck_thresh: float = 2.0,
    ) -> None:
        self.optimizer = optimizer
        self.base_eta = base_eta
        self.base_beta = base_beta

        # Twin-trajectory state
        self._lle_initial_distance: float = 1e-6
        self._lle_steps: int = 0
        self._lle_max_steps: int = 50

        # Smoothing
        self.lle_ema = EMA(initial_value=-1.0, decay=lle_ema_decay)
        self.lle_crit_high = lle_crit_high
        self.lle_crit_low = lle_crit_low
        self.pr_bc_bottleneck_thresh = pr_bc_bottleneck_thresh

        # Safe operational bounds
        self.eta_min = base_eta * 0.01
        self.eta_max = base_eta * 5.0
        self.beta_min = 0.80
        self.beta_max = 0.99

    def step(
        self,
        w_primary: torch.Tensor,
        w_twin: torch.Tensor,
        activations: torch.Tensor,
    ) -> Dict[str, float]:
        """One telemetry + intervention step.

        Parameters
        ----------
        w_primary:
            The monitored layer's weight ``Parameter`` (live view).
        w_twin:
            Shadow twin weight tensor (updated in-place using the primary's
            gradient, which must already be computed before this call).
        activations:
            Batch activations from the monitored layer, ``(batch, features)``.

        Returns
        -------
        dict
            Keys: ``lle``, ``pr_bc``, ``eta``, ``beta``, ``action``.
        """
        # --- 1. PR_bc telemetry ---
        pr_bc = compute_pr_bc(activations)

        # --- 2. Twin-trajectory LLE telemetry ---
        new_distance = linalg.norm(
            w_primary.detach() - w_twin.detach(), "fro"
        ).item()
        lle_instant = compute_twin_trajectory_lle(
            new_distance, self._lle_initial_distance, self._lle_steps
        )
        lle_smoothed = self.lle_ema.update(lle_instant)

        self._lle_steps += 1

        # Re-normalise twin to keep perturbation magnitude constant
        if self._lle_steps >= self._lle_max_steps or new_distance > 1e-4:
            sep = w_primary.detach() - w_twin.detach()
            sep_norm = sep.norm().clamp(min=1e-15)
            w_twin.data = w_primary.detach() - (sep / sep_norm) * self._lle_initial_distance
            self._lle_steps = 0

        # --- 3. Dual-telemetry intervention logic ---
        param_group = self.optimizer.param_groups[0]
        new_eta = param_group["lr"]
        new_beta = param_group.get("momentum", self.base_beta)
        action = "Hold (Criticality)"

        # STATE A — Systemic Chaos (LLE strictly overrides PR_bc)
        if lle_smoothed > self.lle_crit_high:
            new_eta = max(self.eta_min, new_eta * 0.6)
            new_beta = min(self.beta_max, new_beta + 0.02)
            action = "Chaos Clamp (LLE High)"

        # STATE B — Representation Bottleneck (low LLE + collapsing PR_bc)
        elif lle_smoothed < self.lle_crit_low and pr_bc < self.pr_bc_bottleneck_thresh:
            new_eta = min(self.eta_max, new_eta * 1.15)
            new_beta = max(self.beta_min, new_beta - 0.01)
            action = "Push Edge (PR_bc Low)"

        # STATE C — Edge of Chaos — maintain trajectory
        # (no parameter change)

        param_group["lr"] = new_eta
        if "momentum" in param_group:
            param_group["momentum"] = new_beta

        return {
            "lle": lle_smoothed,
            "pr_bc": pr_bc,
            "eta": new_eta,
            "beta": new_beta,
            "action": action,
        }


# ---------------------------------------------------------------------------
# 3. Orthogonal MLP Testbed
# ---------------------------------------------------------------------------


class OrthogonalMLP(nn.Module):
    """Minimal MLP with one Stiefel-constrained hidden layer (mock).

    In production the ``ortho_layer`` weights would be re-orthogonalised at
    every step by the Muon/CANS optimizer.  In this testbed orthogonalisation
    is omitted so the Governor dynamics remain the focus.
    """

    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int) -> None:
        super().__init__()
        self.ortho_layer = nn.Linear(in_dim, hidden_dim, bias=False)
        self.relu = nn.ReLU()
        self.final_layer = nn.Linear(hidden_dim, out_dim)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return ``(output, activations)``."""
        activations = self.relu(self.ortho_layer(x))
        return self.final_layer(activations), activations


# ---------------------------------------------------------------------------
# 4. Predictive Latency Simulation
# ---------------------------------------------------------------------------


def main() -> None:
    DIM_IN, DIM_HIDDEN, DIM_OUT = 128, 256, 10
    BASE_LR = 1e-3
    BASE_MOMENTUM = 0.9
    TOTAL_STEPS = 500

    model = OrthogonalMLP(in_dim=DIM_IN, hidden_dim=DIM_HIDDEN, out_dim=DIM_OUT)
    criterion = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=BASE_LR, momentum=BASE_MOMENTUM)
    scheduler = TopologyScheduler(optimizer, BASE_LR, BASE_MOMENTUM)

    # w_primary is the constrained layer's weight Parameter (live view)
    w_primary = model.ortho_layer.weight
    # Shadow / twin initialised with a tiny perturbation
    w_twin = w_primary.clone().detach() + torch.randn_like(w_primary) * 1e-6

    print("--- OrthogonalMLP Predictive Latency Test ---")
    print(f"DIM_IN={DIM_IN}, DIM_HIDDEN={DIM_HIDDEN}, DIM_OUT={DIM_OUT}")
    print(f"Initial LR: {BASE_LR}, Momentum: {BASE_MOMENTUM}")
    print()
    print("Step | Loss     | PR_bc   | LLE Smooth | LR       | Beta  | Action")
    print("-" * 80)

    for step in range(1, TOTAL_STEPS + 1):
        x_batch = torch.randn(64, DIM_IN)
        y_batch = torch.randn(64, DIM_OUT)

        # --- Forward + backward ---
        optimizer.zero_grad()
        output, activations = model(x_batch)
        loss = criterion(output, y_batch)
        loss.backward()

        # --- Update twin with the same gradient dynamics (pre-intervention LR) ---
        # This must happen before the scheduler might change the LR.
        current_lr = optimizer.param_groups[0]["lr"]
        if w_primary.grad is not None:
            w_twin.data = w_twin.data - current_lr * w_primary.grad.detach()

        # --- Governor telemetry + intervention ---
        telemetry = scheduler.step(w_primary, w_twin, activations)

        # --- Optimise primary (may use Governor-adjusted LR) ---
        optimizer.step()

        # --- Log ---
        if step % 25 == 0 or step <= 3 or step in (249, 250, 251, 252, 253):
            print(
                f"{step:4d} | {loss.item():8.4f} | "
                f"{telemetry['pr_bc']:7.3f} | "
                f"{telemetry['lle']:10.4f} | "
                f"{telemetry['eta']:.2e} | "
                f"{telemetry['beta']:.3f} | {telemetry['action']}"
            )

        # --- Catastrophic LR spike at step 250 ---
        if step == 250:
            print()
            print("=" * 80)
            print("= CATASTROPHIC INJECTION: LR spiked 50× to test Predictive Latency =")
            print("=" * 80)
            print()
            # Force LR well above the stable threshold — the Governor should
            # detect rising λ₁ and begin clamping within 1-2 steps.
            optimizer.param_groups[0]["lr"] = BASE_LR * 50.0

    # --- Final summary ---
    final_lr = optimizer.param_groups[0]["lr"]
    final_beta = optimizer.param_groups[0].get("momentum", BASE_MOMENTUM)
    print()
    print("=" * 80)
    print("SIMULATION COMPLETE")
    print(f"  Final LR   : {final_lr:.4e}  (baseline: {BASE_LR:.4e})")
    print(f"  Final Beta : {final_beta:.3f}  (baseline: {BASE_MOMENTUM:.3f})")
    print("=" * 80)


if __name__ == "__main__":
    main()
