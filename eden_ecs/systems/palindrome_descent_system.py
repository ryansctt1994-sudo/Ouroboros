"""Palindrome Descent System — drives entities through Sammonicus lifecycle."""
import time as _time

from ..core.system import System
from ..components.palindrome import PalindromeState
from ..components.memory import MemoryLattice
from ..core.constants import VETO_THRESHOLD
from ..systems.veto_system import VetoEvent


class PalindromeDescentSystem(System):
    """
    Drives entities with PalindromeState + MemoryLattice down through all
    8 layers of the Sammonicus palindrome descent.

    At Layer 6 (the S→A threshold), symmetry is checked:
    - If ``vitality_divergence > VETO_THRESHOLD``: a ``VetoEvent`` is emitted
      onto ``world.veto_events`` (created if absent).
    - If symmetry passes: descends to Layer 7 (Monad), sets ``symmetry_verified``.
    """

    def __init__(self, descend_rate: int = 10) -> None:
        super().__init__()
        self.descend_rate = descend_rate          # ticks between descents
        self._tick_count: int = 0
        self.tiamat_stats = {
            'entities_spawned': 0,
            'entities_at_layer6': 0,
            'entities_reached_monad': 0,
            'entities_vetoed': 0,
        }

    def name(self) -> str:
        return "🔤 Palindrome Descent"

    def priority(self) -> int:
        return 30

    def process(self, world, delta_time: float) -> None:
        self._tick_count += 1
        if self._tick_count % self.descend_rate != 0:
            return

        entities = world.query(PalindromeState, MemoryLattice)
        for entity in entities:
            ps = entity.get_component(PalindromeState)

            if ps.layer >= 7:
                continue

            if ps.layer == 0:
                self.tiamat_stats['entities_spawned'] += 1

            if ps.layer == 5:
                # About to descend to layer 6 — check ahead
                ps.descend()
                self.tiamat_stats['entities_at_layer6'] += 1
                ps.check_symmetry()

                if ps.vitality_divergence > VETO_THRESHOLD:
                    # Emit veto event onto the event bus
                    event = VetoEvent(
                        entity_id=entity.id,
                        divergence=ps.vitality_divergence,
                        layer=ps.layer,
                        word=ps.word,
                        center=ps.center_letter(),
                        vitality=ps.vitality,
                        timestamp=_time.time(),
                    )
                    world.emit(event)
                    self.tiamat_stats['entities_vetoed'] += 1
                else:
                    # Symmetry passes — descend to Monad
                    ps.descend()
                    ps.symmetry_verified = True
                    self.tiamat_stats['entities_reached_monad'] += 1
            else:
                ps.descend()
