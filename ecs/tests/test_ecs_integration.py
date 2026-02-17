"""
Test suite for ECS integration layer.

Tests runtime vectorizer, manuscript validator, adapters, and orchestrator.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ecs.runtime_vectorizer import RuntimeVectorizer
from ecs.manuscript_validator import ManuscriptValidator, ValidationLevel
from ecs.adapters.quantum_adapter import QuantumAdapter, QuantumState
from ecs.adapters.sync_adapter import SyncAdapter, SyncState
from ecs.adapters.teleport_adapter import TeleportAdapter
from ecs.orchestrator import ECSOrchestrator


class TestRuntimeVectorizer:
    """Test RuntimeVectorizer class."""
    
    def test_initialization(self):
        """Test vectorizer initialization."""
        vectorizer = RuntimeVectorizer(dimensions=7)
        assert vectorizer.dimensions == 7
        assert vectorizer.use_golden_ratio is True
        assert len(vectorizer.vectors_cache) == 0
    
    def test_vectorize_simple(self):
        """Test basic vectorization."""
        vectorizer = RuntimeVectorizer(dimensions=3)
        entity_data = {'value1': 1.0, 'value2': 0.5, 'value3': 0.8}
        vector = vectorizer.vectorize(entity_data)
        
        assert vector.shape == (3,)
        assert np.isclose(np.linalg.norm(vector), 1.0)  # Normalized
    
    def test_batch_vectorize(self):
        """Test batch vectorization."""
        vectorizer = RuntimeVectorizer(dimensions=3)
        entities = [
            {'value': 1.0},
            {'value': 0.5},
            {'value': 0.3}
        ]
        vectors = vectorizer.batch_vectorize(entities)
        
        assert vectors.shape[0] == 3
        assert vectors.shape[1] == 3
    
    def test_compute_similarity(self):
        """Test similarity computation."""
        vectorizer = RuntimeVectorizer(dimensions=3)
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        v3 = np.array([0.0, 1.0, 0.0])
        
        # Identical vectors
        sim = vectorizer.compute_similarity(v1, v2)
        assert np.isclose(sim, 1.0)
        
        # Orthogonal vectors
        sim = vectorizer.compute_similarity(v1, v3)
        assert np.isclose(sim, 0.0)
    
    def test_cache_operations(self):
        """Test vector caching."""
        vectorizer = RuntimeVectorizer(dimensions=3)
        vector = np.array([1.0, 0.0, 0.0])
        
        vectorizer.cache_vector("entity1", vector)
        cached = vectorizer.get_cached_vector("entity1")
        
        assert cached is not None
        assert np.array_equal(cached, vector)
        
        vectorizer.clear_cache()
        assert vectorizer.get_cached_vector("entity1") is None


class TestManuscriptValidator:
    """Test ManuscriptValidator class."""
    
    def test_valid_entity_manuscript(self):
        """Test validation of valid entity manuscript."""
        validator = ManuscriptValidator()
        manuscript = {
            'id': 'entity1',
            'type': 'entity',
            'version': '1.0.0',
            'components': ['comp1', 'comp2']
        }
        result = validator.validate(manuscript)
        assert result.is_valid()
    
    def test_missing_required_field(self):
        """Test validation fails with missing required field."""
        validator = ManuscriptValidator()
        manuscript = {
            'id': 'entity1',
            'type': 'entity'
            # Missing 'version'
        }
        result = validator.validate(manuscript)
        assert not result.is_valid()
        assert len(result.errors) > 0
    
    def test_invalid_type(self):
        """Test validation fails with invalid type."""
        validator = ManuscriptValidator()
        manuscript = {
            'id': 'entity1',
            'type': 'invalid_type',
            'version': '1.0.0'
        }
        result = validator.validate(manuscript)
        assert not result.is_valid()
    
    def test_strict_mode(self):
        """Test strict mode converts warnings to errors."""
        validator = ManuscriptValidator(strict_mode=True)
        manuscript = {
            'id': 'entity1',
            'type': 'entity',
            'version': 'v1'  # Invalid version format
        }
        result = validator.validate(manuscript)
        assert not result.is_valid()  # Warning becomes error in strict mode
    
    def test_json_validation(self):
        """Test validation from JSON string."""
        validator = ManuscriptValidator()
        json_str = '{"id": "entity1", "type": "entity", "version": "1.0.0"}'
        result, manuscript = validator.validate_from_json(json_str)
        assert result.is_valid()
        assert manuscript is not None


class TestQuantumAdapter:
    """Test QuantumAdapter class."""
    
    def test_initialization(self):
        """Test quantum adapter initialization."""
        adapter = QuantumAdapter(num_qubits=2)
        assert adapter.num_qubits == 2
        assert adapter.dimension == 4
        assert adapter.state is not None
    
    def test_reset(self):
        """Test quantum state reset."""
        adapter = QuantumAdapter(num_qubits=2)
        adapter.reset()
        
        # Should be in |00⟩ state
        assert np.isclose(adapter.state.amplitudes[0], 1.0)
        assert np.isclose(np.sum(np.abs(adapter.state.amplitudes[1:])), 0.0)
    
    def test_hadamard_gate(self):
        """Test Hadamard gate application."""
        adapter = QuantumAdapter(num_qubits=1)
        adapter.apply_hadamard(0)
        
        # After H gate on |0⟩, should be (|0⟩ + |1⟩)/√2
        expected_prob = 0.5
        assert np.isclose(adapter.state.get_probability(0), expected_prob, atol=0.01)
        assert np.isclose(adapter.state.get_probability(1), expected_prob, atol=0.01)
    
    def test_entanglement(self):
        """Test entanglement creation."""
        adapter = QuantumAdapter(num_qubits=2)
        adapter.apply_hadamard(0)
        adapter.entangle(0, 1)
        
        # Should create Bell state
        # Measurement should show correlation
        # (This is a basic test, full verification would need multiple runs)
        assert adapter.state is not None


class TestSyncAdapter:
    """Test SyncAdapter class."""
    
    def test_initialization(self):
        """Test sync adapter initialization."""
        adapter = SyncAdapter(node_id="node1", tick_rate=60.0)
        assert adapter.node_id == "node1"
        assert adapter.tick_rate == 60.0
        assert adapter.state == SyncState.IDLE
    
    def test_peer_registration(self):
        """Test peer registration."""
        adapter = SyncAdapter(node_id="node1")
        adapter.register_peer("peer1", "192.168.1.1")
        
        assert adapter.get_peer_count() == 1
        
        adapter.unregister_peer("peer1")
        assert adapter.get_peer_count() == 0
    
    def test_clock_synchronization(self):
        """Test clock synchronization."""
        adapter = SyncAdapter(node_id="node1")
        adapter.register_peer("peer1", "192.168.1.1")
        
        import time
        peer_time = time.time() + 1.0  # Peer is 1 second ahead
        offset = adapter.synchronize_clock("peer1", peer_time)
        
        assert offset != 0.0
    
    def test_sync_status(self):
        """Test sync status reporting."""
        adapter = SyncAdapter(node_id="node1", tick_rate=60.0)
        status = adapter.get_sync_status()
        
        assert status['node_id'] == "node1"
        assert status['tick_rate'] == 60.0
        assert 'state' in status


class TestTeleportAdapter:
    """Test TeleportAdapter class."""
    
    def test_initialization(self):
        """Test teleport adapter initialization."""
        adapter = TeleportAdapter(use_encryption=True)
        assert adapter.use_encryption is True
        assert len(adapter.teleport_history) == 0
    
    def test_prepare_and_execute_teleport(self):
        """Test teleport preparation and execution."""
        adapter = TeleportAdapter(use_encryption=False)
        
        entity_state = {
            'id': 'entity1',
            'type': 'entity',
            'value': 42
        }
        
        # Prepare teleport
        package = adapter.prepare_teleport(entity_state)
        assert 'snapshot' in package
        assert 'hash' in package
        
        # Execute teleport
        reconstructed = adapter.execute_teleport(package)
        assert reconstructed['id'] == 'entity1'
        assert reconstructed['value'] == 42
    
    def test_encrypted_teleport(self):
        """Test teleport with encryption."""
        adapter = TeleportAdapter(use_encryption=True)
        
        entity_state = {'id': 'entity1', 'data': 'secret'}
        
        package = adapter.prepare_teleport(entity_state)
        reconstructed = adapter.execute_teleport(package)
        
        assert reconstructed['data'] == 'secret'
    
    def test_component_teleport(self):
        """Test component teleportation."""
        adapter = TeleportAdapter()
        
        component = {'type': 'health', 'value': 100}
        teleported = adapter.teleport_component(component, "entity1", "entity2")
        
        assert teleported['type'] == 'health'
        assert teleported['metadata']['teleported'] is True
    
    def test_teleport_stats(self):
        """Test teleport statistics."""
        adapter = TeleportAdapter()
        stats = adapter.get_teleport_stats()
        
        assert 'total_teleports' in stats
        assert stats['encryption_enabled'] is True


class TestECSOrchestrator:
    """Test ECSOrchestrator class."""
    
    def test_initialization(self):
        """Test orchestrator initialization."""
        orch = ECSOrchestrator(node_id="test_node")
        assert orch.node_id == "test_node"
        assert orch.vectorizer is not None
        assert orch.validator is not None
        assert orch.quantum is not None
        assert orch.sync is not None
        assert orch.teleport is not None
    
    def test_start_stop(self):
        """Test orchestrator start/stop."""
        orch = ECSOrchestrator()
        assert not orch.active
        
        orch.start()
        assert orch.active
        
        orch.stop()
        assert not orch.active
    
    def test_entity_registration(self):
        """Test entity registration."""
        orch = ECSOrchestrator()
        orch.start()
        
        entity = {
            'id': 'entity1',
            'type': 'entity',
            'version': '1.0.0',
            'value': 42
        }
        
        success = orch.register_entity('entity1', entity)
        assert success
        assert 'entity1' in orch.entity_registry
    
    def test_entity_unregistration(self):
        """Test entity unregistration."""
        orch = ECSOrchestrator()
        orch.start()
        
        entity = {
            'id': 'entity1',
            'type': 'entity',
            'version': '1.0.0'
        }
        
        orch.register_entity('entity1', entity)
        assert orch.unregister_entity('entity1')
        assert 'entity1' not in orch.entity_registry
    
    def test_entity_similarity(self):
        """Test entity similarity calculation."""
        orch = ECSOrchestrator()
        orch.start()
        
        entity1 = {
            'id': 'entity1',
            'type': 'entity',
            'version': '1.0.0',
            'value': 1.0
        }
        
        entity2 = {
            'id': 'entity2',
            'type': 'entity',
            'version': '1.0.0',
            'value': 1.0
        }
        
        orch.register_entity('entity1', entity1)
        orch.register_entity('entity2', entity2)
        
        similarity = orch.get_entity_similarity('entity1', 'entity2')
        assert 0.0 <= similarity <= 1.0
    
    def test_get_status(self):
        """Test status reporting."""
        orch = ECSOrchestrator(node_id="test")
        orch.start()
        
        status = orch.get_status()
        assert status['node_id'] == "test"
        assert status['active'] is True
        assert 'vectorizer' in status
        assert 'quantum' in status
        assert 'sync' in status


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
