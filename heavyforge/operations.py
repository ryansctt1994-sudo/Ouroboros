from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import SealedJudgeReceipt
from .kernel import DEFAULT_AGENTS, heavy_run_sealed
from .ledger import LedgerEntry, append_to_ledger_locked, read_ledger_entries, verify_ledger_chain
from .provider_protocol import ProviderProtocol


class OperationIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunAppendResult:
    sealed_receipt: SealedJudgeReceipt
    ledger_entry: LedgerEntry
    ledger_verified_after_append: bool


async def run_and_append(
    provider: ProviderProtocol,
    user_prompt: str,
    ledger_path: Path,
    run_id: str | None = None,
    agents: tuple[tuple[str, str], ...] = DEFAULT_AGENTS,
    worker_timeout: float = 20.0,
    judge_timeout: float = 30.0,
    ledger_lock_timeout: float = 5.0,
) -> RunAppendResult:
    """Execute a sealed HEAVYFORGE run and append it to the authority ledger.

    Flow:
        heavy_run_sealed -> append_to_ledger_locked -> verify_ledger_chain

    The function fails closed if the ledger does not verify after append.
    """

    sealed_receipt = await heavy_run_sealed(
        provider=provider,
        user_prompt=user_prompt,
        run_id=run_id,
        agents=agents,
        worker_timeout=worker_timeout,
        judge_timeout=judge_timeout,
    )

    ledger_entry = append_to_ledger_locked(
        ledger_path=ledger_path,
        receipt=sealed_receipt,
        timeout=ledger_lock_timeout,
    )

    entries = read_ledger_entries(ledger_path)
    ledger_verified = verify_ledger_chain(entries)
    if not ledger_verified:
        raise OperationIntegrityError("Ledger failed verification after append.")

    return RunAppendResult(
        sealed_receipt=sealed_receipt,
        ledger_entry=ledger_entry,
        ledger_verified_after_append=ledger_verified,
    )
