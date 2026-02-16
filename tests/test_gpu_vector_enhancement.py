"""
Test suite for GPU Vector Enhancement

Tests the GPU-accelerated vector operations for ECS components including:
- Vector operations (add, multiply, dot product)
- Magnitude and normalization
- Batch operations
- ECS bridge integration
"""

import pytest
import sys
import os

# Add parent directory to path for test execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.gpu_vector_enhancement import (
    GPUVectorProcessor,
    ECSVectorBridge,
    VectorOperation
)


class TestGPUVectorProcessor:
    """Test GPUVectorProcessor class"""
    
    def test_initialization(self):
        """Test processor initialization"""
        processor = GPUVectorProcessor(use_gpu=False)
        assert processor.device in ["cpu", "gpu"]
        assert len(processor.operation_history) == 0
    
    def test_add_vectors(self):
        """Test vector addition"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        v1 = [1.0, 2.0, 3.0]
        v2 = [4.0, 5.0, 6.0]
        
        result = processor.add_vectors(v1, v2)
        
        assert result == [5.0, 7.0, 9.0]
        assert len(processor.operation_history) == 1
        assert processor.operation_history[0].operation_type == "add"
    
    def test_multiply_vector(self):
        """Test scalar multiplication"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        v = [1.0, 2.0, 3.0]
        scalar = 2.0
        
        result = processor.multiply_vector(v, scalar)
        
        assert result == [2.0, 4.0, 6.0]
        assert len(processor.operation_history) == 1
    
    def test_dot_product(self):
        """Test dot product calculation"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        v1 = [1.0, 2.0, 3.0]
        v2 = [4.0, 5.0, 6.0]
        
        result = processor.dot_product(v1, v2)
        
        expected = 1.0*4.0 + 2.0*5.0 + 3.0*6.0  # 32.0
        assert abs(result - expected) < 0.001
    
    def test_magnitude(self):
        """Test vector magnitude"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        v = [3.0, 4.0]
        
        result = processor.magnitude(v)
        
        expected = 5.0  # 3-4-5 triangle
        assert abs(result - expected) < 0.001
    
    def test_normalize(self):
        """Test vector normalization"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        v = [3.0, 4.0]
        
        result = processor.normalize(v)
        
        # Check that result has magnitude 1
        mag = processor.magnitude(result)
        assert abs(mag - 1.0) < 0.001
    
    def test_normalize_zero_vector(self):
        """Test normalization of zero vector"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        v = [0.0, 0.0, 0.0]
        
        result = processor.normalize(v)
        
        # Should return original vector
        assert result == v
    
    def test_batch_add(self):
        """Test batch vector addition"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        vectors1 = [[1.0, 2.0], [3.0, 4.0]]
        vectors2 = [[0.1, 0.2], [0.3, 0.4]]
        
        result = processor.batch_add(vectors1, vectors2)
        
        expected = [[1.1, 2.2], [3.3, 4.4]]
        
        for i in range(len(result)):
            for j in range(len(result[i])):
                assert abs(result[i][j] - expected[i][j]) < 0.001
    
    def test_get_performance_stats(self):
        """Test performance statistics"""
        processor = GPUVectorProcessor(use_gpu=False)
        
        # No operations yet
        stats = processor.get_performance_stats()
        assert stats['total_operations'] == 0
        assert stats['total_time'] == 0.0
        
        # Perform some operations
        processor.add_vectors([1.0, 2.0], [3.0, 4.0])
        processor.multiply_vector([1.0, 2.0], 2.0)
        
        stats = processor.get_performance_stats()
        assert stats['total_operations'] == 2
        assert stats['total_time'] > 0.0
        assert stats['device'] == processor.device
        assert 'operations_by_type' in stats


class TestECSVectorBridge:
    """Test ECSVectorBridge class"""
    
    def test_initialization(self):
        """Test bridge initialization"""
        bridge = ECSVectorBridge(use_gpu=False)
        assert isinstance(bridge.processor, GPUVectorProcessor)
        assert len(bridge.entity_vectors) == 0
    
    def test_register_entity_vector(self):
        """Test entity vector registration"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        entity_id = "entity_1"
        vector = [1.0, 2.0, 3.0]
        
        bridge.register_entity_vector(entity_id, vector)
        
        assert entity_id in bridge.entity_vectors
        assert bridge.entity_vectors[entity_id] == vector
    
    def test_get_entity_vector(self):
        """Test getting entity vector"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        entity_id = "entity_1"
        vector = [1.0, 2.0, 3.0]
        bridge.register_entity_vector(entity_id, vector)
        
        result = bridge.get_entity_vector(entity_id)
        
        assert result == vector
    
    def test_get_nonexistent_entity(self):
        """Test getting vector for nonexistent entity"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        result = bridge.get_entity_vector("nonexistent")
        
        assert result is None
    
    def test_update_entity_vector(self):
        """Test updating entity vector"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        entity_id = "entity_1"
        vector1 = [1.0, 2.0, 3.0]
        vector2 = [4.0, 5.0, 6.0]
        
        bridge.register_entity_vector(entity_id, vector1)
        bridge.update_entity_vector(entity_id, vector2)
        
        result = bridge.get_entity_vector(entity_id)
        assert result == vector2
    
    def test_compute_entity_interaction(self):
        """Test entity interaction computation"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        entity_id1 = "entity_1"
        entity_id2 = "entity_2"
        
        bridge.register_entity_vector(entity_id1, [1.0, 0.0, 0.0])
        bridge.register_entity_vector(entity_id2, [1.0, 0.0, 0.0])
        
        interaction = bridge.compute_entity_interaction(entity_id1, entity_id2)
        
        # Dot product of [1,0,0] and [1,0,0] should be 1.0
        assert abs(interaction - 1.0) < 0.001
    
    def test_compute_interaction_missing_entity(self):
        """Test interaction with missing entity"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        bridge.register_entity_vector("entity_1", [1.0, 2.0, 3.0])
        
        interaction = bridge.compute_entity_interaction("entity_1", "nonexistent")
        
        assert interaction == 0.0
    
    def test_batch_update_entities(self):
        """Test batch entity updates"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        entity_ids = ["entity_1", "entity_2"]
        initial_vectors = [[1.0, 2.0], [3.0, 4.0]]
        delta_vectors = [[0.1, 0.2], [0.3, 0.4]]
        
        # Register initial vectors
        for i, entity_id in enumerate(entity_ids):
            bridge.register_entity_vector(entity_id, initial_vectors[i])
        
        # Batch update
        bridge.batch_update_entities(entity_ids, delta_vectors)
        
        # Check results
        for i, entity_id in enumerate(entity_ids):
            result = bridge.get_entity_vector(entity_id)
            expected = [initial_vectors[i][j] + delta_vectors[i][j] for j in range(2)]
            
            for j in range(len(result)):
                assert abs(result[j] - expected[j]) < 0.001
    
    def test_batch_update_new_entities(self):
        """Test batch update with new entities"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        entity_ids = ["new_entity_1", "new_entity_2"]
        delta_vectors = [[1.0, 2.0], [3.0, 4.0]]
        
        # Update entities that don't exist yet
        bridge.batch_update_entities(entity_ids, delta_vectors)
        
        # Should create entities with delta as initial value
        for i, entity_id in enumerate(entity_ids):
            result = bridge.get_entity_vector(entity_id)
            assert result is not None
    
    def test_get_stats(self):
        """Test bridge statistics"""
        bridge = ECSVectorBridge(use_gpu=False)
        
        # Register some entities
        bridge.register_entity_vector("entity_1", [1.0, 2.0, 3.0])
        bridge.register_entity_vector("entity_2", [4.0, 5.0, 6.0])
        
        # Perform an operation
        bridge.compute_entity_interaction("entity_1", "entity_2")
        
        stats = bridge.get_stats()
        
        assert stats['total_entities'] == 2
        assert 'processor_stats' in stats
        assert stats['processor_stats']['total_operations'] > 0


class TestVectorOperation:
    """Test VectorOperation dataclass"""
    
    def test_creation(self):
        """Test creating VectorOperation"""
        op = VectorOperation(
            operation_type="add",
            input_vectors=[[1.0, 2.0], [3.0, 4.0]],
            output_vector=[4.0, 6.0],
            execution_time=0.001,
            device="cpu"
        )
        
        assert op.operation_type == "add"
        assert len(op.input_vectors) == 2
        assert op.output_vector == [4.0, 6.0]
        assert op.execution_time == 0.001
        assert op.device == "cpu"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
