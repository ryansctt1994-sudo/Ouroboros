# HEAVYFORGE v0.1

Status: `ARCHITECTURE_FROZEN_FOR_PHASE_1_IMPLEMENTATION`  
Authority: `DESIGN_SPECIFICATION`  
Authority Weight: `0`  
Last Corrective Pass: `HEAVYFORGE_DEBUG_PASS_001`

HEAVYFORGE v0.1 is a parallel reasoning kernel for Grok Heavy-like test-time compute. It is not an agent chatroom. It is an execution discipline for running multiple model workers, validating their outputs, adjudicating disagreement, calculating authority deterministically, and preserving audit receipts.

This document is a design specification only. It does not confer implementation authority. Implementation authority requires runnable code, tests, sealed receipts, and replay verification.

---

## Prime Doctrine

```text
Capability may propose.
Models may witness.
Judges may analyze.
Only the Kernel may authorize.
Only external replay evidence may promote to REPLAY_VERIFIED.
```

---

## Corrected Trust Flow

```text
User Prompt
  -> Kernel
  -> Parallel Worker Swarm
  -> WorkerOutput validation
  -> JudgeDecision validation
  -> Kernel authority calculation
  -> SealedJudgeReceipt
  -> Hash-chained authority ledger
  -> Optional external replay/audit
  -> Signed VerificationReceipt
  -> Kernel verification of replay evidence
  -> Optional promotion record appended to ledger
```

Critical correction: promotion must never mutate the original sealed receipt. If a run is later promoted to `REPLAY_VERIFIED`, the promotion is represented as a new signed verification artifact or ledger entry that points back to the original sealed receipt hash.

---

## Non-Negotiable Invariants

```text
Consensus is not authority.
Confidence is not authority.
A model may not assign its own legitimacy.
A raw boolean may not promote authority.
Formatting repair is tainted evidence.
A repaired Judge forces DRAFT.
A repaired Worker caps authority at PLAUSIBLE.
REPLAY_VERIFIED requires a signed external VerificationReceipt.
Boot failures never enter the authority ledger.
Diagnostics have authority_weight = 0.
The original sealed receipt is immutable after write.
```

---

## Core Components

| Component | Role | Authority |
|---|---|---:|
| Worker agents | Produce structured witness outputs | None |
| Judge | Produces structured adjudicative analysis | None |
| Kernel | Calculates authority deterministically | Yes |
| Authority Ledger | Stores sealed authority receipts and promotion records | Records only |
| Diagnostic Stream | Stores boot/failure diagnostics | None |
| Trusted Verifier Registry | Signed trust policy for verifiers | Policy only |
| External Verifier | Produces signed replay evidence | Evidence only |
| DiagnosticAudit | Read-only forensic observer | None |

Correct separation:

```text
Workers produce WorkerOutput.
Judge produces JudgeDecision.
Kernel produces JudgeReceipt.
Kernel seals JudgeReceipt.
Verifier produces VerificationReceipt.
Kernel verifies VerificationReceipt.
Ledger records sealed results.
Diagnostics record failure only.
```

---

## Phase 1 Implementation Order

1. Raw `asyncio` execution kernel.
2. Pydantic contracts for `WorkerOutput`, `JudgeDecision`, and `JudgeReceipt`.
3. Deterministic authority truth table.
4. Single schema-repair rule.
5. StubProvider-based adversarial tests.
6. Canonical JSON, SHA-256, and Ed25519 receipt sealing.
7. Hash-chained JSONL authority ledger.
8. Signed local verifier registry with source-pinned root key.
9. Strict boot protocol and diagnostic panic stream.
10. Read-only DiagnosticAudit CLI.

Do not add LangGraph, CrewAI, a UI, memory, autonomous tools, or hosted deployment until Phase 1A and Phase 1B tests pass.

---

## Execution Kernel Rule

Use raw Python `asyncio` for Phase 1A.

```text
TaskGroup supervises.
Worker catches.
Kernel receives WorkerOutput from every task.
Broken workers become failed witnesses.
A broken swarm still produces a receipt.
```

Worker failure behavior:

```text
SUCCESS -> WorkerOutput(failed=false)
TIMEOUT -> WorkerOutput(failed=true, failure_type=TIMEOUT)
API_ERROR -> WorkerOutput(failed=true, failure_type=API_ERROR)
SCHEMA_INVALID -> one repair attempt
SCHEMA_REPAIR_FAILED -> failed witness
EMPTY_RESPONSE -> failed witness
SAFETY_REFUSAL -> preserved, not repaired into compliance
```

---

## Provider Boundary

The Kernel must depend on a `ProviderProtocol`, not a concrete model SDK.

```python
class ProviderProtocol(Protocol):
    async def complete_worker(self, agent_name: str, role_prompt: str, user_prompt: str) -> str: ...
    async def repair_worker_output(self, agent_name: str, bad_output: str, validation_error: str) -> str: ...
    async def complete_judge(self, judge_prompt: str, worker_outputs_json: str) -> str: ...
    async def repair_judge_output(self, bad_output: str, validation_error: str) -> str: ...
```

Testing rule:

```text
Primary: StubProvider injected into Kernel.
Secondary: AsyncMock for interaction assertions.
Avoid: monkeypatching provider internals as the normal testing path.
```

---

## Core Contracts

### WorkerOutput

```python
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
```

### JudgeDecision

```python
class JudgeDecision(BaseModel):
    consensus: list[str] = Field(default_factory=list)
    unresolved_disputes: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    strongest_answer: str = ""
    judge_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_notes: list[str] = Field(default_factory=list)
    judge_warnings: list[str] = Field(default_factory=list)
```

Critical correction:

```text
JudgeDecision has no authority_level field.
The model cannot grade its own legitimacy.
```

### JudgeReceipt

```python
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
```

---

## Schema Repair Doctrine

```text
One repair is admissible.
Two repairs is laundering.
Invalid after repair is failure evidence.
Repair must preserve raw_output.
Repair must be visible to the Judge and Kernel.
```

Allowed repair:

```text
Malformed JSON or schema mismatch -> one repair attempt
```

Forbidden repair patterns:

```text
Timeout retry loops
Provider outage laundering
Safety refusal repair
Repeated fix-your-JSON loops
Silent replacement of original output
```

Evidence classification:

```text
Native valid schema = clean witness.
Repaired schema = admissible but tainted witness.
Repair failed = failed witness.
Judge repaired = authority forced to DRAFT.
```

---

## Authority Levels

```text
DRAFT
PLAUSIBLE
EVIDENCE_SUPPORTED
REPLAY_VERIFIED
```

Truth rules:

```text
Judge failed -> DRAFT.
Judge repaired -> DRAFT.
No workers -> DRAFT.
Any worker failed -> DRAFT.
No strongest answer -> DRAFT.
Judge confidence below threshold -> DRAFT.

Any repaired worker -> PLAUSIBLE maximum.
Any unresolved disputes -> PLAUSIBLE maximum.
Any missing evidence -> PLAUSIBLE maximum.
No evidence_notes -> PLAUSIBLE maximum.

Clean run + coherent answer -> PLAUSIBLE.
Clean run + evidence + no missing evidence + no disputes -> EVIDENCE_SUPPORTED.
Clean run + valid signed external verification evidence -> REPLAY_VERIFIED.
```

A signed external verification artifact is necessary but not sufficient. `REPLAY_VERIFIED` requires all of the following:

```text
VerificationReceipt exists.
target_run_id matches JudgeReceipt.run_id.
target_receipt_hash matches SealedJudgeReceipt.seal.receipt_hash.
verification_result == PASSED.
verifier_id is trusted by the immutable registry snapshot.
verifier key is active for the relevant ledger sequence.
verification_method is approved.
signature verifies.
original run has no failed workers.
Judge was not repaired.
there are no unresolved disputes.
there is no missing evidence.
```

---

## Receipt Sealing

A `JudgeReceipt` becomes a `SealedJudgeReceipt` after canonical hashing and signing.

```python
class ReceiptSeal(BaseModel):
    receipt_hash: str
    canonicalization: str
    hash_algorithm: str = "SHA-256"
    signer_id: str
    signer_key_id: str
    signature_algorithm: str = "Ed25519"
    signature: str
```

Hashing law:

```text
Hash the receipt with seal=None.
Then sign the receipt_hash.
Never hash the signature into itself.
```

---

## VerificationReceipt

Raw `replay_verified: bool` is forbidden.

```python
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
```

Doctrine:

```text
Model cannot self-promote.
Caller cannot flag-promote.
Only signed replay evidence can promote.
```

---

## Trusted Verifier Registry

Use a local signed registry file for v0.1:

```text
trusted_verifiers.json
```

Trust chain:

```text
Source-pinned RootTrustAnchor
   -> verifies Signed TrustedVerifierRegistry
   -> resolves Verifier public keys
   -> verifies VerificationReceipt
   -> binds SealedJudgeReceipt
   -> allows Kernel promotion calculation
```

Registry loading rule:

```text
Load registry once at Kernel boot.
Verify registry signature.
Reject stale version.
Build immutable VerifiedRegistrySnapshot.
Never re-read mutable registry during one Kernel run.
```

Sequence-bound key validity:

```text
not_before_sequence
revoked_at_sequence
status = ACTIVE | RETIRED | REVOKED
approved_methods = [...]
```

---

## Root Trust Anchor

Use a source-code-pinned root public key for v0.1.

```text
Root public key is not secret.
Root public key must be hard to silently swap.
Therefore: source-pinned constant, not environment variable.
```

Environment overrides are allowed only in explicit unsafe test mode:

```text
HEAVYFORGE_ALLOW_UNPINNED_ROOT_FOR_TESTS=1
HEAVYFORGE_TEST_ROOT_PUBLIC_KEY_B64=...
```

Production must reject this.

Final rule:

```text
The registry is configurable.
The root is pinned.
The verifier set is rotatable.
The root rotates only by code release.
```

---

## Hash-Chained Authority Ledger

The main ledger is append-only JSONL protected by cooperative file locking.

```python
class LedgerEntry(BaseModel):
    sequence: int
    previous_entry_hash: str | None
    receipt_hash: str
    receipt: SealedJudgeReceipt
    entry_hash: str | None = None
```

Hash law:

```text
entry_hash = SHA256(canonical_json({
  sequence,
  previous_entry_hash,
  receipt_hash,
  receipt,
  entry_hash=None
}))
```

Ledger verification checks:

```text
sequence continuity
previous_entry_hash continuity
receipt_hash recomputation
entry_hash recomputation
```

Main ledger purity rule:

```text
Only successful Kernel execution receipts and promotion records go into the authority ledger.
Boot failures never go into the authority ledger.
Diagnostics never go into the authority ledger.
```

---

## Kernel Boot Protocol

Final boot sequence:

```text
1. Generate boot_id.
2. Resolve source-pinned RootTrustAnchor.
3. Load trusted_verifiers.json.
4. Verify registry signature using root public key.
5. Load persistent state.
6. Reject registry if registry_version < last_accepted_registry_version.
7. Lock and verify authority ledger hash-chain.
8. Build immutable VerifiedRegistrySnapshot.
9. Atomically update .heavyforge_state only after all checks pass.
10. Start Kernel services.
```

Boot failure rule:

```text
If registry fails, panic.
If ledger fails, panic.
If state corrupt, panic.
If test root appears in production, panic.
No partial service start.
```

---

## Panic Doctrine

```text
Authority Ledger = trusted operational history.
Diagnostic Stream = forensic failure history.
```

Boot failures write a `DiagnosticReceipt`, not a `JudgeReceipt`.

```python
class DiagnosticReceipt(BaseModel):
    diagnostic_id: str
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
    timestamp: str
    authority_weight: int = 0
    safe_details: dict[str, Any] = Field(default_factory=dict)
    diagnostic_hash: str | None = None
```

Diagnostic doctrine:

```text
Failure is recorded.
Failure is not hidden.
Failure is not authority.
Failure does not contaminate the ledger.
```

---

## Kernel Panic Codes and Exit Codes

Panic codes:

```text
ROOT_KEY_UNRESOLVED
REGISTRY_SCHEMA_INVALID
REGISTRY_SIGNATURE_MISMATCH
REGISTRY_STALE_VERSION
REGISTRY_ROOT_KEY_INACTIVE
LEDGER_LOCK_TIMEOUT
LEDGER_CHAIN_BREAK
LEDGER_PARSE_FAILURE
STATE_FILE_CORRUPT
STATE_VERSION_WRITE_FAILED
UNPINNED_ROOT_IN_PRODUCTION
UNKNOWN_BOOT_FAILURE
```

Exit codes:

```text
0   success
10  security / root trust failure
11  registry failure
12  registry stale-version failure
13  ledger integrity failure
14  persistent state failure
15  diagnostic write failure
99  unknown failure
```

stderr line:

```text
HEAVYFORGE_KERNEL_PANIC code=REGISTRY_SIGNATURE_MISMATCH boot_id=boot_abc diagnostic_hash=sha256:...
```

---

## Diagnostic Stream and Audit

`diagnostics/panic.jsonl` is separate from the authority ledger.

Serialization law:

```text
One compact JSON object per line.
diagnostic_hash excluded/nulled during hash computation.
Written line includes diagnostic_hash.
Every line independently validates as DiagnosticReceipt.
Malformed diagnostic lines invalidate the diagnostic stream.
Malformed diagnostics never touch authority ledger.
authority_weight must always equal 0.
```

Read-only observer:

```python
class DiagnosticAudit(Protocol):
    def read_diagnostics(self) -> list[DiagnosticReceipt]: ...
    def verify_diagnostic_stream(self) -> bool: ...
    def summarize_panics(self) -> dict: ...
    def find_by_code(self, code: KernelPanicCode) -> list[DiagnosticReceipt]: ...
```

Boundary:

```text
DiagnosticAudit may observe.
DiagnosticAudit may alert.
DiagnosticAudit may summarize.
DiagnosticAudit may not write.
DiagnosticAudit may not authorize.
DiagnosticAudit may not repair.
DiagnosticAudit may not promote.
```

---

## CLI Utility

Use `argparse` for v0.1.

Commands:

```text
heavyforge-diagnostics verify --path diagnostics/panic.jsonl
heavyforge-diagnostics summary --path diagnostics/panic.jsonl
heavyforge-diagnostics latest --path diagnostics/panic.jsonl
heavyforge-diagnostics tail --path diagnostics/panic.jsonl --last 20
heavyforge-diagnostics find --path diagnostics/panic.jsonl --code LEDGER_CHAIN_BREAK
```

CLI rule:

```text
CLI is a read-only viewer.
CLI imports diagnostic models and hash verification only.
CLI never imports ledger append, promotion, or registry mutation logic.
```

---

## Repository Scaffold Target

```text
heavyforge/
  contracts.py
  enums.py
  provider_protocol.py
  worker.py
  judge.py
  authority.py
  receipts.py
  verification.py
  registry.py
  ledger.py
  boot.py
  diagnostics.py
  cli/diagnostics_cli.py
  testing/stub_provider.py

tests/
  test_worker_timeout_isolation.py
  test_schema_repair_once.py
  test_judge_cannot_assign_authority.py
  test_authority_truth_table.py
  test_receipt_sealing.py
  test_verification_receipt_binding.py
  test_registry_integrity.py
  test_ledger_hash_chain.py
  test_kernel_boot_panic.py
  test_diagnostic_stream.py
```

---

## Final Test Doctrine

Tests must prove failure semantics, not prompt quality.

```text
test_no_unhandled_worker_exception_reaches_taskgroup
test_timeout_does_not_cancel_swarm
test_schema_repair_attempted_once
test_schema_repair_failure_fails_closed
test_raw_output_preserved_on_repair
test_judge_cannot_assign_authority
test_worker_failure_forces_draft
test_judge_repair_forces_draft
test_worker_repair_caps_at_plausible
test_unresolved_dispute_caps_at_plausible
test_missing_evidence_caps_at_plausible
test_replay_verified_requires_verification_receipt
test_verification_receipt_wrong_hash_rejected
test_untrusted_verifier_rejected
test_revoked_verifier_rejected
test_registry_signature_mismatch_panics
test_stale_registry_panics
test_ledger_chain_break_panics
test_diagnostic_authority_weight_zero
test_diagnostic_hash_tamper_detected
test_diagnostic_audit_has_no_ledger_write_path
```

MVP success condition:

```text
A broken swarm still produces a valid authority receipt.
A broken boot still produces a diagnostic receipt.
A corrupt ledger prevents startup.
A stale registry prevents startup.
A fake replay flag cannot promote.
A model cannot assign authority.
A monitor cannot write authority.
```

---

## Phase Roadmap

### Phase 1A — Execution Kernel

Raw asyncio, workers, judge, Pydantic contracts, timeout handling, single repair policy, JSONL receipts.

### Phase 1B — Adversarial Harness

StubProvider, pytest, truth-table tests, timeout tests, schema-failure tests, receipt roundtrip tests.

### Phase 1C — Cryptographic Sealing

Canonical JSON, SHA-256, Ed25519 receipt signatures, sealed receipts.

### Phase 1D — Ledger and Registry

Hash-chained ledger, portalocker locking, source-pinned root key, signed registry, immutable registry snapshot.

### Phase 1E — Boot and Panic Doctrine

Strict boot protocol, state version tracking, DiagnosticReceipt, panic codes, exit codes, stderr format.

### Phase 1F — DiagnosticAudit CLI

Read-only diagnostic verifier, summary, latest, tail, find.

### Phase 2 — LangGraph Port

Only after Phase 1 invariants pass. Workers become graph nodes. Shared state becomes graph state. Receipt writer becomes terminal node.

### Phase 3 — Hosted Mobile Console

FastAPI backend, simple mobile UI, run history, authority labels, dissent tab, diagnostic panel.

### Phase 4 — Enterprise Hardening

Vault/KMS-backed signing keys, transparency-log anchoring, external replay service, distributed locking, registry distribution, OS-level least privilege.

---

## Freeze Statement

```text
SPECIFICATION != EXECUTION
DESIGN != REPLAY
CONSENSUS != AUTHORITY
NO RECEIPT, NO AUTHORITY
```

This file is the corrected architecture index. Full implementation should begin with Phase 1A and Phase 1B tests before any LangGraph, CrewAI, UI, or autonomous tool layer is added.
