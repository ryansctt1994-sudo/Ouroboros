"""Palindrome descent component — Sammonicus lifecycle."""
from dataclasses import dataclass, field
from typing import List

from ..core.component import Component
from ..core.constants import PALINDROME_ROOT, PALINDROME_LAYERS, manacher_radii, VETO_THRESHOLD


@dataclass
class PalindromeState(Component):
    """
    Tracks a living palindrome as it descends through 8 layers toward the Monad.

    Descent sequence (shed 1 char from each end per layer):
      Layer 0: ABRAXISASIXARBA (15)
      Layer 1: BRAXISASIXARB   (13)
      Layer 2: RAXISASIXAR     (11)
      Layer 3: AXISASIXA       (9)
      Layer 4: XISASIX         (7)
      Layer 5: ISASI            (5)
      Layer 6: SAS              (3)
      Layer 7: A                (1)
    """

    word: str = PALINDROME_ROOT
    layer: int = 0
    vitality: float = 1.0
    vitality_divergence: float = 0.0
    symmetry_verified: bool = False
    descent_history: List[str] = field(default_factory=list)

    def descend(self) -> bool:
        """
        Shed 2 letters (one from each edge) and advance one layer.

        Returns
        -------
        bool
            ``False`` if already at the Monad (layer 7), ``True`` otherwise.
        """
        if self.layer >= 7:
            return False
        self.descent_history.append(self.word)
        self.word = self.word[1:-1]
        self.layer += 1
        self.vitality *= 0.85
        return True

    def check_symmetry(self) -> bool:
        """
        Run Manacher's algorithm on the current word to verify perfect symmetry.

        Sets ``vitality_divergence`` based on how far from perfect the word is.
        Returns ``True`` if divergence is exactly 0 (word is a perfect palindrome).
        """
        if not self.word:
            self.vitality_divergence = 0.0
            return True

        radii = manacher_radii(self.word)
        n = len(self.word)
        # For a perfect palindrome, the center character's radius == n // 2
        center_idx = n // 2
        max_radius = radii[center_idx]
        expected = n // 2
        divergence = abs(expected - max_radius) / max(expected, 1)
        self.vitality_divergence = divergence
        return divergence == 0.0

    def is_at_threshold(self) -> bool:
        """True if at layer 6 (the S→A shift)."""
        return self.layer == 6

    def center_letter(self) -> str:
        """Return the middle character of the current word."""
        if not self.word:
            return ""
        return self.word[len(self.word) // 2]
