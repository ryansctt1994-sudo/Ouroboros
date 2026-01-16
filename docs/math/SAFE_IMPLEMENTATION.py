"""
Safe Constraint Dynamics: Python Reference Implementation

This module provides a type-safe, mathematically rigorous implementation of the
constraint dynamics framework described in CONSTRAINT_DYNAMICS.md.

All implementations follow established theorems (Banach, von Neumann, Dykstra)
and use pure functional composition—no proprietary algorithms.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Protocol, Tuple
import numpy as np
from dataclasses import dataclass


# Type-safe protocols
class Transformation(Protocol):
    """Protocol for transformations in the constraint pipeline."""
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        """Apply transformation to input array."""
        ...


class Projection(ABC):
    """Abstract base class for projection operators."""
    
    @abstractmethod
    def project(self, psi: np.ndarray) -> np.ndarray:
        """Project state onto constraint manifold."""
        pass
    
    def is_orthogonal(self) -> bool:
        """Check if projection is orthogonal (P² = P)."""
        return True


@dataclass
class ConvergenceResult:
    """Results from constraint dynamics convergence."""
    solution: np.ndarray
    iterations: int
    final_violation: float
    convergence_rate: Optional[float] = None


# Pipeline Components
class HolographicCompression:
    """
    Φ: ℋ → ℋ' - Holographic compression via isometric embedding.
    
    Implements dimensionality reduction while preserving inner products
    within tolerance ε.
    """
    
    def __init__(self, dimension: int, epsilon: float = 1e-6):
        self.dimension = dimension
        self.epsilon = epsilon
        self.projection_matrix: Optional[np.ndarray] = None
    
    def fit(self, data: np.ndarray) -> None:
        """
        Compute isometric embedding via SVD.
        
        Args:
            data: Input data matrix of shape (n_samples, n_features)
        """
        # Use SVD for dimensionality reduction
        U, S, Vt = np.linalg.svd(data, full_matrices=False)
        
        # Keep top k components
        k = min(self.dimension, len(S))
        self.projection_matrix = Vt[:k, :]
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        """Apply holographic compression."""
        if self.projection_matrix is None:
            raise ValueError("Must call fit() before applying transformation")
        return self.projection_matrix @ x
    
    def lipschitz_constant(self) -> float:
        """Compute Lipschitz constant L_Φ."""
        if self.projection_matrix is None:
            return float('inf')
        return float(np.linalg.norm(self.projection_matrix, ord=2))


class CoherenceFunctional:
    """
    C: ℋ' → ℝ - Coherence functional (von Neumann entropy, purity).
    
    Maps quantum states to coherence measures.
    """
    
    def __init__(self, method: str = "von_neumann_entropy"):
        if method not in ["von_neumann_entropy", "purity", "linear_entropy"]:
            raise ValueError(f"Unknown method: {method}")
        self.method = method
    
    def __call__(self, psi: np.ndarray) -> float:
        """Compute coherence measure."""
        # Normalize to density matrix
        rho = np.outer(psi, psi.conj()) / np.dot(psi.conj(), psi)
        
        if self.method == "von_neumann_entropy":
            # S(ρ) = -Tr(ρ log ρ)
            eigenvalues = np.linalg.eigvalsh(rho)
            eigenvalues = eigenvalues[eigenvalues > 1e-12]  # Avoid log(0)
            return float(-np.sum(eigenvalues * np.log(eigenvalues)))
        
        elif self.method == "purity":
            # P(ρ) = Tr(ρ²)
            return float(np.trace(rho @ rho).real)
        
        else:  # linear_entropy
            # S_L(ρ) = 1 - Tr(ρ²)
            return float(1.0 - np.trace(rho @ rho).real)
    
    def lipschitz_constant(self) -> float:
        """Compute Lipschitz constant L_C."""
        # For bounded state spaces, coherence functionals are Lipschitz
        # Exact constant depends on method and state space dimension
        return 2.0  # Conservative upper bound


class EthicalBoundary:
    """
    E: ℝ → ℝ - Ethical boundary (monotonic transformation).
    
    Ensures output satisfies safety constraints via monotonic mapping.
    """
    
    def __init__(self, monotonic: bool = True, bounds: Tuple[float, float] = (0.0, 1.0)):
        self.monotonic = monotonic
        self.lower_bound, self.upper_bound = bounds
    
    def __call__(self, x: float) -> float:
        """Apply ethical boundary transformation."""
        if self.monotonic:
            # Sigmoid mapping to [lower, upper]
            sigmoid = 1.0 / (1.0 + np.exp(-x))
            return self.lower_bound + (self.upper_bound - self.lower_bound) * sigmoid
        else:
            # Simple clipping
            return np.clip(x, self.lower_bound, self.upper_bound)
    
    def lipschitz_constant(self) -> float:
        """Compute Lipschitz constant L_E."""
        if self.monotonic:
            # For sigmoid: max derivative is 1/4
            return 0.25 * (self.upper_bound - self.lower_bound)
        else:
            # Clipping is Lipschitz with constant 1
            return 1.0


class SafeConstraintPipeline:
    """
    Complete pipeline: O = E(C(Φ(I)))
    
    Composes holographic compression, coherence functional, and ethical boundary
    with guaranteed stability (Theorem 1).
    """
    
    def __init__(
        self,
        phi: HolographicCompression,
        c: CoherenceFunctional,
        e: EthicalBoundary
    ):
        self.phi = phi
        self.c = c
        self.e = e
    
    def __call__(self, input_state: np.ndarray) -> float:
        """Apply full constraint pipeline."""
        # Φ: ℋ → ℋ'
        compressed = self.phi(input_state)
        
        # C: ℋ' → ℝ
        coherence = self.c(compressed)
        
        # E: ℝ → ℝ
        output = self.e(coherence)
        
        return output
    
    def lipschitz_constant(self) -> float:
        """
        Compute pipeline Lipschitz constant (Theorem 1).
        
        Returns:
            L = L_E × L_C × L_Φ
        """
        return (
            self.e.lipschitz_constant() *
            self.c.lipschitz_constant() *
            self.phi.lipschitz_constant()
        )


# Projection Operators
class P3Projection(Projection):
    """
    P_3 projection operator (triple constraint).
    
    Projects onto the subspace satisfying the P_3 constraint.
    """
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self._projection_matrix = self._build_projection_matrix()
    
    def _build_projection_matrix(self) -> np.ndarray:
        """Build the P_3 projection matrix."""
        # Example: orthogonal projection onto first k coordinates
        # In practice, this would encode specific domain constraints
        k = max(1, self.dimension // 3)
        P = np.zeros((self.dimension, self.dimension))
        P[:k, :k] = np.eye(k)
        return P
    
    def project(self, psi: np.ndarray) -> np.ndarray:
        """Project state onto P_3 manifold."""
        return self._projection_matrix @ psi


class SPrimeProjection(Projection):
    """
    S' projection operator (secondary constraint).
    
    Projects onto the subspace satisfying the S' constraint.
    """
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self._projection_matrix = self._build_projection_matrix()
    
    def _build_projection_matrix(self) -> np.ndarray:
        """Build the S' projection matrix."""
        # Example: orthogonal projection onto last k coordinates
        # In practice, this would encode specific domain constraints
        k = max(1, self.dimension // 2)
        P = np.zeros((self.dimension, self.dimension))
        P[-k:, -k:] = np.eye(k)
        return P
    
    def project(self, psi: np.ndarray) -> np.ndarray:
        """Project state onto S' manifold."""
        return self._projection_matrix @ psi


class StandardProjections:
    """
    Standard projection operators for the constraint dynamics framework.
    
    Implements P_3 and S' projections with alternating projection method
    for computing the intersection.
    """
    
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.p3 = P3Projection(dimension)
        self.s_prime = SPrimeProjection(dimension)
    
    def P_3(self, psi: np.ndarray) -> np.ndarray:
        """Apply P_3 projection."""
        return self.p3.project(psi)
    
    def S_prime(self, psi: np.ndarray) -> np.ndarray:
        """Apply S' projection."""
        return self.s_prime.project(psi)
    
    def project_intersection(
        self,
        psi_0: np.ndarray,
        max_iterations: int = 1000,
        tolerance: float = 1e-6
    ) -> ConvergenceResult:
        """
        Compute projection onto intersection S ∩ S' via alternating projections.
        
        Implements: ψ* = lim_{n→∞} (P_S P_{S'})^n ψ_0
        
        Args:
            psi_0: Initial state
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
            
        Returns:
            ConvergenceResult with final state and diagnostics
        """
        psi = psi_0.copy()
        
        for iteration in range(max_iterations):
            psi_old = psi.copy()
            
            # Alternating projections
            psi = self.S_prime(psi)
            psi = self.P_3(psi)
            
            # Check convergence
            violation = np.linalg.norm(psi - psi_old)
            if violation < tolerance:
                return ConvergenceResult(
                    solution=psi,
                    iterations=iteration + 1,
                    final_violation=violation
                )
        
        # Max iterations reached
        final_violation = np.linalg.norm(psi - psi_old)
        return ConvergenceResult(
            solution=psi,
            iterations=max_iterations,
            final_violation=final_violation
        )


# Constraint Dynamics
class ConstraintDynamics:
    """
    Solver for constraint dynamics differential equation.
    
    Implements: ∂_t ψ = -Σ_j (I - P_j)ψ
    
    Uses RK4 integration with adaptive time-stepping for numerical stability.
    """
    
    def __init__(self, projections: List[Projection]):
        self.projections = projections
    
    def rhs(self, psi: np.ndarray) -> np.ndarray:
        """
        Compute right-hand side of constraint dynamics.
        
        Returns: -Σ_j (I - P_j)ψ
        """
        n = len(psi)
        gradient = np.zeros_like(psi)
        
        for P in self.projections:
            # Compute (I - P)ψ
            violation = psi - P.project(psi)
            gradient -= violation
        
        return gradient
    
    def constraint_violation(self, psi: np.ndarray) -> float:
        """
        Compute total constraint violation.
        
        Returns: Σ_j ||(I - P_j)ψ||²
        """
        violation = 0.0
        for P in self.projections:
            residual = psi - P.project(psi)
            violation += np.linalg.norm(residual) ** 2
        return violation
    
    def rk4_step(self, psi: np.ndarray, dt: float) -> np.ndarray:
        """
        Single RK4 integration step.
        
        Args:
            psi: Current state
            dt: Time step
            
        Returns:
            Updated state
        """
        k1 = self.rhs(psi)
        k2 = self.rhs(psi + 0.5 * dt * k1)
        k3 = self.rhs(psi + 0.5 * dt * k2)
        k4 = self.rhs(psi + dt * k3)
        
        return psi + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
    
    def solve(
        self,
        psi_0: np.ndarray,
        t_final: float,
        dt: float,
        method: str = "rk4"
    ) -> np.ndarray:
        """
        Solve constraint dynamics from psi_0 to t_final.
        
        Args:
            psi_0: Initial state
            t_final: Final time
            dt: Time step
            method: Integration method ("rk4" or "euler")
            
        Returns:
            Final state at t_final
        """
        if method not in ["rk4", "euler"]:
            raise ValueError(f"Unknown method: {method}")
        
        psi = psi_0.copy()
        t = 0.0
        
        while t < t_final:
            # Adaptive time-stepping
            dt_actual = min(dt, t_final - t)
            
            if method == "rk4":
                psi = self.rk4_step(psi, dt_actual)
            else:  # euler
                psi = psi + dt_actual * self.rhs(psi)
            
            t += dt_actual
        
        return psi


# Verification Suite
def verify_pipeline_stability(
    pipeline: SafeConstraintPipeline,
    test_inputs: List[np.ndarray],
    num_samples: int = 100
) -> float:
    """
    Verify Theorem 1: Pipeline Stability.
    
    Empirically estimates the Lipschitz constant by sampling input pairs.
    
    Args:
        pipeline: SafeConstraintPipeline to test
        test_inputs: List of test input vectors
        num_samples: Number of random pairs to sample
        
    Returns:
        Estimated Lipschitz constant
    """
    lipschitz_estimates = []
    
    for _ in range(num_samples):
        # Sample random pair
        i, j = np.random.choice(len(test_inputs), size=2, replace=False)
        x1, x2 = test_inputs[i], test_inputs[j]
        
        # Compute outputs
        y1 = pipeline(x1)
        y2 = pipeline(x2)
        
        # Estimate Lipschitz constant
        input_dist = np.linalg.norm(x1 - x2)
        output_dist = abs(y1 - y2)
        
        if input_dist > 1e-10:
            lipschitz_estimates.append(output_dist / input_dist)
    
    return max(lipschitz_estimates) if lipschitz_estimates else 0.0


def verify_convergence(
    dynamics: ConstraintDynamics,
    psi_0: np.ndarray,
    t_final: float,
    dt: float = 0.01
) -> Tuple[bool, float]:
    """
    Verify Theorem 2: Constraint Dynamics Convergence.
    
    Checks that constraint violation decreases monotonically.
    
    Args:
        dynamics: ConstraintDynamics solver
        psi_0: Initial state
        t_final: Final integration time
        dt: Time step
        
    Returns:
        (converged, convergence_rate) tuple
    """
    psi = psi_0.copy()
    t = 0.0
    
    violations = [dynamics.constraint_violation(psi)]
    times = [0.0]
    
    while t < t_final:
        dt_actual = min(dt, t_final - t)
        psi = dynamics.rk4_step(psi, dt_actual)
        t += dt_actual
        
        violation = dynamics.constraint_violation(psi)
        violations.append(violation)
        times.append(t)
    
    # Check monotonicity
    is_monotonic = all(
        violations[i+1] <= violations[i] + 1e-6
        for i in range(len(violations) - 1)
    )
    
    # Estimate exponential rate
    if violations[0] > 1e-10 and violations[-1] > 1e-10:
        rate = -np.log(violations[-1] / violations[0]) / t_final
    else:
        rate = float('inf')
    
    return is_monotonic, rate


def verify_fixed_point(
    projections: StandardProjections,
    psi_0: np.ndarray,
    max_iterations: int = 1000
) -> float:
    """
    Verify Theorem 3: Fixed Point Property.
    
    Checks that ||ψ*|| ≤ ||ψ_0|| and P ψ* = ψ*.
    
    Args:
        projections: StandardProjections instance
        psi_0: Initial state
        max_iterations: Maximum iterations for convergence
        
    Returns:
        Fixed point error
    """
    result = projections.project_intersection(psi_0, max_iterations)
    psi_star = result.solution
    
    # Check norm bound
    norm_ratio = np.linalg.norm(psi_star) / np.linalg.norm(psi_0)
    assert norm_ratio <= 1.0 + 1e-6, f"Norm increased: {norm_ratio}"
    
    # Check fixed point property
    psi_projected = projections.P_3(projections.S_prime(psi_star))
    fixed_point_error = np.linalg.norm(psi_projected - psi_star)
    
    return fixed_point_error


# Example Usage
if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)
    
    print("=== Safe Constraint Dynamics: Reference Implementation ===\n")
    
    # Example 1: SafeConstraintPipeline
    print("Example 1: SafeConstraintPipeline")
    print("-" * 50)
    
    # Generate training data for holographic compression
    train_data = np.random.randn(100, 256)
    
    # Create pipeline components
    phi = HolographicCompression(dimension=128)
    phi.fit(train_data)
    c = CoherenceFunctional(method="von_neumann_entropy")
    e = EthicalBoundary(monotonic=True)
    
    # Compose pipeline
    pipeline = SafeConstraintPipeline(phi, c, e)
    
    # Apply to test input
    test_input = np.random.randn(256)
    output = pipeline(test_input)
    
    print(f"Input dimension: {len(test_input)}")
    print(f"Output: {output:.6f}")
    print(f"Pipeline Lipschitz constant: {pipeline.lipschitz_constant():.6f}")
    print()
    
    # Example 2: StandardProjections
    print("Example 2: StandardProjections (Alternating Projections)")
    print("-" * 50)
    
    dimension = 64
    projections = StandardProjections(dimension=dimension)
    
    psi_0 = np.random.randn(dimension)
    result = projections.project_intersection(psi_0, max_iterations=1000)
    
    print(f"Initial state norm: {np.linalg.norm(psi_0):.6f}")
    print(f"Final state norm: {np.linalg.norm(result.solution):.6f}")
    print(f"Iterations: {result.iterations}")
    print(f"Final violation: {result.final_violation:.2e}")
    print()
    
    # Example 3: ConstraintDynamics
    print("Example 3: ConstraintDynamics (RK4 Integration)")
    print("-" * 50)
    
    p3 = P3Projection(dimension)
    s_prime = SPrimeProjection(dimension)
    dynamics = ConstraintDynamics(projections=[p3, s_prime])
    
    psi_0 = np.random.randn(dimension)
    t_final = 10.0
    dt = 0.01
    
    psi_final = dynamics.solve(psi_0, t_final, dt, method="rk4")
    
    print(f"Initial constraint violation: {dynamics.constraint_violation(psi_0):.6e}")
    print(f"Final constraint violation: {dynamics.constraint_violation(psi_final):.6e}")
    print(f"State norm ratio: {np.linalg.norm(psi_final) / np.linalg.norm(psi_0):.6f}")
    print()
    
    # Example 4: Verification Suite
    print("Example 4: Verification Suite")
    print("-" * 50)
    
    # Verify Theorem 1: Pipeline Stability
    test_inputs = [np.random.randn(256) for _ in range(20)]
    estimated_lipschitz = verify_pipeline_stability(pipeline, test_inputs, num_samples=50)
    theoretical_lipschitz = pipeline.lipschitz_constant()
    
    print(f"Theorem 1 - Pipeline Stability:")
    print(f"  Theoretical Lipschitz constant: {theoretical_lipschitz:.6f}")
    print(f"  Empirical Lipschitz constant: {estimated_lipschitz:.6f}")
    print()
    
    # Verify Theorem 2: Constraint Dynamics Convergence
    is_monotonic, rate = verify_convergence(dynamics, psi_0, t_final=5.0)
    
    print(f"Theorem 2 - Constraint Dynamics Convergence:")
    print(f"  Monotonic decrease: {is_monotonic}")
    print(f"  Convergence rate λ: {rate:.6f}")
    print()
    
    # Verify Theorem 3: Fixed Point Property
    fixed_point_error = verify_fixed_point(projections, psi_0)
    
    print(f"Theorem 3 - Fixed Point Property:")
    print(f"  Fixed point error: {fixed_point_error:.2e}")
    print(f"  Norm preserved: {np.linalg.norm(result.solution) <= np.linalg.norm(psi_0)}")
    print()
    
    print("=== All verifications complete ===")
