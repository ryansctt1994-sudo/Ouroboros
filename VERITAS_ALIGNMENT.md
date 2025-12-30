# VERITAS_ALIGNMENT

Purpose
This document describes operational integration between the Ouroboros Delta semantic framework and the Veritas Master Stack ledger. It covers manifest-tip policy, verifier notes, decision flows, API endpoints, and example payloads to enable deterministic, auditable binary anchoring of ternary semantic events.

1. Overview
The Veritas alignment translates Ouroboros ternary semantics into Veritas ledger artifacts, ensuring deterministic hashing, canonical payloads, and adjudication workflows. Veritas remains a SHA-256 anchored append-only ledger with manifest-tip policies to support replication and verification.

2. Manifest-tip Policy
- Each node maintains a manifest pointing to the current tip(s) of the ledger.
- Manifest entries include: tip_hash, tip_index, timestamp, node_id, and signature.
- Policy: only tips that validate canonical payloads and schema are accepted. Conflicting tips trigger an adjudication window where the majority-validated tip is selected, while the others are marked contested.

3. Verifier Notes
- Canonicalization: JSON with sort_keys=true, separators=(',',':'), explicit nulls for optional fields.
- Before hashing, remove or zero current_hash and include chain.prev_hash as provided.
- Verification steps:
  1. Retrieve record and canonicalize according to schema.
  2. Recompute sha256(prev_hash + '|' + canonical_payload) and compare with current_hash.
  3. Validate schema and evidence pointers for 0-state entries.

4. Decision Flow & API Examples
- Decisions: ALLOW, REFUSE, ESCALATE, OVERRIDE_ALLOW
- Example POST /ledger/events payload (ternary-annotated):
{
  "run_id":"RUN-2025-12-29-A1",
  "event_index":42,
  "ouroboros_state":"+1",
  "state_bits":"01",
  "semantic_reason":"positive_geodesic_detected",
  "chain":{"prev_hash":"<64-hex>"}
}

- Example response:
{
  "status":"accepted",
  "current_hash":"<64-hex>",
  "manifest_tip":"<64-hex>",
  "decision":"ALLOW"
}

5. Adjudication & Reconciliation
- 0-state entries create tickets for evidence review. Tickets include evidence_pointers, proof snapshots, and time-bounded windows for admin action.
- Admin override records must include admin_uid, justification, and link to the updated ledger event.

6. Verifier API Contract
- GET /ledger/verify?hash=<sha256> → returns verification status and canonical payload
- GET /ledger/tip → returns current manifest tip(s)
- POST /ledger/events → submit event (returns current_hash and acceptance status)

7. Operational Recommendations
- Keep canonicalization library consistent across nodes.
- Use streaming/ incremental mechanisms for large payloads.
- Log and audit all adjudication steps as separate ledger events for immutability.

---
