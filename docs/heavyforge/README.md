# HEAVYFORGE v0.1

Status: `ARCHITECTURE_FROZEN_FOR_PHASE_1_IMPLEMENTATION`  
Authority: `DESIGN_SPECIFICATION`  
Authority Weight: `0`

HEAVYFORGE v0.1 is a parallel reasoning kernel for Grok Heavy-like test-time compute. It is not an agent chatroom. It is an execution discipline for running multiple model workers, validating their outputs, adjudicating disagreement, calculating authority deterministically, and preserving audit receipts.

## Prime Doctrine

```text
Capability may propose.
Models may witness.
Judges may analyze.
Only the Kernel may authorize.
Only external replay may promote to REPLAY_VERIFIED.
```

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
  -> Optional external VerificationReceipt
  -> Kernel promotion check
```

## Non-Negotiable Invariants

```text
Consensus is not authority.
Confidence is not authority.
A model may not assign its own legitimacy.
A raw boolean may not promote authority.
Formatting repair is tainted evidence.
A repaired Judge forces DRAFT.
REPLAY_VERIFIED requires a signed external VerificationReceipt.
Boot failures never enter the authority ledger.
Diagnostics have authority_weight = 0.
```

## Core Components

| Component | Role | Authority |
|---|---|---:|
| Worker agents | Produce structured witness outputs | None |
| Judge | Produces structured adjudicative analysis | None |
| Kernel | Calculates authority deterministically | Yes |
| Authority Ledger | Stores sealed authority receipts | Records only |
| Diagnostic Stream | Stores boot/failure diagnostics | None |
| Trusted Verifier Registry | Signed trust policy for verifiers | Policy only |
| External Verifier | Produces signed replay evidence | Evidence only |

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

## Authority Levels

```text
DRAFT
PLAUSIBLE
EVIDENCE_SUPPORTED
REPLAY_VERIFIED
```

Rules:

```text
Any worker failure -> DRAFT.
Judge failure -> DRAFT.
Judge repair -> DRAFT.
Worker repair -> PLAUSIBLE maximum.
Unresolved disputes -> PLAUSIBLE maximum.
Missing evidence -> PLAUSIBLE maximum.
Clean evidence-supported run -> EVIDENCE_SUPPORTED.
Signed external replay verification -> REPLAY_VERIFIED.
```

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

## Freeze Statement

```text
SPECIFICATION != EXECUTION
DESIGN != REPLAY
CONSENSUS != AUTHORITY
NO RECEIPT, NO AUTHORITY
```

This file is the initial architecture index. Full implementation should begin with Phase 1A and Phase 1B tests before any LangGraph, CrewAI, UI, or autonomous tool layer is added.
