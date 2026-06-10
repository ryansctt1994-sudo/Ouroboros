from __future__ import annotations

from .contracts import JudgeDecision, WorkerOutput
from .enums import AuthorityLevel


AUTHORITY_RANK = {
    AuthorityLevel.DRAFT: 0,
    AuthorityLevel.PLAUSIBLE: 1,
    AuthorityLevel.EVIDENCE_SUPPORTED: 2,
    AuthorityLevel.REPLAY_VERIFIED: 3,
}


def min_authority(a: AuthorityLevel, b: AuthorityLevel) -> AuthorityLevel:
    return a if AUTHORITY_RANK[a] <= AUTHORITY_RANK[b] else b


def calculate_authority_level(
    worker_results: list[WorkerOutput],
    judge_decision: JudgeDecision | None,
    judge_failed: bool,
    judge_repaired: bool,
    replay_verified: bool = False,
    min_judge_confidence: float = 0.65,
) -> AuthorityLevel:
    """Calculate authority deterministically from system state.

    The Judge never assigns authority. External replay may enable
    REPLAY_VERIFIED only if all lower integrity gates are clean.
    """

    if judge_failed or judge_decision is None:
        return AuthorityLevel.DRAFT

    if judge_repaired:
        return AuthorityLevel.DRAFT

    if not worker_results:
        return AuthorityLevel.DRAFT

    if any(worker.failed for worker in worker_results):
        return AuthorityLevel.DRAFT

    if not judge_decision.strongest_answer.strip():
        return AuthorityLevel.DRAFT

    if judge_decision.judge_confidence < min_judge_confidence:
        return AuthorityLevel.DRAFT

    if replay_verified:
        level = AuthorityLevel.REPLAY_VERIFIED
    elif judge_decision.evidence_notes:
        level = AuthorityLevel.EVIDENCE_SUPPORTED
    else:
        level = AuthorityLevel.PLAUSIBLE

    if any(worker.repaired for worker in worker_results):
        level = min_authority(level, AuthorityLevel.PLAUSIBLE)

    if judge_decision.unresolved_disputes:
        level = min_authority(level, AuthorityLevel.PLAUSIBLE)

    if judge_decision.missing_evidence:
        level = min_authority(level, AuthorityLevel.PLAUSIBLE)

    if not judge_decision.evidence_notes:
        level = min_authority(level, AuthorityLevel.PLAUSIBLE)

    return level
