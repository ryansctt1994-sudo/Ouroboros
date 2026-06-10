from __future__ import annotations

import base64
import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, Field

from .receipts import canonical_json_bytes, sha256_hex


class RegistryIntegrityError(RuntimeError):
    pass


class RegistrySchemaError(RuntimeError):
    pass


class RootTrustError(RuntimeError):
    pass


class TrustedVerifierRegistry(Protocol):
    def resolve_public_key(
        self,
        verifier_id: str,
        key_id: str,
        ledger_sequence: int,
    ) -> Ed25519PublicKey | None:
        ...

    def is_method_approved(
        self,
        verifier_id: str,
        method: str,
    ) -> bool:
        ...


@dataclass(frozen=True)
class RootTrustAnchor:
    root_key_id: str
    algorithm: str
    public_key_b64: str
    status: str = "ACTIVE"

    def public_key(self) -> Ed25519PublicKey:
        if self.algorithm != "Ed25519":
            raise RootTrustError(f"Unsupported root key algorithm: {self.algorithm}")
        return Ed25519PublicKey.from_public_bytes(base64.b64decode(self.public_key_b64))


@dataclass(frozen=True)
class VerifierRecord:
    verifier_id: str
    public_key_id: str
    public_key: Ed25519PublicKey
    status: str = "ACTIVE"
    not_before_sequence: int = 0
    revoked_at_sequence: int | None = None
    approved_methods: tuple[str, ...] = ()


@dataclass(frozen=True)
class StaticVerifierRegistry:
    """Small immutable registry for tests and local Phase 1 execution."""

    verifiers: tuple[VerifierRecord, ...]

    def resolve_public_key(
        self,
        verifier_id: str,
        key_id: str,
        ledger_sequence: int,
    ) -> Ed25519PublicKey | None:
        for verifier in self.verifiers:
            if verifier.verifier_id != verifier_id:
                continue
            if verifier.public_key_id != key_id:
                continue
            if verifier.status != "ACTIVE":
                return None
            if ledger_sequence < verifier.not_before_sequence:
                return None
            if verifier.revoked_at_sequence is not None and ledger_sequence >= verifier.revoked_at_sequence:
                return None
            return verifier.public_key
        return None

    def is_method_approved(self, verifier_id: str, method: str) -> bool:
        for verifier in self.verifiers:
            if verifier.verifier_id == verifier_id:
                return method in verifier.approved_methods
        return False


@dataclass(frozen=True)
class VerifiedRegistrySnapshot(StaticVerifierRegistry):
    registry_version: int = 0
    registry_id: str = ""
    root_key_id: str = ""
    signer_id: str = ""
    registry_hash: str = ""


class RegistryVerifierConfig(BaseModel):
    verifier_id: str
    public_key_id: str
    algorithm: str = "Ed25519"
    public_key_b64: str
    status: str = "ACTIVE"
    not_before_sequence: int = 0
    revoked_at_sequence: int | None = None
    approved_methods: list[str] = Field(default_factory=list)


class SignedRegistryConfig(BaseModel):
    registry_version: int
    registry_id: str
    root_key_id: str
    signer_id: str
    verifiers: list[RegistryVerifierConfig]
    registry_signature: str


def registry_payload_for_signature(registry_data: dict[str, Any]) -> dict[str, Any]:
    payload = deepcopy(registry_data)
    payload.pop("registry_signature", None)
    return payload


def compute_registry_hash(registry_data: dict[str, Any]) -> str:
    return sha256_hex(canonical_json_bytes(registry_payload_for_signature(registry_data)))


def resolve_root_anchor(
    root_key_id: str,
    root_anchors: tuple[RootTrustAnchor, ...],
) -> RootTrustAnchor:
    for anchor in root_anchors:
        if anchor.root_key_id == root_key_id and anchor.status == "ACTIVE":
            return anchor
    raise RootTrustError(f"Unknown or inactive root key: {root_key_id}")


def verify_registry_integrity(
    registry_data: dict[str, Any],
    root_public_key: Ed25519PublicKey,
) -> bool:
    signature_b64 = registry_data.get("registry_signature")
    if not signature_b64:
        return False

    try:
        root_public_key.verify(
            base64.b64decode(signature_b64),
            canonical_json_bytes(registry_payload_for_signature(registry_data)),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def build_verified_registry_snapshot(
    registry_data: dict[str, Any],
    root_anchors: tuple[RootTrustAnchor, ...],
) -> VerifiedRegistrySnapshot:
    try:
        config = SignedRegistryConfig.model_validate(registry_data)
    except Exception as exc:
        raise RegistrySchemaError(str(exc)) from exc

    root_anchor = resolve_root_anchor(config.root_key_id, root_anchors)

    if not verify_registry_integrity(registry_data, root_anchor.public_key()):
        raise RegistryIntegrityError("Registry signature verification failed.")

    verifier_records: list[VerifierRecord] = []
    for verifier in config.verifiers:
        if verifier.algorithm != "Ed25519":
            raise RegistrySchemaError(f"Unsupported verifier algorithm: {verifier.algorithm}")
        verifier_records.append(
            VerifierRecord(
                verifier_id=verifier.verifier_id,
                public_key_id=verifier.public_key_id,
                public_key=Ed25519PublicKey.from_public_bytes(
                    base64.b64decode(verifier.public_key_b64)
                ),
                status=verifier.status,
                not_before_sequence=verifier.not_before_sequence,
                revoked_at_sequence=verifier.revoked_at_sequence,
                approved_methods=tuple(verifier.approved_methods),
            )
        )

    return VerifiedRegistrySnapshot(
        verifiers=tuple(verifier_records),
        registry_version=config.registry_version,
        registry_id=config.registry_id,
        root_key_id=config.root_key_id,
        signer_id=config.signer_id,
        registry_hash=compute_registry_hash(registry_data),
    )


def load_registry_json(registry_path: Path) -> dict[str, Any]:
    try:
        return json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RegistrySchemaError(str(exc)) from exc


def load_verified_registry_snapshot(
    registry_path: Path,
    root_anchors: tuple[RootTrustAnchor, ...],
) -> VerifiedRegistrySnapshot:
    return build_verified_registry_snapshot(
        registry_data=load_registry_json(registry_path),
        root_anchors=root_anchors,
    )
