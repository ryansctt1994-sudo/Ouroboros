"""
arc_agi_3 — ARC-AGI-3 Interactive Reasoning Environment package.

Public API surface:

    InteractiveReasoningEnv  — procedurally generated reasoning environment
    EngramObservatory        — asynchronous TensorBoard telemetry daemon
    FGRPO                    — Focal Group Relative Policy Optimisation
    EMPG                     — Entropy-Modulated Policy Gradients
"""

from .engram_observatory import EngramObservatory
from .interactive_reasoning_env import InteractiveReasoningEnv, EnvStep
from .policy_gradients import EMPG, FGRPO

__all__ = [
    "InteractiveReasoningEnv",
    "EnvStep",
    "EngramObservatory",
    "FGRPO",
    "EMPG",
]
