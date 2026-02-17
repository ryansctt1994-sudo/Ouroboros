"""
Runtime Vectorizer Module

Provides runtime vectorization for ECS entities and components,
enabling efficient data processing and transformation.
"""

import numpy as np
from typing import Dict, List, Any, Optional


class RuntimeVectorizer:
    """
    Runtime vectorizer for ECS entities.
    
    Converts entity states and components into optimized vector representations
    for efficient processing in consciousness computation.
    """
    
    def __init__(self, dimensions: int = 7, use_golden_ratio: bool = True):
        """
        Initialize the runtime vectorizer.
        
        Args:
            dimensions: Number of dimensions for vector space (default: 7 for METACUBE)
            use_golden_ratio: Whether to use golden ratio (φ) for scaling
        """
        self.dimensions = dimensions
        self.use_golden_ratio = use_golden_ratio
        self.phi = 1.618033988749895  # Golden ratio
        self.vectors_cache: Dict[str, np.ndarray] = {}
        
    def vectorize(self, entity_data: Dict[str, Any]) -> np.ndarray:
        """
        Vectorize entity data into n-dimensional space.
        
        Args:
            entity_data: Dictionary containing entity attributes
            
        Returns:
            Numpy array representing the vectorized entity
        """
        vector = np.zeros(self.dimensions)
        
        # Extract numeric values from entity data
        numeric_values = []
        for key, value in entity_data.items():
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))
            elif isinstance(value, bool):
                numeric_values.append(1.0 if value else 0.0)
                
        # Fill vector with normalized values
        for i, val in enumerate(numeric_values[:self.dimensions]):
            if self.use_golden_ratio:
                vector[i] = val * (self.phi ** (i / self.dimensions))
            else:
                vector[i] = val
                
        # Normalize vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector
    
    def batch_vectorize(self, entities: List[Dict[str, Any]]) -> np.ndarray:
        """
        Vectorize multiple entities in batch.
        
        Args:
            entities: List of entity data dictionaries
            
        Returns:
            2D numpy array where each row is a vectorized entity
        """
        vectors = []
        for entity_data in entities:
            vectors.append(self.vectorize(entity_data))
        return np.array(vectors)
    
    def compute_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        dot_product = np.dot(vector1, vector2)
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
    
    def cache_vector(self, entity_id: str, vector: np.ndarray) -> None:
        """
        Cache a vector for future retrieval.
        
        Args:
            entity_id: Unique identifier for the entity
            vector: Vector to cache
        """
        self.vectors_cache[entity_id] = vector.copy()
    
    def get_cached_vector(self, entity_id: str) -> Optional[np.ndarray]:
        """
        Retrieve a cached vector.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            Cached vector or None if not found
        """
        return self.vectors_cache.get(entity_id)
    
    def clear_cache(self) -> None:
        """Clear all cached vectors."""
        self.vectors_cache.clear()
