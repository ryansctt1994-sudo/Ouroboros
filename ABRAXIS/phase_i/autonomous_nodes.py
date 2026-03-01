"""
ABRAXIS Phase I — Autonomous Nodes
===================================
MIT License — © 2025-2026 The Ouroboros Foundation
See /LICENSE for the Ethical Use Covenant.

Implements the three pillars of Phase I:

1. **Self-Healing Systems** — each node monitors itself and restarts failed
   subsystems without human intervention.

2. **Spore Factory Replication** — nodes can snapshot their state into a
   compressed *spore* and seed new peer nodes from that spore.

3. **Governance Thresholds** — a weighted-vote consensus layer prevents any
   single node from making unilateral decisions above the configured
   threshold.

The implementation is intentionally dependency-free (stdlib only) so it
can be embedded in any Python ≥ 3.9 environment, including the EDEN-ECS
runtime.
"""

from __future__ import annotations

import asyncio
import json
import logging
import pickle
import time
import uuid
import zlib
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Self-Healing Subsystem
# ---------------------------------------------------------------------------


@dataclass
class SubsystemSpec:
    """Declaration of a monitored subsystem."""

    name: str
    factory: Callable[[], Any]            # callable that returns a new instance
    max_restarts: int = 5
    restart_delay_s: float = 1.0


class SelfHealingNode:
    """
    Wraps one or more subsystems and restarts them if they raise uncaught
    exceptions.

    Usage::

        node = SelfHealingNode("worker")
        node.register(SubsystemSpec("processor", lambda: MyProcessor()))
        await node.run()
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._specs: Dict[str, SubsystemSpec] = {}
        self._instances: Dict[str, Any] = {}
        self._restart_counts: Dict[str, int] = {}
        self._running = False

    def register(self, spec: SubsystemSpec) -> None:
        self._specs[spec.name] = spec
        self._instances[spec.name] = spec.factory()
        self._restart_counts[spec.name] = 0

    def get(self, name: str) -> Any:
        """Return the live instance for a subsystem."""
        return self._instances[name]

    async def _watch(self, name: str) -> None:
        """Watchdog coroutine for one subsystem."""
        spec = self._specs[name]
        while self._running:
            instance = self._instances[name]
            if hasattr(instance, "run"):
                try:
                    await instance.run()
                except Exception as exc:  # pylint: disable=broad-except
                    count = self._restart_counts[name] + 1
                    self._restart_counts[name] = count
                    if count > spec.max_restarts:
                        logger.error(
                            "[%s] subsystem '%s' exceeded max restarts (%d). Halting.",
                            self.node_id, name, spec.max_restarts,
                        )
                        self._running = False
                        return
                    logger.warning(
                        "[%s] subsystem '%s' crashed (%s). Restart %d/%d in %.1fs.",
                        self.node_id, name, exc, count, spec.max_restarts,
                        spec.restart_delay_s,
                    )
                    await asyncio.sleep(spec.restart_delay_s)
                    self._instances[name] = spec.factory()
            else:
                await asyncio.sleep(1.0)

    async def run(self) -> None:
        """Start all subsystem watchdogs."""
        self._running = True
        tasks = [asyncio.create_task(self._watch(n)) for n in self._specs]
        if tasks:
            await asyncio.gather(*tasks)

    def stop(self) -> None:
        self._running = False

    @property
    def health(self) -> Dict[str, Any]:
        return {
            name: {
                "restarts": self._restart_counts.get(name, 0),
                "alive": name in self._instances,
            }
            for name in self._specs
        }


# ---------------------------------------------------------------------------
# Spore Factory
# ---------------------------------------------------------------------------


@dataclass
class Spore:
    """
    Compressed checkpoint of an autonomous node's state.

    A spore can seed a new node or restore a crashed one.
    """

    origin_id: str
    spore_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    payload: bytes = field(default_factory=bytes)   # zlib-compressed pickle

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_json(self) -> str:
        d = asdict(self)
        d["payload"] = self.payload.hex()
        return json.dumps(d)

    @classmethod
    def from_json(cls, raw: str) -> "Spore":
        d = json.loads(raw)
        d["payload"] = bytes.fromhex(d["payload"])
        return cls(**d)


class SporeFactory:
    """
    Creates spores from node state and germinates new nodes from spores.

    Spore lifecycle::

        factory = SporeFactory(node_id="root")
        spore   = factory.sporulate(state_dict)
        new_state = factory.germinate(spore)
    """

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id

    def sporulate(self, state: Dict[str, Any]) -> Spore:
        """Compress ``state`` into a Spore."""
        raw = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
        compressed = zlib.compress(raw, level=9)
        spore = Spore(origin_id=self.node_id, payload=compressed)
        logger.debug(
            "[%s] sporulated %d bytes → %d bytes (spore=%s)",
            self.node_id, len(raw), len(compressed), spore.spore_id,
        )
        return spore

    def germinate(self, spore: Spore) -> Dict[str, Any]:
        """
        Decompress a Spore back into a state dict.

        Security note: spores are deserialized with ``pickle.loads``.  Only
        germinate spores that originate from trusted nodes in your deployment.
        Do not accept raw spore payloads from untrusted network sources without
        first verifying a cryptographic signature over the payload.
        """
        raw = zlib.decompress(spore.payload)
        state: Dict[str, Any] = pickle.loads(raw)  # noqa: S301
        logger.debug(
            "[%s] germinated spore %s from origin=%s",
            self.node_id, spore.spore_id, spore.origin_id,
        )
        return state

    def seed_node(self, spore: Spore) -> "AutonomousNode":
        """Germinate a spore into a new AutonomousNode."""
        state = self.germinate(spore)
        new_id = f"node-{str(uuid.uuid4())[:6]}"
        node = AutonomousNode(node_id=new_id)
        node.restore_state(state)
        return node


# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------


@dataclass
class GovernanceVote:
    voter_id: str
    proposal_id: str
    approve: bool
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)


class GovernanceCouncil:
    """
    Weighted-vote governance layer.

    A proposal passes only when the weighted approval ratio exceeds
    ``threshold`` (default 0.67, i.e. 2/3 supermajority).
    """

    DEFAULT_THRESHOLD = 0.67

    def __init__(self, threshold: float = DEFAULT_THRESHOLD) -> None:
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")
        self.threshold = threshold
        self._proposals: Dict[str, str] = {}          # id → description
        self._votes: Dict[str, List[GovernanceVote]] = {}

    def propose(self, description: str) -> str:
        proposal_id = str(uuid.uuid4())[:8]
        self._proposals[proposal_id] = description
        self._votes[proposal_id] = []
        logger.info("[governance] proposal %s: %s", proposal_id, description)
        return proposal_id

    def vote(self, proposal_id: str, voter_id: str, approve: bool,
             weight: float = 1.0) -> None:
        if proposal_id not in self._proposals:
            raise KeyError(f"Unknown proposal: {proposal_id}")
        # Replace existing vote from same voter
        self._votes[proposal_id] = [
            v for v in self._votes[proposal_id] if v.voter_id != voter_id
        ]
        self._votes[proposal_id].append(
            GovernanceVote(voter_id, proposal_id, approve, weight)
        )

    def tally(self, proposal_id: str) -> Tuple[bool, float]:
        """
        Return ``(passed, approval_ratio)`` for a proposal.

        The ratio is the fraction of total weight that voted to approve.
        """
        votes = self._votes.get(proposal_id, [])
        if not votes:
            return False, 0.0
        total = sum(v.weight for v in votes)
        approve = sum(v.weight for v in votes if v.approve)
        ratio = approve / total if total else 0.0
        passed = ratio >= self.threshold
        logger.info(
            "[governance] tally %s → %s (%.0f%%)",
            proposal_id, "PASSED" if passed else "FAILED", ratio * 100,
        )
        return passed, ratio

    def proposals(self) -> Dict[str, str]:
        return dict(self._proposals)


# ---------------------------------------------------------------------------
# Autonomous Node
# ---------------------------------------------------------------------------


class AutonomousNode:
    """
    A single Phase I autonomous node.

    Combines self-healing, spore factory, and governance into one unit.
    Nodes can be connected to peers to form a distributed mesh.
    """

    def __init__(self, node_id: Optional[str] = None) -> None:
        self.node_id = node_id or f"node-{str(uuid.uuid4())[:6]}"
        self.healing = SelfHealingNode(self.node_id)
        self.spore_factory = SporeFactory(self.node_id)
        self.governance = GovernanceCouncil()
        self._state: Dict[str, Any] = {
            "node_id": self.node_id,
            "created_at": time.time(),
            "ticks": 0,
        }
        self._peers: List["AutonomousNode"] = []

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def snapshot(self) -> Spore:
        """Take a spore snapshot of the current state."""
        return self.spore_factory.sporulate(dict(self._state))

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore internal state from a dict (e.g. after germination)."""
        self._state.update(state)

    # ------------------------------------------------------------------
    # Peer mesh
    # ------------------------------------------------------------------

    def connect_peer(self, peer: "AutonomousNode") -> None:
        if peer is not self and peer not in self._peers:
            self._peers.append(peer)
            logger.info("[%s] connected to peer %s", self.node_id, peer.node_id)

    def replicate_to_peers(self) -> List["AutonomousNode"]:
        """
        Sporulate and seed a new child node from the current state,
        sharing it with all connected peers.
        """
        spore = self.snapshot()
        new_node = self.spore_factory.seed_node(spore)
        for peer in self._peers:
            peer.connect_peer(new_node)
        logger.info(
            "[%s] replicated → %s (spore=%s)",
            self.node_id, new_node.node_id, spore.spore_id,
        )
        return [new_node]

    # ------------------------------------------------------------------
    # Tick / async run
    # ------------------------------------------------------------------

    async def tick(self) -> None:
        """One heartbeat tick — update internal state."""
        self._state["ticks"] += 1
        self._state["last_tick"] = time.time()

    async def run(self, tick_interval_s: float = 1.0) -> None:
        """Run the node continuously."""
        logger.info("[%s] starting autonomous run loop", self.node_id)
        while True:
            await self.tick()
            await asyncio.sleep(tick_interval_s)

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    @property
    def info(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "state": dict(self._state),
            "health": self.healing.health,
            "peers": [p.node_id for p in self._peers],
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="ABRAXIS Phase I — Autonomous Node runtime"
    )
    parser.add_argument("--node-id", default=None, help="Node identifier")
    parser.add_argument(
        "--tick-interval", type=float, default=1.0,
        help="Tick interval in seconds",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    node = AutonomousNode(node_id=args.node_id)
    asyncio.run(node.run(tick_interval_s=args.tick_interval))


if __name__ == "__main__":
    main()
