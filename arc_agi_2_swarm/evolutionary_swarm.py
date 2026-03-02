"""
evolutionary_swarm.py – LLM-guided evolutionary search over ARC-AGI-2
program space.

The ``EvolutionarySwarm`` maintains a fixed-size population of
``Candidate`` programs.  Each generation it:

1. Evaluates fitness via ``FitnessEvaluator``.
2. Selects elite survivors (truncation selection).
3. Produces offspring via *mutation* (single-operation substitution) and
   *crossover* (splice two parent programs).
4. Optionally requests LLM-guided mutations through a pluggable
   ``LLMMutationProvider`` callable.
5. Logs every generation to ``VeritasAegisLogger`` / ``Chronicle`` when
   either bridge is supplied.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .dsl_primitives import Grid

# ---------------------------------------------------------------------------
# Logging bridges (optional dependencies – accept any object with the
# expected interface so the swarm degrades gracefully when not wired up).
# ---------------------------------------------------------------------------

class _NullLogger:
    """No-op stand-in used when a real logger is not supplied."""

    def log(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        pass

    def record(self, *args: Any, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    """A single candidate program in the population.

    Attributes
    ----------
    program_id:
        Unique identifier for this candidate (auto-generated UUID).
    code:
        Source code of the program as a Python string.
    dsl_ops:
        Ordered list of DSL operation descriptors, e.g.
        ``[{"op": "rotate_grid", "args": {"k": 1}}, ...]``.
    fitness:
        Fitness score assigned by ``FitnessEvaluator``
        (higher is better; ``None`` if not yet evaluated).
    generation:
        Generation index in which this candidate was created.
    parent_ids:
        IDs of parent candidates (empty for seed candidates).
    metadata:
        Arbitrary key/value metadata (provenance, mutation history …).
    """

    program_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    code: str = ""
    dsl_ops: List[Dict[str, Any]] = field(default_factory=list)
    fitness: Optional[float] = None
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        """Return a stable SHA-256 hex digest of the program's DSL ops."""
        payload = json.dumps(self.dsl_ops, sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------------------
# EvolutionarySwarm
# ---------------------------------------------------------------------------

# Type alias for a function that produces one mutated Candidate from a parent.
LLMMutationProvider = Callable[[Candidate], Candidate]

# Type alias for a function (grid, ops) -> grid that executes DSL ops.
ProgramExecutor = Callable[[Grid, List[Dict[str, Any]]], Grid]


class EvolutionarySwarm:
    """Manages a population of candidate programs and drives evolution.

    Parameters
    ----------
    population_size:
        Maximum number of candidates kept between generations.
    elite_fraction:
        Fraction of top-scoring candidates that survive unchanged.
    mutation_rate:
        Probability that a single offspring is produced via mutation
        (vs. crossover).
    seed_candidates:
        Initial candidate population.  If *None* or shorter than
        ``population_size``, the remainder is filled with empty candidates.
    llm_mutation_provider:
        Optional callable ``(Candidate) -> Candidate`` that uses an LLM to
        suggest a mutation.  When *None*, a random DSL-op substitution is
        used instead.
    veritas_logger:
        Logger implementing ``.log(event, payload)`` – e.g. a
        ``VeritasAegisLogger`` instance.
    chronicle:
        Append-only evidence log implementing ``.record(entry)`` – e.g. a
        ``Chronicle`` instance.
    rng_seed:
        Optional random seed for reproducibility.
    """

    # Built-in set of DSL operations available for random mutation.
    _BUILTIN_OPS: List[str] = [
        "identity",
        "rotate_grid",
        "flip_grid",
        "apply_symmetry",
        "recolor",
        "fill_region",
        "extract_objects",
    ]

    def __init__(
        self,
        population_size: int = 50,
        elite_fraction: float = 0.2,
        mutation_rate: float = 0.7,
        seed_candidates: Optional[List[Candidate]] = None,
        llm_mutation_provider: Optional[LLMMutationProvider] = None,
        veritas_logger: Optional[Any] = None,
        chronicle: Optional[Any] = None,
        rng_seed: Optional[int] = None,
    ) -> None:
        if not 0.0 < elite_fraction < 1.0:
            raise ValueError("elite_fraction must be in (0, 1)")
        if not 0.0 <= mutation_rate <= 1.0:
            raise ValueError("mutation_rate must be in [0, 1]")

        self.population_size = population_size
        self.elite_fraction = elite_fraction
        self.mutation_rate = mutation_rate
        self.llm_mutation_provider = llm_mutation_provider
        self.veritas_logger = veritas_logger or _NullLogger()
        self.chronicle = chronicle or _NullLogger()
        self._rng = random.Random(rng_seed)
        self.generation: int = 0

        # Initialise population
        self.population: List[Candidate] = list(seed_candidates or [])
        while len(self.population) < self.population_size:
            self.population.append(Candidate(generation=0))

        self.veritas_logger.log(
            "swarm.init",
            {
                "population_size": self.population_size,
                "elite_fraction": self.elite_fraction,
                "mutation_rate": self.mutation_rate,
                "timestamp": time.time(),
            },
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evolve(
        self,
        fitness_fn: Callable[[Candidate], float],
        num_generations: int = 10,
    ) -> Candidate:
        """Run the evolutionary loop for *num_generations* steps.

        Parameters
        ----------
        fitness_fn:
            Callable that accepts a ``Candidate`` and returns a scalar
            fitness (higher = better).
        num_generations:
            Number of generational steps to perform.

        Returns
        -------
        Candidate
            The best candidate found across all generations.
        """
        best: Optional[Candidate] = None
        for _ in range(num_generations):
            best = self._step(fitness_fn, best)
        return best  # type: ignore[return-value]

    def best_candidate(self) -> Optional[Candidate]:
        """Return the population member with the highest fitness."""
        scored = [c for c in self.population if c.fitness is not None]
        if not scored:
            return None
        return max(scored, key=lambda c: c.fitness)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _step(
        self,
        fitness_fn: Callable[[Candidate], float],
        prev_best: Optional[Candidate],
    ) -> Candidate:
        """Perform one evolutionary generation."""
        self.generation += 1

        # 1. Evaluate fitness for unevaluated candidates.
        for candidate in self.population:
            if candidate.fitness is None:
                candidate.fitness = fitness_fn(candidate)

        # 2. Sort by fitness (descending).
        self.population.sort(key=lambda c: c.fitness or 0.0, reverse=True)

        # 3. Identify current best.
        current_best = self.population[0]
        if prev_best is None or (current_best.fitness or 0.0) > (
            prev_best.fitness or 0.0
        ):
            prev_best = copy.deepcopy(current_best)

        # 4. Log generation stats.
        gen_stats = {
            "generation": self.generation,
            "best_fitness": current_best.fitness,
            "mean_fitness": sum(c.fitness or 0.0 for c in self.population)
            / len(self.population),
            "timestamp": time.time(),
        }
        self.veritas_logger.log("swarm.generation", gen_stats)
        self.chronicle.record(
            {"type": "generation", "data": gen_stats}
        )

        # 5. Truncation selection: keep elite.
        n_elite = max(1, int(self.elite_fraction * self.population_size))
        elites: List[Candidate] = self.population[:n_elite]

        # 6. Produce offspring to fill remaining slots.
        offspring: List[Candidate] = []
        while len(offspring) < self.population_size - n_elite:
            if self._rng.random() < self.mutation_rate:
                parent = self._rng.choice(elites)
                child = self._mutate(parent)
            else:
                sample = self._rng.sample(elites, min(2, len(elites)))
                p1 = sample[0]
                p2 = sample[1] if len(sample) > 1 else sample[0]
                child = self._crossover(p1, p2)
            child.generation = self.generation
            offspring.append(child)

        self.population = elites + offspring
        return prev_best  # type: ignore[return-value]

    def _mutate(self, parent: Candidate) -> Candidate:
        """Return a new Candidate derived by mutating *parent*."""
        if self.llm_mutation_provider is not None:
            try:
                return self.llm_mutation_provider(parent)
            except Exception:  # noqa: BLE001
                pass  # Fall through to built-in mutation

        child = copy.deepcopy(parent)
        child.program_id = str(uuid.uuid4())
        child.parent_ids = [parent.program_id]
        child.fitness = None

        if child.dsl_ops:
            # Replace a random operation with a different one.
            idx = self._rng.randrange(len(child.dsl_ops))
            new_op = self._rng.choice(
                [o for o in self._BUILTIN_OPS if o != child.dsl_ops[idx].get("op")]
                or self._BUILTIN_OPS
            )
            child.dsl_ops[idx] = {"op": new_op, "args": {}}
        else:
            # Inject a random operation.
            op = self._rng.choice(self._BUILTIN_OPS)
            child.dsl_ops = [{"op": op, "args": {}}]

        child.metadata["mutation"] = "op_substitution"
        return child

    def _crossover(self, p1: Candidate, p2: Candidate) -> Candidate:
        """Return a child produced by splicing DSL ops from *p1* and *p2*."""
        child = Candidate(
            parent_ids=[p1.program_id, p2.program_id],
            fitness=None,
        )
        ops1 = p1.dsl_ops
        ops2 = p2.dsl_ops

        if not ops1:
            child.dsl_ops = copy.deepcopy(ops2)
        elif not ops2:
            child.dsl_ops = copy.deepcopy(ops1)
        else:
            # Single-point crossover at a random splice point.
            cut1 = self._rng.randint(0, len(ops1))
            cut2 = self._rng.randint(0, len(ops2))
            child.dsl_ops = (
                copy.deepcopy(ops1[:cut1]) + copy.deepcopy(ops2[cut2:])
            )

        child.metadata["mutation"] = "crossover"
        return child
