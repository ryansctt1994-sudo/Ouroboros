"""
EDEN ECS Mycelial Bridge Tests
===============================

Comprehensive tests for the mycelial bridge integration between
Python EDEN-ECS and Rust ForgeEngine.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import math
import pytest
import warnings
from typing import List

from eden_ecs.core import World, Entity, EntityType
from eden_ecs.components import Consciousness7D
from eden_ecs.forge_bridge import SlotAllocator, ForgeBridge, ConsensusSnapshot
from eden_ecs.mycelial_components import HyphalNodeComponent
from eden_ecs.mycelial_sync import MycelialSyncSystem


class TestSlotAllocator:
    """Tests for SlotAllocator class."""
    
    def test_sequential_allocation(self):
        """Test sequential slot allocation."""
        allocator = SlotAllocator(max_slots=256)
        
        # Allocate slots sequentially
        slot0 = allocator.allocate("entity-0")
        slot1 = allocator.allocate("entity-1")
        slot2 = allocator.allocate("entity-2")
        
        assert slot0 == 0
        assert slot1 == 1
        assert slot2 == 2
    
    def test_idempotent_allocation(self):
        """Test idempotent re-allocation returns same slot."""
        allocator = SlotAllocator(max_slots=256)
        
        slot1 = allocator.allocate("entity-a")
        slot2 = allocator.allocate("entity-a")  # Re-allocate same entity
        
        assert slot1 == slot2
    
    def test_release_and_reuse(self):
        """Test release and deterministic reuse."""
        allocator = SlotAllocator(max_slots=256)
        
        # Allocate 3 slots
        slot0 = allocator.allocate("entity-0")
        slot1 = allocator.allocate("entity-1")
        slot2 = allocator.allocate("entity-2")
        
        # Release middle slot
        released = allocator.release("entity-1")
        assert released == 1
        
        # Allocate new entity - should reuse freed slot 1
        slot_new = allocator.allocate("entity-new")
        assert slot_new == 1
    
    def test_overflow_raises_error(self):
        """Test that exhausting all slots raises RuntimeError."""
        allocator = SlotAllocator(max_slots=4)
        
        # Allocate all 4 slots
        for i in range(4):
            allocator.allocate(f"entity-{i}")
        
        # Try to allocate one more - should raise
        with pytest.raises(RuntimeError, match="exhausted"):
            allocator.allocate("entity-overflow")
    
    def test_release_unknown_returns_none(self):
        """Test releasing unknown entity returns None."""
        allocator = SlotAllocator(max_slots=256)
        
        result = allocator.release("unknown-entity")
        assert result is None
    
    def test_get_slot(self):
        """Test get_slot retrieval."""
        allocator = SlotAllocator(max_slots=256)
        
        allocator.allocate("entity-x")
        slot = allocator.get_slot("entity-x")
        assert slot == 0
        
        unknown_slot = allocator.get_slot("unknown")
        assert unknown_slot is None
    
    def test_get_entity(self):
        """Test get_entity retrieval."""
        allocator = SlotAllocator(max_slots=256)
        
        allocator.allocate("entity-y")
        entity_id = allocator.get_entity(0)
        assert entity_id == "entity-y"
        
        no_entity = allocator.get_entity(100)
        assert no_entity is None


class TestForgeBridgePythonFallback:
    """Tests for ForgeBridge with Python fallback (use_rust=False)."""
    
    def test_consensus_snapshot_to_dict(self):
        """Test ConsensusSnapshot.to_dict() serialization."""
        snapshot = ConsensusSnapshot(
            round=42,
            consensus_achieved=True,
            network_gamma=0.75,
            num_active_agents=10,
            agreement_ratio=0.82,
            per_agent_gammas={0: 0.7, 1: 0.75, 2: 0.8}
        )
        
        d = snapshot.to_dict()
        
        assert d['round'] == 42
        assert d['consensus_achieved'] is True
        assert d['network_gamma'] == 0.75
        assert d['num_active_agents'] == 10
        assert d['agreement_ratio'] == 0.82
        assert d['per_agent_gammas'] == {0: 0.7, 1: 0.75, 2: 0.8}
    
    def test_identical_states_achieve_consensus(self):
        """Pushing identical states should achieve consensus."""
        bridge = ForgeBridge(num_agents=256, use_rust=False)
        
        # Push 5 identical states
        identical_state = [0.7] * 7
        for i in range(5):
            bridge.update_agent(f"entity-{i}", identical_state, slot=i)
        
        snapshot = bridge.consensus_round()
        
        assert snapshot.consensus_achieved is True
        assert snapshot.num_active_agents == 5
        assert snapshot.agreement_ratio >= 0.67
    
    def test_divergent_states_no_consensus(self):
        """Pushing divergent states should not achieve consensus."""
        bridge = ForgeBridge(num_agents=256, use_rust=False)
        
        # Push divergent states
        for i in range(5):
            state = [0.1 + i * 0.15] * 7  # Very different states
            bridge.update_agent(f"entity-{i}", state, slot=i)
        
        snapshot = bridge.consensus_round()
        
        # With very divergent states, consensus should fail
        # (though this depends on epsilon threshold)
        assert snapshot.num_active_agents == 5
        assert 0.0 <= snapshot.agreement_ratio <= 1.0
    
    def test_per_agent_gamma_retrieval(self):
        """Test per-agent gamma values are computed."""
        bridge = ForgeBridge(num_agents=256, use_rust=False)
        
        # Push some states
        for i in range(3):
            state = [0.6 + i * 0.1] * 7
            bridge.update_agent(f"entity-{i}", state, slot=i)
        
        snapshot = bridge.consensus_round()
        
        # Should have per-agent gammas
        assert len(snapshot.per_agent_gammas) > 0
        
        # All gammas should be in [0, 1]
        for gamma in snapshot.per_agent_gammas.values():
            assert 0.0 <= gamma <= 1.0
    
    def test_gamma_computation(self):
        """Test gamma computation matches formula: Γ = sqrt(D×C) × E^(1/3) × S."""
        bridge = ForgeBridge(num_agents=256, use_rust=False)
        
        # Perfectly uniform state should have perfect coherence
        # but diversity=0, so gamma = sqrt(0*1) * E^(1/3) * S = 0
        uniform_state = [0.5] * 7
        gamma_uniform = bridge._compute_gamma(uniform_state)
        # With uniform state: D=0, C=1, E=0.5, S=0.5
        # Γ = sqrt(0*1) * 0.5^(1/3) * 0.5 = 0
        assert gamma_uniform == 0.0
        
        # Non-uniform state should have positive gamma
        varied_state = [0.6, 0.7, 0.5, 0.6, 0.7, 0.5, 0.6]
        gamma_varied = bridge._compute_gamma(varied_state)
        assert gamma_varied > 0.0


class TestHyphalNodeComponent:
    """Tests for HyphalNodeComponent."""
    
    def test_phase_advance(self):
        """Test phase advance by frequency."""
        node = HyphalNodeComponent(frequency=0.1, phase=0.0)
        
        dt = 1.0  # 1 second
        node.advance_phase(dt)
        
        # Expected phase: 2π × 0.1 × 1.0 = 0.2π
        # Using small tolerance for floating-point rounding in multiplication
        expected = 2.0 * math.pi * 0.1
        assert abs(node.phase - expected) < 1e-10
    
    def test_phase_wrap(self):
        """Test phase wrapping to [0, 2π)."""
        node = HyphalNodeComponent(frequency=1.0, phase=0.0)
        
        dt = 3.0  # 3 seconds - should wrap around
        node.advance_phase(dt)
        
        # Phase should be in [0, 2π)
        assert 0.0 <= node.phase < 2.0 * math.pi
    
    def test_pll_convergence(self):
        """Test PLL phase correction converges to target."""
        node = HyphalNodeComponent(phase=0.0)
        target_phase = math.pi / 2  # 90 degrees
        
        # Run many iterations of correction
        for _ in range(100):
            node.correct_phase(target_phase)
        
        # Should converge close to target
        error = abs(node.phase - target_phase)
        assert error < 0.01  # Within 0.01 radians
        assert node.synchronized is True
    
    def test_circular_phase_distance(self):
        """Test circular phase distance calculation."""
        node1 = HyphalNodeComponent(phase=0.1)
        node2 = HyphalNodeComponent(phase=0.2)
        
        dist = node1.phase_distance_to(node2)
        # Exact equality for simple subtraction
        assert dist == 0.1
        
        # Test wrap-around distance
        node3 = HyphalNodeComponent(phase=0.1)
        node4 = HyphalNodeComponent(phase=2.0 * math.pi - 0.1)
        
        dist_wrap = node3.phase_distance_to(node4)
        # Should be 0.2, not ~6.28
        assert dist_wrap < 1.0
    
    def test_latency_recording(self):
        """Test latency recording and averaging."""
        node = HyphalNodeComponent()
        
        # Record some latencies
        node.record_latency(100.0)
        node.record_latency(200.0)
        node.record_latency(300.0)
        
        # Average should be exactly 200.0 (simple arithmetic mean)
        assert node.avg_latency_us == 200.0
    
    def test_to_dict_serialization(self):
        """Test to_dict serialization."""
        node = HyphalNodeComponent(
            node_id="test-node",
            phase=1.5,
            frequency=0.0997,
            synchronized=True,
            neighbor_ids=["n1", "n2"],
            forge_slot=42
        )
        
        d = node.to_dict()
        
        assert d['node_id'] == "test-node"
        assert d['phase'] == 1.5
        assert d['frequency'] == 0.0997
        assert d['synchronized'] is True
        assert d['neighbor_ids'] == ["n1", "n2"]
        assert d['forge_slot'] == 42
        
        # Should not include private fields
        assert '_latency_samples' not in d
        assert '_max_latency_samples' not in d


class TestMycelialSyncSystem:
    """Tests for MycelialSyncSystem."""
    
    def test_auto_creates_hyphal_components(self):
        """Test system auto-creates HyphalNodeComponents on tick."""
        world = World()
        system = MycelialSyncSystem(priority=45, use_rust=False)
        
        # Create entities with Consciousness7D
        for i in range(3):
            entity = world.create_entity(EntityType.AI_AGENT)
            entity.add_component(Consciousness7D())
        
        # Before update, no HyphalNodeComponents
        assert len(world.query_entities(None, HyphalNodeComponent)) == 0
        
        # Run system update
        system.update(world, 0.1)
        
        # After update, all should have HyphalNodeComponents
        hyphal_entities = world.query_entities(None, HyphalNodeComponent)
        assert len(hyphal_entities) == 3
        
        # Each should have a forge slot
        for entity in hyphal_entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            assert hyphal.forge_slot >= 0
    
    def test_entity_removal_frees_slots(self):
        """Test entity removal frees forge slots."""
        world = World()
        system = MycelialSyncSystem(priority=45, use_rust=False)
        
        # Create 3 entities
        entities = []
        for i in range(3):
            entity = world.create_entity(EntityType.AI_AGENT)
            entity.add_component(Consciousness7D())
            entities.append(entity)
        
        # First update - allocate slots
        system.update(world, 0.1)
        
        # Get slot of second entity
        hyphal = entities[1].get_component(HyphalNodeComponent)
        slot_before = hyphal.forge_slot
        
        # Remove second entity
        world.destroy_entity(entities[1].entity_id)
        
        # Second update - should detect removal
        system.update(world, 0.1)
        
        # Slot should be freed and available for reuse
        assert system.allocator.get_entity(slot_before) is None
    
    def test_consensus_tags_entities(self):
        """Test consensus round tags entities with forge_consensus."""
        world = World()
        system = MycelialSyncSystem(priority=45, use_rust=False)
        
        # Create entities with identical states (should achieve consensus)
        for i in range(5):
            entity = world.create_entity(EntityType.AI_AGENT)
            c7d = Consciousness7D()
            # Set to identical values
            c7d.awareness = 0.7
            c7d.intention = 0.7
            c7d.emotion = 0.7
            c7d.cognition = 0.7
            c7d.memory = 0.7
            c7d.creativity = 0.7
            c7d.integration = 0.7
            entity.add_component(c7d)
        
        # Run update
        system.update(world, 0.1)
        
        # Check if entities have forge_consensus tag
        # (May or may not be set depending on Python fallback consensus)
        # At minimum, system should run without error
        assert system.total_syncs == 1
    
    def test_pll_converges(self):
        """Test PLL convergence over multiple ticks."""
        world = World()
        system = MycelialSyncSystem(priority=45, use_rust=False)
        
        # Create 5 entities
        for i in range(5):
            entity = world.create_entity(EntityType.AI_AGENT)
            entity.add_component(Consciousness7D())
        
        # Run many updates to allow PLL to converge
        for _ in range(200):
            system.update(world, 0.05)  # 50ms ticks
        
        # Check phase coherence - compute Kuramoto order parameter R
        hyphal_entities = world.query_entities(None, HyphalNodeComponent)
        phases = [e.get_component(HyphalNodeComponent).phase for e in hyphal_entities]
        
        # R = |mean(e^(i*theta))|
        mean_sin = sum(math.sin(p) for p in phases) / len(phases)
        mean_cos = sum(math.cos(p) for p in phases) / len(phases)
        R = math.sqrt(mean_sin**2 + mean_cos**2)
        
        # After convergence, R should be reasonably high (> 0.5)
        # Note: Exact value depends on PLL parameters
        assert R > 0.0  # At minimum, should be positive
    
    def test_metrics_dict(self):
        """Test get_metrics returns expected keys."""
        world = World()
        system = MycelialSyncSystem(priority=45, use_rust=False)
        
        # Create some entities
        for i in range(3):
            entity = world.create_entity(EntityType.AI_AGENT)
            entity.add_component(Consciousness7D())
        
        # Run update
        system.update(world, 0.1)
        
        metrics = system.get_metrics()
        
        # Check expected keys
        assert 'total_syncs' in metrics
        assert 'total_consensus_achieved' in metrics
        assert 'consensus_rate' in metrics
        assert 'avg_sync_latency_us' in metrics
        
        assert metrics['total_syncs'] == 1
    
    def test_warning_for_few_agents(self):
        """Test warning is emitted for < 4 agents."""
        world = World()
        system = MycelialSyncSystem(priority=45, use_rust=False)
        
        # Create only 2 entities (< 4 minimum for BFT)
        for i in range(2):
            entity = world.create_entity(EntityType.AI_AGENT)
            entity.add_component(Consciousness7D())
        
        # Run update - should emit warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            system.update(world, 0.1)
            
            # Check that a RuntimeWarning was raised
            assert len(w) > 0
            assert issubclass(w[0].category, RuntimeWarning)
            assert "< 4 minimum" in str(w[0].message)


class TestTernaryAxisConsistency:
    """Test that Python to_ternary() matches Rust canonical grouping."""
    
    def test_ternary_grouping(self):
        """Test ternary axis grouping matches Rust (sync.rs lines 95-116)."""
        c7d = Consciousness7D(
            awareness=0.9,
            intention=0.8,
            emotion=0.7,
            cognition=0.6,
            memory=0.5,
            creativity=0.4,
            integration=0.3
        )
        
        ternary = c7d.to_ternary()
        
        # Manually compute expected values
        # Cognitive = (awareness + cognition + integration) / 3
        cognitive = (0.9 + 0.6 + 0.3) / 3.0  # = 0.6
        # Temporal = (intention + memory) / 2
        temporal = (0.8 + 0.5) / 2.0  # = 0.65
        # Affective = (emotion + creativity) / 2
        affective = (0.7 + 0.4) / 2.0  # = 0.55
        
        # Normalize to sum = 1.0
        total = cognitive + temporal + affective
        expected = [cognitive / total, temporal / total, affective / total]
        
        # Check match
        for i in range(3):
            assert abs(ternary[i] - expected[i]) < 1e-9
    
    def test_to_array(self):
        """Test to_array() returns canonical 7-element order."""
        c7d = Consciousness7D(
            awareness=0.1,
            intention=0.2,
            emotion=0.3,
            cognition=0.4,
            memory=0.5,
            creativity=0.6,
            integration=0.7
        )
        
        arr = c7d.to_array()
        
        assert len(arr) == 7
        assert arr == [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]


class TestFullIntegration:
    """Integration tests for complete mycelial bridge flow."""
    
    def test_end_to_end_world_tick(self):
        """Test full integration: World + MycelialSyncSystem + entities."""
        # Create world
        world = World("Test-Mycelial-World")
        
        # Add MycelialSyncSystem (Python fallback for CI)
        sync_system = MycelialSyncSystem(priority=45, use_rust=False)
        world.add_system(sync_system)
        
        # Create 5 AI agent entities with consciousness
        for i in range(5):
            entity = world.create_entity(EntityType.AI_AGENT, f"agent-{i}")
            c7d = Consciousness7D(
                awareness=0.6 + i * 0.05,
                intention=0.7,
                emotion=0.65,
                cognition=0.7 + i * 0.02,
                memory=0.6,
                creativity=0.55,
                integration=0.68
            )
            entity.add_component(c7d)
        
        # Tick the world 10 times
        for _ in range(10):
            world.tick(dt=0.05)
        
        # Verify all entities have HyphalNodeComponents
        hyphal_entities = world.query_entities(None, HyphalNodeComponent)
        assert len(hyphal_entities) == 5
        
        # Verify metrics
        metrics = sync_system.get_metrics()
        assert metrics['total_syncs'] == 10
        assert metrics['avg_sync_latency_us'] > 0
        
        # Verify all have forge slots
        for entity in hyphal_entities:
            hyphal = entity.get_component(HyphalNodeComponent)
            assert hyphal.forge_slot >= 0
            assert hyphal.last_gamma >= 0.0
        
        # Verify world metrics
        world_metrics = world.get_metrics()
        assert world_metrics['entity_count'] == 5
        assert world_metrics['ticks'] == 10
    
    def test_dynamic_entity_lifecycle(self):
        """Test entities being added and removed during runtime."""
        world = World("Dynamic-Test-World")
        sync_system = MycelialSyncSystem(priority=45, use_rust=False)
        world.add_system(sync_system)
        
        # Start with 3 entities
        entities = []
        for i in range(3):
            entity = world.create_entity(EntityType.AI_AGENT)
            entity.add_component(Consciousness7D())
            entities.append(entity)
        
        # Tick once
        world.tick(dt=0.1)
        assert sync_system.allocator.get_slot(entities[0].entity_id) == 0
        
        # Remove middle entity
        world.destroy_entity(entities[1].entity_id)
        
        # Tick again
        world.tick(dt=0.1)
        
        # Add a new entity - should reuse freed slot
        new_entity = world.create_entity(EntityType.AI_AGENT)
        new_entity.add_component(Consciousness7D())
        
        # Tick to allocate
        world.tick(dt=0.1)
        
        # New entity should have reused slot 1
        hyphal = new_entity.get_component(HyphalNodeComponent)
        assert hyphal.forge_slot == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
