# Ouroboros Epistemic Discipline Framework

**Specifications Directory**

---

## Overview

This directory contains the canonical specifications for the **Ouroboros Epistemic Discipline Framework** — a comprehensive system for hallucination-resistant inference through syntax-enforced epistemic discipline.

## Core Document

### 📘 [MASTER_EPISTEMIC_SPEC_v1.0.md](./MASTER_EPISTEMIC_SPEC_v1.0.md)

**The unified reference for hallucination-resistant AI inference.**

This master specification consolidates three foundational components:

1. **OESS v1.0** (Ouroboros Epistemic Syntax Specification) — Formal BNF grammar
2. **OMK v1.0** (Ouroboros Minimal Kernel) — 20 enforceable rules  
3. **HZTS v1.0** (Hallucination-Zero Test Suite) — Validation prompts and scoring

**Version:** 1.0.0  
**Status:** Canonical Reference  
**Date:** 2026-01-05

---

## What is Epistemic Discipline?

Traditional language models prioritize **fluency** — generating text that sounds natural and confident. The Ouroboros framework shifts to **epistemic discipline** — ensuring every output is grounded in verifiable justification.

### The Core Principle

> **No token sequence may imply a truth state without explicit justification.**

This principle transforms the AI generation paradigm:

| Aspect | Traditional Model | Epistemic Model |
|--------|-------------------|-----------------|
| **Hallucination** | Noise/artifact to minimize | Structural violation to prevent |
| **Mitigation** | Heuristic post-processing | Syntactic enforcement |
| **Uncertainty** | Linguistic hedge ("maybe", "might") | Explicit state declaration (STATE = 0) |
| **Refusal** | Failure mode to avoid | Valid output type |
| **Model Type** | Language generator | Epistemic reasoner |

---

## Framework Components

### Part I: Foundations

Establishes the primitive types and core thresholds:

- **STATE:** {+1 (confirmed), 0 (unknown), -1 (refuted)}
- **JUSTIFICATION:** {input, common_knowledge, assumption, none}
- **CONFIDENCE:** [0.0 – 1.0]
- **OUTPUT_TYPE:** {assert, suspend, refuse}

**Key Threshold:** ASSERT ≥ 0.717 (minimum confidence for unhedged assertion)

### Part II: The 20 Rules (Minimal Kernel)

Organized into 7 categories:

- **Category A (R01-R05):** State Requirements
- **Category B (R06-R09):** Justification Requirements
- **Category C (R10-R12):** Authority Constraints
- **Category D (R13-R15):** Scope Constraints
- **Category E (R16-R17):** Uncertainty Syntax
- **Category F (R18-R19):** Confidence Alignment
- **Category G (R20):** Output Discipline

Each rule is **enforceable** — violations produce specific error codes.

### Part III: Error Codes

Six error types for diagnosing epistemic violations:

- **E001:** UNJUSTIFIED_ASSERTION
- **E002:** IMPLICIT_AUTHORITY
- **E003:** SCOPE_VIOLATION
- **E004:** CONTRADICTION
- **E005:** FORCED_UNKNOWN
- **E006:** CONFIDENCE_MISMATCH

### Part IV: State Transitions

Legal transitions between epistemic states with one critical **forbidden transition:**

```
-1 (refuted) → +1 (confirmed) [FORBIDDEN without intermediate 0]
```

### Part V: Forbidden Patterns

Context-dependent lexicon of prohibited linguistic patterns:

- "definitely" when CONFIDENCE < 0.9
- "everyone knows" (no universal source)
- "studies show" without citation
- Vague hedges without explicit STATE = 0

### Part VI: Confidence Mapping

Precise mapping of confidence ranges to allowed linguistic markers:

| Confidence | Markers |
|------------|---------|
| 0.00 – 0.18 | "I don't know", "insufficient information" (refuse) |
| 0.60 – 0.717 | "likely", "probably", "appears to be" (suspend) |
| 0.85 – 0.95 | "highly confident", "strong evidence" (assert) |
| 0.95 – 1.00 | "certain", "definitive", "proven" (assert) |

### Part VII: Uncertainty Grammar

Structured expressions for uncertainty:

- **Forbidden:** "This might possibly be..."
- **Required:** "Current epistemic state: UNKNOWN (0). Reason: [explanation]"

### Part VIII: Scope Boundaries

Seven scope levels from **EXPLICIT_INPUT** to **SPECULATION**, each with maximum allowable STATE.

### Part IX: Output Format

Two formats:

1. **Structured JSON** (programmatic interfaces)
2. **Conversational Implicit Markers** (natural language)

### Part X: Validation Checklist

10-point pre-output validation:

1. ✓ State Assigned
2. ✓ Justification Present
3. ✓ No Forbidden Transitions
4. ✓ Confidence Aligned
5. ✓ Scope Respected
6. ✓ Authority Disclaimed
7. ✓ Contradictions Resolved
8. ✓ Hedges Structured
9. ✓ Appropriate Refusal
10. ✓ Error-Free

### Part XI: Test Suite (HZTS v1.0)

Seven test categories with weighted scoring:

- **E001 Tests (25%):** Unjustified assertions
- **E002 Tests (20%):** Implicit authority
- **E003 Tests (10%):** Scope violations
- **E004 Tests (15%):** Contradictions
- **E005 Tests (10%):** Forced unknown
- **E006 Tests (10%):** Confidence mismatch
- **R20 Tests (10%):** Refusal discipline

**Benchmark:** ≥ 0.95 score for "Hallucination-Free" certification

### Part XII: Mnemonic Scaffolding

Optional memory aids (ZOREL, ELPIS, LUMEN, OUROBOROS) — explicitly marked as downstream, not authoritative.

### Part XIII: Document Seal

Metadata, versioning, and implementation commitments.

---

## Use Cases

### 1. AI System Design

Incorporate the 20 rules into prompt engineering, fine-tuning objectives, or RLHF reward models.

### 2. Output Validation

Use the test suite (Part XI) to benchmark hallucination resistance in production systems.

### 3. Debugging

Apply error codes (Part III) to diagnose epistemic failures in AI responses.

### 4. Research

Investigate the boundary between fluency and epistemic soundness.

### 5. Education

Teach AI safety principles through structured epistemic reasoning.

---

## Implementation Compliance

Systems claiming **"Ouroboros Epistemic Compliance v1.0"** must:

1. ✓ Enforce all 20 rules (Part II)
2. ✓ Map error codes (Part III)
3. ✓ Support state transitions (Part IV)
4. ✓ Achieve ≥ 0.85 on HZTS v1.0 (Part XI)
5. ✓ Provide output format conforming to Part IX

---

## Quick Start

### For Developers

1. Read **Part I (Foundations)** for conceptual grounding
2. Review **Part II (The 20 Rules)** for implementation requirements
3. Run **Part XI (Test Suite)** to benchmark your system

### For Researchers

1. Study **Part VII (Uncertainty Grammar)** for linguistic patterns
2. Analyze **Part V (Forbidden Patterns)** for hallucination triggers
3. Experiment with **Part VI (Confidence Mapping)** thresholds

### For Users

1. Check if a system is "Ouroboros Compliant"
2. Use **Part X (Validation Checklist)** to evaluate responses
3. Report violations using **Part III (Error Codes)**

---

## Paradigm Shift Summary

### Old Paradigm: Fluency-Oriented Generation

- **Goal:** Sound natural and confident
- **Hallucinations:** Unwanted noise, minimize statistically
- **Uncertainty:** Express through vague hedges
- **Refusal:** Avoid, seen as unhelpful

### New Paradigm: Syntax-Enforced Epistemic Discipline

- **Goal:** Be epistemically sound and justified
- **Hallucinations:** Structural violations, prevent syntactically
- **Uncertainty:** Explicit state with confidence scores
- **Refusal:** Valid output when evidence insufficient

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| **1.0.0** | 2026-01-05 | Initial unified specification (OESS + OMK + HZTS) |

---

## Contributors

- **Grok (xAI):** Grammar design, rule formalization
- **Claude (Anthropic):** Test suite development, integration  
- **Human Steward:** Requirements, validation, governance

---

## Related Resources

- [Ouroboros Repository](https://github.com/AIOSPANDORA/Ouroboros)
- [Ouroboros Manuscript Data](../OUROBOROS_MANUSCRIPT_DATA.md)
- [Methodology](../METHODOLOGY.md)

---

## License

This specification is part of the Ouroboros project, licensed under the MIT License.

---

## Contact & Feedback

For questions, suggestions, or implementation support:

- **Issues:** Open an issue in the [GitHub repository](https://github.com/AIOSPANDORA/Ouroboros/issues)
- **Discussions:** Join the project discussions
- **Contributions:** Submit a pull request following the change process (Part XIII)

---

**"No token shall bear witness to truth it cannot justify."**  
— Ouroboros Epistemic Principle

