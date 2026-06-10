from __future__ import annotations

import base64
from datetime import UTC, datetime

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from heavyforge.contracts import SealedJudgeReceipt, VerificationReceipt, WorkerOutput
from heavyforge.enums import AuthorityLevel, VerificationResult
from heavyforge.receipts import canonical_json_bytes, seal_receipt_unsigned_phase1
from heavyforge.registry import StaticVerifierRegistry, VerifierRecord
from heavyforge.verification import has_valid_verification_receipt, verification_payload_for_signature


def sample_sealed_receipt() -> SealedJudgeReceipt:
    receipt = SealedJudgeReceipt(
        run_id="run_verified",
        user_prompt="test",
        consensus=["ok"],
        unresolved_disputes=[],
        missing_evidence=[],
        strongest_answer="answer",
        authority_level=AuthorityLevel.EVIDENCE_SUPPORTED,
        timestamp=datetime.now(UTC).isoformat(),
        agents=[WorkerOutput(agent_name="direct_solver", answer="ok", confidence=0.8)],
    )
    return seal_receipt_unsigned_phase1(receipt)


def signed_verification_receipt(
    private_key: Ed25519PrivateKey,
    target: SealedJudgeReceipt,
    method: str = "REPLAY_FULL_KERNEL_V1",
    target_hash_override: str | None = None,
    result: VerificationResult = VerificationResult.PASSED,
) -> VerificationReceipt:
    assert target.seal is not None
    receipt = VerificationReceipt(
        verification_id="ver_001",
        target_run_id=target.run_id,
        target_receipt_hash=target_hash_override or target.seal.receipt_hash,
        verifier_id="local_replay_service",
        verifier_public_key_id="local_key_001",
        verification_result=result,
        verification_method=method,
        replay_artifacts_hash=None,
        timestamp=datetime.now(UTC).isoformat(),
        signature="",
    )
    signature = private_key.sign(canonical_json_bytes(verification_payload_for_signature(receipt)))
    receipt.signature = base64.b64encode(signature).decode("ascii")
    return receipt


def registry_for(private_key: Ed25519PrivateKey, revoked_at_sequence: int | None = None) -> StaticVerifierRegistry:
    return StaticVerifierRegistry(
        verifiers=(
            VerifierRecord(
                verifier_id="local_replay_service",
                public_key_id="local_key_001",
                public_key=private_key.public_key(),
                status="ACTIVE",
                not_before_sequence=0,
                revoked_at_sequence=revoked_at_sequence,
                approved_methods=("REPLAY_FULL_KERNEL_V1",),
            ),
        )
    )


def test_valid_verification_receipt_binds_to_sealed_receipt():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    verification = signed_verification_receipt(private_key, target)

    assert has_valid_verification_receipt(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is True


def test_verification_receipt_wrong_hash_rejected():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    verification = signed_verification_receipt(
        private_key,
        target,
        target_hash_override="0" * 64,
    )

    assert has_valid_verification_receipt(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is False


def test_unapproved_verification_method_rejected():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    verification = signed_verification_receipt(
        private_key,
        target,
        method="UNAPPROVED_METHOD",
    )

    assert has_valid_verification_receipt(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key),
        ledger_sequence=1,
    ) is False


def test_revoked_verifier_rejected():
    private_key = Ed25519PrivateKey.generate()
    target = sample_sealed_receipt()
    verification = signed_verification_receipt(private_key, target)

    assert has_valid_verification_receipt(
        judge_receipt=target,
        verification_receipt=verification,
        trusted_registry=registry_for(private_key, revoked_at_sequence=1),
        ledger_sequence=1,
    ) is False
