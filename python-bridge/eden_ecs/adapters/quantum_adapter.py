"""
Quantum System Adapter
======================

Adapter that connects QuantumSystem to the ECS validation and vectorization framework.
Enables quantum-ready component mapping, state validation, and integration monitoring.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import time
from typing import Dict, List, Any, Optional
from ..core import System, World, Entity
from ..components import QuantumResonance
from ..systems import QuantumSystem


# Constants
QUANTUM_RESONANCE_FREQUENCY = 750e12  # 750 THz UV
MAX_QUANTUM_AMPLITUDE = 10.0  # Maximum reasonable amplitude


class QuantumSystemAdapter:
    """
    Adapter for QuantumSystem integration with ECS validation framework.
    
    Features:
    - Quantum-ready component mapping
    - Real-time state validation
    - Vector integration
    - Performance monitoring
    """
    
    def __init__(self, quantum_system: QuantumSystem):
        """
        Initialize adapter with QuantumSystem instance.
        
        Args:
            quantum_system: QuantumSystem to adapt
        """
        self.system = quantum_system
        self.adapter_id = f"quantum_adapter_{id(self)}"
        
        # Metrics
        self.total_updates = 0
        self.total_entities_processed = 0
        self.last_update_time = 0.0
        self.avg_update_duration = 0.0
        
        # Validation state
        self.validated_vectors = []
        self.validation_timestamp = 0.0
    
    def get_component_mapping(self) -> Dict[str, str]:
        """
        Get quantum component to vector mapping.
        
        Returns:
            Dictionary mapping component names to vector IDs
        """
        return {
            "QuantumResonance": "eden_ecs.components.QuantumResonance",
            "quantum_phase": "field:phase",
            "amplitude": "field:amplitude",
            "frequency": "field:frequency",
        }
    
    def validate_quantum_state(self, entity: Entity) -> Dict[str, Any]:
        """
        Validate quantum state of an entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            Validation result dictionary
        """
        if not entity.has_component(QuantumResonance):
            return {
                "valid": False,
                "reason": "Missing QuantumResonance component",
                "entity_id": entity.entity_id
            }
        
        quantum = entity.get_component(QuantumResonance)
        
        # Validate quantum parameters
        if quantum.frequency != QUANTUM_RESONANCE_FREQUENCY:
            return {
                "valid": False,
                "reason": f"Invalid frequency: {quantum.frequency} (expected {QUANTUM_RESONANCE_FREQUENCY} Hz)",
                "entity_id": entity.entity_id
            }
        
        if not (0.0 <= quantum.amplitude <= MAX_QUANTUM_AMPLITUDE):
            return {
                "valid": False,
                "reason": f"Amplitude out of range: {quantum.amplitude} (max {MAX_QUANTUM_AMPLITUDE})",
                "entity_id": entity.entity_id
            }
        
        return {
            "valid": True,
            "entity_id": entity.entity_id,
            "quantum_phase": quantum.phase,
            "amplitude": quantum.amplitude
        }
    
    def get_runtime_vectors(self, world: World) -> List[Dict[str, Any]]:
        """
        Extract runtime vectors from quantum entities in the world.
        
        Args:
            world: ECS world
            
        Returns:
            List of runtime vector dictionaries
        """
        vectors = []
        entities = world.query_entities(None, QuantumResonance)
        
        for entity in entities:
            quantum = entity.get_component(QuantumResonance)
            
            # Create runtime vector for this quantum state
            vector = {
                "vector_id": f"runtime.quantum.entity.{entity.entity_id}",
                "type": "component_instance",
                "name": f"QuantumResonance_{entity.entity_id[:8]}",
                "component_type": "QuantumResonance",
                "entity_id": entity.entity_id,
                "entity_name": entity.name,
                "quantum_phase": quantum.phase,
                "amplitude": quantum.amplitude,
                "frequency_hz": quantum.frequency,
                "timestamp": time.time()
            }
            vectors.append(vector)
        
        self.validated_vectors = vectors
        self.validation_timestamp = time.time()
        
        return vectors
    
    def update_with_monitoring(self, world: World, dt: float) -> Dict[str, Any]:
        """
        Update quantum system with integrated monitoring.
        
        Args:
            world: ECS world
            dt: Time delta
            
        Returns:
            Monitoring metrics
        """
        start_time = time.perf_counter()
        
        # Get entity count before update
        entities = world.query_entities(None, QuantumResonance)
        entity_count = len(entities)
        
        # Perform system update
        self.system.update(world, dt)
        
        # Calculate metrics
        update_duration = time.perf_counter() - start_time
        self.total_updates += 1
        self.total_entities_processed += entity_count
        self.last_update_time = update_duration
        
        # Update running average
        alpha = 0.1  # Exponential moving average factor
        self.avg_update_duration = (
            alpha * update_duration + (1 - alpha) * self.avg_update_duration
        )
        
        return {
            "adapter_id": self.adapter_id,
            "system": "QuantumSystem",
            "update_duration_us": update_duration * 1_000_000,
            "entities_processed": entity_count,
            "total_updates": self.total_updates,
            "avg_duration_us": self.avg_update_duration * 1_000_000
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        return {
            "adapter_id": self.adapter_id,
            "system": "QuantumSystem",
            "priority": self.system.priority,
            "total_updates": self.total_updates,
            "total_entities_processed": self.total_entities_processed,
            "last_update_time_us": self.last_update_time * 1_000_000,
            "avg_update_duration_us": self.avg_update_duration * 1_000_000,
            "validated_vectors": len(self.validated_vectors),
            "validation_timestamp": self.validation_timestamp,
            "status": "CONNECTED" if self.total_updates > 0 else "IDLE"
        }
    
    def get_status(self) -> str:
        """Get adapter status string."""
        if self.total_updates == 0:
            return "IDLE"
        elif self.total_updates < 10:
            return "INITIALIZING"
        else:
            return "ACTIVE"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"QuantumSystemAdapter(updates={self.total_updates}, status={self.get_status()})"
