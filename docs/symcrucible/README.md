# SymCrucible Transition Console v0.2

**Status:** DEMO_INSTRUMENT  
**Authority:** TIER_UI / AUTHORITY_WEIGHT_0  
**Boundary:** not a production verifier, not a replicated receipt system, not an authority kernel.

SymCrucible Transition Console is a browser-native demonstration instrument for governed agentic execution. It does not validate intelligence. It validates proposed transitions.

The console demonstrates a complete transition path:

1. classify the proposal,
2. evaluate it against an external policy,
3. issue one of five verdicts,
4. seal the decision into a SHA-256 hash-chained chronicle,
5. allow tamper testing,
6. replay and verify the chain.

## Files

- `index.html` — flagship self-contained console.
- `cards.json` — default proposal deck.
- `policy.json` — default ordered first-match-wins gate policy.
- `examples/policy-strict.json` — stricter policy that escalates external actions.
- `examples/medguide-triage-deck.json` — clinical-support framing, demo only.
- `examples/devops-incident-deck.json` — infrastructure incident-response framing.

## How to run

Open `index.html` directly for a local demo. Browser security blocks sibling JSON fetches over `file://`, so the console falls back to built-in defaults and exposes **Load deck...** and **Load policy...** pickers.

For fetched external config, serve the repo root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000/
```

## Doctrine

A model output, artifact, or action is not valid because it exists. It becomes reviewable only when the transition that produced it can be classified, checked, gated, recorded, tamper-tested, and replayed.

The central rule is:

```text
Do not validate intelligence.
Validate transitions.
```

## Freeze block

```text
SYMCRUCIBLE_TRANSITION_CONSOLE_v0.2
Status: DEMO_INSTRUMENT
Authority: TIER_UI / AUTHORITY_WEIGHT_0
Role: flagship browser-native transition-governance artifact
Boundary: not a production verifier, not a replicated receipt system, not an authority kernel
```

## Next upgrades

The natural v0.3 path is to accept arbitrary workflow graph JSON, run the static graph checks against real workflows, and connect replay to a durable external chronicle rather than browser-local receipts.
