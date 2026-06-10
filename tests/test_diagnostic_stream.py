from heavyforge.contracts import DiagnosticReceipt
from heavyforge.diagnostics import LocalDiagnosticAudit, append_diagnostic_unlocked, serialize_diagnostic_receipt
from heavyforge.enums import KernelPanicCode


def test_diagnostic_authority_weight_zero():
    receipt = DiagnosticReceipt(
        boot_id="boot_test",
        phase="KERNEL_BOOT",
        panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
        message="ledger failed",
    )

    line = serialize_diagnostic_receipt(receipt)
    parsed = DiagnosticReceipt.model_validate_json(line)

    assert parsed.authority_weight == 0
    assert parsed.diagnostic_hash is not None


def test_diagnostic_hash_tamper_detected(tmp_path):
    path = tmp_path / "panic.jsonl"
    receipt = DiagnosticReceipt(
        boot_id="boot_test",
        phase="KERNEL_BOOT",
        panic_code=KernelPanicCode.REGISTRY_SIGNATURE_MISMATCH,
        message="registry failed",
    )
    append_diagnostic_unlocked(path, receipt)

    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("registry failed", "registry passed"), encoding="utf-8")

    audit = LocalDiagnosticAudit(path)
    assert audit.verify_diagnostic_stream() is False


def test_diagnostic_summary_counts_panics(tmp_path):
    path = tmp_path / "panic.jsonl"
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_one",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
            message="ledger failed",
        ),
    )
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_two",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
            message="ledger failed again",
        ),
    )

    audit = LocalDiagnosticAudit(path)
    assert audit.verify_diagnostic_stream() is True
    assert audit.summarize_panics()[KernelPanicCode.LEDGER_CHAIN_BREAK.value] == 2
