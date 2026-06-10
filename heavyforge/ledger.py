from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .contracts import SealedJudgeReceipt
from .receipts import canonical_json_bytes, compute_receipt_hash, sha256_hex


class LedgerEntry(BaseModel):
    sequence: int
    previous_entry_hash: str | None
    receipt_hash: str
    receipt: SealedJudgeReceipt
    entry_hash: str | None = None


def compute_entry_hash(entry: LedgerEntry) -> str:
    payload = entry.model_dump(mode="json")
    payload["entry_hash"] = None
    return sha256_hex(canonical_json_bytes(payload))


def make_ledger_entry(
    receipt: SealedJudgeReceipt,
    previous: LedgerEntry | None = None,
) -> LedgerEntry:
    sequence = 0 if previous is None else previous.sequence + 1
    previous_hash = None if previous is None else previous.entry_hash
    receipt_hash = compute_receipt_hash(receipt)

    entry = LedgerEntry(
        sequence=sequence,
        previous_entry_hash=previous_hash,
        receipt_hash=receipt_hash,
        receipt=receipt,
        entry_hash=None,
    )
    entry.entry_hash = compute_entry_hash(entry)
    return entry


def append_to_ledger_unlocked(ledger_path: Path, receipt: SealedJudgeReceipt) -> LedgerEntry:
    """Append without file locking.

    Phase 1D keeps this pure and testable. Production/local concurrent writers
    should wrap this with portalocker in the boot/ledger manager layer.
    """

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    entries = read_ledger_entries(ledger_path)
    previous = entries[-1] if entries else None
    entry = make_ledger_entry(receipt=receipt, previous=previous)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(entry.model_dump_json() + "\n")
        handle.flush()
    return entry


def read_ledger_entries(ledger_path: Path) -> list[LedgerEntry]:
    if not ledger_path.exists():
        return []

    entries: list[LedgerEntry] = []
    with ledger_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entries.append(LedgerEntry.model_validate_json(line))
    return entries


def verify_ledger_chain(entries: list[LedgerEntry]) -> bool:
    previous_hash: str | None = None

    for expected_sequence, entry in enumerate(entries):
        if entry.sequence != expected_sequence:
            return False

        if entry.previous_entry_hash != previous_hash:
            return False

        if compute_receipt_hash(entry.receipt) != entry.receipt_hash:
            return False

        if compute_entry_hash(entry) != entry.entry_hash:
            return False

        previous_hash = entry.entry_hash

    return True
