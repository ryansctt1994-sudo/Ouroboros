"""
Training optimization modules for AIOSPANDORA.

This package provides training enhancements including:
- Convergence detection with phase-aware loss smoothing
- Dynamic tensor memory management
- Fair model orchestration
"""

from .convergence_detector import EnhancedConvergenceV2
from .tensor_warden import DynamicTensorWardenV2
from .model_orchestrator import FairModelOrchestrator

__all__ = [
    'EnhancedConvergenceV2',
    'DynamicTensorWardenV2',
    'FairModelOrchestrator',
]
