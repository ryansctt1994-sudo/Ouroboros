# OS–AI Kernel Boundary: Foundational Principles

## Overview

The OS–AI boundary is not merely an interface—it is a **semantic grinder** where intent is irreversibly compressed into consequence.

## Core Axioms

### 1. No Layer May Certify Its Own Correctness
- Not the model
- Not the runtime
- Not the orchestration logic
- Only the environment—the part that can kill the process—decides what is real

### 2. Containment Is Environmental, Not Contractual
- True containment is a property of the environment that does not care what the agent believes
- A kernel-enforced boundary does not negotiate, interpret, or empathize
- It simply refuses states that violate physics

### 3. Fail-Closed Punishes Uncertainty, Not Behavior
- Unknown states are more dangerous than known failures
- If the system cannot verify, it must terminate
- This is epistemic hygiene, not pessimism

### 4. Minimal Vocabulary = Attack Surface Reduction
- Every new verb is a new grammar
- Every new grammar is a new place for intent to hide
- Reducing the action space prevents unintended semantics from emerging

### 5. One-Way Observability
- The AI can be observed by the host
- The AI cannot infer host state beyond what is explicitly leased
- "Ignorant stops look stronger"

## Properties of a Strong Boundary

| Property | Description |
|----------|-------------|
| Kernel-enforced invariants only | No safety property depends on AI honesty |
| One-way observability | AI cannot infer host state |
| Fail-closed defaults | Ambiguity resolves to termination |
| Minimal syscall vocabulary | Fewer verbs = fewer unintended sentences |
| No semantic feedback | AI should not learn *why* it was stopped |

## The Core Insight

> Any place where the AI's model of the OS matters more than the OS's model of the AI is a failure point.

Reality is defined by physics, not explanations. The moment explanations influence enforcement, the boundary weakens.
