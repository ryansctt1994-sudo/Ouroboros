from datetime import UTC, datetime

from heavyforge.contracts import SealedJudgeReceipt, WorkerOutput
from heavyforge.enums import AuthorityLevel
from heavyforge.receipts import compute_receipt_hash, seal_receipt_unsigned_phase1


def sample_receipt(run_id: str = "seal_test") -> SealedJudgeReceipt:
    return SealedJudgeReceipt(
        run_id=run_id,
        user_prompt="test",
        consensus=["ok"],
        unresolved_disputes=["No failed agents.", "No repaired agents."],
        missing_evidence=[],
        strongest_answer="answer",
        authority_level=AuthorityLevel.EVIDENCE_SUPPORTED,
        timestamp=datetime.now(UTC).isoformat(),
        agents=[WorkerOutput(agent_name="direct_solver", answer="ok", confidence=0.8)],
    )


def test_receipt_seal_hash_matches_recomputed_payload():
    receipt = seal_receipt_unsigned_phase1(sample_receipt())

    assert receipt.seal is not None
    assert receipt.seal.receipt_hash == compute_receipt_hash(receipt)


def test_receipt_hash_survives_roundtrip_validation():
    receipt = seal_receipt_unsigned_phase1(sample_receipt())
    serialized = receipt.model_dump_json()
    roundtrip = SealedJudgeReceipt.model_validate_json(serialized)

    assert roundtrip.seal is not None
    assert roundtrip.seal.receipt_hash == compute_receipt_hash(roundtrip)


def test_receipt_hash_detects_mutation_after_seal():
    receipt = seal_receipt_unsigned_phase1(sample_receipt())
    assert receipt.seal is not None
    original_hash = receipt.seal.receipt_hash

    receipt.strongest_answer = "tampered"

    assert compute_receipt_hash(receipt) != original_hash
