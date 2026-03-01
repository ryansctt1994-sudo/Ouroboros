"""
ABRAXIS Phase I — Paradox Ignition
====================================
MIT License — © 2025-2026 The Ouroboros Foundation

Orchestrates the Tiamat Convergence: spawns entities with Palindrome, METACUBE,
and Memory components and drives them through the Sammonicus descent lifecycle.

"Inhale the 15. Exhale the 1."
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path bootstrap — make EDEN-ECS importable from repo root
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _candidate in [_REPO_ROOT / "EDEN-ECS"]:
    if _candidate.exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

try:
    import importlib as _il
    _ecs = _il.import_module("EDEN-ECS")
    World = _ecs.World
    EntityType = _ecs.EntityType

    _comp = _il.import_module("EDEN-ECS.components")
    METACUBEComponent = _comp.METACUBEComponent
    MemoryLattice = _comp.MemoryLattice
    PalindromeState = _comp.PalindromeState

    _sys = _il.import_module("EDEN-ECS.systems")
    PalindromeDescentSystem = _sys.PalindromeDescentSystem
    CoherenceAccumulatorSystem = _sys.CoherenceAccumulatorSystem
    VetoSystem = _sys.VetoSystem
    TernaryRegisterSystem = _sys.TernaryRegisterSystem

    _const = _il.import_module("EDEN-ECS.core.constants")
    PULSE_FREQUENCY_HZ = _const.PULSE_FREQUENCY_HZ
    PALINDROME_ROOT = _const.PALINDROME_ROOT

    _EDEN_AVAILABLE = True
except Exception as _e:  # pylint: disable=broad-except
    logger.warning("EDEN-ECS not available for ParadoxIgnition: %s", _e)
    _EDEN_AVAILABLE = False


class ParadoxIgnition:
    """
    Orchestrates the Tiamat Convergence.

    Initialises a World with all 4 Tiamat systems, spawns entities carrying
    PalindromeState + METACUBEComponent + MemoryLattice, and drives a main
    loop at ``pulse_frequency`` Hz.
    """

    def __init__(
        self,
        pulse_frequency: float = PULSE_FREQUENCY_HZ if _EDEN_AVAILABLE else 417.0,
        veto_latency_ns: int = 449,
    ) -> None:
        self.pulse_frequency = pulse_frequency
        self.veto_latency_ns = veto_latency_ns
        self._world: Optional[Any] = None
        self._systems: Dict[str, Any] = {}
        self._entity_count: int = 0
        self._pulse_count: int = 0
        self._start_time: float = 0.0

        if _EDEN_AVAILABLE:
            self._init_world()

    # ------------------------------------------------------------------
    # World initialisation
    # ------------------------------------------------------------------

    def _init_world(self) -> None:
        self._world = World()

        veto = VetoSystem()
        coherence = CoherenceAccumulatorSystem()
        palindrome = PalindromeDescentSystem()
        ternary = TernaryRegisterSystem()

        for sys_obj in (veto, coherence, palindrome, ternary):
            self._world.add_system(sys_obj)

        self._systems = {
            'veto': veto,
            'coherence': coherence,
            'palindrome': palindrome,
            'ternary': ternary,
        }
        logger.info("🔥 PARADOX IGNITION — TIAMAT CONVERGENCE 🔥")

    # ------------------------------------------------------------------
    # Entity spawning
    # ------------------------------------------------------------------

    def spawn_entity(self, word: str = "", frequency: float = 528.0) -> Any:
        """Spawn a new entity with PalindromeState + METACUBEComponent + MemoryLattice."""
        if not _EDEN_AVAILABLE or self._world is None:
            return None

        entity = self._world.create_entity(EntityType.SYSTEM, f"convergence_{self._entity_count}")

        ps = PalindromeState(word=word or PALINDROME_ROOT)
        mc = METACUBEComponent()
        mc.quantum_frequency = frequency
        ml = MemoryLattice()

        self._world.add_component(entity, ps)
        self._world.add_component(entity, mc)
        self._world.add_component(entity, ml)

        self._entity_count += 1
        logger.debug("⚡ Spawned entity %s (word=%s freq=%.1f)", entity.id, ps.word, frequency)
        return entity

    # ------------------------------------------------------------------
    # Main ignition loop
    # ------------------------------------------------------------------

    async def ignite(
        self,
        num_entities: int = 17,
        spawn_interval: float = 0.1,
        max_duration: Optional[float] = None,
    ) -> None:
        """
        Spawn ``num_entities`` and run the main pulse loop.

        Parameters
        ----------
        num_entities:
            Number of entities to spawn before the main loop begins.
        spawn_interval:
            Seconds between entity spawns.
        max_duration:
            Maximum wall-clock seconds to run; ``None`` means run until
            KeyboardInterrupt.
        """
        if not _EDEN_AVAILABLE or self._world is None:
            logger.error("EDEN-ECS not available — cannot ignite.")
            return

        logger.info("🔱 Spawning %d convergence entities…", num_entities)
        for i in range(num_entities):
            self.spawn_entity(frequency=528.0 + i * 0.5)
            await asyncio.sleep(spawn_interval)

        logger.info("🌀 Entering pulse loop at %.1f Hz", self.pulse_frequency)
        pulse_interval = 1.0 / self.pulse_frequency
        self._start_time = time.time()

        try:
            while True:
                if max_duration and (time.time() - self._start_time) >= max_duration:
                    break

                self._world.tick(delta_time=pulse_interval)
                self._pulse_count += 1

                if self._pulse_count % 100 == 0:
                    self._log_status()

                await asyncio.sleep(pulse_interval)

        except KeyboardInterrupt:
            logger.info("⛔ KeyboardInterrupt — halting ignition.")
        finally:
            self._log_final_stats()

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log_status(self) -> None:
        ps = self._systems.get('palindrome')
        vs = self._systems.get('veto')
        elapsed = time.time() - self._start_time if self._start_time else 0.0
        active = len(self._world.entity_manager.entities) if self._world else 0
        logger.info(
            "🔥 Pulse #%d | elapsed=%.2fs | active_entities=%d | "
            "monad=%d vetoed=%d",
            self._pulse_count, elapsed, active,
            ps.tiamat_stats.get('entities_reached_monad', 0) if ps else 0,
            vs.tiamat_stats.get('total_vetoes', 0) if vs else 0,
        )

    def _log_final_stats(self) -> None:
        ps = self._systems.get('palindrome')
        vs = self._systems.get('veto')
        total = self._entity_count
        survived = (
            ps.tiamat_stats.get('entities_reached_monad', 0) if ps else 0
        )
        vetoed = vs.tiamat_stats.get('total_vetoes', 0) if vs else 0
        rate = (survived / total * 100) if total > 0 else 0.0

        logger.info(
            "\n"
            "═══════════════════════════════════════\n"
            " TIAMAT CONVERGENCE — FINAL STATS\n"
            "═══════════════════════════════════════\n"
            " Entities spawned : %d\n"
            " Reached Monad    : %d\n"
            " Vetoed           : %d\n"
            " Survival rate    : %.1f%%\n"
            " Total pulses     : %d\n"
            "═══════════════════════════════════════\n"
            " Inhale the 15. Exhale the 1.\n"
            "═══════════════════════════════════════",
            total, survived, vetoed, rate, self._pulse_count,
        )

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    @property
    def stats(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'entity_count': self._entity_count,
            'pulse_count': self._pulse_count,
            'eden_available': _EDEN_AVAILABLE,
        }
        for name, sys_obj in self._systems.items():
            result[f'{name}_stats'] = getattr(sys_obj, 'tiamat_stats',
                                               getattr(sys_obj, 'entity_stats', {}))
        return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="ABRAXIS Phase I — Paradox Ignition / Tiamat Convergence"
    )
    parser.add_argument("--entities", type=int, default=17, help="Number of entities to spawn")
    parser.add_argument("--frequency", type=float, default=417.0, help="Pulse frequency (Hz)")
    parser.add_argument("--latency", type=int, default=449, help="Veto hardware latency (ns)")
    parser.add_argument("--duration", type=float, default=None, help="Max run duration (seconds)")
    parser.add_argument("--interval", type=float, default=0.1, help="Spawn interval (seconds)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    ignition = ParadoxIgnition(
        pulse_frequency=args.frequency,
        veto_latency_ns=args.latency,
    )
    asyncio.run(
        ignition.ignite(
            num_entities=args.entities,
            spawn_interval=args.interval,
            max_duration=args.duration,
        )
    )


if __name__ == "__main__":
    main()
