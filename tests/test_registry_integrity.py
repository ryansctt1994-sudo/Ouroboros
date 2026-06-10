from __future__ import annotations

import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from heavyforge.boot import KernelBootError, initialize_environment_with_registry
from heavyforge.enums import KernelPanicCode
from heavyforge.receipts import canonical_json_bytes
from heavyforge.registry import RootTrustAnchor, registry_payload_for_signature


def public_key_b64(private_key: Ed25519PrivateKey) -> str:
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(public_bytes).decode("ascii")


def signed_registry(
    root_key: Ed25519PrivateKey,
    verifier_key: Ed25519PrivateKey,
    version: int = 1,
    root_key_id: str = "root_001",
) -> dict:
    registry = {
        "registry_version": version,
        "registry_id": "heavyforge_test_registry",
        "root_key_id": root_key_id,
        "signer_id": "root_authority",
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


def write_registry(path, registry: dict) -> None:
    path.write_text(json.dumps(registry, sort_keys=True), encoding="utf-8")


def test_signed_registry_boots_and_builds_snapshot(tmp_path):
    root_key = Ed25519PrivateKey.generate()
    verifier_key = Ed25519PrivateKey.generate()
    registry_path = tmp_path / "trusted_verifiers.json"
    ledger_path = tmp_path / "ledger.jsonl"
    state_path = tmp_path / ".heavyforge_state"

    write_registry(registry_path, signed_registry(root_key, verifier_key, version=2))
    root_anchor = RootTrustAnchor(
        root_key_id="root_001",
        algorithm="Ed25519",
        public_key_b64=public_key_b64(root_key),
    )

    env = initialize_environment_with_registry(
        ledger_path=ledger_path,
        state_path=state_path,
        registry_path=registry_path,
        root_anchors=(root_anchor,),
        boot_id="boot_registry_ok",
    )

    assert env.registry_snapshot is not None
    assert env.registry_snapshot.registry_version == 2
    assert env.state["last_accepted_registry_version"] == 2


def test_tampered_registry_signature_rejected(tmp_path):
    root_key = Ed25519PrivateKey.generate()
    verifier_key = Ed25519PrivateKey.generate()
    registry = signed_registry(root_key, verifier_key, version=1)
    registry["verifiers"][0]["status"] = "REVOKED"

    registry_path = tmp_path / "trusted_verifiers.json"
    write_registry(registry_path, registry)
    root_anchor = RootTrustAnchor(
        root_key_id="root_001",
        algorithm="Ed25519",
        public_key_b64=public_key_b64(root_key),
    )

    try:
        initialize_environment_with_registry(
            ledger_path=tmp_path / "ledger.jsonl",
            state_path=tmp_path / ".heavyforge_state",
            registry_path=registry_path,
            root_anchors=(root_anchor,),
            boot_id="boot_tamper",
        )
        raise AssertionError("Expected KernelBootError")
    except KernelBootError as exc:
        assert exc.panic_code == KernelPanicCode.REGISTRY_SIGNATURE_MISMATCH


def test_stale_registry_replay_rejected(tmp_path):
    root_key = Ed25519PrivateKey.generate()
    verifier_key = Ed25519PrivateKey.generate()
    registry_path = tmp_path / "trusted_verifiers.json"
    state_path = tmp_path / ".heavyforge_state"
    state_path.write_text('{"last_accepted_registry_version":5}', encoding="utf-8")

    write_registry(registry_path, signed_registry(root_key, verifier_key, version=4))
    root_anchor = RootTrustAnchor(
        root_key_id="root_001",
        algorithm="Ed25519",
        public_key_b64=public_key_b64(root_key),
    )

    try:
        initialize_environment_with_registry(
            ledger_path=tmp_path / "ledger.jsonl",
            state_path=state_path,
            registry_path=registry_path,
            root_anchors=(root_anchor,),
            boot_id="boot_stale",
        )
        raise AssertionError("Expected KernelBootError")
    except KernelBootError as exc:
        assert exc.panic_code == KernelPanicCode.REGISTRY_STALE_VERSION


def test_unknown_root_key_rejected(tmp_path):
    root_key = Ed25519PrivateKey.generate()
    verifier_key = Ed25519PrivateKey.generate()
    registry_path = tmp_path / "trusted_verifiers.json"

    write_registry(
        registry_path,
        signed_registry(root_key, verifier_key, version=1, root_key_id="missing_root"),
    )
    root_anchor = RootTrustAnchor(
        root_key_id="root_001",
        algorithm="Ed25519",
        public_key_b64=public_key_b64(root_key),
    )

    try:
        initialize_environment_with_registry(
            ledger_path=tmp_path / "ledger.jsonl",
            state_path=tmp_path / ".heavyforge_state",
            registry_path=registry_path,
            root_anchors=(root_anchor,),
            boot_id="boot_unknown_root",
        )
        raise AssertionError("Expected KernelBootError")
    except KernelBootError as exc:
        assert exc.panic_code == KernelPanicCode.ROOT_KEY_UNRESOLVED
