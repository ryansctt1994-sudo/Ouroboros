"""GGCC Crucible Kinetic Synthesis - Phase 3 Modular Systems.

This package contains advanced modular systems for Phase 3 activation
within the GGCC (Guardian Gate Constellation Control) lattice.

Modules:
    - NodeBalancer v2: Φ-Aware Memoization
    - GradientEngine v2: Chebyshev-Proxied Gradient Management
    - SymmetryMonitor v2: Auto-drift Detection and Kalman-backed Filters
    - TransientManager v2: Epoch-Driven Cleanup
    - Coupling Interface: Static/Dynamic Impedance Matching
    - GGCC Phase 3 Controller: Modular System Coordinator

All modules are designed for zero-cascade deployment impact with
monitored fitness control and AMUSED-tagged logging.

Round 3 of the GGCC Crucible Kinetic Synthesis phase.
"""

from .node_balancer import NodeBalancerV2
from .gradient_engine import GradientEngineV2
from .symmetry_monitor import SymmetryMonitorV2
from .transient_manager import TransientManagerV2
from .coupling_interface import CouplingInterface
from .controller import GGCCPhase3Controller

__version__ = "3.0.0"
__phase__ = "Phase 3: GGCC Crucible Kinetic Synthesis - Round 3"
__all__ = [
    "NodeBalancerV2",
    "GradientEngineV2",
    "SymmetryMonitorV2",
    "TransientManagerV2",
    "CouplingInterface",
    "GGCCPhase3Controller",
]
