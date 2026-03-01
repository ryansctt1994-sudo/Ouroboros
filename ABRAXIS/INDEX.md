# ABRAXIS Docs Index / Manifest

This manifest links every known ABRAXIS artefact to the relevant section of
[`CANONICAL_PROGRESSION.md`](CANONICAL_PROGRESSION.md).

---

## Repository files (present)

| File | Type | Canonical section(s) |
|---|---|---|
| `SESSION_TRANSCRIPTS.md` (root) | Session notes | Phase 1, Phase 3 |
| `MYCELIAL_BRIDGE_SUMMARY.md` (root) | Summary | Phase 1, Phase 4, Phase 7 |
| `docs/session_artifacts/SESSION_SUMMARY.md` | Session summary | Phase 1 |
| `rituals_map.py` (root) | Python ritual map | Phase 0 |
| `python-bridge/eden_ecs/forge_bridge.py` | Python code | Phase 1, Phase 4 |
| `python-bridge/eden_ecs/mycelial_components.py` | Python code | Phase 4, Phase 7 |
| `docs/ARCHITECTURE.md` | Architecture doc | Phase 6 |
| `docs/SYMBIONT_LORE_SPEC.md` | Lore + engineering spec | Phase 8, Phase 9 |
| `MASTERSTACK_KERNEL_v2.0.kernel` | Kernel spec | Phase 8 (KyuGraph, GraphBit) |
| `ANDROID_RUSTORACLE_SUMMARY.md` (root) | Summary | Phase 9 |
| `knowledge_base.json` (root) | Flat memory stub | Phase 6 |
| `vectors.json` (root) | Vector index stub | Phase 6 |
| `ELPIS/METACUBE/forge_standalone/src/consensus.rs` | Rust source | Phase 2 |
| `ABRAXIS/CANONICAL_PROGRESSION.md` | **This canonical doc** | All phases |
| `geodesic_mycelium_agent/` | Python agent scaffold | All phases (runtime) |

---

## Expected PDFs (absent — gaps)

These PDFs are referenced in session notes but not present in the repository.
Each entry points to the gap entry in the canonical doc.

| Expected filename | Topic | Gap ID | Equivalent on-disk |
|---|---|---|---|
| `TwoRailEncoding.pdf` | Two-Rail Encoding (α+ω=15) | Γ-2 | `SESSION_TRANSCRIPTS.md` |
| `TriWeavon.pdf` | Tri-Weavon multi-agent consensus | Γ-1 | `consensus.rs` |
| `CoherenceMCP.pdf` | Coherence-MCP | Γ-3 | `forge_bridge.py` |
| `PhasonicScheduler.pdf` | Phasonic scheduler / bridge | Γ-4 | `mycelial_components.py` |
| `LindbladSilk.pdf` | Lindblad modeling + Silk tail | Γ-5 | session notes |
| `GraphRAG.pdf` | Hybrid vector-graph memory | Γ-6 | `docs/ARCHITECTURE.md` |
| `PrometheanReckoning.pdf` | Hardware possession (Thor/Orin) | Γ-7 | `ANDROID_RUSTORACLE_SUMMARY.md` |

---

## How to add a new PDF

1. Drop the PDF into this `ABRAXIS/` folder.
2. Add a row to the **Repository files** table above with its type and phase(s).
3. Remove (or update) the corresponding row in the **Expected PDFs** table.
4. Update `CANONICAL_PROGRESSION.md` to replace the gap note with a proper citation.
