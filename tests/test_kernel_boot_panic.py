from heavyforge.boot import KernelBootError, boot_main_minimal, initialize_environment_minimal, load_state
from heavyforge.enums import KernelPanicCode
from heavyforge.ledger import make_ledger_entry
from tests.test_ledger_hash_chain import sample_receipt


def test_boot_rejects_stale_registry(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    state_path = tmp_path / ".heavyforge_state"
    state_path.write_text('{"last_accepted_registry_version":5}', encoding="utf-8")

    try:
        initialize_environment_minimal(
            ledger_path=ledger_path,
            state_path=state_path,
            registry_version=4,
            boot_id="boot_test",
        )
        raise AssertionError("Expected KernelBootError")
    except KernelBootError as exc:
        assert exc.panic_code == KernelPanicCode.REGISTRY_STALE_VERSION


def test_boot_rejects_broken_ledger_chain(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    state_path = tmp_path / ".heavyforge_state"

    first = make_ledger_entry(sample_receipt("run_1"))
    second = make_ledger_entry(sample_receipt("run_2"), previous=first)
    second.previous_entry_hash = "tampered"
    ledger_path.write_text(
        first.model_dump_json() + "\n" + second.model_dump_json() + "\n",
        encoding="utf-8",
    )

    try:
        initialize_environment_minimal(
            ledger_path=ledger_path,
            state_path=state_path,
            registry_version=0,
            boot_id="boot_test",
        )
        raise AssertionError("Expected KernelBootError")
    except KernelBootError as exc:
        assert exc.panic_code == KernelPanicCode.LEDGER_CHAIN_BREAK


def test_successful_boot_updates_state_atomically(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    state_path = tmp_path / ".heavyforge_state"

    env = initialize_environment_minimal(
        ledger_path=ledger_path,
        state_path=state_path,
        registry_version=2,
        boot_id="boot_test",
    )

    state = load_state(state_path)
    assert env.boot_id == "boot_test"
    assert state["last_accepted_registry_version"] == 2
    assert state["last_successful_boot_id"] == "boot_test"


def test_boot_main_writes_diagnostic_on_panic(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    state_path = tmp_path / ".heavyforge_state"
    diagnostics_path = tmp_path / "diagnostics" / "panic.jsonl"
    state_path.write_text('{"last_accepted_registry_version":5}', encoding="utf-8")

    exit_code = boot_main_minimal(
        ledger_path=ledger_path,
        state_path=state_path,
        diagnostics_path=diagnostics_path,
        registry_version=4,
    )

    assert exit_code == 12
    assert diagnostics_path.exists()
    assert KernelPanicCode.REGISTRY_STALE_VERSION.value in diagnostics_path.read_text(encoding="utf-8")
