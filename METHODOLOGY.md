# METHODOLOGY

Purpose
Describe experimental setup, reproducibility notes, data schema, benchmarking procedures, and how to reproduce results from the FALSIFIABILITY_AUDIT.

1. Environment
- Python >=3.9
- Required packages: see requirements.txt
- Recommended: docker image with pinned package versions for reproducibility

2. Reproducible Runs
- Use fixed RNG seeds where relevant. Include environment.yml or Dockerfile for exact environments.

3. Data Schema (ledger event)
- run_id: string
- event_index: integer
- ouroboros_state: "+1" | "0" | "-1"
- state_bits: string (2-bit representation)
- semantic_reason: string
- chain: { prev_hash: hex64 }
- current_hash: hex64

4. Benchmarking
- Deterministic Hash Test: script in tests/ to run canonicalization across nodes and compare hashes.
- Geodesic Benchmarks: measure integration time and error vs reference integrator.

5. Artifacts
- All generated artifacts (fixtures, CSVs, logs) should be stored alongside commit and optionally anchored in the ledger for traceability.

---
