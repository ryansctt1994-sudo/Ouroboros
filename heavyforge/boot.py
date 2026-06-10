from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .contracts import DiagnosticReceipt
from .diagnostics import append_diagnostic_unlocked
from .enums import KernelPanicCode
from .ledger import LedgerLockError, read_ledger_entries, verify_ledger_chain


EXIT_CODES: dict[KernelPanicCode, int] = {
    KernelPanicCode.ROOT_KEY_UNRESOLVED: 10,
    KernelPanicCode.REGISTRY_ROOT_KEY_INACTIVE: 10,
    KernelPanicCode.UNPINNED_ROOT_IN_PRODUCTION: 10,
    KernelPanicCode.REGISTRY_SCHEMA_INVALID: 11,
    KernelPanicCode.REGISTRY_SIGNATURE_MISMATCH: 11,
    KernelPanicCode.REGISTRY_STALE_VERSION: 12,
    KernelPanicCode.LEDGER_LOCK_TIMEOUT: 13,
    KernelPanicCode.LEDGER_CHAIN_BREAK: 13,
    KernelPanicCode.LEDGER_PARSE_FAILURE: 13,
    KernelPanicCode.STATE_FILE_CORRUPT: 14,
    KernelPanicCode.STATE_VERSION_WRITE_FAILED: 14,
    KernelPanicCode.UNKNOWN_BOOT_FAILURE: 99,
}


class KernelBootError(RuntimeError):
    def __init__(
        self,
        panic_code: KernelPanicCode,
        message: str,
        exit_code: int | None = None,
        safe_details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.panic_code = panic_code
        self.exit_code = exit_code if exit_code is not None else EXIT_CODES[panic_code]
        self.safe_details = safe_details or {}


@dataclass(frozen=True)
class KernelEnvironment:
    boot_id: str
    ledger_path: Path
    state_path: Path
    last_sequence: int | None
    last_entry_hash: str | None
    state: dict[str, Any]


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise KernelBootError(
            panic_code=KernelPanicCode.STATE_FILE_CORRUPT,
            message="Persistent state file is corrupt or unreadable.",
            safe_details={"state_path": str(state_path), "error": type(exc).__name__},
        ) from exc


def initialize_environment_minimal(
    ledger_path: Path,
    state_path: Path,
    registry_version: int = 0,
    boot_id: str | None = None,
) -> KernelEnvironment:
    """Minimal Phase 1E boot gate.

    Full signed registry/root verification is deferred to the registry bootloader.
    This gate enforces stale-version rejection and ledger-chain integrity.
    """

    actual_boot_id = boot_id or f"boot_{uuid4().hex}"
    state = load_state(state_path)
    last_accepted = int(state.get("last_accepted_registry_version", 0))

    if registry_version < last_accepted:
        raise KernelBootError(
            panic_code=KernelPanicCode.REGISTRY_STALE_VERSION,
            message="Registry version is lower than last accepted version.",
            safe_details={
                "registry_version": registry_version,
                "last_accepted_registry_version": last_accepted,
            },
        )

    try:
        entries = read_ledger_entries(ledger_path)
    except LedgerLockError as exc:
        raise KernelBootError(
            panic_code=KernelPanicCode.LEDGER_LOCK_TIMEOUT,
            message="Unable to acquire ledger lock during boot.",
            safe_details={"ledger_path": str(ledger_path)},
        ) from exc
    except Exception as exc:
        raise KernelBootError(
            panic_code=KernelPanicCode.LEDGER_PARSE_FAILURE,
            message="Ledger entries are unreadable or malformed.",
            safe_details={"ledger_path": str(ledger_path), "error": type(exc).__name__},
        ) from exc

    if not verify_ledger_chain(entries):
        raise KernelBootError(
            panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
            message="Ledger hash-chain verification failed.",
            safe_details={"ledger_path": str(ledger_path)},
        )

    last_sequence = entries[-1].sequence if entries else None
    last_entry_hash = entries[-1].entry_hash if entries else None
    new_state = {
        **state,
        "last_accepted_registry_version": max(registry_version, last_accepted),
        "last_successful_boot_id": actual_boot_id,
        "last_successful_ledger_sequence": last_sequence,
        "last_successful_ledger_hash": last_entry_hash,
    }

    try:
        atomic_write_json(state_path, new_state)
    except Exception as exc:
        raise KernelBootError(
            panic_code=KernelPanicCode.STATE_VERSION_WRITE_FAILED,
            message="Atomic persistent state update failed.",
            safe_details={"state_path": str(state_path), "error": type(exc).__name__},
        ) from exc

    return KernelEnvironment(
        boot_id=actual_boot_id,
        ledger_path=ledger_path,
        state_path=state_path,
        last_sequence=last_sequence,
        last_entry_hash=last_entry_hash,
        state=new_state,
    )


def build_diagnostic_receipt_from_error(
    error: KernelBootError,
    boot_id: str,
    registry_path: Path | None = None,
    ledger_path: Path | None = None,
) -> DiagnosticReceipt:
    return DiagnosticReceipt(
        boot_id=boot_id,
        phase="KERNEL_BOOT",
        panic_code=error.panic_code,
        message=str(error),
        registry_path=str(registry_path) if registry_path else None,
        ledger_path=str(ledger_path) if ledger_path else None,
        safe_details=error.safe_details,
    )


def print_panic_line(receipt: DiagnosticReceipt, exit_code: int) -> None:
    print(
        "HEAVYFORGE_KERNEL_PANIC "
        f"code={receipt.panic_code.value} "
        f"boot_id={receipt.boot_id} "
        f"diagnostic_hash={receipt.diagnostic_hash} "
        f"exit_code={exit_code}",
        file=sys.stderr,
    )


def boot_main_minimal(
    ledger_path: Path,
    state_path: Path,
    diagnostics_path: Path,
    registry_version: int = 0,
) -> int:
    boot_id = f"boot_{uuid4().hex}"
    try:
        initialize_environment_minimal(
            ledger_path=ledger_path,
            state_path=state_path,
            registry_version=registry_version,
            boot_id=boot_id,
        )
        return 0
    except KernelBootError as error:
        try:
            receipt = build_diagnostic_receipt_from_error(
                error=error,
                boot_id=boot_id,
                ledger_path=ledger_path,
            )
            append_diagnostic_unlocked(diagnostics_path, receipt)
            print_panic_line(receipt, error.exit_code)
        except Exception as diagnostic_error:
            print(
                "HEAVYFORGE_KERNEL_PANIC "
                f"code={error.panic_code.value} "
                f"boot_id={boot_id} "
                "diagnostic_write_failed=true "
                f"diagnostic_error={type(diagnostic_error).__name__} "
                f"exit_code={error.exit_code}",
                file=sys.stderr,
            )
        return error.exit_code
