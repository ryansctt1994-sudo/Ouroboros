"""
Distributed system integration modules.

This package provides cross-repo integration features including:
- Distributed time synchronization
- Latency monitoring
- API version compatibility
- Configuration management
- Failure correlation
"""

from .logical_clock import HybridLogicalClock
from .path_tracker import CriticalPathTracker
from .version_guard import APIVersionGuard
from .config_registry import GlobalConfigRegistry
from .failure_correlator import FailureCorrelator

__all__ = [
    'HybridLogicalClock',
    'CriticalPathTracker',
    'APIVersionGuard',
    'GlobalConfigRegistry',
    'FailureCorrelator',
]
