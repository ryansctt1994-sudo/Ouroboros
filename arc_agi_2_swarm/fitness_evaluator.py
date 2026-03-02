"""
fitness_evaluator.py – Fitness scoring for ARC-AGI-2 candidate programs.

``FitnessEvaluator`` computes a composite fitness score for a
``Candidate`` program consisting of three components:

1. **Exact-match accuracy** – fraction of training pairs where the
   candidate's output matches the target grid exactly.
2. **Simplicity penalty (MDL)** – Minimum Description Length approximation
   penalising longer programs.
3. **KL-divergence guidance** – when a ``LogprobBridge`` is supplied the
   evaluator incorporates :math:`D_{KL}` between the candidate's predicted
   output distribution and the ground-truth one-hot distribution as an
   additional reward signal.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as _np

from .dsl_primitives import Grid, _as_grid, _to_numpy

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

TrainingPair = Tuple[Any, Any]  # (input_grid, output_grid)


# ---------------------------------------------------------------------------
# FitnessScore
# ---------------------------------------------------------------------------

@dataclass
class FitnessScore:
    """Breakdown of a candidate's composite fitness.

    Attributes
    ----------
    total:
        Composite scalar (higher is better).
    exact_match:
        Fraction of training pairs solved exactly (0.0 – 1.0).
    mdl_penalty:
        Non-negative penalty for program complexity (bits).
    kl_bonus:
        Non-negative reward from KL-divergence guidance (0 when no
        ``LogprobBridge`` is provided).
    details:
        Per-pair breakdown ``[{"pair": i, "match": bool}, ...]``.
    """

    total: float = 0.0
    exact_match: float = 0.0
    mdl_penalty: float = 0.0
    kl_bonus: float = 0.0
    details: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# LogprobBridge stub
# ---------------------------------------------------------------------------

class _NullLogprobBridge:
    """No-op bridge used when a real ``LogprobBridge`` is not supplied."""

    def kl_divergence(
        self,
        predicted: Any,
        target: Any,
        **kwargs: Any,
    ) -> float:
        """Return 0 (no KL guidance available)."""
        return 0.0


# ---------------------------------------------------------------------------
# FitnessEvaluator
# ---------------------------------------------------------------------------

class FitnessEvaluator:
    """Evaluate candidate programs on ARC-AGI-2 training pairs.

    Parameters
    ----------
    training_pairs:
        Sequence of ``(input_grid, target_output_grid)`` NumPy arrays.
    mdl_lambda:
        Weight applied to the MDL penalty (larger value → stronger
        preference for short programs).  Default ``0.01``.
    kl_weight:
        Weight applied to the KL-divergence bonus.  Default ``0.1``.
    logprob_bridge:
        Optional ``LogprobBridge`` instance exposing a ``kl_divergence``
        method.  When *None* a no-op bridge is used.
    veritas_logger:
        Optional logger implementing ``.log(event, payload)``
        (e.g. a ``VeritasAegisLogger``).
    chronicle:
        Optional append-only log implementing ``.record(entry)``
        (e.g. a ``Chronicle``).
    program_executor:
        Callable ``(input_grid, dsl_ops) -> output_grid`` that executes a
        candidate's DSL op sequence.  When *None* the ``identity``
        primitive is applied (all outputs equal the input).
    """

    def __init__(
        self,
        training_pairs: Sequence[TrainingPair],
        mdl_lambda: float = 0.01,
        kl_weight: float = 0.1,
        logprob_bridge: Optional[Any] = None,
        veritas_logger: Optional[Any] = None,
        chronicle: Optional[Any] = None,
        program_executor: Optional[Any] = None,
    ) -> None:
        if not training_pairs:
            raise ValueError("training_pairs must not be empty")
        self._pairs: List[Tuple[_np.ndarray, _np.ndarray]] = [
            (_to_numpy(_as_grid(inp)), _to_numpy(_as_grid(tgt)))
            for inp, tgt in training_pairs
        ]
        self.mdl_lambda = mdl_lambda
        self.kl_weight = kl_weight
        self._bridge = logprob_bridge or _NullLogprobBridge()
        self._logger = veritas_logger or _NullLogger()
        self._chronicle = chronicle or _NullLogger()
        self._executor = program_executor or _default_executor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, candidate: Any) -> FitnessScore:
        """Compute a ``FitnessScore`` for *candidate*.

        Parameters
        ----------
        candidate:
            A ``Candidate`` instance from ``evolutionary_swarm``.

        Returns
        -------
        FitnessScore
        """
        t_start = time.time()
        score = FitnessScore()

        # 1. Exact-match accuracy
        n_match = 0
        for i, (inp, tgt) in enumerate(self._pairs):
            try:
                out = _to_numpy(self._executor(inp, candidate.dsl_ops))
                match = _np.array_equal(out, tgt)
            except Exception:  # noqa: BLE001
                match = False
            n_match += int(match)
            score.details.append({"pair": i, "match": match})

        score.exact_match = n_match / len(self._pairs)

        # 2. MDL penalty (bits ≈ number of operations × a constant)
        n_ops = max(1, len(candidate.dsl_ops))
        score.mdl_penalty = self.mdl_lambda * math.log2(n_ops + 1)

        # 3. KL-divergence bonus from LogprobBridge
        kl_total = 0.0
        for i, (inp, tgt) in enumerate(self._pairs):
            try:
                out = _to_numpy(self._executor(inp, candidate.dsl_ops))
                # Flatten both grids to 1-D probability-like distributions.
                kl = self._bridge.kl_divergence(
                    _softmax_flat(out), _softmax_flat(tgt)
                )
                kl_total += max(0.0, float(kl))
            except Exception:  # noqa: BLE001
                kl_total += 0.0

        mean_kl = kl_total / len(self._pairs)
        # Transform: higher KL → lower bonus; bonus in [0, kl_weight].
        score.kl_bonus = self.kl_weight / (1.0 + mean_kl)

        # 4. Composite score (maximise)
        score.total = score.exact_match + score.kl_bonus - score.mdl_penalty

        # 5. Logging
        elapsed = time.time() - t_start
        entry = {
            "candidate_id": getattr(candidate, "program_id", "unknown"),
            "total": score.total,
            "exact_match": score.exact_match,
            "mdl_penalty": score.mdl_penalty,
            "kl_bonus": score.kl_bonus,
            "elapsed_s": elapsed,
        }
        self._logger.log("fitness.evaluate", entry)
        self._chronicle.record({"type": "fitness", "data": entry})

        return score

    def __call__(self, candidate: Any) -> float:
        """Convenience wrapper returning only the total fitness scalar."""
        return self.evaluate(candidate).total


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

class _NullLogger:
    def log(self, *args: Any, **kwargs: Any) -> None:
        pass

    def record(self, *args: Any, **kwargs: Any) -> None:
        pass


def _default_executor(
    grid: _np.ndarray,
    dsl_ops: List[Dict[str, Any]],
) -> _np.ndarray:
    """Execute a list of DSL ops sequentially on *grid*.

    Each op descriptor must have an ``"op"`` key matching a function name
    in :mod:`dsl_primitives`.
    """
    from . import dsl_primitives as _prim

    result = _as_grid(grid)
    for op_desc in dsl_ops:
        op_name = str(op_desc.get("op", "identity"))
        args = dict(op_desc.get("args", {}))
        fn = getattr(_prim, op_name, None)
        if fn is None:
            continue
        result = fn(result, **args)
    return _to_numpy(result)


def _softmax_flat(arr: _np.ndarray) -> _np.ndarray:
    """Return a softmax-normalised flat float64 array from *arr*."""
    flat = arr.astype(_np.float64).ravel()
    flat = flat - flat.max()
    exp = _np.exp(flat)
    s = exp.sum()
    return exp / s if s > 0 else _np.ones_like(exp) / len(exp)
