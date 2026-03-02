"""
GPU Vector Enhancement - Bridge between ECS Components and GPU-based Vector Operations

This module provides GPU-accelerated vector operations for ECS components,
enabling high-performance computation for large-scale simulations.
"""

import sys
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

# Try to import GPU libraries, fall back to CPU if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: NumPy not available, using CPU-only mode")

try:
    # Try to import JAX for GPU acceleration
    import jax
    import jax.numpy as jnp
    HAS_JAX = True
except ImportError:
    HAS_JAX = False


@dataclass
class VectorOperation:
    """Represents a vector operation"""
    operation_type: str
    input_vectors: List[Any]
    output_vector: Optional[Any] = None
    execution_time: float = 0.0
    device: str = "cpu"


class GPUVectorProcessor:
    """
    GPU-accelerated vector processor for ECS components
    
    Provides high-performance vector operations including:
    - Vector addition, subtraction, multiplication
    - Dot products and cross products
    - Normalization and magnitude calculations
    - Batch operations for multiple entities
    """
    
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu and HAS_JAX
        self.device = "gpu" if self.use_gpu else "cpu"
        self.operation_history: List[VectorOperation] = []
        
        if self.use_gpu:
            print(f"✓ GPU Vector Processor initialized (JAX backend)")
        elif HAS_NUMPY:
            print(f"✓ Vector Processor initialized (NumPy CPU backend)")
        else:
            print(f"⚠ Vector Processor initialized (Pure Python fallback)")
    
    def _to_array(self, data: Any) -> Any:
        """Convert data to appropriate array format"""
        if self.use_gpu:
            return jnp.array(data)
        elif HAS_NUMPY:
            return np.array(data)
        else:
            return list(data) if not isinstance(data, list) else data
    
    def add_vectors(self, v1: List[float], v2: List[float]) -> List[float]:
        """Add two vectors"""
        start_time = time.time()
        
        if self.use_gpu:
            a1 = jnp.array(v1)
            a2 = jnp.array(v2)
            result = a1 + a2
            result = result.tolist()
        elif HAS_NUMPY:
            a1 = np.array(v1)
            a2 = np.array(v2)
            result = (a1 + a2).tolist()
        else:
            result = [v1[i] + v2[i] for i in range(len(v1))]
        
        execution_time = time.time() - start_time
        
        self.operation_history.append(VectorOperation(
            operation_type="add",
            input_vectors=[v1, v2],
            output_vector=result,
            execution_time=execution_time,
            device=self.device
        ))
        
        return result
    
    def multiply_vector(self, v: List[float], scalar: float) -> List[float]:
        """Multiply vector by scalar"""
        start_time = time.time()
        
        if self.use_gpu:
            arr = jnp.array(v)
            result = (arr * scalar).tolist()
        elif HAS_NUMPY:
            arr = np.array(v)
            result = (arr * scalar).tolist()
        else:
            result = [x * scalar for x in v]
        
        execution_time = time.time() - start_time
        
        self.operation_history.append(VectorOperation(
            operation_type="multiply_scalar",
            input_vectors=[v],
            output_vector=result,
            execution_time=execution_time,
            device=self.device
        ))
        
        return result
    
    def dot_product(self, v1: List[float], v2: List[float]) -> float:
        """Calculate dot product of two vectors"""
        start_time = time.time()
        
        if self.use_gpu:
            a1 = jnp.array(v1)
            a2 = jnp.array(v2)
            result = float(jnp.dot(a1, a2))
        elif HAS_NUMPY:
            a1 = np.array(v1)
            a2 = np.array(v2)
            result = float(np.dot(a1, a2))
        else:
            result = sum(v1[i] * v2[i] for i in range(len(v1)))
        
        execution_time = time.time() - start_time
        
        self.operation_history.append(VectorOperation(
            operation_type="dot_product",
            input_vectors=[v1, v2],
            output_vector=result,
            execution_time=execution_time,
            device=self.device
        ))
        
        return result
    
    def magnitude(self, v: List[float]) -> float:
        """Calculate magnitude of a vector"""
        start_time = time.time()
        
        if self.use_gpu:
            arr = jnp.array(v)
            result = float(jnp.linalg.norm(arr))
        elif HAS_NUMPY:
            arr = np.array(v)
            result = float(np.linalg.norm(arr))
        else:
            result = sum(x**2 for x in v) ** 0.5
        
        execution_time = time.time() - start_time
        
        self.operation_history.append(VectorOperation(
            operation_type="magnitude",
            input_vectors=[v],
            output_vector=result,
            execution_time=execution_time,
            device=self.device
        ))
        
        return result
    
    def normalize(self, v: List[float]) -> List[float]:
        """Normalize a vector"""
        mag = self.magnitude(v)
        if mag == 0:
            return v
        return self.multiply_vector(v, 1.0 / mag)
    
    def batch_add(self, vectors1: List[List[float]], vectors2: List[List[float]]) -> List[List[float]]:
        """Add multiple vectors in batch (GPU-accelerated)"""
        start_time = time.time()
        
        if self.use_gpu:
            a1 = jnp.array(vectors1)
            a2 = jnp.array(vectors2)
            result = (a1 + a2).tolist()
        elif HAS_NUMPY:
            a1 = np.array(vectors1)
            a2 = np.array(vectors2)
            result = (a1 + a2).tolist()
        else:
            result = [
                [vectors1[i][j] + vectors2[i][j] for j in range(len(vectors1[i]))]
                for i in range(len(vectors1))
            ]
        
        execution_time = time.time() - start_time
        
        self.operation_history.append(VectorOperation(
            operation_type="batch_add",
            input_vectors=[vectors1, vectors2],
            output_vector=result,
            execution_time=execution_time,
            device=self.device
        ))
        
        return result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.operation_history:
            return {
                'total_operations': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'device': self.device
            }
        
        total_time = sum(op.execution_time for op in self.operation_history)
        
        return {
            'total_operations': len(self.operation_history),
            'total_time': total_time,
            'average_time': total_time / len(self.operation_history),
            'device': self.device,
            'operations_by_type': self._count_by_type()
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count operations by type"""
        counts = {}
        for op in self.operation_history:
            counts[op.operation_type] = counts.get(op.operation_type, 0) + 1
        return counts


class ECSVectorBridge:
    """
    Bridge between ECS components and GPU vector operations
    
    Provides integration layer for ECS entities to use GPU-accelerated
    vector operations seamlessly.
    """
    
    def __init__(self, use_gpu: bool = True):
        self.processor = GPUVectorProcessor(use_gpu)
        self.entity_vectors: Dict[str, List[float]] = {}
    
    def register_entity_vector(self, entity_id: str, vector: List[float]) -> None:
        """Register a vector for an ECS entity"""
        self.entity_vectors[entity_id] = vector
    
    def get_entity_vector(self, entity_id: str) -> Optional[List[float]]:
        """Get vector for an entity"""
        return self.entity_vectors.get(entity_id)
    
    def update_entity_vector(self, entity_id: str, new_vector: List[float]) -> None:
        """Update vector for an entity"""
        self.entity_vectors[entity_id] = new_vector
    
    def compute_entity_interaction(self, entity_id1: str, entity_id2: str) -> float:
        """Compute interaction strength between two entities (dot product)"""
        v1 = self.entity_vectors.get(entity_id1)
        v2 = self.entity_vectors.get(entity_id2)
        
        if v1 is None or v2 is None:
            return 0.0
        
        return self.processor.dot_product(v1, v2)
    
    def batch_update_entities(self, entity_ids: List[str], delta_vectors: List[List[float]]) -> None:
        """Update multiple entities in batch"""
        current_vectors = [self.entity_vectors.get(eid, [0.0]*len(delta_vectors[0])) 
                          for eid in entity_ids]
        
        new_vectors = self.processor.batch_add(current_vectors, delta_vectors)
        
        for i, entity_id in enumerate(entity_ids):
            self.entity_vectors[entity_id] = new_vectors[i]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the bridge"""
        return {
            'total_entities': len(self.entity_vectors),
            'processor_stats': self.processor.get_performance_stats()
        }


# Example usage and testing
if __name__ == "__main__":
    print("🚀 GPU Vector Enhancement Module\n")
    print("="*60)
    
    # Test GPU Vector Processor
    processor = GPUVectorProcessor(use_gpu=True)
    
    v1 = [1.0, 2.0, 3.0]
    v2 = [4.0, 5.0, 6.0]
    
    print("\nTest 1: Vector Addition")
    result = processor.add_vectors(v1, v2)
    print(f"  {v1} + {v2} = {result}")
    
    print("\nTest 2: Scalar Multiplication")
    result = processor.multiply_vector(v1, 2.0)
    print(f"  {v1} * 2.0 = {result}")
    
    print("\nTest 3: Dot Product")
    result = processor.dot_product(v1, v2)
    print(f"  {v1} · {v2} = {result}")
    
    print("\nTest 4: Vector Magnitude")
    result = processor.magnitude(v1)
    print(f"  |{v1}| = {result:.3f}")
    
    print("\nTest 5: Vector Normalization")
    result = processor.normalize(v1)
    print(f"  normalize({v1}) = {[f'{x:.3f}' for x in result]}")
    
    print("\nTest 6: Batch Operations")
    vectors1 = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
    vectors2 = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
    result = processor.batch_add(vectors1, vectors2)
    print(f"  Batch add {len(vectors1)} vectors")
    for i, r in enumerate(result):
        print(f"    {vectors1[i]} + {vectors2[i]} = {r}")
    
    print("\n" + "="*60)
    print("Performance Statistics:")
    stats = processor.get_performance_stats()
    print(f"  Device: {stats['device']}")
    print(f"  Total Operations: {stats['total_operations']}")
    print(f"  Total Time: {stats['total_time']*1000:.3f}ms")
    print(f"  Average Time: {stats['average_time']*1000:.6f}ms")
    print(f"  Operations by Type:")
    for op_type, count in stats['operations_by_type'].items():
        print(f"    {op_type}: {count}")
    
    # Test ECS Bridge
    print("\n" + "="*60)
    print("Testing ECS Vector Bridge:")
    print("="*60)
    
    bridge = ECSVectorBridge(use_gpu=True)
    
    # Register entities
    bridge.register_entity_vector("entity_1", [1.0, 0.0, 0.0])
    bridge.register_entity_vector("entity_2", [0.0, 1.0, 0.0])
    bridge.register_entity_vector("entity_3", [1.0, 1.0, 0.0])
    
    print("\nRegistered 3 entities with vectors")
    
    # Compute interactions
    interaction = bridge.compute_entity_interaction("entity_1", "entity_3")
    print(f"\nInteraction (entity_1, entity_3): {interaction}")
    
    # Batch update
    entity_ids = ["entity_1", "entity_2", "entity_3"]
    deltas = [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2], [0.3, 0.3, 0.3]]
    bridge.batch_update_entities(entity_ids, deltas)
    
    print("\nAfter batch update:")
    for eid in entity_ids:
        vec = bridge.get_entity_vector(eid)
        print(f"  {eid}: {[f'{x:.1f}' for x in vec]}")
    
    print("\n" + "="*60)
    print("Bridge Statistics:")
    bridge_stats = bridge.get_stats()
    print(f"  Total Entities: {bridge_stats['total_entities']}")
    print(f"  Total Vector Operations: {bridge_stats['processor_stats']['total_operations']}")
