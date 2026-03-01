"""Tests for ParadoxIgnition orchestrator."""
import importlib
import sys
import os
import unittest

_REPO_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_pi_mod = importlib.import_module('ABRAXIS.phase_i.paradox_ignition')
ParadoxIgnition = _pi_mod.ParadoxIgnition


class TestParadoxIgnitionInit(unittest.TestCase):
    def test_creates_instance(self):
        pi = ParadoxIgnition()
        self.assertIsNotNone(pi)

    def test_default_pulse_frequency(self):
        pi = ParadoxIgnition(pulse_frequency=417.0)
        self.assertEqual(pi.pulse_frequency, 417.0)

    def test_initial_entity_count_zero(self):
        pi = ParadoxIgnition()
        self.assertEqual(pi._entity_count, 0)

    def test_initial_pulse_count_zero(self):
        pi = ParadoxIgnition()
        self.assertEqual(pi._pulse_count, 0)

    def test_stats_property(self):
        pi = ParadoxIgnition()
        stats = pi.stats
        self.assertIn('entity_count', stats)
        self.assertIn('pulse_count', stats)
        self.assertIn('eden_available', stats)


class TestEntitySpawning(unittest.TestCase):
    def test_spawn_entity_increments_count(self):
        pi = ParadoxIgnition()
        if not pi._world:
            self.skipTest("EDEN-ECS not available")
        pi.spawn_entity()
        self.assertEqual(pi._entity_count, 1)

    def test_spawn_multiple_entities(self):
        pi = ParadoxIgnition()
        if not pi._world:
            self.skipTest("EDEN-ECS not available")
        for _ in range(5):
            pi.spawn_entity()
        self.assertEqual(pi._entity_count, 5)

    def test_spawn_entity_with_custom_word(self):
        pi = ParadoxIgnition()
        if not pi._world:
            self.skipTest("EDEN-ECS not available")
        entity = pi.spawn_entity(word="ABA", frequency=432.0)
        self.assertIsNotNone(entity)

    def test_spawn_entities_appear_in_world(self):
        pi = ParadoxIgnition()
        if not pi._world:
            self.skipTest("EDEN-ECS not available")
        pi.spawn_entity()
        self.assertEqual(len(pi._world.entity_manager.entities), 1)


class TestStatsTracking(unittest.TestCase):
    def test_stats_reflect_spawned_entities(self):
        pi = ParadoxIgnition()
        if not pi._world:
            self.skipTest("EDEN-ECS not available")
        pi.spawn_entity()
        pi.spawn_entity()
        self.assertEqual(pi.stats['entity_count'], 2)

    def test_systems_present_in_stats(self):
        pi = ParadoxIgnition()
        if not pi._world:
            self.skipTest("EDEN-ECS not available")
        stats = pi.stats
        for key in ('palindrome_stats', 'veto_stats', 'coherence_stats', 'ternary_stats'):
            self.assertIn(key, stats)


class TestLogging(unittest.TestCase):
    def test_log_final_stats_no_error(self):
        pi = ParadoxIgnition()
        pi._start_time = 0.0
        # Should not raise
        pi._log_final_stats()

    def test_log_status_no_error(self):
        pi = ParadoxIgnition()
        pi._start_time = 0.0
        pi._pulse_count = 100
        pi._log_status()


if __name__ == '__main__':
    unittest.main()
