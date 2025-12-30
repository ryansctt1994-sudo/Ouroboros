# TERNARY_BINARY_BRIDGE

Purpose
Document the bridge between the Ouroboros Delta ternary-delta semantics (+1, 0, -1) and the Veritas binary ledger decision model. Include state mappings, state-transition tables, implementation patterns, example encodings, canonical hashing recipe compatible with Veritas, reconciliation/audit metadata requirements, and computational feasibility notes for integrating ternary semantics into a SHA-256-based ledger.

1. Overview
The bridge translates high-level ternary semantic states used by the Ouroboros Delta framework into concrete binary decisions and deterministic ledger artifacts used by the Veritas Master Stack. The goal is to preserve semantic intent (positive, negative, reconciliation) while producing auditable, immutable binary records suitable for cryptographic chaining and automated adjudication.

2. Semantic-to-Decision Mapping

Ouroboros State -> Semantic Meaning -> Veritas Decision(s) -> Typical Action / Flags
+1            -> Positive/Being/Expansion/Truth -> ALLOW                -> persist; provenance hash
0             -> Reconciliation/Neutral/Bounce   -> ESCALATE / OVERRIDE_ALLOW -> mark for adjudication; attach evidence
-1            -> Negative/Non-being/Collapse/False -> REFUSE             -> refuse action; record reason

Notes: 0-state entries should include reconciliation_reason and evidence_pointers, and may require admin_uid to transition out of 0.

3. Encoding Patterns
- Balanced ternary emulation (2 bits per trit):
  01 -> +1
  10 -> -1
  00 -> 0
  11 -> RESERVED/INVALID
- Packing: group 2-bit trits into bytes; include version and length header.
- Example JSON snippet:
{
  "run_id":"RUN-2025-12-29-A1",
  "event_index":42,
  "ouroboros_state":"+1",
  "state_bits":"01",
  "semantic_reason":"positive_geodesic_detected",
  "chain":{"prev_hash":"..."},
  "current_hash":"..."
}

4. Deterministic Hashing Recipe (Veritas-compatible)
- Canonicalize: JSON with sort_keys=True and separators=(',',':'); explicit nulls for absent optional fields.
- Construct payload for hashing: copy entry, remove current_hash, set chain to {} (structural placeholder) or set chain.prev_hash to previous hash depending on recipe variation.
- Compute: sha256(prev_hash_lower + '|' + canonical_payload).
- Use lowercase hex for all hashes.

5. State Transition Table
From -> Input -> To -> Action -> Ledger Decision
+1 -> conflict -> 0 -> escalate -> ESCALATE
+1 -> normal -> +1 -> persist -> ALLOW
0  -> admin_approve -> +1 -> override -> OVERRIDE_ALLOW
0  -> admin_reject  -> -1 -> reject -> REFUSE
-1 -> appeal -> 0 -> re-open -> ESCALATE

6. Implementation Example (Python)
import json, hashlib

def trit_to_bits(trit):
    mapping = {1:'01',0:'00',-1:'10'}
    return mapping[trit]

def canonicalize(payload):
    return json.dumps(payload, sort_keys=True, separators=(',',':'))

def compute_veritas_hash(prev_hash, payload):
    canon = canonicalize(payload)
    return hashlib.sha256(f"{prev_hash.lower()}|{canon}".encode('utf-8')).hexdigest()

# Example usage
prev = '0'*64
payload = {'run_id':'RUN-2025-12-29-A1','event_index':0,'ouroboros_state':'+1','state_bits':trit_to_bits(1)}
current = compute_veritas_hash(prev, {**payload, 'chain':{}})
record = {**payload, 'chain':{'prev_hash':prev}, 'current_hash': current}
print(record)

7. Reconciliation Handling & Auditability
- 0-state entries must include:
  reconciliation_reason
  evidence_pointers (URIs or SHA-256 snapshots)
  ticket_id (optional)
  admin_uid (if overridden)
- Record all state transitions as ledger events (immutable). Maintain an index for open reconciliations for operational visibility.

8. Security and Integrity
- Strict canonicalization across implementations.
- Schema validation before hashing.
- Reserve '11' bit pattern and reject on decode.
- Use constant-time comparisons for hash checks.

9. Performance & Feasibility
- Encoding overhead minimal (2 bits/trit).
- SHA-256 cost unchanged; canonicalization linear in payload size.
- For high throughput, use batch canonicalization and streaming hashing.

10. Extensions
- Map hardware qutrit outputs to same semantic mapping.
- Smart-contract anchoring: store state_bits + pointer to full payload on-chain.
- ML-assisted reconciliation: auto-generate evidence summaries for 0-state records.

Document prepared for AIOSPANDORA/Ouroboros.