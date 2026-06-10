from heavyforge.cli.diagnostics_cli import main
from heavyforge.contracts import DiagnosticReceipt
from heavyforge.diagnostics import append_diagnostic_unlocked
from heavyforge.enums import KernelPanicCode


def test_diagnostics_cli_verify_returns_zero_for_valid_stream(tmp_path):
    path = tmp_path / "panic.jsonl"
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_cli",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
            message="ledger failed",
        ),
    )

    assert main(["verify", "--path", str(path)]) == 0


def test_diagnostics_cli_verify_returns_two_for_tampered_stream(tmp_path):
    path = tmp_path / "panic.jsonl"
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_cli",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
            message="ledger failed",
        ),
    )
    path.write_text(
        path.read_text(encoding="utf-8").replace("ledger failed", "ledger passed"),
        encoding="utf-8",
    )

    assert main(["verify", "--path", str(path)]) == 2


def test_diagnostics_cli_summary_outputs_counts(tmp_path, capsys):
    path = tmp_path / "panic.jsonl"
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_cli",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.REGISTRY_STALE_VERSION,
            message="stale registry",
        ),
    )

    assert main(["summary", "--path", str(path)]) == 0
    captured = capsys.readouterr()
    assert KernelPanicCode.REGISTRY_STALE_VERSION.value in captured.out


def test_diagnostics_cli_find_filters_by_code(tmp_path, capsys):
    path = tmp_path / "panic.jsonl"
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_one",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.REGISTRY_STALE_VERSION,
            message="stale registry",
        ),
    )
    append_diagnostic_unlocked(
        path,
        DiagnosticReceipt(
            boot_id="boot_two",
            phase="KERNEL_BOOT",
            panic_code=KernelPanicCode.LEDGER_CHAIN_BREAK,
            message="ledger failed",
        ),
    )

    assert main([
        "find",
        "--path",
        str(path),
        "--code",
        KernelPanicCode.LEDGER_CHAIN_BREAK.value,
    ]) == 0
    captured = capsys.readouterr()
    assert "boot_two" in captured.out
    assert "boot_one" not in captured.out
