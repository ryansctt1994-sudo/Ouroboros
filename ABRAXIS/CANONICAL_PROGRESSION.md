# Abraxis / Cathedral-OS: Canonical Progression Document

**Version:** 1.0  
**Date:** 2026-03-01  
**Status:** Living document — gaps marked explicitly where source PDFs are absent

---

## Purpose

This document consolidates the scattered session notes, transcripts, and architecture sketches
from the ABRAXIS research thread into a single, coherent reference.  It tracks the conceptual
journey from the early **Abraxis** exploration (multi-agent coherence, mycelial memory, quantum-
inspired encodings) through the current **Cathedral-OS** specification (Bevy ECS, KyuGraph,
GraphBit, hardware possession).

---

## Narrative Progression (Phases)

### Phase 0 — Void Initialization
*Source: `rituals_map.py`, `SESSION_TRANSCRIPTS.md`*

The foundational insight: structure must precede signal.  Ritual 0 established that 100 % of
unstructured prompts were vetoed.  An empty truth-space produces only silence.

> **Key lesson:** Build the walls (auth, feature flags, integrity) before adding signal.

---

### Phase 1 — Mycelial Substrate
*Source: `MYCELIAL_BRIDGE_SUMMARY.md`, `docs/session_artifacts/SESSION_SUMMARY.md`*

The network metaphor shifted from trees to mycelium: growth via branching/anastomosis, nutrient-
guided exploration, spore reproduction, and decentralised BFT consensus — mirroring how fungal
networks share resources without a central hub.

Four differentiators from standard neural networks:

| Property | Description |
|---|---|
| Growth not training | Topology changes over time (branch, prune, anastomose) |
| Nutrient-guided exploration | Follows knowledge-manifold gradients, not only loss gradients |
| Spore reproduction | Compressed subgraph neuroevolution; topology transferred across nodes |
| BFT consensus | Local Byzantine-fault-tolerant rounds analogous to nutrient sharing |

**Implementation artefact:** `python-bridge/eden_ecs/forge_bridge.py` + `mycelial_components.py`

---

### Phase 2 — Multi-Agent Consensus: Tri-Weavon
*Source: assumed from session notes; corresponding PDF **not present** in ABRAXIS — see gap note Γ-1*

The **Tri-Weavon** model extends binary consensus to a three-strand braid:

```
Agent A ──╮
           ├──▶  Weave Round  ──▶  Consensus State ∈ {+1, 0, −1}
Agent B ──╯╮
Agent C ────╯
```

- Strand 1 (α): positive-valence evidence
- Strand 2 (0): null/abstention
- Strand 3 (ω): negative-valence evidence

The sum invariant **α + ω = 15** (see Phase 3 — Two-Rail Encoding) constrains the weave so that
opposing rails always balance to the same total.

**> Gap Γ-1:** No Tri-Weavon PDF found in `ABRAXIS/`.  Content reconstructed from `SESSION_TRANSCRIPTS.md`
> and `ELPIS/METACUBE/forge_standalone/src/consensus.rs` (PBFT threshold logic).

---

### Phase 3 — Two-Rail Encoding  (α + ω = 15)
*Source: `SESSION_TRANSCRIPTS.md` (Symbolic Fidelity Markers); assumed PDF **TwoRailEncoding.pdf** absent — see Γ-2*

The Two-Rail Encoding assigns a numeric complement pair to every binary symbol:

| Rail | Symbol | Numeric value |
|---|---|---|
| Alpha (α) | positive / affirm | `a` |
| Omega (ω) | negative / negate | `15 − a` |

The invariant `α + ω = 15` ensures that corrupted single-rail transmission can be detected and
reconstructed from the surviving rail.  When both rails arrive intact, the sum provides an
integrity checksum; a deviation flags tampering or noise.

Relationship to ternary state space Σ = {+1, 0, −1}: the midpoint of the 0–15 range (7.5) maps to
the ternary null state.

**> Gap Γ-2:** `TwoRailEncoding.pdf` not found in `ABRAXIS/`.  The encoding is reconstructed
> from the Symbolic Fidelity Markers section of `SESSION_TRANSCRIPTS.md` and the Setun ternary
> design referenced in `docs/session_artifacts/SESSION_SUMMARY.md`.

---

### Phase 4 — Coherence-MCP and Phasonic Scheduler/Bridge
*Source: assumed PDFs **CoherenceMCP.pdf** and **PhasonicScheduler.pdf** absent — see Γ-3, Γ-4*

**Coherence-MCP** is the Model Context Protocol layer responsible for maintaining coherent shared
context across multiple agents.  It tracks:

- Current active rails (which agents hold which encoding rails)
- Coherence score C ∈ [0, 1] computed from pairwise agreement
- Veto threshold: if C < 0.5 any agent may broadcast a veto

**Phasonic Scheduler** schedules work according to a phase-locked loop (PLL) analogous to the
`HyphalNodeComponent.advance_phase()` implementation:

```
phase += 2π × freq × Δt      (default freq = 0.0997 Hz — the "Chuckle Constant")
PLL correction gain ≈ 0.332
Synchronised when |phase_error| < 0.1 radians
```

The **Phasonic Bridge** connects the scheduler to external tool-calling surfaces (MCP servers,
WebSocket endpoints) by mapping phase gates to permission windows:  a tool call is admitted only
when the scheduling phase is within the authorised sector.

**> Gap Γ-3:** `CoherenceMCP.pdf` not found.  Reconstructed from `python-bridge/` PLL code.  
**> Gap Γ-4:** `PhasonicScheduler.pdf` not found.  Reconstructed from `MYCELIAL_BRIDGE_SUMMARY.md`
> and `HyphalNodeComponent` source.

---

### Phase 5 — Lindblad Modeling and Silk Damping Tail (R ≈ e/2 ≈ 1.36)
*Source: assumed PDF **LindbladSilk.pdf** absent — see Γ-5*

The system uses a **Lindblad master-equation** formalism to model decoherence of agent state under
environmental noise:

```
dρ/dt = −i[H, ρ] + Σ_k (L_k ρ L_k† − ½{L_k†L_k, ρ})
```

where ρ is the density matrix of the agent's belief state, H is the Hamiltonian of the knowledge
space, and L_k are Lindblad jump operators (each representing a noise channel such as truncated
context, hallucination injection, or latency spikes).

The **Silk Damping Tail** refers to the asymptotic damping envelope:

```
R  ≈  e / 2  ≈  1.3591...
```

This value emerges from the leading eigenvalue of the Lindblad superoperator for the canonical
two-level Silk noise model: the ratio of the steady-state coherence to the initial coherence
approaches `e/2` in the long-time limit.  Practically it sets the floor below which additional
damping operators produce diminishing returns.

**> Gap Γ-5:** No Lindblad/Silk PDF found.  Derived from session discussion; exact operator
> definitions depend on the specific noise model used per deployment.

---

### Phase 6 — Hybrid Vector-Graph Memory (Qdrant + Neo4j / GraphRAG)
*Source: `docs/ARCHITECTURE.md`, `knowledge_base.json`, assumed PDF absent — Γ-6*

Memory architecture is **dual-rail** (mirroring the Two-Rail encoding):

| Store | Technology | Purpose |
|---|---|---|
| Vector | Qdrant | Semantic similarity search; embedding neighbours |
| Graph | Neo4j / KyuGraph | Relational provenance, causal chains, entity linking |

**GraphRAG** combines both: a retrieval query hits Qdrant for top-k candidates, then expands
through the Neo4j/KyuGraph subgraph to surface relational context not captured by cosine distance
alone.

The `knowledge_base.json` file in the repo root is a flat-file stub that can be swapped out for a
live Qdrant/Neo4j backend without changing the agent interface (see `geodesic_mycelium_agent/agent.py`).

**> Gap Γ-6:** Full GraphRAG PDF absent.  The hybrid approach is documented in
> `docs/ARCHITECTURE.md` (LOL:D Memory section) and `vectors.json`.

---

### Phase 7 — Mycelium / Bio-Digital Interfaces
*Source: `MYCELIAL_BRIDGE_SUMMARY.md`, `EDEN-ECS/` framework*

The bio-digital interface layer is expressed through the EDEN-ECS `MycelialSync` system.
Concrete implementation details live in `python-bridge/eden_ecs/mycelial_components.py`.

Conceptual model:
- **Spore** = compressed subgraph checkpoint  
- **Hypha** = directed edge carrying phase-locked timing signal  
- **Anastomosis** = merging of two agent subgraphs when their cosine similarity > threshold τ  
- **Fruit body** = materialised agent response (a completed reasoning chain persisted to GraphBit)

---

### Phase 8 — Cathedral-OS Specification
*Source: `docs/SYMBIONT_LORE_SPEC.md`, `MASTERSTACK_KERNEL_v2.0.kernel`, implied Bevy ECS design*

Cathedral-OS is the name for the full integrated runtime.  Key specification items:

#### 8a. Bevy ECS Required Components / Observers

Bevy's `#[require(Component)]` macro and the new **Observers** system (event-driven, reactive)
replace the polling tick-loop for low-latency component updates.  Required components:

| Component | Purpose |
|---|---|
| `AgentState` | Current phase, coherence score, active rails |
| `MemoryHandle` | Pointer into the hybrid vector-graph memory |
| `ToolRegistry` | Available MCP tools and permission windows |
| `PhasonicClock` | PLL phase accumulator |

Observers fire when `AgentState.coherence` drops below the veto threshold, triggering a
`CoherenceVetoEvent` that propagates to all braid-partner agents.

#### 8b. KyuGraph

KyuGraph is the project-internal graph engine (lightweight, embedded, no external process).
It exposes a property-graph API compatible with Neo4j Cypher for query portability.  At runtime
it is backed by `GraphBit`.

#### 8c. GraphBit

GraphBit is the binary-serialised on-disk format for KyuGraph snapshots.  Each bit-packed node
record stores:

```
[entity_id: u64][component_flags: u32][edge_list_offset: u32]
```

Providing O(1) random access to any entity by ID and O(deg) adjacency traversal.

---

### Phase 9 — Promethean Reckoning: Hardware Possession
*Source: `hardware/` directory (if present), assumed PDF **PrometheanReckoning.pdf** absent — Γ-7*

The **Promethean Reckoning** refers to the decision to anchor the system to specific high-performance
edge hardware rather than cloud-only deployment:

| Hardware | Role |
|---|---|
| NVIDIA Thor (Orin successor) | Primary inference SoC; INT8/FP8 quantised models |
| NVIDIA Orin | Current generation edge SoC; fallback / dev target |
| GSP / RISC-V firmware | GPU System Processor; runs scheduling and power control |

The RISC-V GSP firmware is the lowest-privilege trust anchor: it runs the Phasonic Bridge
permission checks before any GPU kernel is launched.  This fulfils the "Gavel" pillar from
`docs/SYMBIONT_LORE_SPEC.md` (formal verification of AI bids at the hardware level).

**> Gap Γ-7:** `PrometheanReckoning.pdf` not found.  Hardware details sourced from
> `docs/SYMBIONT_LORE_SPEC.md` and `ANDROID_RUSTORACLE_SUMMARY.md`.

---

## Gap Register

| ID | Expected artefact | Status | Equivalent / fallback |
|---|---|---|---|
| Γ-1 | Tri-Weavon PDF | ❌ absent | `SESSION_TRANSCRIPTS.md` + `consensus.rs` |
| Γ-2 | TwoRailEncoding PDF | ❌ absent | `SESSION_TRANSCRIPTS.md` Symbolic Fidelity Markers |
| Γ-3 | CoherenceMCP PDF | ❌ absent | `python-bridge/` PLL implementation |
| Γ-4 | PhasonicScheduler PDF | ❌ absent | `MYCELIAL_BRIDGE_SUMMARY.md` |
| Γ-5 | LindbladSilk PDF | ❌ absent | Session discussion notes |
| Γ-6 | GraphRAG PDF | ❌ absent | `docs/ARCHITECTURE.md`, `vectors.json` |
| Γ-7 | PrometheanReckoning PDF | ❌ absent | `docs/SYMBIONT_LORE_SPEC.md`, `ANDROID_RUSTORACLE_SUMMARY.md` |

---

## Concept-to-Source Provenance Map

| Concept | Phase | Primary source(s) | Gap? |
|---|---|---|---|
| Tri-Weavon / multi-agent consensus | 2 | `consensus.rs`, `SESSION_TRANSCRIPTS.md` | Γ-1 |
| Coherence-MCP | 4 | `python-bridge/eden_ecs/` | Γ-3 |
| Two-Rail Encoding (α+ω=15) | 3 | `SESSION_TRANSCRIPTS.md` | Γ-2 |
| Phasonic scheduler / bridge | 4 | `MYCELIAL_BRIDGE_SUMMARY.md`, `mycelial_components.py` | Γ-4 |
| Lindblad modeling | 5 | Session notes | Γ-5 |
| Silk damping tail R≈e/2≈1.36 | 5 | Session notes | Γ-5 |
| Hybrid vector-graph memory (Qdrant+Neo4j) | 6 | `docs/ARCHITECTURE.md`, `knowledge_base.json` | Γ-6 |
| GraphRAG | 6 | `vectors.json`, `docs/ARCHITECTURE.md` | Γ-6 |
| Mycelium / bio-digital interfaces | 7 | `MYCELIAL_BRIDGE_SUMMARY.md`, `mycelial_components.py` | — |
| Cathedral-OS / Bevy ECS required components | 8a | `docs/SYMBIONT_LORE_SPEC.md` | — |
| Bevy Observers | 8a | Architecture design notes | — |
| KyuGraph | 8b | `MASTERSTACK_KERNEL_v2.0.kernel` | — |
| GraphBit | 8c | `MASTERSTACK_KERNEL_v2.0.kernel` | — |
| Promethean Reckoning (Thor/Orin, GSP/RISC-V) | 9 | `docs/SYMBIONT_LORE_SPEC.md`, `ANDROID_RUSTORACLE_SUMMARY.md` | Γ-7 |

---

## How to Use This Document

1. **Orient yourself** using the Phase narrative above.
2. **Find the source** of any concept via the Provenance Map.
3. **Check the Gap Register** before citing a concept — if the source PDF is absent, the entry
   notes the equivalent code or prose file used as a substitute.
4. **Fire up the agent** with `python -m geodesic_mycelium_agent --dry-run` (see
   `geodesic_mycelium_agent/README.md`).
