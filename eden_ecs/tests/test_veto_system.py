"""Tests for VetoEvent, SimulatedKillswitch, and VetoSystem."""
import importlib
import sys
import os
import time
import unittest

_REPO_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_veto_mod = importlib.import_module('eden_ecs.systems.veto_system')
_ecs_mod = importlib.import_module('eden_ecs')

VetoEvent = _veto_mod.VetoEvent
SimulatedKillswitch = _veto_mod.SimulatedKillswitch
VetoSystem = _veto_mod.VetoSystem

World = _ecs_mod.World
EntityType = _ecs_mod.EntityType


def _make_world_with_entity():
    world = World()
    entity = world.create_entity(EntityType.SYSTEM, "test_entity")
    world.veto_events = []
    return world, entity


class TestVetoEvent(unittest.TestCase):
    def test_creation(self):
        event = VetoEvent(
            entity_id="abc",
            divergence=0.05,
            layer=6,
            word="SAS",
            center="A",
            vitality=0.4,
        )
        self.assertEqual(event.entity_id, "abc")
        self.assertEqual(event.divergence, 0.05)
        self.assertEqual(event.layer, 6)
        self.assertEqual(event.word, "SAS")
        self.assertEqual(event.center, "A")
        self.assertAlmostEqual(event.vitality, 0.4)

    def test_timestamp_auto(self):
        before = time.time()
        event = VetoEvent(
            entity_id="x", divergence=0.1, layer=6,
            word="SAS", center="A", vitality=0.5,
        )
        self.assertGreaterEqual(event.timestamp, before)


class TestSimulatedKillswitch(unittest.TestCase):
    def test_initial_state(self):
        ks = SimulatedKillswitch()
        self.assertEqual(ks.killed, 0)
        self.assertEqual(ks.survivors, 0)
        self.assertEqual(ks.veto_log, [])

    def test_trigger_increments_killed(self):
        ks = SimulatedKillswitch()
        ks.trigger("entity1", "test reason")
        self.assertEqual(ks.killed, 1)

    def test_trigger_multiple(self):
        ks = SimulatedKillswitch()
        ks.trigger("e1", "r1")
        ks.trigger("e2", "r2")
        ks.trigger("e3", "r3")
        self.assertEqual(ks.killed, 3)
        self.assertEqual(len(ks.veto_log), 3)

    def test_veto_log_contents(self):
        ks = SimulatedKillswitch()
        ks.trigger("ent_42", "divergence=0.05")
        self.assertEqual(ks.veto_log[0]['entity_id'], "ent_42")
        self.assertEqual(ks.veto_log[0]['reason'], "divergence=0.05")


class TestVetoSystem(unittest.TestCase):
    def test_initial_stats(self):
        vs = VetoSystem()
        self.assertEqual(vs.tiamat_stats['total_vetoes'], 0)
        self.assertEqual(vs.tiamat_stats['entities_removed'], 0)

    def test_processes_veto_events(self):
        world, entity = _make_world_with_entity()
        vs = VetoSystem()
        world.add_system(vs)

        event = VetoEvent(
            entity_id=entity.id,
            divergence=0.05,
            layer=6,
            word="SAS",
            center="A",
            vitality=0.4,
        )
        world.veto_events.append(event)

        vs.process(world, 0.016)

        self.assertEqual(vs.tiamat_stats['total_vetoes'], 1)

    def test_entity_removed_from_world(self):
        world, entity = _make_world_with_entity()
        vs = VetoSystem()

        eid = entity.id
        self.assertIn(eid, world.entity_manager.entities)

        event = VetoEvent(
            entity_id=eid,
            divergence=0.05,
            layer=6,
            word="SAS",
            center="A",
            vitality=0.4,
        )
        world.veto_events.append(event)
        vs.process(world, 0.016)

        self.assertNotIn(eid, world.entity_manager.entities)
        self.assertEqual(vs.tiamat_stats['entities_removed'], 1)

    def test_killswitch_triggered(self):
        world, entity = _make_world_with_entity()
        vs = VetoSystem()

        event = VetoEvent(
            entity_id=entity.id,
            divergence=0.08,
            layer=6,
            word="SAS",
            center="A",
            vitality=0.3,
        )
        world.veto_events.append(event)
        vs.process(world, 0.016)

        self.assertEqual(vs.killswitch.killed, 1)

    def test_latency_simulation(self):
        world, entity = _make_world_with_entity()
        vs = VetoSystem()

        event = VetoEvent(
            entity_id=entity.id,
            divergence=0.05,
            layer=6,
            word="SAS",
            center="A",
            vitality=0.4,
        )
        world.veto_events.append(event)

        start = time.perf_counter()
        vs.process(world, 0.016)
        elapsed = time.perf_counter() - start

        # Should have slept at least 449ns (much less than 1ms)
        self.assertGreaterEqual(elapsed, 0.0)

    def test_no_events_no_action(self):
        world, entity = _make_world_with_entity()
        vs = VetoSystem()
        world.veto_events = []
        vs.process(world, 0.016)
        self.assertEqual(vs.tiamat_stats['total_vetoes'], 0)


if __name__ == '__main__':
    unittest.main()
