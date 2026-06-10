from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from heavyforge.enums import AuthorityLevel


class Decision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class PolicyStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class ReviewMode(str, Enum):
    OBSERVE = "observe"
    WARN = "warn"
    ENFORCE = "enforce"


class ReplayStatus(str, Enum):
    NOT_REPLAY_VERIFIED = "NOT_REPLAY_VERIFIED"
    REPLAY_VERIFIED = "REPLAY_VERIFIED"


class CheckConclusion(str, Enum):
    SUCCESS = "success"
    NEUTRAL = "neutral"
    ACTION_REQUIRED = "action_required"
    FAILURE = "failure"


class ChangedFile(BaseModel):
    path: str
    additions: int = 0
    deletions: int = 0

    @property
    def changed_lines(self) -> int:
        return self.additions + self.deletions


class DiffSummary(BaseModel):
    changed_files: list[ChangedFile] = Field(default_factory=list)
    changed_lines: int = 0
    additions: int = 0
    deletions: int = 0
    added_lines: list[str] = Field(default_factory=list)


class PolicyResult(BaseModel):
    name: str
    status: PolicyStatus
    reason: str
    evidence: list[str] = Field(default_factory=list)


class KaskalCodeReceipt(BaseModel):
    receipt_id: str = Field(default_factory=lambda: f"kcr_{uuid4().hex}")
    project: str = "unknown"
    commit_sha: str | None = None
    pr_number: int | None = None
    mode: ReviewMode = ReviewMode.OBSERVE
    decision: Decision
    check_conclusion: CheckConclusion
    authority_level: AuthorityLevel = AuthorityLevel.EVIDENCE_SUPPORTED
    replay_status: ReplayStatus = ReplayStatus.NOT_REPLAY_VERIFIED
    receipt_hash: str
    ledger_sequence: int | None = None
    changed_files: list[str]
    changed_lines: int
    policy_results: list[PolicyResult]
    summary: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)
