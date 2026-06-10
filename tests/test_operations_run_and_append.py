import pytest

from heavyforge.enums import AuthorityLevel
from heavyforge.ledger import read_ledger_entries, verify_ledger_chain
from heavyforge.operations import run_and_append
from heavyforge.testing.stub_provider import StubProvider


@pytest.mark.asyncio
async def test_run_and_append_creates_sealed_receipt_and_ledger_entry(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    provider = StubProvider()

    result = await run_and_append(
        provider=provider,
        user_prompt="Test prompt.",
        ledger_path=ledger_path,
        run_id="hf_run_append_test",
        worker_timeout=0.2,
        judge_timeout=0.2,
    )

    assert result.sealed_receipt.seal is not None
    assert result.sealed_receipt.authority_level == AuthorityLevel.EVIDENCE_SUPPORTED
    assert result.ledger_entry.sequence == 0
    assert result.ledger_verified_after_append is True

    entries = read_ledger_entries(ledger_path)
    assert len(entries) == 1
    assert verify_ledger_chain(entries) is True
    assert entries[0].receipt.run_id == "hf_run_append_test"


@pytest.mark.asyncio
async def test_run_and_append_assigns_contiguous_sequences(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    provider = StubProvider()

    first = await run_and_append(
        provider=provider,
        user_prompt="First prompt.",
        ledger_path=ledger_path,
        run_id="hf_run_1",
        worker_timeout=0.2,
        judge_timeout=0.2,
    )
    second = await run_and_append(
        provider=provider,
        user_prompt="Second prompt.",
        ledger_path=ledger_path,
        run_id="hf_run_2",
        worker_timeout=0.2,
        judge_timeout=0.2,
    )

    assert first.ledger_entry.sequence == 0
    assert second.ledger_entry.sequence == 1
    assert verify_ledger_chain(read_ledger_entries(ledger_path)) is True
