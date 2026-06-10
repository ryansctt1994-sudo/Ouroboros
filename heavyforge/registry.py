from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


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
