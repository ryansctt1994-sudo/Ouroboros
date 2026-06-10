from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import DiagnosticAuditReport, DiagnosticReceipt
from .enums import KernelPanicCode
from .receipts import compute_diagnostic_hash


class DiagnosticIntegrityError(RuntimeError):
    pass


def serialize_diagnostic_receipt(receipt: DiagnosticReceipt) -> str:
    receipt.diagnostic_hash = compute_diagnostic_hash(receipt)
    return receipt.model_dump_json() + "\n"


def parse_diagnostic_line(line: str) -> DiagnosticReceipt:
    receipt = DiagnosticReceipt.model_validate_json(line)
    expected_hash = compute_diagnostic_hash(receipt)

    if receipt.diagnostic_hash != expected_hash:
        raise DiagnosticIntegrityError("Diagnostic hash mismatch.")

    if receipt.authority_weight != 0:
        raise DiagnosticIntegrityError("Diagnostic receipt has nonzero authority weight.")

    return receipt


def append_diagnostic_unlocked(path: Path, receipt: DiagnosticReceipt) -> DiagnosticReceipt:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(serialize_diagnostic_receipt(receipt))
        handle.flush()
    return receipt


@dataclass(frozen=True)
class LocalDiagnosticAudit:
    diagnostics_path: Path

    def read_diagnostics(self) -> list[DiagnosticReceipt]:
        if not self.diagnostics_path.exists():
            return []

        receipts: list[DiagnosticReceipt] = []
        with self.diagnostics_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                receipts.append(parse_diagnostic_line(line))
        return receipts

    def verify_diagnostic_stream(self) -> bool:
        try:
            self.read_diagnostics()
            return True
        except Exception:
            return False

    def summarize_panics(self) -> dict[str, int]:
        summary: dict[str, int] = {}
        for receipt in self.read_diagnostics():
            code = receipt.panic_code.value
            summary[code] = summary.get(code, 0) + 1
        return summary

    def find_by_code(self, code: KernelPanicCode) -> list[DiagnosticReceipt]:
        return [
            receipt
            for receipt in self.read_diagnostics()
            if receipt.panic_code == code
        ]

    def latest(self) -> DiagnosticReceipt | None:
        receipts = self.read_diagnostics()
        return receipts[-1] if receipts else None

    def tail(self, last: int = 20) -> list[DiagnosticReceipt]:
        if last <= 0:
            return []
        return self.read_diagnostics()[-last:]

    def report(self) -> DiagnosticAuditReport:
        latest = self.latest()
        valid = self.verify_diagnostic_stream()
        summary = self.summarize_panics() if valid else {}
        return DiagnosticAuditReport(
            diagnostic_stream_valid=valid,
            panic_counts=summary,
            latest_panic_code=latest.panic_code.value if latest else None,
            latest_panic_hash=latest.diagnostic_hash if latest else None,
            requires_operator_review=bool(summary) or not valid,
        )
