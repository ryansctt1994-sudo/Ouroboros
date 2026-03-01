"""Coherence Accumulator System — computes χ̄ per entity."""
from typing import Dict

from ..core.system import System
from ..core.constants import chi_bar, ALPHA, PHI, LAMBDA, DELTA, THETA
from ..components.palindrome import PalindromeState
from ..components.metacube import METACUBEComponent


_REFERENCE_FREQ = 528.0  # Hz


class CoherenceAccumulatorSystem(System):
    """
    Computes the coherence accumulator χ̄ for each entity that has both a
    PalindromeState and a METACUBEComponent.

    χ̄ is modulated by:
    - Palindrome vitality
    - METACUBE quantum_frequency (normalized to 528 Hz)
    - Layer factor (1.0 at layer 0, decreasing toward layer 7)

    The result is cached per entity_id and used to update
    ``METACUBEComponent.quantum_coherence``.
    """

    def __init__(self) -> None:
        super().__init__()
        self._cache: Dict[str, float] = {}
        self.tiamat_stats = {
            'entities_above_threshold': 0,
            'entities_below_threshold': 0,
            'max_chi': 0.0,
            'min_chi': float('inf'),
        }

    def name(self) -> str:
        return "🌀 Coherence Accumulator"

    def priority(self) -> int:
        return 40

    def process(self, world, delta_time: float) -> None:
        above = below = 0
        max_chi = 0.0
        min_chi = float('inf')

        entities = world.query(PalindromeState, METACUBEComponent)
        for entity in entities:
            ps = entity.get_component(PalindromeState)
            mc = entity.get_component(METACUBEComponent)

            base_chi = chi_bar(ALPHA, PHI, LAMBDA, DELTA)

            # Palindrome vitality modulation
            vitality_mod = ps.vitality

            # METACUBE frequency modulation (normalized to 528 Hz)
            freq_mod = mc.quantum_frequency / _REFERENCE_FREQ

            # Layer factor: 1.0 at layer 0, decreasing
            layer_factor = max(0.0, 1.0 - ps.layer / 8.0)

            chi = base_chi * vitality_mod * freq_mod * layer_factor
            self._cache[entity.id] = chi

            # Update quantum_coherence as ratio chi / THETA
            ratio = chi / THETA if THETA != 0 else 0.0
            mc.quantum_coherence = max(0.0, min(1.0, ratio))

            if chi >= THETA:
                above += 1
            else:
                below += 1

            if chi > max_chi:
                max_chi = chi
            if chi < min_chi:
                min_chi = chi

        self.tiamat_stats['entities_above_threshold'] = above
        self.tiamat_stats['entities_below_threshold'] = below
        self.tiamat_stats['max_chi'] = max_chi
        self.tiamat_stats['min_chi'] = min_chi if min_chi != float('inf') else 0.0

    def get_chi(self, entity_id: str) -> float:
        """Return the cached χ̄ value for the given entity."""
        return self._cache.get(entity_id, 0.0)
