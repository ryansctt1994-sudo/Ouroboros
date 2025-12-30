# Ouroboros

Ouroboros: A project integrating the Ouroboros Delta ternary semantics with the Veritas binary ledger.

Contents
- OUROBOROS_DELTA_MANUSCRIPT.md — theoretical manuscript
- TERNARY_BINARY_BRIDGE.md — ternary→binary bridge documentation
- VERITAS_ALIGNMENT.md — operational ledger integration (this file)
- FALSIFIABILITY_AUDIT.md — tests and measurable predictions
- METHODOLOGY.md — experimental and reproducibility notes
- visualization/torus_geodesics.py — enhanced plotting script (geodesics + curvature)
- visualization/README.md — how to run visualization locally
- requirements.txt — Python dependencies
- LICENSE — CC BY 4.0

Usage
1. Install dependencies: pip install -r requirements.txt
2. Run visualization: python visualization/torus_geodesics.py (requires a display or use a headless backend and save figures)
3. Run tests: see tests/ (not included) — use fixtures in /tests/fixtures

Contributing
- Open issues or PRs against this repository. Maintain canonicalization compatibility when changing payload schemas.

License
This project is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0). See LICENSE for details.

---
