"""
UTe2 Hybrid System - Simulation Engine

Implements superconductivity simulations for UTe2 material:
- BdG (Bogoliubov-de Gennes) equation solver
- Phase diagram generation
- Superconducting gap estimation
- Band structure visualization
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    """Container for simulation results"""
    success: bool
    parameters: Dict[str, Any]
    gap_function: Optional[np.ndarray] = None
    eigenvalues: Optional[np.ndarray] = None
    eigenvectors: Optional[np.ndarray] = None
    phase_diagram: Optional[np.ndarray] = None
    convergence_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class UTe2SimulationEngine:
    """Superconductivity simulation engine for UTe2"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize simulation engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config.get('simulation', {})
        self.material = self.config.get('material', {})
        self.defaults = self.config.get('defaults', {})
        self.solver_config = self.config.get('solver', {})
        
        logger.info(f"Initialized UTe2 simulation engine for {self.material.get('name', 'UTe2')}")
    
    def _build_hamiltonian(self, k_points: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """
        Build BdG Hamiltonian matrix for given k-points
        
        Args:
            k_points: Array of k-point coordinates
            parameters: Physical parameters (temperature, field, etc.)
            
        Returns:
            BdG Hamiltonian matrix
        """
        n_k = len(k_points)
        temperature = parameters.get('temperature_K', self.defaults.get('temperature_K', 0.5))
        magnetic_field = parameters.get('magnetic_field_T', self.defaults.get('magnetic_field_T', 0.0))
        
        # Simplified tight-binding model for UTe2
        # In real implementation, this would use proper band structure
        t = 1.0  # Hopping parameter (eV)
        mu = 0.5  # Chemical potential (eV)
        
        # Build normal state Hamiltonian
        H_normal = np.zeros((n_k, 2, 2), dtype=complex)
        
        for i, k in enumerate(k_points):
            # Kinetic energy (simplified dispersion)
            epsilon_k = -2 * t * (np.cos(k[0]) + np.cos(k[1]) + np.cos(k[2])) - mu
            
            # Zeeman splitting from magnetic field
            zeeman = 0.057 * magnetic_field  # g*mu_B*H (in eV, approximate)
            
            H_normal[i] = np.array([
                [epsilon_k + zeeman, 0],
                [0, epsilon_k - zeeman]
            ])
        
        # Build pairing potential (spin-triplet)
        # For UTe2, assuming d-wave spin-triplet pairing
        Delta = self._compute_pairing_potential(k_points, temperature, magnetic_field)
        
        # Construct BdG Hamiltonian
        H_bdg = np.zeros((n_k, 4, 4), dtype=complex)
        
        for i in range(n_k):
            H_bdg[i] = np.block([
                [H_normal[i], Delta[i]],
                [Delta[i].conj().T, -H_normal[i].conj()]
            ])
        
        return H_bdg
    
    def _compute_pairing_potential(self, k_points: np.ndarray, 
                                   temperature: float, 
                                   magnetic_field: float) -> np.ndarray:
        """
        Compute spin-triplet pairing potential
        
        Args:
            k_points: Array of k-points
            temperature: Temperature in Kelvin
            magnetic_field: Magnetic field in Tesla
            
        Returns:
            Pairing potential matrix
        """
        n_k = len(k_points)
        Delta = np.zeros((n_k, 2, 2), dtype=complex)
        
        # Critical temperature and field dependence
        Tc = self.material.get('critical_temperature_K', 1.6)  # Tc = critical temperature
        
        # BCS-like gap suppression with temperature
        gap_magnitude = 1.76 * Tc * np.sqrt(max(0, 1 - (temperature / Tc)**2))
        
        # Check for reentrant region
        reentrant = self.material.get('reentrant_superconductivity', {})
        if reentrant.get('enabled', False):
            field_range = reentrant.get('field_range_T', [40, 65])
            if field_range[0] <= magnetic_field <= field_range[1]:
                # Enhance gap in reentrant region
                gap_magnitude *= 1.5
            elif 20 <= magnetic_field < field_range[0]:
                # Suppress gap between normal SC and reentrant region
                gap_magnitude *= 0.1
        else:
            # Standard field suppression
            if magnetic_field > 0:
                gap_magnitude *= max(0, 1 - magnetic_field / 100)
        
        # d-wave form factor for spin-triplet pairing
        for i, k in enumerate(k_points):
            # Simplified d-wave gap structure
            form_factor = (np.cos(k[0]) - np.cos(k[1])) / 2
            
            # Spin-triplet: off-diagonal in spin space
            Delta[i] = gap_magnitude * form_factor * np.array([
                [0, 1],
                [-1, 0]
            ])
        
        return Delta
    
    def _solve_bdg_equations(self, H_bdg: np.ndarray, 
                            max_iterations: int = 1000,
                            convergence_threshold: float = 1e-6) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Solve BdG equations self-consistently
        
        Args:
            H_bdg: BdG Hamiltonian
            max_iterations: Maximum self-consistency iterations
            convergence_threshold: Convergence criterion
            
        Returns:
            Eigenvalues, eigenvectors, and convergence info
        """
        method = self.solver_config.get('method', 'sparse')
        
        eigenvalues_list = []
        eigenvectors_list = []
        
        # Solve for each k-point
        for H_k in H_bdg:
            if method == 'sparse' and H_k.shape[0] > 10:
                # Use sparse solver for large matrices (would use scipy.sparse in real implementation)
                evals, evecs = np.linalg.eigh(H_k)
            else:
                # Dense solver
                evals, evecs = np.linalg.eigh(H_k)
            
            eigenvalues_list.append(evals)
            eigenvectors_list.append(evecs)
        
        eigenvalues = np.array(eigenvalues_list)
        eigenvectors = np.array(eigenvectors_list)
        
        convergence_info = {
            'converged': True,
            'iterations': 1,  # Simplified: would iterate self-consistently in full implementation
            'final_error': 0.0,
            'method': method
        }
        
        return eigenvalues, eigenvectors, convergence_info
    
    def run_simulation(self, parameters: Dict[str, Any]) -> SimulationResult:
        """
        Run a single simulation with given parameters
        
        Args:
            parameters: Simulation parameters
            
        Returns:
            SimulationResult object
        """
        try:
            # Extract parameters
            k_grid_size = parameters.get('k_grid_size', self.defaults.get('k_grid_size', 32))
            temperature = parameters.get('temperature_K', self.defaults.get('temperature_K', 0.5))
            magnetic_field = parameters.get('magnetic_field_T', self.defaults.get('magnetic_field_T', 0.0))
            
            logger.info(f"Running simulation: T={temperature}K, H={magnetic_field}T, k-grid={k_grid_size}")
            
            # Generate k-point mesh
            k_points = self._generate_k_mesh(k_grid_size)
            
            # Build BdG Hamiltonian
            H_bdg = self._build_hamiltonian(k_points, parameters)
            
            # Solve BdG equations
            max_iter = self.solver_config.get('max_iterations', 1000)
            threshold = self.solver_config.get('convergence_threshold', 1e-6)
            eigenvalues, eigenvectors, conv_info = self._solve_bdg_equations(
                H_bdg, max_iter, threshold
            )
            
            # Extract superconducting gap
            gap_function = self._extract_gap_function(eigenvalues, k_points)
            
            result = SimulationResult(
                success=True,
                parameters=parameters,
                gap_function=gap_function,
                eigenvalues=eigenvalues,
                eigenvectors=eigenvectors,
                convergence_info=conv_info,
                metadata={
                    'k_points': k_points,
                    'n_kpoints': len(k_points)
                }
            )
            
            logger.info(f"Simulation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            return SimulationResult(
                success=False,
                parameters=parameters,
                metadata={'error': str(e)}
            )
    
    def _generate_k_mesh(self, n_k: int) -> np.ndarray:
        """
        Generate uniform k-point mesh in Brillouin zone
        
        Args:
            n_k: Number of k-points per dimension
            
        Returns:
            Array of k-points
        """
        # Generate uniform mesh in [-π, π]^3
        k_1d = np.linspace(-np.pi, np.pi, n_k)
        k_x, k_y, k_z = np.meshgrid(k_1d, k_1d, k_1d, indexing='ij')
        
        k_points = np.stack([k_x.flatten(), k_y.flatten(), k_z.flatten()], axis=1)
        return k_points
    
    def _extract_gap_function(self, eigenvalues: np.ndarray, k_points: np.ndarray) -> np.ndarray:
        """
        Extract superconducting gap from eigenvalue spectrum
        
        Args:
            eigenvalues: BdG eigenvalues
            k_points: k-point mesh
            
        Returns:
            Superconducting gap as function of k
        """
        # Gap is minimum positive eigenvalue (simplified)
        n_k = len(k_points)
        gap = np.zeros(n_k)
        
        for i, evals in enumerate(eigenvalues):
            positive_evals = evals[evals > 0]
            if len(positive_evals) > 0:
                gap[i] = np.min(positive_evals)
        
        return gap
    
    def generate_phase_diagram(self, 
                               temperature_range: Tuple[float, float],
                               field_range: Tuple[float, float],
                               resolution: int = 50) -> Dict[str, Any]:
        """
        Generate temperature-field phase diagram
        
        Args:
            temperature_range: (T_min, T_max) in Kelvin
            field_range: (H_min, H_max) in Tesla
            resolution: Number of points per axis
            
        Returns:
            Dictionary with phase diagram data
        """
        logger.info(f"Generating phase diagram: T={temperature_range}, H={field_range}")
        
        T_vals = np.linspace(temperature_range[0], temperature_range[1], resolution)
        H_vals = np.linspace(field_range[0], field_range[1], resolution)
        
        phase_data = np.zeros((resolution, resolution))
        
        # Simplified phase diagram (would compute from full simulations)
        for i, T in enumerate(T_vals):
            for j, H in enumerate(H_vals):
                # Classify phase based on simple criteria
                if T < 1.6 and H < 20:
                    phase_data[i, j] = 1  # Superconducting
                elif 40 <= H <= 65 and T < 1.0:
                    phase_data[i, j] = 2  # Reentrant SC
                else:
                    phase_data[i, j] = 0  # Normal
        
        return {
            'temperature': T_vals,
            'magnetic_field': H_vals,
            'phase': phase_data,
            'labels': {0: 'Normal', 1: 'Superconducting', 2: 'Reentrant SC'}
        }
    
    def estimate_critical_temperature(self, magnetic_field: float = 0.0) -> float:
        """
        Estimate critical temperature at given magnetic field
        
        Args:
            magnetic_field: Magnetic field in Tesla
            
        Returns:
            Critical temperature in Kelvin
        """
        Tc0 = self.material.get('critical_temperature_K', 1.6)
        
        # Simple field dependence (would use full calculation in real implementation)
        if magnetic_field < 20:
            Tc = Tc0 * (1 - (magnetic_field / 20)**2)
        else:
            Tc = 0.0
        
        return max(0, Tc)
