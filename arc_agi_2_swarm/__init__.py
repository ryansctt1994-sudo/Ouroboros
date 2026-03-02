"""
arc_agi_2_swarm – Phase 1 Evolutionary + DSL hybrid swarm for ARC-AGI-2.

Public API surface:
    dsl_primitives        – NumPy/CuPy-optimised grid transformation library
    evolutionary_swarm    – LLM-guided evolutionary search over program space
    fitness_evaluator     – Exact-match + MDL + KL-divergence fitness scoring
    repl_agent_scaffold   – Execute-critique-refine agentic REPL loop
"""

from .dsl_primitives import (
    identity,
    rotate_grid,
    flip_grid,
    apply_symmetry,
    recolor,
    fill_region,
    extract_objects,
)
from .evolutionary_swarm import EvolutionarySwarm, Candidate
from .fitness_evaluator import FitnessEvaluator, FitnessScore
from .repl_agent_scaffold import ReplAgentScaffold

__all__ = [
    # dsl_primitives
    "identity",
    "rotate_grid",
    "flip_grid",
    "apply_symmetry",
    "recolor",
    "fill_region",
    "extract_objects",
    # evolutionary_swarm
    "EvolutionarySwarm",
    "Candidate",
    # fitness_evaluator
    "FitnessEvaluator",
    "FitnessScore",
    # repl_agent_scaffold
    "ReplAgentScaffold",
]
