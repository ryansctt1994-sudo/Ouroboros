"""
ABRAXIS — Cathedral-OS integration package for AIOSPANDORA/Ouroboros.

Sub-packages
------------
phase_h  — Multi-user WebSocket voice-to-gnosis dashboard
phase_i  — Autonomous nodes: self-healing, spore factory, governance
"""
from .eden_ecs_bridge import EdenEcsBridge, create_abraxis_world

__all__ = ["EdenEcsBridge", "create_abraxis_world"]
