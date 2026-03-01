"""
ABRAXIS unit tests — Phase H, Phase I, and EDEN-ECS bridge.
Run with: pytest ABRAXIS/tests/ -v
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Make the repo root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# ---------------------------------------------------------------------------
# Phase H tests
# ---------------------------------------------------------------------------

from ABRAXIS.phase_h.websocket_dashboard import (
    GnosisProcessor,
    VoicePacket,
    GnosisResponse,
    GnosisHub,
)


class TestGnosisProcessor:
    def setup_method(self):
        self.proc = GnosisProcessor()

    def test_returns_gnosis_response(self):
        packet = VoicePacket(client_id="test", transcript="hello world this is a test")
        response = self.proc.process(packet)
        assert isinstance(response, GnosisResponse)
        assert response.client_id == "test"
        assert response.transcript == "hello world this is a test"

    def test_coherence_in_range(self):
        packet = VoicePacket(client_id="c1", transcript="some words here")
        response = self.proc.process(packet)
        assert 0.0 <= response.coherence <= 1.0

    def test_short_transcript_low_coherence(self):
        packet = VoicePacket(client_id="c1", transcript="hi")
        response = self.proc.process(packet)
        # Single word → very low coherence
        assert response.coherence < 0.5

    def test_long_transcript_higher_coherence(self):
        words = " ".join(["word"] * 25)
        packet = VoicePacket(client_id="c1", transcript=words)
        response = self.proc.process(packet)
        # 25 words → should reach max base score
        assert response.coherence >= 0.5

    def test_vetoed_packet_message(self):
        # Force veto by emptying transcript (zero coherence)
        packet = VoicePacket(client_id="c1", transcript="")
        response = self.proc.process(packet)
        # Empty transcript → coherence 0 → vetoed
        assert "vetoed" in response.gnosis

    def test_phase_admitted_is_bool(self):
        packet = VoicePacket(client_id="c1", transcript="testing phase admission")
        response = self.proc.process(packet)
        assert isinstance(response.phase_admitted, bool)

    def test_packet_id_is_string(self):
        packet = VoicePacket(client_id="c1", transcript="test")
        response = self.proc.process(packet)
        assert isinstance(response.packet_id, str)
        assert len(response.packet_id) > 0

    def test_eden_bridge_attachment(self):
        class FakeBridge:
            def score(self, transcript: str) -> float:
                return 0.99

        self.proc.attach_eden_bridge(FakeBridge())
        packet = VoicePacket(client_id="c1", transcript="test bridge")
        response = self.proc.process(packet)
        assert response.coherence == 0.99


class TestGnosisHub:
    def test_hub_creation(self):
        hub = GnosisHub(host="127.0.0.1", port=9000)
        assert hub.host == "127.0.0.1"
        assert hub.port == 9000

    def test_hub_attach_eden_bridge(self):
        hub = GnosisHub()
        hub.attach_eden_bridge(None)  # should not raise


# ---------------------------------------------------------------------------
# Phase I tests
# ---------------------------------------------------------------------------

from ABRAXIS.phase_i.autonomous_nodes import (
    AutonomousNode,
    SelfHealingNode,
    SporeFactory,
    Spore,
    GovernanceCouncil,
    SubsystemSpec,
)


class TestGovernanceCouncil:
    def setup_method(self):
        self.gov = GovernanceCouncil(threshold=0.67)

    def test_propose_returns_id(self):
        pid = self.gov.propose("test proposal")
        assert isinstance(pid, str)
        assert pid in self.gov.proposals()

    def test_supermajority_passes(self):
        pid = self.gov.propose("upgrade node firmware")
        self.gov.vote(pid, "alice", approve=True)
        self.gov.vote(pid, "bob", approve=True)
        self.gov.vote(pid, "carol", approve=True)
        self.gov.vote(pid, "dave", approve=False)
        passed, ratio = self.gov.tally(pid)
        assert passed is True
        assert abs(ratio - 0.75) < 1e-9

    def test_minority_fails(self):
        pid = self.gov.propose("risky change")
        self.gov.vote(pid, "alice", approve=True)
        self.gov.vote(pid, "bob", approve=False)
        self.gov.vote(pid, "carol", approve=False)
        passed, ratio = self.gov.tally(pid)
        assert passed is False
        assert ratio < 0.67

    def test_empty_proposal_fails(self):
        pid = self.gov.propose("no votes yet")
        passed, ratio = self.gov.tally(pid)
        assert passed is False
        assert ratio == 0.0

    def test_weighted_votes(self):
        pid = self.gov.propose("weighted vote test")
        self.gov.vote(pid, "supernode", approve=True, weight=3.0)
        self.gov.vote(pid, "regular", approve=False, weight=1.0)
        passed, ratio = self.gov.tally(pid)
        assert passed is True  # 3/(3+1) = 0.75 > 0.67

    def test_vote_replacement(self):
        pid = self.gov.propose("flip vote")
        self.gov.vote(pid, "alice", approve=False)
        self.gov.vote(pid, "alice", approve=True)   # flip
        votes = self.gov._votes[pid]
        assert len(votes) == 1
        assert votes[0].approve is True

    def test_unknown_proposal_raises(self):
        try:
            self.gov.vote("nonexistent", "alice", approve=True)
            assert False, "Should have raised KeyError"
        except KeyError:
            pass


class TestSporeFactory:
    def setup_method(self):
        self.factory = SporeFactory("origin-node")

    def test_sporulate_and_germinate_roundtrip(self):
        state = {"key": "value", "number": 42, "nested": {"a": [1, 2, 3]}}
        spore = self.factory.sporulate(state)
        recovered = self.factory.germinate(spore)
        assert recovered == state

    def test_spore_has_origin_id(self):
        spore = self.factory.sporulate({"x": 1})
        assert spore.origin_id == "origin-node"

    def test_spore_serialisation_roundtrip(self):
        state = {"hello": "world"}
        spore = self.factory.sporulate(state)
        json_str = spore.to_json()
        loaded = Spore.from_json(json_str)
        recovered = self.factory.germinate(loaded)
        assert recovered == state

    def test_seed_node_creates_autonomous_node(self):
        state = {"node_id": "seed", "ticks": 5, "created_at": 0.0}
        spore = self.factory.sporulate(state)
        new_node = self.factory.seed_node(spore)
        assert isinstance(new_node, AutonomousNode)
        # Verify that the germinated state was actually restored
        assert new_node._state.get("ticks") == 5
        assert new_node._state.get("node_id") == "seed"

    def test_spore_payload_is_smaller_for_compressible_data(self):
        repetitive = {"data": "aaaa" * 1000}
        import pickle, zlib
        raw = len(pickle.dumps(repetitive))
        spore = self.factory.sporulate(repetitive)
        assert len(spore.payload) < raw


class TestAutonomousNode:
    def test_node_creation(self):
        node = AutonomousNode("test-node")
        assert node.node_id == "test-node"

    def test_node_default_id(self):
        node = AutonomousNode()
        assert node.node_id.startswith("node-")

    def test_snapshot_and_restore(self):
        node = AutonomousNode("snap-node")
        node._state["custom"] = "data"
        spore = node.snapshot()
        new_node = AutonomousNode("restored")
        new_node.restore_state(SporeFactory("x").germinate(spore))
        assert new_node._state.get("custom") == "data"

    def test_connect_peer(self):
        a = AutonomousNode("a")
        b = AutonomousNode("b")
        a.connect_peer(b)
        assert b in a._peers

    def test_connect_self_is_ignored(self):
        node = AutonomousNode("self")
        node.connect_peer(node)
        assert node not in node._peers

    def test_replicate_to_peers(self):
        root = AutonomousNode("root")
        peer = AutonomousNode("peer")
        root.connect_peer(peer)
        new_nodes = root.replicate_to_peers()
        assert len(new_nodes) == 1
        # The new node should now be connected to peer as well
        assert new_nodes[0] in peer._peers

    def test_tick_increments_count(self):
        node = AutonomousNode("ticker")
        asyncio.run(node.tick())
        asyncio.run(node.tick())
        assert node._state["ticks"] == 2

    def test_info_structure(self):
        node = AutonomousNode("info-node")
        info = node.info
        assert "node_id" in info
        assert "state" in info
        assert "health" in info
        assert "peers" in info


class TestSelfHealingNode:
    def test_register_and_get(self):
        node = SelfHealingNode("healer")

        class DummySubsystem:
            pass

        spec = SubsystemSpec(name="dummy", factory=DummySubsystem)
        node.register(spec)
        assert isinstance(node.get("dummy"), DummySubsystem)

    def test_health_report(self):
        node = SelfHealingNode("healer2")

        class Sub:
            pass

        node.register(SubsystemSpec("s1", Sub))
        h = node.health
        assert "s1" in h
        assert h["s1"]["restarts"] == 0

    def test_stop(self):
        node = SelfHealingNode("stopper")
        node._running = True
        node.stop()
        assert not node._running


# ---------------------------------------------------------------------------
# EDEN-ECS bridge tests
# ---------------------------------------------------------------------------

from ABRAXIS.eden_ecs_bridge import (
    AbraxisNodeComponent,
    PhasonicClockComponent,
    GovernanceStateComponent,
    EdenEcsBridge,
    create_abraxis_world,
)


class TestAbraxisComponents:
    def test_node_component_advance(self):
        comp = AbraxisNodeComponent("n1")
        assert comp.tick_count == 0
        comp.advance()
        assert comp.tick_count == 1

    def test_phasonic_clock_advance(self):
        import math
        clock = PhasonicClockComponent()
        # Advance and check phase is in [0, 2π)
        phase = clock.advance()
        assert 0.0 <= phase < 2 * math.pi

    def test_governance_state_record(self):
        gov = GovernanceStateComponent(threshold=0.67)
        gov.pending_proposals = 2
        gov.record(passed=True)
        assert gov.passed_proposals == 1
        assert gov.pending_proposals == 1

    def test_governance_state_record_veto(self):
        gov = GovernanceStateComponent()
        gov.pending_proposals = 1
        gov.record(passed=False)
        assert gov.vetoed_proposals == 1


class TestEdenEcsBridge:
    def test_create_bridge(self):
        bridge = EdenEcsBridge()
        assert bridge is not None

    def test_register_node(self):
        bridge = EdenEcsBridge()
        bridge.register_node("n1")
        status = bridge.status()
        assert "n1" in status["registered_nodes"]

    def test_score_returns_float(self):
        bridge = EdenEcsBridge()
        bridge.register_node("scorer")
        score = bridge.score("hello world test transcript", node_id="scorer")
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_tick_all(self):
        bridge = EdenEcsBridge()
        bridge.register_node("t1")
        bridge.register_node("t2")
        before = bridge._abraxis_components["t1"].tick_count
        bridge.tick_all()
        after = bridge._abraxis_components["t1"].tick_count
        assert after == before + 1

    def test_create_abraxis_world(self):
        bridge = create_abraxis_world(["alpha", "beta"])
        status = bridge.status()
        assert "alpha" in status["registered_nodes"]
        assert "beta" in status["registered_nodes"]

    def test_create_abraxis_world_default(self):
        bridge = create_abraxis_world()
        assert "primary" in bridge.status()["registered_nodes"]
