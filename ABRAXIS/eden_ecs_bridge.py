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
- Expose Tiamat Convergence methods: ``manifest()``, ``pulse()``,
  ``get_status()``, ``get_entity_state()``.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path setup — make eden_ecs importable if running from the repo root
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
# Insert repo root first so eden_ecs/ takes priority over python-bridge/eden_ecs/
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_pb = _REPO_ROOT / "python-bridge"
if _pb.exists() and str(_pb) not in sys.path:
    sys.path.append(str(_pb))


# ---------------------------------------------------------------------------
# EDEN-ECS components for ABRAXIS
# ---------------------------------------------------------------------------

try:
    from eden_ecs.core.component import Component  # type: ignore[import]
    from eden_ecs.core.entity import EntityType  # type: ignore[import]
    _EDEN_ECS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    # Provide a minimal stub so ABRAXIS works without EDEN-ECS installed
    _EDEN_ECS_AVAILABLE = False

    class Component:  # type: ignore[no-redef]
        """Minimal stub when EDEN-ECS is not installed."""


# ---------------------------------------------------------------------------
# Tiamat Convergence — optional imports
# ---------------------------------------------------------------------------

try:
    import importlib as _il
    _ecs = _il.import_module("eden_ecs")
    _comp = _il.import_module("eden_ecs.components")
    _sys_mod = _il.import_module("eden_ecs.systems")
    _const = _il.import_module("eden_ecs.core.constants")

    _METACUBEComponent = _comp.METACUBEComponent
    _MemoryLattice = _comp.MemoryLattice
    _PalindromeState = _comp.PalindromeState
    _PalindromeDescentSystem = _sys_mod.PalindromeDescentSystem
    _CoherenceAccumulatorSystem = _sys_mod.CoherenceAccumulatorSystem
    _VetoSystem = _sys_mod.VetoSystem
    _TernaryRegisterSystem = _sys_mod.TernaryRegisterSystem
    _TIAMAT_AVAILABLE = True
except Exception:  # pylint: disable=broad-except
    _TIAMAT_AVAILABLE = False


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
        self._tiamat_entities: Dict[str, Any] = {}  # entity_id → entity
        self._tiamat_systems: Dict[str, Any] = {}
        self._init_world()

    def _init_world(self) -> None:
        if not self._eden_available:
            logger.debug("EDEN-ECS not available — running in standalone mode.")
            return
        try:
            from eden_ecs.core.world import World  # type: ignore[import]
            self._world = World()
            logger.info("EDEN-ECS World initialised for ABRAXIS bridge.")
            if _TIAMAT_AVAILABLE:
                self._init_tiamat_systems()
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Could not initialise EDEN-ECS World: %s", exc)

    def _init_tiamat_systems(self) -> None:
        """Attach Tiamat Convergence systems to the world."""
        try:
            systems = {
                'veto': _VetoSystem(),
                'coherence': _CoherenceAccumulatorSystem(),
                'palindrome': _PalindromeDescentSystem(),
                'ternary': _TernaryRegisterSystem(),
            }
            for sys_obj in systems.values():
                self._world.add_system(sys_obj)
            systems['veto'].attach_to_world(self._world)
            self._tiamat_systems = systems
            logger.info("Tiamat Convergence systems attached to ABRAXIS world.")
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Could not attach Tiamat systems: %s", exc)

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
                entity = self._world.create_entity(EntityType.SYSTEM, f"abraxis_{node_id}")
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

    # ------------------------------------------------------------------
    # Tiamat Convergence — manifest / pulse / get_status / get_entity_state
    # ------------------------------------------------------------------

    def manifest(self, word: str = "", frequency: float = 528.0) -> Optional[str]:
        """
        Spawn a Tiamat Convergence entity with PalindromeState + METACUBEComponent
        + MemoryLattice.

        Returns the entity ID, or ``None`` if unavailable.
        """
        if not _TIAMAT_AVAILABLE or self._world is None:
            logger.debug("manifest() — Tiamat not available.")
            return None
        try:
            from eden_ecs.core.entity import EntityType  # type: ignore[import]
            entity = self._world.create_entity(EntityType.SYSTEM, "tiamat_manifest")
            ps = _PalindromeState(word=word or "ABRAXISASIXARBA")
            mc = _METACUBEComponent()
            mc.quantum_frequency = frequency
            ml = _MemoryLattice()
            self._world.add_component(entity, ps)
            self._world.add_component(entity, mc)
            self._world.add_component(entity, ml)
            self._tiamat_entities[entity.id] = entity
            logger.debug("manifest() → entity %s (word=%s freq=%.1f)", entity.id, ps.word, frequency)
            return entity.id
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("manifest() failed: %s", exc)
            return None

    def pulse(
        self,
        frequency: float = 417.0,
        duration_ns: int = 0,
        cycles: int = 1,
    ) -> None:
        """
        Send ``cycles`` ticks through the EDEN-ECS world at the given frequency.

        Parameters
        ----------
        frequency:
            Pulse frequency in Hz (used to compute delta_time).
        duration_ns:
            Optional pause in nanoseconds between cycles.
        cycles:
            Number of world ticks to execute.
        """
        if self._world is None:
            logger.debug("pulse() — world not available.")
            return
        delta_time = 1.0 / frequency if frequency > 0 else 1.0 / 417.0
        for _ in range(cycles):
            self._world.tick(delta_time=delta_time)
            if duration_ns > 0:
                time.sleep(duration_ns / 1e9)

    def get_status(self) -> Dict[str, Any]:
        """
        Return entity counts, system stats, and key constants.
        """
        entity_count = (
            len(self._world.entity_manager.entities) if self._world else 0
        )
        sys_stats: Dict[str, Any] = {}
        for name, sys_obj in self._tiamat_systems.items():
            sys_stats[name] = getattr(sys_obj, 'tiamat_stats',
                                       getattr(sys_obj, 'entity_stats', {}))

        constants: Dict[str, Any] = {}
        if _TIAMAT_AVAILABLE:
            try:
                constants = {
                    'PHI': _const.PHI,
                    'ALPHA': _const.ALPHA,
                    'THETA': _const.THETA,
                    'LAMBDA': _const.LAMBDA,
                    'DELTA': _const.DELTA,
                    'VETO_THRESHOLD': _const.VETO_THRESHOLD,
                    'PULSE_FREQUENCY_HZ': _const.PULSE_FREQUENCY_HZ,
                    'PALINDROME_ROOT': _const.PALINDROME_ROOT,
                }
            except Exception:  # pylint: disable=broad-except
                pass

        return {
            'eden_available': self._eden_available,
            'tiamat_available': _TIAMAT_AVAILABLE,
            'entity_count': entity_count,
            'tiamat_entity_count': len(self._tiamat_entities),
            'system_stats': sys_stats,
            'constants': constants,
        }

    def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Return detailed state for a Tiamat entity.

        Includes palindrome, metacube, coherence, and ternary data.
        """
        if self._world is None:
            return None
        entity = self._world.entity_manager.entities.get(entity_id)
        if entity is None:
            return None

        result: Dict[str, Any] = {'entity_id': entity_id}

        if _TIAMAT_AVAILABLE:
            ps = entity.get_component(_PalindromeState)
            if ps:
                result['palindrome'] = {
                    'word': ps.word,
                    'layer': ps.layer,
                    'vitality': ps.vitality,
                    'vitality_divergence': ps.vitality_divergence,
                    'symmetry_verified': ps.symmetry_verified,
                    'center': ps.center_letter(),
                    'descent_history': list(ps.descent_history),
                }

            mc = entity.get_component(_METACUBEComponent)
            if mc:
                result['metacube'] = {
                    'quantum_frequency': mc.quantum_frequency,
                    'quantum_coherence': mc.quantum_coherence,
                    'coherence': mc.coherence(),
                }

            coherence_sys = self._tiamat_systems.get('coherence')
            if coherence_sys:
                result['chi'] = coherence_sys.get_chi(entity_id)

            ternary_sys = self._tiamat_systems.get('ternary')
            if ternary_sys:
                reg = ternary_sys.get_register(entity_id)
                result['ternary'] = {
                    'state': reg.state,
                    'direction': reg.direction,
                    'ternary_value': reg.ternary_value,
                }

        return result


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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="ABRAXIS EDEN-ECS Bridge — Tiamat Convergence testing CLI"
    )
    subparsers = parser.add_subparsers(dest="command")

    manifest_p = subparsers.add_parser("manifest", help="Spawn a Tiamat entity")
    manifest_p.add_argument("--word", default="", help="Palindrome word (default: PALINDROME_ROOT)")
    manifest_p.add_argument("--frequency", type=float, default=528.0, help="Quantum frequency (Hz)")

    pulse_p = subparsers.add_parser("pulse", help="Send pulses through the world")
    pulse_p.add_argument("--frequency", type=float, default=417.0, help="Pulse frequency (Hz)")
    pulse_p.add_argument("--cycles", type=int, default=1, help="Number of ticks")

    subparsers.add_parser("status", help="Print world/system status")

    entity_p = subparsers.add_parser("entity", help="Print state of a specific entity")
    entity_p.add_argument("entity_id", help="Entity ID")

    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    bridge = EdenEcsBridge()

    if args.command == "manifest":
        eid = bridge.manifest(word=args.word, frequency=args.frequency)
        print(json.dumps({"entity_id": eid}))
    elif args.command == "pulse":
        bridge.pulse(frequency=args.frequency, cycles=args.cycles)
        print(json.dumps({"pulses_sent": args.cycles}))
    elif args.command == "status":
        print(json.dumps(bridge.get_status(), indent=2, default=str))
    elif args.command == "entity":
        state = bridge.get_entity_state(args.entity_id)
        print(json.dumps(state, indent=2, default=str))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
