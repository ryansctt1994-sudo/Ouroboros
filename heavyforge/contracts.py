from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import AuthorityLevel, FailureType, KernelPanicCode, VerificationResult


class WorkerOutput(BaseModel):
    agent_name: str
    answer: str = ""
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    failed: bool = False
    failure_type: FailureType = FailureType.NONE
    error_msg: str | None = None
    repaired: bool = False
    raw_output: str | None = None


class JudgeDecision(BaseModel):
    consensus: list[str] = Field(default_factory=list)
    unresolved_disputes: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    strongest_answer: str = ""
    judge_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_notes: list[str] = Field(default_factory=list)
    judge_warnings: list[str] = Field(default_factory=list)


class JudgeReceipt(BaseModel):
    run_id: str
    user_prompt: str
    consensus: list[str]
    unresolved_disputes: list[str]
    missing_evidence: list[str]
    strongest_answer: str
    authority_level: AuthorityLevel
    timestamp: str
    agents: list[WorkerOutput]
    judge_failed: bool = False
    judge_repaired: bool = False
    judge_error_msg: str | None = None


class ReceiptSeal(BaseModel):
    receipt_hash: str
    canonicalization: str = "json.dumps(sort_keys=True,separators=(',',':'))"
    hash_algorithm: str = "SHA-256"
    signer_id: str = "heavyforge_kernel"
    signer_key_id: str = "UNSIGNED_PHASE_1"
    signature_algorithm: str = "UNSIGNED_PHASE_1"
    signature: str = ""


class SealedJudgeReceipt(JudgeReceipt):
    seal: ReceiptSeal | None = None


class VerificationReceipt(BaseModel):
    verification_id: str
    target_run_id: str
    target_receipt_hash: str
    verifier_id: str
    verifier_public_key_id: str
    verification_result: VerificationResult
    verification_method: str
    replay_artifacts_hash: str | None = None
    timestamp: str
    signature: str


class DiagnosticReceipt(BaseModel):
    diagnostic_id: str = Field(default_factory=lambda: f"diag_{uuid4().hex}")
    boot_id: str
    phase: str
    panic_code: KernelPanicCode
    message: str
    registry_path: str | None = None
    ledger_path: str | None = None
    registry_version_seen: int | None = None
    last_known_registry_version: int | None = None
    ledger_sequence_seen: int | None = None
    failing_sequence: int | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    authority_weight: int = 0
    safe_details: dict[str, Any] = Field(default_factory=dict)
    diagnostic_hash: str | None = None


class DiagnosticAuditReport(BaseModel):
    diagnostic_stream_valid: bool
    panic_counts: dict[str, int]
    latest_panic_code: str | None = None
    latest_panic_hash: str | None = None
    requires_operator_review: bool
    authority_weight: int = 0
