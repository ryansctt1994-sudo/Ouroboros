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
    min_judge_confidence: float = 0.65,
) -> AuthorityLevel:
    """Calculate base authority deterministically from run state.

    This function intentionally cannot emit REPLAY_VERIFIED. Replay promotion is
    handled by heavyforge.promotion after VerificationReceipt validation.
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

    if judge_decision.evidence_notes:
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


def run_integrity_allows_replay_promotion(receipt) -> bool:
    """Return whether a sealed run is clean enough for replay promotion."""

    if receipt.authority_level != AuthorityLevel.EVIDENCE_SUPPORTED:
        return False

    if receipt.judge_failed or receipt.judge_repaired:
        return False

    if receipt.unresolved_disputes:
        # build_receipt records "No failed agents" / "No repaired agents" notes
        # as disputes for operator visibility. These exact benign notes do not
        # block promotion; all other unresolved disputes do.
        benign = {"No failed agents.", "No repaired agents."}
        if any(dispute not in benign for dispute in receipt.unresolved_disputes):
            return False

    if receipt.missing_evidence:
        return False

    if any(agent.failed or agent.repaired for agent in receipt.agents):
        return False

    return True
