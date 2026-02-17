"""
ECS System Adapters
===================

Adapters that connect loose systems to the ECS architecture,
enabling validation, monitoring, and integration.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

from .quantum_adapter import QuantumSystemAdapter
from .sync_adapter import SynchronizationSystemAdapter
from .teleport_adapter import TeleportationSystemAdapter

__all__ = [
    "QuantumSystemAdapter",
    "SynchronizationSystemAdapter",
    "TeleportationSystemAdapter",
]
