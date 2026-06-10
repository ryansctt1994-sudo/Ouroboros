from datetime import UTC, datetime

from heavyforge.contracts import SealedJudgeReceipt, WorkerOutput
from heavyforge.enums import AuthorityLevel
from heavyforge.ledger import append_to_ledger_locked, read_ledger_entries, verify_ledger_chain
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


def test_locked_append_assigns_contiguous_sequences(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"

    first = append_to_ledger_locked(ledger_path, sample_receipt("run_1"))
    second = append_to_ledger_locked(ledger_path, sample_receipt("run_2"))

    entries = read_ledger_entries(ledger_path)

    assert first.sequence == 0
    assert second.sequence == 1
    assert [entry.sequence for entry in entries] == [0, 1]
    assert verify_ledger_chain(entries) is True
