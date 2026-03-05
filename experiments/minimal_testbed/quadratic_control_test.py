"""Quadratic Control Validation — Twin-Trajectory LLE Governor (Script 2).

A self-contained controlled experiment that validates the ``TopologyScheduler``
on a convex quadratic loss ``f(x) = ½ xᵀAx`` with a controllable condition
number κ.  Unlike the OrthogonalMLP testbed, the ground-truth dynamics are
known analytically, so the twin-trajectory LLE signal can be interpreted
without confounds from deep-network non-linearities.

Key methodological features
----------------------------
* **Convex Quadratic Environment** — ``ConvexQuadraticLoss`` with explicit κ.
* **Twin-Trajectory LLE** — tracks exponential separation between a primary
  parameter vector and an infinitesimally perturbed replica.
* **EMA smoothing + hysteresis** — the Governor uses an Exponential Moving
  Average on λ₁ and width-gated regime switching to avoid control chatter.

Run::

    python experiments/minimal_testbed/quadratic_control_test.py

Two external perturbations are injected to test the Governor's resilience:

* **Step 200** — LR is forced 15× above the baseline.
* **Step 350** — LR is collapsed to 0.5 % of the baseline.

References
----------
* "Empirical Analysis of Stochastic Dynamical Systems in Neural Network
  Optimization" — Geometry-Aware Optimizer Dynamics (internal manuscript).
"""

import math
from typing import Dict

import torch
import torch.optim as optim
import torch.linalg as linalg

# Use float64 throughout for clean mathematical analysis
torch.set_default_dtype(torch.float64)

# ---------------------------------------------------------------------------
# 1. Environment: Convex Quadratic Loss  f(x) = ½ xᵀAx
# ---------------------------------------------------------------------------


class ConvexQuadraticLoss:
    """Quadratic loss with a precisely controlled condition number κ.

    The Hessian ``A = Q Λ Qᵀ`` has eigenvalues log-spaced from ``1/κ``
    to ``1``, giving condition number exactly ``κ``.

    Parameters
    ----------
    dim:
        Dimensionality of the parameter vector.
    kappa:
        Target condition number ``σ_max / σ_min``.
    """

    def __init__(self, dim: int, kappa: float = 100.0) -> None:
        eigenvalues = torch.linspace(1.0 / kappa, 1.0, dim)
        # Random orthogonal matrix via QR decomposition
        Q, _ = torch.linalg.qr(torch.randn(dim, dim))
        self.A = Q @ torch.diag(eigenvalues) @ Q.T
        self.dim = dim
        self.kappa = kappa

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        """Compute ``½ xᵀAx`` and set ``x.grad = Ax`` (analytical gradient).

        The gradient is assigned directly so that ``optimizer.step()`` can
        consume it without requiring ``loss.backward()``.
        """
        loss = 0.5 * x.T @ self.A @ x
        # Analytical gradient of ½ xᵀAx is Ax (A is symmetric)
        x.grad = self.A @ x
        return loss


# ---------------------------------------------------------------------------
# 2. Telemetry Primitives
# ---------------------------------------------------------------------------


def compute_twin_trajectory_lle(
    current_distance: float,
    initial_distance: float,
    steps: int,
) -> float:
    """Finite-Time Largest Lyapunov Exponent proxy via twin-trajectory separation.

    Approximates ``λ₁ ≈ (1/k) · ln(‖dₖ‖ / ‖d₀‖)``.

    A negative value indicates converging trajectories (stable regime).
    A positive value indicates exponentially diverging trajectories (chaotic).

    Parameters
    ----------
    current_distance:
        Current separation ‖x′ − x‖.
    initial_distance:
        Initial separation ‖d₀‖ (before this measurement window).
    steps:
        Number of steps in the current measurement window.

    Returns
    -------
    float
        Instantaneous LLE estimate.  Returns ``-1.0`` on degenerate inputs.
    """
    if steps <= 0 or initial_distance < 1e-12:
        return -1.0
    current_distance = max(current_distance, 1e-15)
    return (1.0 / steps) * math.log(current_distance / initial_distance)


class EMA:
    """Exponential Moving Average for telemetry hysteresis.

    Parameters
    ----------
    initial_value:
        Starting value of the moving average.
    decay:
        Smoothing factor in [0, 1).  Higher → more smoothing.
    """

    def __init__(self, initial_value: float, decay: float) -> None:
        self.value = initial_value
        self.decay = decay

    def update(self, new_value: float) -> float:
        """Update EMA and return the new smoothed value."""
        self.value = self.decay * self.value + (1.0 - self.decay) * new_value
        return self.value


# ---------------------------------------------------------------------------
# 3. The Dynamic Topology Scheduler (Upgraded Governor)
# ---------------------------------------------------------------------------


class TopologyScheduler:
    """Closed-loop controller using smoothed Twin-Trajectory LLE telemetry.

    Uses EMA smoothing and hysteresis-gated regime switching to avoid
    control oscillations when the LLE signal is noisy.

    Parameters
    ----------
    optimizer:
        The PyTorch optimizer to govern.
    base_eta:
        Baseline learning rate used to set the operational clamp bounds.
    base_beta:
        Baseline momentum coefficient.
    lle_ema_decay:
        EMA decay applied to the raw LLE signal.
    lle_crit_high:
        Smoothed LLE above this threshold → "Chaos Clamp" intervention.
    lle_crit_low:
        Smoothed LLE below this threshold → "Push to Edge" intervention.
    """

    def __init__(
        self,
        optimizer: optim.Optimizer,
        base_eta: float,
        base_beta: float,
        lle_ema_decay: float = 0.95,
        lle_crit_high: float = 0.005,
        lle_crit_low: float = -0.01,
    ) -> None:
        self.optimizer = optimizer
        self.base_eta = base_eta
        self.base_beta = base_beta

        # Twin-trajectory state
        self._lle_initial_distance: float = 1e-6
        self._lle_current_distance: float = 1e-6
        self._lle_steps: int = 0
        self._lle_max_steps: int = 50  # Re-normalisation window

        # Smoothing
        self.lle_ema = EMA(initial_value=-1.0, decay=lle_ema_decay)
        self.lle_crit_high = lle_crit_high
        self.lle_crit_low = lle_crit_low

        # Safe operational bounds
        self.eta_min = base_eta * 0.05
        self.eta_max = base_eta * 2.0
        self.beta_min = 0.80
        self.beta_max = 0.99

    def step(
        self,
        x_current: torch.Tensor,
        x_perturbed: torch.Tensor,
        loss_func: ConvexQuadraticLoss,
    ) -> Dict[str, float]:
        """Perform one twin-trajectory step, compute telemetry, intervene.

        The primary parameter ``x_current`` has already had its gradient set
        by ``loss_func`` before this call; ``optimizer.step()`` is called
        *after* this method returns.

        Parameters
        ----------
        x_current:
            Primary parameter vector (gradient already set via loss_func).
        x_perturbed:
            Shadow / twin parameter vector.  Updated in-place via identical
            gradient dynamics during this call.
        loss_func:
            The ``ConvexQuadraticLoss`` instance (used to update the twin).

        Returns
        -------
        dict
            Keys: ``lle_smooth``, ``lle_instant``, ``new_eta``, ``new_beta``,
            ``distance``.
        """
        eta = self.optimizer.param_groups[0]["lr"]

        # --- 1. Update the perturbed replica with identical gradient dynamics ---
        grad_perturbed = loss_func.A @ x_perturbed
        x_perturbed.data = x_perturbed.data - eta * grad_perturbed

        # --- 2. Compute twin-trajectory separation ---
        new_distance = linalg.norm(
            x_current.detach() - x_perturbed.detach(), "fro"
        ).item()
        lle_instant = compute_twin_trajectory_lle(
            new_distance, self._lle_initial_distance, self._lle_steps
        )
        lle_smoothed = self.lle_ema.update(lle_instant)

        self._lle_current_distance = new_distance
        self._lle_steps += 1

        # Re-normalise twin to keep perturbation small
        if self._lle_steps >= self._lle_max_steps or new_distance > 1e-4:
            sep = x_current.detach() - x_perturbed.detach()
            sep_norm = sep.norm().clamp(min=1e-15)
            direction = sep / sep_norm
            x_perturbed.data = (
                x_current.detach() - direction * self._lle_initial_distance
            )
            self._lle_steps = 0

        # --- 3. Hysteresis-gated intervention ---
        param_group = self.optimizer.param_groups[0]
        new_eta = param_group["lr"]
        new_beta = param_group.get("momentum", self.base_beta)

        if lle_smoothed > self.lle_crit_high:
            # Chaos imminent — clamp down
            new_eta = max(self.eta_min, new_eta * 0.75)
            new_beta = min(self.beta_max, new_beta + 0.01)
        elif lle_smoothed < self.lle_crit_low:
            # Over-constrained / freezing — push toward edge
            new_eta = min(self.eta_max, new_eta * 1.1)
            new_beta = max(self.beta_min, new_beta - 0.005)
        # else: edge of chaos — hold

        param_group["lr"] = new_eta
        if "momentum" in param_group:
            param_group["momentum"] = new_beta

        return {
            "lle_smooth": lle_smoothed,
            "lle_instant": lle_instant,
            "new_eta": new_eta,
            "new_beta": new_beta,
            "distance": new_distance,
        }


# ---------------------------------------------------------------------------
# 4. Simulation Loop
# ---------------------------------------------------------------------------


def main() -> None:
    DIM = 100
    KAPPA = 500.0  # High condition number for a challenging optimisation landscape
    BASE_LR = 1e-3
    BASE_MOMENTUM = 0.9
    TOTAL_STEPS = 500

    # Primary parameter vector (requires_grad for SGD compatibility)
    x = torch.randn(DIM, 1)
    x.requires_grad_(True)

    # Infinitesimally perturbed shadow replica (no grad needed)
    x_perturbed = x.clone().detach() + torch.randn(DIM, 1) * 1e-6

    loss_function = ConvexQuadraticLoss(dim=DIM, kappa=KAPPA)
    optimizer = optim.SGD([x], lr=BASE_LR, momentum=BASE_MOMENTUM)
    scheduler = TopologyScheduler(optimizer, BASE_LR, BASE_MOMENTUM)

    print(
        f"--- Quadratic Control Validation  "
        f"(Dim={DIM}, κ={KAPPA:.0f}) ---"
    )
    print(f"Initial LR: {BASE_LR}, Momentum: {BASE_MOMENTUM}")
    print("-" * 105)
    print(
        "Step | Loss       | LLE Inst  | LLE Smooth | Norm(x)  "
        "| New LR   | New Beta | Action"
    )
    print("-" * 105)

    for step in range(1, TOTAL_STEPS + 1):
        # --- Compute loss and analytical gradient ---
        optimizer.zero_grad()
        loss = loss_function(x)
        # x.grad is now set analytically by loss_function; no backward() needed.

        # --- Governor step (updates twin, computes LLE, intervenes) ---
        telemetry = scheduler.step(x, x_perturbed, loss_function)

        # --- Optimise primary ---
        optimizer.step()

        # --- Log ---
        lle_smooth = telemetry["lle_smooth"]
        if lle_smooth > scheduler.lle_crit_high:
            action = "Chaos Clamp"
        elif lle_smooth < scheduler.lle_crit_low:
            action = "Push Edge"
        else:
            action = "Hold"

        if step % 50 == 0 or step <= 3 or step in (199, 200, 201, 349, 350, 351):
            print(
                f"{step:4d} | {loss.item():10.4f} | "
                f"{telemetry['lle_instant']:9.4f} | "
                f"{telemetry['lle_smooth']:10.4f} | "
                f"{linalg.norm(x).item():8.4f} | "
                f"{telemetry['new_eta']:.2e} | "
                f"{telemetry['new_beta']:.3f} | {action}"
            )

        # --- External perturbation: LR spike ---
        if step == 200:
            print()
            print("=" * 105)
            print(
                "= EXTERNAL PERTURBATION: LR spiked 15× "
                "to test EMA/Hysteresis damping ="
            )
            print("=" * 105)
            print()
            optimizer.param_groups[0]["lr"] = BASE_LR * 15

        # --- External perturbation: LR collapse ---
        if step == 350:
            print()
            print("=" * 105)
            print(
                "= EXTERNAL PERTURBATION: LR collapsed to 0.5% "
                "to induce deep-freeze regime ="
            )
            print("=" * 105)
            print()
            optimizer.param_groups[0]["lr"] = BASE_LR * 0.005

    print()
    print("=" * 105)
    print("SIMULATION COMPLETE")
    final_lr = optimizer.param_groups[0]["lr"]
    final_beta = optimizer.param_groups[0].get("momentum", BASE_MOMENTUM)
    print(f"  Final LR   : {final_lr:.4e}  (baseline: {BASE_LR:.4e})")
    print(f"  Final Beta : {final_beta:.3f}  (baseline: {BASE_MOMENTUM:.3f})")
    print(f"  Final ‖x‖  : {linalg.norm(x).item():.6f}  (target: 0)")
    print("=" * 105)


if __name__ == "__main__":
    main()
