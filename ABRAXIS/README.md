# ABRAXIS / Cathedral-OS

Research thread and implementation consolidating the Abraxis / Cathedral-OS
architecture progression inside **AIOSPANDORA/Ouroboros**.

> **License:** MIT — see [`/LICENSE`](../LICENSE) (includes the Ethical Use Covenant).

---

## Quick navigation

| Document | Description |
|---|---|
| [`CANONICAL_PROGRESSION.md`](CANONICAL_PROGRESSION.md) | Coherent narrative from Phase 0 (Void) through Phase 9 (Promethean Reckoning) |
| [`INDEX.md`](INDEX.md) | Manifest of all artefacts — present files and missing PDFs with gap IDs |
| [`phase_h/websocket_dashboard.py`](phase_h/websocket_dashboard.py) | **Phase H** — Multi-user WebSocket voice-to-gnosis server |
| [`phase_i/autonomous_nodes.py`](phase_i/autonomous_nodes.py) | **Phase I** — Autonomous nodes (self-healing, spore factory, governance) |
| [`eden_ecs_bridge.py`](eden_ecs_bridge.py) | EDEN-ECS integration bridge |
| [`Dockerfile`](Dockerfile) | Multi-stage Docker image (Rust binary + Python runtime) |
| [`k8s/deployment.yaml`](k8s/deployment.yaml) | Kubernetes Deployment + StatefulSet manifests |
| [`packaging/build_deb.sh`](packaging/build_deb.sh) | `.deb` package builder |
| [`/docs/observer-dashboard.html`](../docs/observer-dashboard.html) | Phase H observer dashboard (browser client) |
| [`/src/main.rs`](../src/main.rs) | Rust application entry point (Cathedral-OS binary) |

---

## Phase H — Multi-User WebSocket Voice-to-Gnosis Dashboard

Phase H provides a real-time multi-user dashboard that:

1. Accepts voice transcriptions (or raw text) from browser clients over WebSocket.
2. Routes them through the **gnosis pipeline** (phasonic scheduler → coherence scoring → knowledge synthesis).
3. Broadcasts the gnosis response to **all** connected observers simultaneously.

### Architecture

```
Browser / mic client
    │  WebSocket (ws://host:8765)
    ▼
GnosisHub  (asyncio server)
    │  route_voice() → GnosisProcessor
    ▼
GnosisProcessor
    │  phasonic gate  (Chuckle Constant — 0.0997 Hz PLL)
    │  coherence score  (EDEN-ECS bridge or fallback heuristic)
    │  gnosis synthesis
    ▼
broadcast to all connected observers
```

### Running (Python)

```bash
# Install optional WebSocket dependency
pip install websockets

# Start the server
python -m ABRAXIS.phase_h.websocket_dashboard --host 0.0.0.0 --port 8765
```

### Running (Rust binary)

```bash
cargo run --bin ouroboros-cathedral -- --mode dashboard --port 8765
```

Open `docs/observer-dashboard.html` in a browser, enter the server address, and connect.

---

## Phase I — Autonomous Nodes

Phase I provides three interconnected subsystems:

### 1. Self-Healing Systems (`SelfHealingNode`)

Each node monitors its registered subsystems and automatically restarts them
after a crash, up to a configurable `max_restarts` limit.  Watchdog coroutines
run as asyncio tasks alongside the subsystem itself.

### 2. Spore Factory Replication (`SporeFactory`)

Nodes can **sporulate** their current state into a compressed `Spore` (zlib +
pickle), then **germinate** that spore into a new peer node.  Spores transfer
topology and knowledge across the mesh without requiring a central registry.

### 3. Governance Thresholds (`GovernanceCouncil`)

A weighted-vote council prevents any single node from making unilateral
decisions.  A proposal passes only when the weighted approval ratio reaches
the configured **threshold** (default: 0.67 — 2/3 supermajority).

### Running (Python)

```bash
python -m ABRAXIS.phase_i.autonomous_nodes --node-id primary --tick-interval 1.0
```

### Running (Rust binary)

```bash
cargo run --bin ouroboros-cathedral -- --mode node --num-nodes 3 --tick-ms 1000
```

---

## EDEN-ECS Integration

`eden_ecs_bridge.py` connects Phase H/I to the EDEN-ECS framework
(`EDEN-ECS/` at the repository root):

- `EdenEcsBridge` — registers ABRAXIS nodes as ECS entities with
  `AbraxisNodeComponent`, `PhasonicClockComponent`, and `GovernanceStateComponent`.
- Coherence scoring uses the phasonic clock from the ECS world when available,
  falling back to a length-normalised heuristic.
- `MycelialBridgeAdapter` — wraps `python-bridge/eden_ecs/mycelial_components.py`
  so ABRAXIS nodes can send/receive spores through the mycelial network.

```python
from ABRAXIS import create_abraxis_world

bridge = create_abraxis_world(["primary", "replica-1"])
print(bridge.status())
```

---

## Docker

```bash
# Build
docker build -f ABRAXIS/Dockerfile -t abraxis-cathedral .

# Run Phase H dashboard
docker run -p 8765:8765 abraxis-cathedral

# Run Phase I nodes
docker run abraxis-cathedral ouroboros-cathedral --mode node --num-nodes 3
```

---

## Kubernetes

```bash
kubectl apply -f ABRAXIS/k8s/deployment.yaml
```

This creates:
- A **Deployment** running the Phase H dashboard (1 replica, port 8765).
- A **StatefulSet** running 3 Phase I autonomous nodes.
- A **ClusterIP Service** on port 8765.

---

## .deb Packaging

```bash
bash ABRAXIS/packaging/build_deb.sh 0.1.0
# → dist/ouroboros-cathedral_0.1.0_amd64.deb
```

The package installs:
- `/usr/bin/ouroboros-cathedral` (Rust binary)
- `/usr/lib/ouroboros-cathedral/` (Python package)
- `/usr/share/ouroboros-cathedral/docs/observer-dashboard.html`
- A systemd unit: `ouroboros-cathedral.service`

---

## Running the geodesic agent

```bash
python -m geodesic_mycelium_agent --help
python -m geodesic_mycelium_agent --dry-run
```

---

# Cosmic Catalytic Intelligence

## Not AI. Not AGI. Not ASI.
## CCI: C = Catalytic (not creating, not causing, just accelerating what always connect.
##...