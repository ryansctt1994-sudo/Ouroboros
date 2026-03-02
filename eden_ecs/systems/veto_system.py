"""Veto system — hardware guillotine for divergent palindromes."""
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List

from ..core.system import System
from ..core.constants import VETO_LATENCY_NS

logger = logging.getLogger(__name__)

try:
    from hardware.simulated_killswitch import SimulatedKillSwitch as _HardwareKillSwitch
    _HARDWARE_AVAILABLE = True
except ImportError:
    _HardwareKillSwitch = None
    _HARDWARE_AVAILABLE = False


@dataclass
class VetoEvent:
    """Emitted when a palindrome entity fails its symmetry check at Layer 6."""
    entity_id: str
    divergence: float
    layer: int
    word: str
    center: str
    vitality: float
    timestamp: float = field(default_factory=time.time)


class SimulatedKillswitch:
    """
    ECS-oriented killswitch that delegates to hardware.SimulatedKillSwitch
    when available, tracking veto events with entity_id and reason.

    Tracks the veto log, survivor count, and killed count.
    """

    def __init__(self) -> None:
        self._hw = _HardwareKillSwitch(latency_ns=VETO_LATENCY_NS) if _HARDWARE_AVAILABLE else None
        self.veto_log: List[Dict] = []
        self.survivors: int = 0
        self.killed: int = 0

    def trigger(self, entity_id: str, reason: str) -> None:
        """Record a kill event."""
        entry = {
            'entity_id': entity_id,
            'reason': reason,
            'timestamp': time.time(),
        }
        self.veto_log.append(entry)
        self.killed += 1
        logger.warning(
            "⚡ KILLSWITCH ⚡ | entity=%s | reason=%s", entity_id, reason
        )


class VetoSystem(System):
    """
    Listens for VetoEvents on ``world.veto_events``, simulates the 449 ns
    hardware guillotine latency, triggers the killswitch, and removes the
    offending entity from the world.
    """

    def __init__(self) -> None:
        super().__init__()
        self.killswitch = SimulatedKillswitch()
        self.tiamat_stats = {
            'total_vetoes': 0,
            'entities_removed': 0,
        }

    def name(self) -> str:
        return "🗡️ Veto / Hardware Guillotine"

    def priority(self) -> int:
        return 100  # Run first

    def process(self, world, delta_time: float) -> None:
        events: List[VetoEvent] = getattr(world, 'veto_events', [])
        if not events:
            return

        pending = list(events)
        events.clear()

        for event in pending:
            # Simulate 449 ns hardware latency
            time.sleep(VETO_LATENCY_NS / 1e9)

            reason = (
                f"divergence={event.divergence:.4f} > 0.0300 "
                f"at layer={event.layer} word={event.word} "
                f"center={event.center} vitality={event.vitality:.4f}"
            )
            logger.warning(
                "🔱 VETO TRIGGERED 🔱 | entity=%s | %s", event.entity_id, reason
            )

            self.killswitch.trigger(event.entity_id, reason)
            self.tiamat_stats['total_vetoes'] += 1

            # Remove entity from world
            if event.entity_id in world.entity_manager.entities:
                del world.entity_manager.entities[event.entity_id]
                self.tiamat_stats['entities_removed'] += 1
                logger.info(
                    "💀 Entity %s excised from the World.", event.entity_id
                )
