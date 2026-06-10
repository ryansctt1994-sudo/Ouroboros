from __future__ import annotations

from tests.test_verification_receipt_binding import (
    registry_for,
    sample_sealed_receipt,
    signed_verification_receipt,
)

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from heavyforge.contracts import WorkerOutput
from heavyforge.enums import AuthorityLevel, FailureType
from heavyforge.promotion import can_promote_to_replay_verified, promoted_authority_level


def test_valid_verification_receipt_promotes_to_replay_verified():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    verification = signed_verification_receipt(private_key, target)

    assert can_promote_to_replay_verified(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is True

    assert promoted_authority_level(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) == AuthorityLevel.REPLAY_VERIFIED


def test_missing_verification_receipt_cannot_promote():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()

    assert can_promote_to_replay_verified(
        judge_receipt=target,
        verification_receipt=None,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is False

    assert promoted_authority_level(
        judge_receipt=target,
        verification_receipt=None,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) == AuthorityLevel.EVIDENCE_SUPPORTED


def test_failed_worker_blocks_promotion_even_with_valid_verification():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    target.agents = [
        WorkerOutput(
            agent_name="builder",
            failed=True,
            failure_type=FailureType.TIMEOUT,
            error_msg="timeout",
        )
    ]
    verification = signed_verification_receipt(private_key, target)

    assert can_promote_to_replay_verified(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is False


def test_judge_repair_blocks_promotion_even_with_valid_verification():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    target.judge_repaired = True
    verification = signed_verification_receipt(private_key, target)

    assert can_promote_to_replay_verified(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is False
