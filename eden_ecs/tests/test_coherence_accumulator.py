"""Tests for chi_bar coherence accumulator and constants."""
import importlib
import math
import sys
import os
import unittest
import warnings

_REPO_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_constants = importlib.import_module('eden_ecs.core.constants')

chi_bar = _constants.chi_bar
PHI = _constants.PHI
ALPHA = _constants.ALPHA
THETA = _constants.THETA
LAMBDA = _constants.LAMBDA
DELTA = _constants.DELTA


class TestChiBarFormula(unittest.TestCase):
    def test_chi_bar_approximate_value(self):
        result = chi_bar(alpha=ALPHA, phi=PHI, lam=LAMBDA, delta=DELTA)
        # Expected ≈ 0.813–0.815
        self.assertAlmostEqual(result, 0.813, delta=0.005)

    def test_chi_bar_positive(self):
        result = chi_bar(alpha=ALPHA, phi=PHI, lam=LAMBDA, delta=DELTA)
        self.assertGreater(result, 0.0)

    def test_chi_bar_domain_error(self):
        # |λ|δ >= 1 should raise ValueError
        with self.assertRaises(ValueError):
            chi_bar(alpha=ALPHA, phi=PHI, lam=10.0, delta=0.5)

    def test_chi_bar_log_term_validity(self):
        inner = abs(LAMBDA) * DELTA
        self.assertLess(inner, 1.0, "Log domain must be < 1")
        ratio = (1 + inner) / (1 - inner)
        self.assertGreater(ratio, 1.0, "Log ratio must be > 1")

    def test_chi_bar_requires_keyword_arguments(self):
        # Positional arguments must raise TypeError (keyword-only enforcement)
        with self.assertRaises(TypeError):
            chi_bar(ALPHA, PHI, LAMBDA, DELTA)  # type: ignore[call-arg]

    def test_chi_bar_singularity_warning(self):
        # inner > 0.95 should issue a RuntimeWarning and return a bounded value
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = chi_bar(alpha=ALPHA, phi=PHI, lam=0.98, delta=1.0)
        runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
        self.assertTrue(len(runtime_warnings) > 0, "Expected RuntimeWarning for near-singularity input")
        self.assertFinite(result)

    def assertFinite(self, value):
        self.assertTrue(math.isfinite(value), f"Expected finite value, got {value}")


class TestConstants(unittest.TestCase):
    def test_theta_equals_alpha_phi(self):
        self.assertAlmostEqual(THETA, ALPHA * PHI)

    def test_theta_approximate(self):
        self.assertAlmostEqual(THETA, 7.136, delta=0.01)

    def test_phi_precision(self):
        # φ² == φ + 1
        self.assertAlmostEqual(PHI ** 2, PHI + 1, places=10)

    def test_phi_value(self):
        self.assertAlmostEqual(PHI, 1.618033988749895, places=12)

    def test_alpha_value(self):
        self.assertAlmostEqual(ALPHA, 75 / 17)


if __name__ == '__main__':
    unittest.main()
