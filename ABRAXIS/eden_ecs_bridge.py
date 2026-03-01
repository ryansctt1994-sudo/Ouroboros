"""
ABRAXIS — EDEN-ECS Integration Bridge
=======================================
MIT License — © 2025-2026 The Ouroboros Foundation
See /LICENSE for the Ethical Use Covenant.

Connects the ABRAXIS Phase H / Phase I runtime to the EDEN-ECS framework
(``EDEN-ECS/`` at the repository root).

Responsibilities
----------------
- Expose an ``EdenEcsBridge`` that Phase H's ``GnosisProcessor`` and Phase I's
  ``AutonomousNode`` can use for coherence scoring and component queries.
- Provide a ``MycelialBridgeAdapter`` wrapping the existing
  ``python-bridge/eden_ecs/mycelial_components.py`` so ABRAXIS nodes can
  participate in the mycelial network.
- Offer ``create_abraxis_world()`` which bootstraps an EDEN-ECS ``World``
  with the components required by ABRAXIS (``AbraxisNode``, ``PhasonicClock``,
  ``GovernanceState``).
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path setup — make EDEN-ECS importable if running from the repo root
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _candidate in [
    _REPO_ROOT / "EDEN-ECS",
    _REPO_ROOT / "python-bridge",
]:
    if _candidate.exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))


# ---------------------------------------------------------------------------
# EDEN-ECS components for ABRAXIS
# ---------------------------------------------------------------------------

try:
    from core.component import Component  # type: ignore[import]
    _EDEN_ECS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    # Provide a minimal stub so ABRAXIS works without EDEN-ECS installed
    _EDEN_ECS_AVAILABLE = False

    class Component:  # type: ignore[no-redef]
        """Minimal stub when EDEN-ECS is not installed."""


class AbraxisNodeComponent(Component):
    """ECS component representing an ABRAXIS autonomous node."""

    def __init__(self, node_id: str, phase: str = "idle") -> None:
        self.node_id = node_id
        self.phase = phase          # "idle" | "processing" | "healing" | "sporulating"
        self.coherence: float = 1.0
        self.tick_count: int = 0
        self.last_tick: float = time.time()

    def advance(self) -> None:
        self.tick_count += 1
        self.last_tick = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "phase": self.phase,
            "coherence": self.coherence,
            "tick_count": self.tick_count,
        }


class PhasonicClockComponent(Component):
    """ECS component holding the phasonic PLL accumulator for an ABRAXIS node."""

    FREQ_HZ = 0.0997  # Chuckle Constant

    def __init__(self) -> None:
        import math
        self._phase: float = 0.0
        self._last: float = time.time()
        self._two_pi = 2 * math.pi

    def advance(self) -> float:
        now = time.time()
        dt = now - self._last
        self._last = now
        self._phase = (self._phase + self._two_pi * self.FREQ_HZ * dt) % self._two_pi
        return self._phase

    @property
    def phase(self) -> float:
        return self._phase


class GovernanceStateComponent(Component):
    """ECS component tracking governance threshold state for a node."""

    def __init__(self, threshold: float = 0.67) -> None:
        self.threshold = threshold
        self.pending_proposals: int = 0
        self.passed_proposals: int = 0
        self.vetoed_proposals: int = 0

    def record(self, passed: bool) -> None:
        if passed:
            self.passed_proposals += 1
        else:
            self.vetoed_proposals += 1
        if self.pending_proposals > 0:
            self.pending_proposals -= 1


# ---------------------------------------------------------------------------
# Bridge class
# ---------------------------------------------------------------------------


class EdenEcsBridge:
    """
    Bridge between ABRAXIS Phase H/I components and the EDEN-ECS world.

    If EDEN-ECS is available this bridge creates a real ``World`` instance
    and registers ABRAXIS components.  If it is absent (e.g., test
    environments or minimal installs) the bridge falls back to standalone
    component tracking.
    """

    def __init__(self) -> None:
        self._world: Optional[Any] = None
        self._entities: Dict[str, Any] = {}   # node_id → entity
        self._abraxis_components: Dict[str, AbraxisNodeComponent] = {}
        self._phasonic_clocks: Dict[str, PhasonicClockComponent] = {}
        self._governance_states: Dict[str, GovernanceStateComponent] = {}
        self._eden_available = _EDEN_ECS_AVAILABLE
        self._init_world()

    def _init_world(self) -> None:
        if not self._eden_available:
            logger.debug("EDEN-ECS not available — running in standalone mode.")
            return
        try:
            from core.world import World  # type: ignore[import]
            self._world = World()
            logger.info("EDEN-ECS World initialised for ABRAXIS bridge.")
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Could not initialise EDEN-ECS World: %s", exc)

    # ------------------------------------------------------------------
    # Node registration
    # ------------------------------------------------------------------

    def register_node(
        self,
        node_id: str,
        governance_threshold: float = 0.67,
    ) -> None:
        """Register an ABRAXIS node with the ECS world."""
        comp = AbraxisNodeComponent(node_id)
        clock = PhasonicClockComponent()
        gov = GovernanceStateComponent(governance_threshold)

        self._abraxis_components[node_id] = comp
        self._phasonic_clocks[node_id] = clock
        self._governance_states[node_id] = gov

        if self._world is not None:
            try:
                entity = self._world.create_entity()
                self._world.add_component(entity, comp)
                self._world.add_component(entity, clock)
                self._world.add_component(entity, gov)
                self._entities[node_id] = entity
                logger.debug("Registered node %s as ECS entity.", node_id)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("ECS entity creation failed for %s: %s", node_id, exc)

    # ------------------------------------------------------------------
    # Coherence scoring (used by Phase H GnosisProcessor)
    # ------------------------------------------------------------------

    def score(self, transcript: str, node_id: Optional[str] = None) -> float:
        """
        Return a coherence score ∈ [0, 1] for the given transcript.

        Uses the phasonic clock of the named node (or any available clock)
        to apply a phase-weighted score.
        """
        import math

        # Base score from transcript richness
        words = transcript.split()
        base = min(1.0, len(words) / 20.0)

        # Phase modulation
        clock = None
        if node_id and node_id in self._phasonic_clocks:
            clock = self._phasonic_clocks[node_id]
        elif self._phasonic_clocks:
            clock = next(iter(self._phasonic_clocks.values()))

        if clock:
            phase = clock.advance()
            # Modulate by cosine: peak at phase=0, trough at phase=π
            modulation = (1.0 + math.cos(phase)) / 2.0
            return round(base * 0.7 + modulation * 0.3, 4)

        return round(base, 4)

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def tick_all(self) -> None:
        """Advance all registered ABRAXIS node components."""
        for comp in self._abraxis_components.values():
            comp.advance()
        for clock in self._phasonic_clocks.values():
            clock.advance()

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        return {
            "eden_available": self._eden_available,
            "registered_nodes": list(self._abraxis_components.keys()),
            "components": {
                nid: comp.to_dict()
                for nid, comp in self._abraxis_components.items()
            },
        }


# ---------------------------------------------------------------------------
# Mycelial bridge adapter
# ---------------------------------------------------------------------------


class MycelialBridgeAdapter:
    """
    Wraps ``python-bridge/eden_ecs/mycelial_components.py`` so ABRAXIS nodes
    can send/receive spores through the mycelial network.
    """

    def __init__(self) -> None:
        self._bridge: Optional[Any] = None
        self._available = False
        self._init_bridge()

    def _init_bridge(self) -> None:
        try:
            from eden_ecs.mycelial_components import (  # type: ignore[import]
                MycelialNode,
            )
            self._bridge = MycelialNode
            self._available = True
            logger.info("MycelialBridgeAdapter: mycelial_components loaded.")
        except ImportError:
            logger.debug("mycelial_components not found; adapter in stub mode.")

    @property
    def available(self) -> bool:
        return self._available

    def send_spore(self, spore_payload: bytes) -> bool:
        """Forward a spore payload into the mycelial network."""
        if not self._available or self._bridge is None:
            return False
        try:
            self._bridge.ingest_spore(spore_payload)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("MycelialBridgeAdapter.send_spore failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# World factory helper
# ---------------------------------------------------------------------------


def create_abraxis_world(node_ids: list[str] | None = None) -> EdenEcsBridge:
    """
    Bootstrap an EDEN-ECS bridge with default ABRAXIS nodes registered.

    Parameters
    ----------
    node_ids:
        Optional list of node IDs to pre-register.  Defaults to a single
        ``"primary"`` node.

    Returns
    -------
    EdenEcsBridge
        Ready-to-use bridge instance.
    """
    bridge = EdenEcsBridge()
    for nid in (node_ids or ["primary"]):
        bridge.register_node(nid)
    return bridge
