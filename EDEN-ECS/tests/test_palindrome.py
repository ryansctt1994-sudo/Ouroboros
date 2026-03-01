"""Tests for PalindromeState component and Manacher's algorithm."""
import importlib
import sys
import os
import unittest

# Ensure the repo root is on the path
_REPO_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_palindrome_mod = importlib.import_module('EDEN-ECS.components.palindrome')
_constants_mod = importlib.import_module('EDEN-ECS.core.constants')

PalindromeState = _palindrome_mod.PalindromeState
manacher_radii = _constants_mod.manacher_radii
PALINDROME_ROOT = _constants_mod.PALINDROME_ROOT


EXPECTED_WORDS = [
    "ABRAXISASIXARBA",   # Layer 0 (initial)
    "BRAXISASIXARB",     # Layer 1
    "RAXISASIXAR",       # Layer 2
    "AXISASIXA",         # Layer 3
    "XISASIX",           # Layer 4
    "ISASI",             # Layer 5
    "SAS",               # Layer 6
    "A",                 # Layer 7 (Monad)
]


class TestPalindromeStateInit(unittest.TestCase):
    def test_default_word(self):
        ps = PalindromeState()
        self.assertEqual(ps.word, PALINDROME_ROOT)
        self.assertEqual(ps.word, "ABRAXISASIXARBA")

    def test_default_layer(self):
        ps = PalindromeState()
        self.assertEqual(ps.layer, 0)

    def test_default_vitality(self):
        ps = PalindromeState()
        self.assertAlmostEqual(ps.vitality, 1.0)

    def test_symmetry_verified_false(self):
        ps = PalindromeState()
        self.assertFalse(ps.symmetry_verified)

    def test_descent_history_empty(self):
        ps = PalindromeState()
        self.assertEqual(ps.descent_history, [])


class TestPalindromeDescentSequence(unittest.TestCase):
    def test_all_words_in_order(self):
        ps = PalindromeState()
        words = [ps.word]
        for _ in range(7):
            ps.descend()
            words.append(ps.word)
        self.assertEqual(words, EXPECTED_WORDS)

    def test_layer_sizes(self):
        ps = PalindromeState()
        for expected_len in [15, 13, 11, 9, 7, 5, 3, 1]:
            self.assertEqual(len(ps.word), expected_len)
            if expected_len > 1:
                ps.descend()

    def test_descend_returns_false_at_monad(self):
        ps = PalindromeState()
        for _ in range(7):
            result = ps.descend()
            self.assertTrue(result)
        result = ps.descend()
        self.assertFalse(result)

    def test_vitality_decay(self):
        ps = PalindromeState()
        self.assertAlmostEqual(ps.vitality, 1.0)
        ps.descend()
        self.assertAlmostEqual(ps.vitality, 0.85)
        ps.descend()
        self.assertAlmostEqual(ps.vitality, 0.85 ** 2)

    def test_descent_history_populated(self):
        ps = PalindromeState()
        ps.descend()
        self.assertEqual(ps.descent_history, ["ABRAXISASIXARBA"])
        ps.descend()
        self.assertEqual(ps.descent_history, ["ABRAXISASIXARBA", "BRAXISASIXARB"])


class TestCenterLetter(unittest.TestCase):
    def test_center_letter_layer0(self):
        # ABRAXISASIXARBA — middle index 7 → 'A'
        ps = PalindromeState()
        self.assertEqual(ps.center_letter(), 'A')

    def test_center_letter_layer6(self):
        ps = PalindromeState()
        for _ in range(6):
            ps.descend()
        # SAS — middle index 1 → 'A'
        self.assertEqual(ps.center_letter(), 'A')

    def test_center_letter_monad(self):
        ps = PalindromeState()
        for _ in range(7):
            ps.descend()
        self.assertEqual(ps.center_letter(), 'A')


class TestSymmetryCheck(unittest.TestCase):
    def test_perfect_palindrome(self):
        ps = PalindromeState(word="RACECAR")
        result = ps.check_symmetry()
        self.assertTrue(result)
        self.assertEqual(ps.vitality_divergence, 0.0)

    def test_imperfect_palindrome(self):
        ps = PalindromeState(word="ABCDE")
        result = ps.check_symmetry()
        self.assertFalse(result)
        self.assertGreater(ps.vitality_divergence, 0.0)

    def test_root_palindrome_is_symmetric(self):
        ps = PalindromeState()
        result = ps.check_symmetry()
        self.assertTrue(result)

    def test_all_descent_words_are_symmetric(self):
        ps = PalindromeState()
        for _ in range(7):
            result = ps.check_symmetry()
            self.assertTrue(result, f"Expected symmetry at layer {ps.layer}: {ps.word}")
            ps.descend()


class TestIsAtThreshold(unittest.TestCase):
    def test_not_at_threshold_initially(self):
        ps = PalindromeState()
        self.assertFalse(ps.is_at_threshold())

    def test_at_threshold_layer6(self):
        ps = PalindromeState()
        for _ in range(6):
            ps.descend()
        self.assertTrue(ps.is_at_threshold())


class TestManacherAlgorithm(unittest.TestCase):
    def test_single_char(self):
        radii = manacher_radii("A")
        self.assertEqual(radii, [0])

    def test_simple_palindrome(self):
        # "ABA" — center B has radius 1
        radii = manacher_radii("ABA")
        self.assertEqual(radii[1], 1)

    def test_abacaba(self):
        # "ABACABA" — center is index 3 (C), radius 3
        radii = manacher_radii("ABACABA")
        self.assertEqual(radii[3], 3)

    def test_root_palindrome_center(self):
        radii = manacher_radii(PALINDROME_ROOT)
        n = len(PALINDROME_ROOT)
        center = n // 2
        self.assertEqual(radii[center], center)

    def test_non_palindrome(self):
        # "ABCDE" — no character spans the whole string
        radii = manacher_radii("ABCDE")
        n = len("ABCDE")
        self.assertLess(max(radii), n // 2)


if __name__ == '__main__':
    unittest.main()

