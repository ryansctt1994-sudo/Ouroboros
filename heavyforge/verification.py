from __future__ import annotations

import base64
from copy import deepcopy

from cryptography.exceptions import InvalidSignature

from .contracts import SealedJudgeReceipt, VerificationReceipt
from .enums import VerificationResult
from .receipts import canonical_json_bytes
from .registry import TrustedVerifierRegistry


def verification_payload_for_signature(receipt: VerificationReceipt) -> dict:
    payload = deepcopy(receipt.model_dump(mode="json"))
    payload["signature"] = ""
    return payload


def verify_verification_signature(
    verification_receipt: VerificationReceipt,
    public_key,
) -> bool:
    try:
        signature = base64.b64decode(verification_receipt.signature)
        public_key.verify(
            signature,
            canonical_json_bytes(verification_payload_for_signature(verification_receipt)),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def has_valid_verification_receipt(
    judge_receipt: SealedJudgeReceipt,
    verification_receipt: VerificationReceipt | None,
    trusted_registry: TrustedVerifierRegistry,
    ledger_sequence: int,
) -> bool:
    if verification_receipt is None:
        return False

    if judge_receipt.seal is None:
        return False

    if verification_receipt.target_run_id != judge_receipt.run_id:
        return False

    if verification_receipt.target_receipt_hash != judge_receipt.seal.receipt_hash:
        return False

    if verification_receipt.verification_result != VerificationResult.PASSED:
        return False

    if not trusted_registry.is_method_approved(
        verifier_id=verification_receipt.verifier_id,
        method=verification_receipt.verification_method,
    ):
        return False

    public_key = trusted_registry.resolve_public_key(
        verifier_id=verification_receipt.verifier_id,
        key_id=verification_receipt.verifier_public_key_id,
        ledger_sequence=ledger_sequence,
    )
    if public_key is None:
        return False

    return verify_verification_signature(
        verification_receipt=verification_receipt,
        public_key=public_key,
    )
