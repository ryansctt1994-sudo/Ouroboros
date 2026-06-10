from datetime import UTC, datetime

from heavyforge.contracts import SealedJudgeReceipt, WorkerOutput
from heavyforge.enums import AuthorityLevel
from heavyforge.ledger import make_ledger_entry, verify_ledger_chain
from heavyforge.receipts import seal_receipt_unsigned_phase1


def sample_receipt(run_id: str) -> SealedJudgeReceipt:
    receipt = SealedJudgeReceipt(
        run_id=run_id,
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


def test_ledger_chain_verifies_for_valid_entries():
    first = make_ledger_entry(sample_receipt("run_1"))
    second = make_ledger_entry(sample_receipt("run_2"), previous=first)

    assert verify_ledger_chain([first, second]) is True


def test_ledger_chain_detects_receipt_mutation():
    first = make_ledger_entry(sample_receipt("run_1"))
    second = make_ledger_entry(sample_receipt("run_2"), previous=first)

    second.receipt.strongest_answer = "tampered"

    assert verify_ledger_chain([first, second]) is False


def test_ledger_chain_detects_sequence_gap():
    first = make_ledger_entry(sample_receipt("run_1"))
    second = make_ledger_entry(sample_receipt("run_2"), previous=first)
    second.sequence = 99

    assert verify_ledger_chain([first, second]) is False
