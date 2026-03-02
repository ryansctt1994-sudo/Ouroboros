"""
repl_agent_scaffold.py – Execute-critique-refine agentic REPL loop.

``ReplAgentScaffold`` provides a minimal but extensible REPL (Read-Eval-
Print Loop) that lets a reasoning agent iteratively:

1. **Execute** a Python or DSL program against ARC-AGI-2 training pairs.
2. **Critique** the output (exact-match check + optional LLM critique).
3. **Refine** the program by applying a patch suggested by the agent.

The scaffold integrates with ``VeritasAegisLogger`` / ``Chronicle`` so
every execution and refinement is immutably recorded.
"""

from __future__ import annotations

import textwrap
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as _np

from .dsl_primitives import _as_grid, _to_numpy, Grid
from .fitness_evaluator import FitnessEvaluator, FitnessScore, _default_executor

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ReplSession:
    """State of a single REPL refinement session.

    Attributes
    ----------
    session_id:
        Unique identifier for this session.
    program_code:
        Current Python source of the program under refinement.
    dsl_ops:
        Alternative DSL-op representation (mutually exclusive with
        *program_code*; both may be provided).
    history:
        Ordered list of ``{"step", "code", "score", "critique", "patch"}``
        records.
    best_score:
        Highest ``FitnessScore.total`` seen so far.
    best_code:
        Source code that produced *best_score*.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    program_code: str = ""
    dsl_ops: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    best_score: float = float("-inf")
    best_code: str = ""


# ---------------------------------------------------------------------------
# Null bridges
# ---------------------------------------------------------------------------

class _NullLogger:
    def log(self, *args: Any, **kwargs: Any) -> None:
        pass

    def record(self, *args: Any, **kwargs: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# ReplAgentScaffold
# ---------------------------------------------------------------------------

CritiqueProvider = Callable[[str, FitnessScore], str]
PatchProvider = Callable[[str, str], str]  # (code, critique) -> patched_code


class ReplAgentScaffold:
    """Agentic REPL scaffold for iterative program refinement.

    Parameters
    ----------
    fitness_evaluator:
        A ``FitnessEvaluator`` instance used to score programs.
    critique_provider:
        Optional callable ``(code, score) -> critique_text`` that
        generates a natural-language critique.  Defaults to a simple
        rule-based heuristic.
    patch_provider:
        Optional callable ``(code, critique) -> patched_code`` that
        proposes a code patch given a critique.  Defaults to the
        identity (no change).
    max_steps:
        Maximum refinement iterations per session.  Default ``10``.
    veritas_logger:
        Optional ``VeritasAegisLogger``-compatible logger.
    chronicle:
        Optional ``Chronicle``-compatible append-only log.
    """

    def __init__(
        self,
        fitness_evaluator: FitnessEvaluator,
        critique_provider: Optional[CritiqueProvider] = None,
        patch_provider: Optional[PatchProvider] = None,
        max_steps: int = 10,
        veritas_logger: Optional[Any] = None,
        chronicle: Optional[Any] = None,
    ) -> None:
        self._evaluator = fitness_evaluator
        self._critique = critique_provider or _default_critique
        self._patch = patch_provider or _identity_patch
        self.max_steps = max_steps
        self._logger = veritas_logger or _NullLogger()
        self._chronicle = chronicle or _NullLogger()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        initial_code: str = "",
        initial_dsl_ops: Optional[List[Dict[str, Any]]] = None,
        session: Optional[ReplSession] = None,
    ) -> ReplSession:
        """Run the execute-critique-refine loop.

        Parameters
        ----------
        initial_code:
            Starting Python program source.
        initial_dsl_ops:
            Starting DSL-op sequence (used when *initial_code* is empty).
        session:
            Optional existing session to continue.  When *None* a new
            ``ReplSession`` is created.

        Returns
        -------
        ReplSession
            The session after at most ``max_steps`` refinement iterations,
            containing the best code found.
        """
        if session is None:
            session = ReplSession(
                program_code=initial_code,
                dsl_ops=initial_dsl_ops or [],
            )

        self._logger.log(
            "repl.session.start",
            {"session_id": session.session_id, "timestamp": time.time()},
        )

        for step in range(1, self.max_steps + 1):
            # 1. Execute & score
            score, exec_error = self._execute_and_score(session)

            # 2. Critique
            critique = self._critique(session.program_code, score)

            # 3. Record step
            record: Dict[str, Any] = {
                "step": step,
                "code": session.program_code,
                "dsl_ops": list(session.dsl_ops),
                "score": score.total,
                "exact_match": score.exact_match,
                "critique": critique,
                "exec_error": exec_error,
                "timestamp": time.time(),
            }
            session.history.append(record)
            self._chronicle.record({"type": "repl_step", "data": record})
            self._logger.log("repl.step", record)

            # 4. Update best
            if score.total > session.best_score:
                session.best_score = score.total
                session.best_code = session.program_code

            # 5. Stop if perfect score
            if score.exact_match >= 1.0:
                self._logger.log(
                    "repl.session.solved",
                    {"session_id": session.session_id, "step": step},
                )
                break

            # 6. Refine
            patched = self._patch(session.program_code, critique)
            if patched != session.program_code:
                session.program_code = patched
            else:
                # No useful patch; terminate early.
                break

        self._logger.log(
            "repl.session.end",
            {
                "session_id": session.session_id,
                "best_score": session.best_score,
                "steps": len(session.history),
                "timestamp": time.time(),
            },
        )
        return session

    def execute_code(
        self,
        code: str,
        input_grid: _np.ndarray,
    ) -> Tuple[Optional[_np.ndarray], Optional[str]]:
        """Execute *code* against *input_grid* in a sandboxed namespace.

        The code must define a function ``solve(grid)`` that accepts and
        returns a 2-D integer array.

        Returns
        -------
        Tuple[Optional[ndarray], Optional[str]]
            ``(output_grid, error_message)`` where *error_message* is
            ``None`` on success.
        """
        namespace: Dict[str, Any] = {
            "__builtins__": {
                "range": range,
                "len": len,
                "list": list,
                "int": int,
                "enumerate": enumerate,
                "zip": zip,
                "min": min,
                "max": max,
                "abs": abs,
                "print": print,
            }
        }
        try:
            import numpy as np

            namespace["np"] = np
            # Also expose DSL primitives
            from . import dsl_primitives as _prim

            namespace["dsl"] = _prim

            exec(textwrap.dedent(code), namespace)  # noqa: S102
            solve_fn = namespace.get("solve")
            if solve_fn is None:
                return None, "No 'solve' function defined in code."
            result = solve_fn(_np.array(input_grid))
            return _np.asarray(result, dtype=_np.int32), None
        except Exception:  # noqa: BLE001
            return None, traceback.format_exc()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_and_score(
        self, session: ReplSession
    ) -> Tuple[FitnessScore, Optional[str]]:
        """Run the evaluator using the session's current program."""
        # Build a minimal Candidate proxy for the evaluator.
        candidate = _CandidateProxy(
            program_id=session.session_id,
            code=session.program_code,
            dsl_ops=session.dsl_ops,
        )
        try:
            score = self._evaluator.evaluate(candidate)
            return score, None
        except Exception:  # noqa: BLE001
            return FitnessScore(), traceback.format_exc()


# ---------------------------------------------------------------------------
# Proxy / helpers
# ---------------------------------------------------------------------------

class _CandidateProxy:
    """Minimal Candidate-like object for the evaluator."""

    def __init__(
        self,
        program_id: str,
        code: str,
        dsl_ops: List[Dict[str, Any]],
    ) -> None:
        self.program_id = program_id
        self.code = code
        self.dsl_ops = dsl_ops
        self.fitness: Optional[float] = None


def _default_critique(code: str, score: FitnessScore) -> str:
    """Rule-based critique based on *score*."""
    lines = []
    if score.exact_match < 1.0:
        n_failed = sum(
            1 for d in score.details if not d.get("match", False)
        )
        lines.append(
            f"Program fails on {n_failed}/{len(score.details)} training pairs."
        )
    if score.mdl_penalty > 0.5:
        lines.append(
            "Program is complex; consider simplifying the DSL op sequence."
        )
    if score.exact_match >= 1.0:
        lines.append("All training pairs solved exactly.")
    return " ".join(lines) if lines else "No issues detected."


def _identity_patch(code: str, critique: str) -> str:
    """Return *code* unchanged (no-op default patch provider)."""
    return code
