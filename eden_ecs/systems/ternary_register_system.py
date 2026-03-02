"""Ternary Register System — 17-state cycle with NOT gate at state 7."""
from typing import Dict, List

from ..core.system import System
from ..core.constants import CYCLE_LENGTH, FLIP_STATE


def mu_mobius(n: int) -> int:
    """
    Möbius function μ(n).

    Returns
    -------
    int
        1  if n == 1
        0  if n has a squared prime factor
        (-1)^k  if n is a product of k distinct primes
    """
    if n == 1:
        return 1
    prime_factors = 0
    temp = n
    d = 2
    while d * d <= temp:
        if temp % d == 0:
            prime_factors += 1
            temp //= d
            if temp % d == 0:
                return 0  # squared prime factor
        d += 1
    if temp > 1:
        prime_factors += 1
    return (-1) ** prime_factors


class TernaryRegister:
    """
    17-state ternary register cycle.

    States: 0..16.
    Direction flips (+1 ↔ -1) when state 7 is reached (NOT gate).
    Register array: all 0 except register[7] = -1.
    """

    def __init__(self) -> None:
        self.state: int = 0
        self.direction: int = 1            # +1 forward, -1 reverse
        self.register: List[int] = [0] * CYCLE_LENGTH
        self.register[FLIP_STATE] = -1     # NOT gate marker
        self.history: List[int] = [0]

    def step(self) -> int:
        """Advance one step; flip direction when hitting state FLIP_STATE."""
        self.state = (self.state + self.direction) % CYCLE_LENGTH
        if self.state == FLIP_STATE:
            self.direction = -self.direction
        self.history.append(self.state)
        return self.state

    @property
    def ternary_value(self) -> int:
        """Current register value at the active state (-1, 0, or 1)."""
        return self.register[self.state]


class TernaryRegisterSystem(System):
    """
    Manages one TernaryRegister per entity; steps each tick.
    """

    def __init__(self) -> None:
        super().__init__()
        self._registers: Dict[str, TernaryRegister] = {}
        self.entity_stats: Dict[str, Dict] = {}

    def name(self) -> str:
        return "🔢 Ternary Register"

    def priority(self) -> int:
        return 20

    def _get_or_create(self, entity_id: str) -> TernaryRegister:
        if entity_id not in self._registers:
            self._registers[entity_id] = TernaryRegister()
        return self._registers[entity_id]

    def process(self, world, delta_time: float) -> None:
        from ..components.palindrome import PalindromeState
        entities = world.query(PalindromeState)
        for entity in entities:
            reg = self._get_or_create(entity.id)
            reg.step()
            self.entity_stats[entity.id] = {
                'state': reg.state,
                'direction': reg.direction,
                'ternary_value': reg.ternary_value,
                'steps': len(reg.history),
            }

    def get_register(self, entity_id: str) -> TernaryRegister:
        """Return the register for the given entity (creates if absent)."""
        return self._get_or_create(entity_id)
