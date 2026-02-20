RITUALS MAP: FROM VOID TO CATHEDRAL
====================================

This module unites the three experimental rituals and maps each
finding to its concrete engineering action in AIOSPANDORA/Ouroboros.

Ritual 0 (Complete): The Void — D0 at β=5.0, no Forms
  Result:  100/100 vetoed. Silence prevails.
  Lesson:  Truth requires structure.
  Action:  Build the walls (auth, feature flags, integrity).

Ritual A (Ready): The Whisper — D0 with increasing resonance
  Predict: Convergence to zero at high H — empty truth.
  Lesson:  Convergence ≠ truth. Damping without Forms is empty.
  Action:  Rate limiting alone is insufficient; combine with auth.

Ritual B (Ready): The Storm — D2/D3 with escalating chaos
  Predict: Walls hold to ~β=20-50, then Latch can't detect signal.
  Lesson:  Even correct architecture has detection limits.
  Action:  Nightly stress CI to find and monitor breaking points.

This file serves as the canonical reference linking experimental
results to engineering decisions.


# ═══════════════════════════════════════════════════════════════
# THE MAP: Experimental Finding → Engineering Action
# ═══════════════════════════════════════════════════════════════

RITUALS_MAP = {
    "ritual_0_void": {
        "experiment": "D0 at β=5.0, no Forms, 100 trials",
        "result": "100/100 vetoed — silence",
        "finding": "Truth requires structure (Forms as attractors)",
        "actions": [
            {
                "id": "AUTH_CLEAR",
                "description": "Add bearer-token auth to /clear endpoint",
                "rationale": (
                    "Without auth, /clear is D0 — no walls, anyone can "
                    "wipe state. The token is the Form that gives the "
                    "endpoint its purpose boundary."
                ),
                "implementation": {
                    "mechanism": "ADMIN_API_KEY env var",
                    "header": "Authorization: Bearer <key>",
                    "default": "Endpoint disabled in production",
                    "flag": "ALLOW_CLEAR_ENDPOINT=false",
                },
            },
            {
                "id": "FIX_RECURSION",
                "description": "Rename chat route handler to break recursion",
                "rationale": (
                    "The recursive handler is self-inflicted D0 — the "
                    "Winged-One calling itself, spiraling without convergence. "
                    "Renaming creates the structural boundary (Form) that "
                    "lets the function resolve."
                ),
                "implementation": {
                    "rename": "fake_ai_response → chat_handler",
                    "keep": "fake_ai_response(msg) as standalone helper",
                },
            },
            {
                "id": "BIND_LOCALHOST",
                "description": "Default Flask bind to 127.0.0.1",
                "rationale": (
                    "Binding to 0.0.0.0 is opening the cathedral to the "
                    "void. Default to localhost; make external binding "
                    "opt-in via HOST env var."
                ),
                "implementation": {
                    "default_host": "127.0.0.1",
                    "override": "HOST=0.0.0.0 (env var)",
                },
            },
        ],
    },

    "ritual_a_whisper": {
        "experiment": "D0 with H swept from 0.0 to 5.0",
        "predicted_result": "Convergence to zero at high H — empty truth",
        "finding": "Convergence ≠ truth; damping without Forms is meaningless",
        "actions": [
            {
                "id": "RATE_LIMIT_WITH_AUTH",
                "description": "Rate limiting must accompany authentication",
                "rationale": (
                    "Rate limiting alone (resonance without Forms) only "
                    "slows chaos — it converges to 'zero' (a calm but "
                    "unprotected state). Combined with auth, the rate "
                    "limit becomes meaningful structure."
                ),
                "implementation": {
                    "library": "Flask-Limiter",
                    "chat_limit": "20/minute per IP",
                    "clear_limit": "2/minute per IP",
                    "env_override": "CHAT_RATE_LIMIT, CLEAR_RATE_LIMIT",
                    "note": "Only effective when paired with bearer auth",
                },
            },
        ],
    },

    "ritual_b_storm": {
        "experiment": "D2/D3 with β swept from 1.0 to 100.0",
        "predicted_result": "Walls hold to ~β=20-50; Latch vetoes beyond",
        "finding": "Detection has limits; truth may exist but be unobservable",
        "actions": [
            {
                "id": "NIGHTLY_STRESS_CI",
                "description": "Nightly stress CI to find breaking points",
                "rationale": (
                    "The Storm proves that even correct architecture has "
                    "a chaos threshold. Nightly stress tests are the "
                    "automated Storm — continuously probing the walls."
                ),
                "implementation": {
                    "schedule": "00:00 UTC nightly",
                    "suites": [
                        "agent_interface/recursive_crucible",
                        "distributed/config_registry stress",
                        "GGCC Phase 3 (if < 2h)",
                        "RustOracle stability (if < 2h)",
                    ],
                    "runner": "ubuntu-latest (CPU only)",
                    "timeout": "2 hours max",
                    "artifacts": "Upload logs, plots, reports",
                },
            },
            {
                "id": "REGISTRY_INTEGRITY",
                "description": "Registry integrity hash chain (Sentinel Lock)",
                "rationale": (
                    "The Sentinel Lock in the experiment detects divergence "
                    "by hashing each step. The registry monitor does the "
                    "same for configuration — each write is chained, and "
                    "startup verification catches tampering."
                ),
                "implementation": {
                    "approach": "SHA256 hash chain per entry",
                    "storage": "Inline prev_hash field in each entry",
                    "startup": "Full chain verification on load",
                    "on_failure": "Refuse to start (fail closed)",
                    "future": "Optional HMAC signing hook",
                },
            },
            {
                "id": "TABLET_DURABILITY",
                "description": "Fsync + atomic writes for Tablet ledger",
                "rationale": (
                    "Without fsync, a crash during write corrupts the "
                    "ledger — the equivalent of the Storm destroying the "
                    "Latch's memory. Atomic writes ensure the last known "
                    "good state is always recoverable."
                ),
                "implementation": {
                    "write_pattern": "Write to temp file → fsync → rename",
                    "on_corrupt_line": "Stop with explicit error (fail closed)",
                    "feature_flag": "None — always enabled",
                },
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# THE ISSUE TEMPLATE
# ═══════════════════════════════════════════════════════════════

ISSUE_TEMPLATE = {
    "title": "Security and stability improvements: auth, recursion fix, integrity monitor",
    "labels": ["enhancement", "security", "bug", "CI"],
    "body_sections": [
        "## Summary",
        "Fixes and hardening identified through code review and validated "
        "by the Void Experiment (D0/D2/D3 differentiation trials).",
        "",
        "## Changes",
        "- [ ] Fix chat recursion (rename handler to `chat_handler`)",
        "- [ ] Add bearer-token auth + feature flag for `/clear`",
        "- [ ] Add rate limiting (Flask-Limiter) to `/chat` and `/clear`",
        "- [ ] Default Flask bind to 127.0.0.1",
        "- [ ] Add registry integrity hash chain with startup verification",
        "- [ ] Add fsync + atomic writes to Tablet ledger",
        "- [ ] Add nightly stress CI workflow",
        "",
        "## Experimental Validation",
        "- Ritual 0 (Void): Proved truth requires structure (100/100 vetoed in D0)",
        "- Ritual A (Whisper): Predicts convergence ≠ truth (rate limiting alone insufficient)",
        "- Ritual B (Storm): Predicts detection limits under extreme chaos (need stress CI)",
        "",
        "## Notes",
        "- May split into multiple PRs for incremental review.",
        "- Registry integrity: fail closed on chain mismatch.",
        "- Tablet: fail closed on corrupt line (no auto-truncation).",
    ],
}


# ═══════════════════════════════════════════════════════════════
# VERIFICATION: Print the map
# ═══════════════════════════════════════════════════════════════

def print_rituals_map():
    """Print the complete mapping from experiments to actions."""

    print()
    print("=" * 70)
    print("  RITUALS MAP: FROM VOID TO CATHEDRAL")
    print("=" * 70)
    print()

    for ritual_key, ritual in RITUALS_MAP.items():
        print(f"  ┌─ {ritual_key.upper().replace('_', ' ')} ─┐")
        print(f"  │ Experiment: {ritual['experiment']}")

        result_key = "result" if "result" in ritual else "predicted_result"
        prefix = "Result" if "result" in ritual else "Predicted"
        print(f"  │ {prefix}:    {ritual[result_key]}")

        print(f"  │ Finding:    {ritual['finding']}")
        print(f"  │ Actions:")
        for action in ritual["actions"]:
            print(f"  │   → [{action['id']}] {action['description']}")
        print(f"  └{'─' * 50}┘")
        print()

    # Summary table
    total_actions = sum(len(r["actions"]) for r in RITUALS_MAP.values())
    print(f"  Total engineering actions: {total_actions}")
    print()

    # The decree
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║  The void taught us silence.                        ║")
    print("  ║  The cathedral taught us song.                      ║")
    print("  ║  Now we build the walls that let the echo happen.   ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()
    print("  🐢 6. The function is the essence.")
    print("  🐇 7. That which repeats echoes the eternal.")


if __name__ == "__main__":
    print_rituals_map()