from __future__ import annotations

import base64
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from heavyforge.boot import KernelBootError, initialize_environment_with_source_root
from heavyforge.enums import KernelPanicCode
from heavyforge.receipts import canonical_json_bytes
from heavyforge.registry import registry_payload_for_signature
from heavyforge.root_trust import (
    UNSAFE_TEST_ROOT_FLAG,
    UNSAFE_TEST_ROOT_KEY_ID,
    UNSAFE_TEST_ROOT_PUBLIC_KEY_B64,
    RootTrustConfigurationError,
    load_root_trust_anchors,
)


def public_key_b64(private_key: Ed25519PrivateKey) -> str:
    return base64.b64encode(private_key.public_key().public_bytes_raw()).decode("ascii")


def signed_registry(root_key: Ed25519PrivateKey, verifier_key: Ed25519PrivateKey) -> dict:
    registry = {
        "registry_version": 1,
        "registry_id": "heavyforge_test_registry",
        "root_key_id": "test_root",
        "signer_id": "test_root_authority",
        "verifiers": [
            {
                "verifier_id": "local_replay_service",
                "public_key_id": "local_key_001",
                "algorithm": "Ed25519",
                "public_key_b64": public_key_b64(verifier_key),
                "status": "ACTIVE",
                "not_before_sequence": 0,
                "revoked_at_sequence": None,
                "approved_methods": ["REPLAY_FULL_KERNEL_V1"],
            }
        ],
        "registry_signature": "",
    }
    signature = root_key.sign(canonical_json_bytes(registry_payload_for_signature(registry)))
    registry["registry_signature"] = base64.b64encode(signature).decode("ascii")
    return registry


def test_no_source_root_configured_fails_closed(monkeypatch):
    monkeypatch.delenv(UNSAFE_TEST_ROOT_FLAG, raising=False)
    monkeypatch.delenv(UNSAFE_TEST_ROOT_PUBLIC_KEY_B64, raising=False)

    try:
        load_root_trust_anchors(production_mode=True)
        raise AssertionError("Expected RootTrustConfigurationError")
    except RootTrustConfigurationError as exc:
        assert exc.panic_code == KernelPanicCode.ROOT_KEY_UNRESOLVED


def test_production_rejects_unpinned_environment_root(monkeypatch):
    root_key = Ed25519PrivateKey.generate()
    monkeypatch.setenv(UNSAFE_TEST_ROOT_FLAG, "1")
    monkeypatch.setenv(UNSAFE_TEST_ROOT_PUBLIC_KEY_B64, public_key_b64(root_key))

    try:
        load_root_trust_anchors(production_mode=True)
        raise AssertionError("Expected RootTrustConfigurationError")
    except RootTrustConfigurationError as exc:
        assert exc.panic_code == KernelPanicCode.UNPINNED_ROOT_IN_PRODUCTION


def test_nonproduction_can_use_explicit_unsafe_test_root(monkeypatch, tmp_path):
    root_key = Ed25519PrivateKey.generate()
    verifier_key = Ed25519PrivateKey.generate()
    registry_path = tmp_path / "trusted_verifiers.json"
    registry_path.write_text(
        json.dumps(signed_registry(root_key, verifier_key), sort_keys=True),
        encoding="utf-8",
    )

    monkeypatch.setenv(UNSAFE_TEST_ROOT_FLAG, "1")
    monkeypatch.setenv(UNSAFE_TEST_ROOT_KEY_ID, "test_root")
    monkeypatch.setenv(UNSAFE_TEST_ROOT_PUBLIC_KEY_B64, public_key_b64(root_key))

    env = initialize_environment_with_source_root(
        ledger_path=tmp_path / "ledger.jsonl",
        state_path=tmp_path / ".heavyforge_state",
        registry_path=registry_path,
        boot_id="boot_test_root",
        production_mode=False,
    )

    assert env.registry_snapshot is not None
    assert env.registry_snapshot.root_key_id == "test_root"


def test_source_root_boot_panics_in_production_when_env_root_set(monkeypatch, tmp_path):
    root_key = Ed25519PrivateKey.generate()
    monkeypatch.setenv(UNSAFE_TEST_ROOT_FLAG, "1")
    monkeypatch.setenv(UNSAFE_TEST_ROOT_PUBLIC_KEY_B64, public_key_b64(root_key))

    try:
        initialize_environment_with_source_root(
            ledger_path=tmp_path / "ledger.jsonl",
            state_path=tmp_path / ".heavyforge_state",
            registry_path=tmp_path / "trusted_verifiers.json",
            boot_id="boot_prod_reject",
            production_mode=True,
        )
        raise AssertionError("Expected KernelBootError")
    except KernelBootError as exc:
        assert exc.panic_code == KernelPanicCode.UNPINNED_ROOT_IN_PRODUCTION
