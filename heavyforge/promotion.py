from __future__ import annotations

from .authority import run_integrity_allows_replay_promotion
from .contracts import SealedJudgeReceipt, VerificationReceipt
from .enums import AuthorityLevel
from .registry import TrustedVerifierRegistry
from .verification import has_valid_verification_receipt


def can_promote_to_replay_verified(
    judge_receipt: SealedJudgeReceipt,
    verification_receipt: VerificationReceipt | None,
    trusted_registry: TrustedVerifierRegistry,
    ledger_sequence: int,
) -> bool:
    """Return whether a sealed receipt can be promoted to REPLAY_VERIFIED.

    This is the only replay-promotion gate. No caller-facing boolean can promote
    a receipt without a registry-trusted, hash-bound, signed VerificationReceipt.
    """

    if not run_integrity_allows_replay_promotion(judge_receipt):
        return False

    return has_valid_verification_receipt(
        judge_receipt=judge_receipt,
        verification_receipt=verification_receipt,
        trusted_registry=trusted_registry,
        ledger_sequence=ledger_sequence,
    )


def promoted_authority_level(
    judge_receipt: SealedJudgeReceipt,
    verification_receipt: VerificationReceipt | None,
    trusted_registry: TrustedVerifierRegistry,
    ledger_sequence: int,
) -> AuthorityLevel:
    if can_promote_to_replay_verified(
        judge_receipt=judge_receipt,
        verification_receipt=verification_receipt,
        trusted_registry=trusted_registry,
        ledger_sequence=ledger_sequence,
    ):
        return AuthorityLevel.REPLAY_VERIFIED

    return judge_receipt.authority_level
