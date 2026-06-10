from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import DiagnosticReceipt, ReceiptSeal, SealedJudgeReceipt


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def receipt_payload_for_hash(receipt: SealedJudgeReceipt) -> dict[str, Any]:
    data = receipt.model_dump(mode="json")
    data["seal"] = None
    return data


def compute_receipt_hash(receipt: SealedJudgeReceipt) -> str:
    return sha256_hex(canonical_json_bytes(receipt_payload_for_hash(receipt)))


def seal_receipt_unsigned_phase1(receipt: SealedJudgeReceipt) -> SealedJudgeReceipt:
    """Create a deterministic unsigned Phase 1 seal.

    Real Ed25519 signing is intentionally deferred to Phase 1C. This still
    freezes the receipt hash semantics for Phase 1A/1B tests.
    """

    receipt_hash = compute_receipt_hash(receipt)
    receipt.seal = ReceiptSeal(
        receipt_hash=receipt_hash,
        signer_id="heavyforge_kernel_phase1",
        signer_key_id="UNSIGNED_PHASE_1",
        signature_algorithm="UNSIGNED_PHASE_1",
        signature="",
    )
    return receipt


def diagnostic_payload_for_hash(receipt: DiagnosticReceipt) -> dict[str, Any]:
    payload = receipt.model_dump(mode="json")
    payload["diagnostic_hash"] = None
    return payload


def compute_diagnostic_hash(receipt: DiagnosticReceipt) -> str:
    return sha256_hex(canonical_json_bytes(diagnostic_payload_for_hash(receipt)))
