"""Tests for TernaryRegister, TernaryRegisterSystem, and mu_mobius."""
import importlib
import sys
import os
import unittest

_REPO_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_ternary_mod = importlib.import_module('eden_ecs.systems.ternary_register_system')

TernaryRegister = _ternary_mod.TernaryRegister
TernaryRegisterSystem = _ternary_mod.TernaryRegisterSystem
mu_mobius = _ternary_mod.mu_mobius


class TestTernaryRegisterInit(unittest.TestCase):
    def test_initial_state(self):
        reg = TernaryRegister()
        self.assertEqual(reg.state, 0)

    def test_initial_direction(self):
        reg = TernaryRegister()
        self.assertEqual(reg.direction, 1)

    def test_register_array_length(self):
        reg = TernaryRegister()
        self.assertEqual(len(reg.register), 17)

    def test_register_flip_state_is_minus_one(self):
        reg = TernaryRegister()
        self.assertEqual(reg.register[7], -1)

    def test_all_other_registers_are_zero(self):
        reg = TernaryRegister()
        for i, v in enumerate(reg.register):
            if i != 7:
                self.assertEqual(v, 0, f"register[{i}] should be 0")

    def test_initial_history(self):
        reg = TernaryRegister()
        self.assertEqual(reg.history, [0])


class TestTernaryRegisterStepping(unittest.TestCase):
    def test_forward_steps(self):
        reg = TernaryRegister()
        # Should go 0 → 1 → 2 → ... → 6 before flip
        for expected in range(1, 7):
            state = reg.step()
            self.assertEqual(state, expected)
            self.assertEqual(reg.direction, 1)

    def test_not_gate_flips_direction_at_state7(self):
        reg = TernaryRegister()
        for _ in range(7):
            reg.step()
        # At state 7, direction should have flipped
        self.assertEqual(reg.state, 7)
        self.assertEqual(reg.direction, -1)

    def test_direction_persists_after_flip(self):
        reg = TernaryRegister()
        for _ in range(7):
            reg.step()
        # Now going backwards
        state = reg.step()
        # From 7, direction=-1, so state = (7-1) % 17 = 6
        self.assertEqual(state, 6)
        self.assertEqual(reg.direction, -1)

    def test_history_tracking(self):
        reg = TernaryRegister()
        reg.step()
        reg.step()
        # history starts with [0], then appends each step
        self.assertGreaterEqual(len(reg.history), 3)
        self.assertEqual(reg.history[0], 0)

    def test_ternary_value_at_state7(self):
        reg = TernaryRegister()
        for _ in range(7):
            reg.step()
        self.assertEqual(reg.state, 7)
        self.assertEqual(reg.ternary_value, -1)

    def test_ternary_value_at_other_states(self):
        reg = TernaryRegister()
        # State 0 initially
        self.assertEqual(reg.ternary_value, 0)
        reg.step()  # state 1
        self.assertEqual(reg.ternary_value, 0)


class TestMuMobius(unittest.TestCase):
    def test_mu_1(self):
        self.assertEqual(mu_mobius(1), 1)

    def test_mu_2(self):
        self.assertEqual(mu_mobius(2), -1)

    def test_mu_4(self):
        # 4 = 2² → squared prime factor → 0
        self.assertEqual(mu_mobius(4), 0)

    def test_mu_6(self):
        # 6 = 2·3 → 2 distinct primes → (-1)^2 = 1
        self.assertEqual(mu_mobius(6), 1)

    def test_mu_30(self):
        # 30 = 2·3·5 → 3 distinct primes → (-1)^3 = -1
        self.assertEqual(mu_mobius(30), -1)

    def test_mu_210(self):
        # 210 = 2·3·5·7 → 4 distinct primes → (-1)^4 = 1
        self.assertEqual(mu_mobius(210), 1)


class TestTernaryRegisterSystem(unittest.TestCase):
    def _make_world(self):
        _ecs = importlib.import_module('eden_ecs')
        world = _ecs.World()
        return world

    def test_name(self):
        sys_obj = TernaryRegisterSystem()
        self.assertIn("Ternary", sys_obj.name())

    def test_initial_stats_empty(self):
        sys_obj = TernaryRegisterSystem()
        self.assertEqual(sys_obj.entity_stats, {})

    def test_get_register_creates_on_demand(self):
        sys_obj = TernaryRegisterSystem()
        reg = sys_obj.get_register("entity_x")
        self.assertIsInstance(reg, TernaryRegister)

    def test_get_register_same_instance(self):
        sys_obj = TernaryRegisterSystem()
        reg1 = sys_obj.get_register("entity_x")
        reg2 = sys_obj.get_register("entity_x")
        self.assertIs(reg1, reg2)


if __name__ == '__main__':
    unittest.main()
