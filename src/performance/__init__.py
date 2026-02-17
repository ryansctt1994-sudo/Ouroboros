"""
Performance optimization modules for Ouroboros.

This package provides advanced performance optimizations including:
- Thread management with zombie detection
- Adaptive backpressure management
- GPU memory optimization
"""

from .thread_management import ResourceAwareZombieHunterV2
from .backpressure_manager import AdaptiveBackpressureManagerV2
from .gpu_optimizer import GPUMemoryOptimizer

__all__ = [
    'ResourceAwareZombieHunterV2',
    'AdaptiveBackpressureManagerV2',
    'GPUMemoryOptimizer',
]
